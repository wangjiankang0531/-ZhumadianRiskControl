"""Opt-in RAM source routes for the existing landscape HTTP handler.

No fallback from a missing RAM lease to a filesystem cache or producer.
"""
import json
import re
from urllib.parse import parse_qs, unquote, urlsplit
from readonly_source_memory_store import MemoryStoreBusy, MemoryStoreClosed, MAX_PLAN_WAIT_MS


class MemorySourceHTTP:
    # Headers and small geometry JSON are separate writes. Avoid loopback
    # Nagle/delayed-ACK stalls without changing files, leases or budgets.
    disable_nagle_algorithm = True
    memory_sources = None

    def _source_plans_enabled(self):
        return self.memory_sources is not None or super()._source_plans_enabled()

    def _leases(self):
        return self.memory_sources if self.memory_sources is not None else super()._leases()

    def _memory_json(self, value, status=200, marker_sha=None, plan_wait_ms=None):
        raw = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        if status == 202:
            self.send_header("Retry-After", "1")
        if plan_wait_ms is not None:
            self.send_header("X-XNBY-Source-Plan-Wait-Ms", str(plan_wait_ms))
        if marker_sha:
            self.send_header("X-XNBY-Source-Marker-SHA256", marker_sha)
        self.end_headers()
        self.wfile.write(raw)

    def _memory_error(self, error):
        if isinstance(error, MemoryStoreBusy):
            return self.send_error(503, "Source memory budget busy; keep complete current layer")
        if isinstance(error, (FileNotFoundError, PermissionError, TimeoutError, MemoryStoreClosed)):
            return self.send_error(409, "Read-only source unavailable; keep complete current layer")
        return self.send_error(422, "Original source identity failed; no filesystem producer attempted")

    @staticmethod
    def _plan_wait_ms(query):
        if "wait_ms" not in query:
            return 0
        values = query["wait_ms"]
        if (len(values) != 1 or not re.fullmatch(r"0|[1-9][0-9]{0,2}", values[0])
                or int(values[0]) > MAX_PLAN_WAIT_MS):
            raise ValueError("invalid bounded plan wait")
        return int(values[0])

    def do_GET(self):
        if self.memory_sources is None:
            return super().do_GET()
        parsed = urlsplit(self.path)
        # The legacy filesystem handler rejects all plan queries. Intercept
        # only RAM plans, leaving its producer/authorization policy unchanged.
        if parsed.path.startswith(("/api/lod-plan/", "/api/lod-family-plan/")):
            root = re.fullmatch(r"/api/lod-plan/([0-9]{1,4})/([0-9]{1,2})", parsed.path)
            family = re.fullmatch(r"/api/lod-family-plan/([0-9]{1,4})/(Tile_[0-9]+_L[0-9]+_0[0-9u]+\.osgb)", parsed.path)
            if root:
                tile, depth = map(int, root.groups())
                if not 1 <= tile <= 2346 or not 1 <= depth <= 12:
                    return self.send_error(400)
                return self._readonly_plan(tile, depth=depth)
            if family:
                tile, parent = int(family[1]), family[2]
                if not 1 <= tile <= 2346 or not parent.startswith(f"Tile_{tile}_"):
                    return self.send_error(400)
                return self._readonly_plan(tile, parent=parent)
            return self.send_error(400)
        return super().do_GET()

    def _readonly_plan(self, tile, *, depth=None, parent=None):
        if self.memory_sources is None:
            return super()._readonly_plan(tile, depth=depth, parent=parent)
        try:
            query = parse_qs(urlsplit(self.path).query, strict_parsing=True,
                             max_num_fields=1, keep_blank_values=True)
            if set(query) - {"wait_ms"}:
                raise ValueError("unknown plan query")
            wait_ms = self._plan_wait_ms(query)
        except ValueError:
            return self.send_error(400)
        try:
            result = self.memory_sources.plan(tile, depth=depth, parent=parent, wait_ms=wait_ms)
            self._memory_json(result if result is not None else {"status": "preparing_source_memory"},
                              200 if result is not None else 202,
                              plan_wait_ms=wait_ms if "wait_ms" in query else None)
        except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
            self._memory_error(error)

    def _readonly_bundle(self, tile, *, depth=None, parent=None):
        if self.memory_sources is None:
            return super()._readonly_bundle(tile, depth=depth, parent=parent)
        if urlsplit(self.path).query:
            return self.send_error(400)
        token = None
        try:
            granted = self.memory_sources.grant(tile, depth=depth, parent=parent)
            if granted is None:
                return self._memory_json({"status": "preparing_source_memory"}, 202)
            marker, digest = granted
            token = marker["cache_lease"]
            self._memory_json(marker, marker_sha=digest)
        except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
            if token:
                self.memory_sources.release(token)
            self._memory_error(error)

    def _native_response(self, head=False):
        if self.memory_sources is None:
            return super()._native_response(head)
        route = unquote(urlsplit(self.path).path)
        if route != "/native" and not route.startswith("/native/"):
            return False
        match = re.fullmatch(r"/native/(tile_[0-9]+_depth_[0-9]+|family_tile_[0-9]+_[0-9a-f]{16})/(part_[0-9]{3})/(geometry\.(?:gltf|bin)|texture\.png)", route)
        if not match:
            self.send_error(400)
            return True
        try:
            query = parse_qs(urlsplit(self.path).query, strict_parsing=True, max_num_fields=1)
            if set(query) != {"lease"} or len(query["lease"]) != 1:
                raise ValueError("one lease is mandatory")
            raw, media = self.memory_sources.payload(query["lease"][0], *match.groups())
            self.send_response(200)
            self.send_header("Content-Type", media)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if not head:
                self.wfile.write(raw)
        except (ValueError, RuntimeError, KeyError, TypeError, OSError) as error:
            self._memory_error(error)
        return True

