"""Opt-in RAM source routes for the existing landscape HTTP handler.

No fallback from a missing RAM lease to a filesystem cache or producer.
"""
import json
import re
from urllib.parse import parse_qs, unquote, urlsplit
from readonly_source_memory_store import MemoryStoreBusy


class MemorySourceHTTP:
    # Headers and small geometry JSON are separate writes. Avoid loopback
    # Nagle/delayed-ACK stalls without changing files, leases or budgets.
    disable_nagle_algorithm = True
    memory_sources = None

    def _source_plans_enabled(self):
        return self.memory_sources is not None or super()._source_plans_enabled()

    def _leases(self):
        return self.memory_sources if self.memory_sources is not None else super()._leases()

    def _memory_json(self, value, status=200, marker_sha=None):
        raw = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        if status == 202:
            self.send_header("Retry-After", "1")
        if marker_sha:
            self.send_header("X-XNBY-Source-Marker-SHA256", marker_sha)
        self.end_headers()
        self.wfile.write(raw)

    def _memory_error(self, error):
        if isinstance(error, MemoryStoreBusy):
            return self.send_error(503, "Source memory budget busy; keep complete current layer")
        if isinstance(error, (FileNotFoundError, PermissionError, TimeoutError)):
            return self.send_error(409, "Read-only source unavailable; keep complete current layer")
        return self.send_error(422, "Original source identity failed; no filesystem producer attempted")

    def _readonly_plan(self, tile, *, depth=None, parent=None):
        if self.memory_sources is None:
            return super()._readonly_plan(tile, depth=depth, parent=parent)
        if urlsplit(self.path).query:
            return self.send_error(400)
        try:
            result = self.memory_sources.plan(tile, depth=depth, parent=parent)
            self._memory_json(result if result is not None else {"status": "preparing_source_memory"},
                              200 if result is not None else 202)
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

