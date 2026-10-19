"""Read-only R1 API prototype; run behind an HTTPS gateway for production integration."""

import argparse, json, re, threading, uuid, hashlib
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs, unquote
from .common import ApiError, fields, read_json, text, relative, strings
from .auth import JwtVerifier, Policy
from .data import FileStore, CATEGORIES, TOPICS, BUSINESS
from .focus import FocusStore
from .layers import LayerRepository
from . import focus_http, gas_http
from .gas_repository import GasRepository


class Service:
    def __init__(self, config_path):
        path = Path(config_path).resolve()
        c = read_json(path, 1024 * 1024)
        fields(
            c,
            ["schema", "jwt", "policyFile", "data", "auditFile", "businessDatabase", "gas"],
            ["schema", "jwt", "policyFile", "data", "auditFile"],
        )
        if c["schema"] != "xnby.api.config.v1":
            raise ValueError("invalid API configuration")
        self.jwt = JwtVerifier(c["jwt"], path.parent)
        self.policy = Policy(relative(path.parent, c["policyFile"]), self.jwt.tenant)
        self.store = FileStore(c["data"], path.parent)
        self.audit_file = relative(path.parent, c["auditFile"])
        self.focus = FocusStore(relative(path.parent,c["businessDatabase"])) if "businessDatabase" in c else None
        self.gas=None
        if 'gas' in c:
            if self.focus is None:raise ValueError('gas requires a business database')
            g=c['gas'];fields(g,['sourceSystem','sourceSubjects','emergencySystem','resultSubjects'],['sourceSystem','sourceSubjects','emergencySystem','resultSubjects'])
            self.gas=GasRepository(self.focus.path,source_system=g['sourceSystem'],source_subjects=strings(g['sourceSubjects'],100),emergency_system=g['emergencySystem'],result_subjects=strings(g['resultSubjects'],100))
        if self.focus and "layerDocument" in c["data"]:
            self.store.layer_repository=LayerRepository(self.focus.path)
            self.store.layer_tenant=self.jwt.tenant
        self.audit_lock = threading.Lock()
        self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        with self.audit_file.open("a", encoding="utf-8"):
            pass

    def audit(self, request_id, route, status, principal, code):
        entry = {
            "requestId": request_id,
            "at": datetime.now(timezone.utc).isoformat(),
            "route": route,
            "status": status,
            "code": code,
        }
        if principal:
            entry.update(
                subject=principal.subject, policyVersion=principal.policy_version
            )
        try:
            with self.audit_lock, self.audit_file.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            raise ApiError(503, "AUDIT_UNAVAILABLE") from None

    def query(self, raw, allowed):
        try:
            if len(raw) > 4096 or re.search(r"%(?![0-9a-fA-F]{2})", raw):
                raise ValueError("invalid query")
            parsed = parse_qs(
                raw,
                keep_blank_values=True,
                strict_parsing=True,
                encoding="utf-8",
                errors="strict",
                max_num_fields=12,
            )
            if set(parsed) - set(allowed) or any(len(v) != 1 for v in parsed.values()):
                raise ValueError("unknown or duplicate query")
            result = {}
            for k, v in parsed.items():
                value = v[0]
                if k in ("offset", "limit"):
                    if not re.fullmatch(r"[0-9]{1,6}", value):
                        raise ValueError("invalid page")
                    result[k] = int(value)
                    if (
                        k == "limit"
                        and not 1 <= result[k] <= 200
                        or k == "offset"
                        and result[k] > 10000
                    ):
                        raise ValueError("invalid page")
                else:
                    result[k] = text(
                        value, 128 if k == "sourceSystem" else 256, k != "search"
                    )
            if (
                "topic" in result
                and result["topic"] not in TOPICS
                or "category" in result
                and result["category"] not in CATEGORIES
                and result["category"] != "unregistered"
                or "objectType" in result
                and result["objectType"] not in BUSINESS
            ):
                raise ValueError("invalid filter")
            return result
        except (ValueError, TypeError, UnicodeError):
            raise ApiError(400, "INVALID_QUERY") from None

    def dispatch(self, handler):
        if handler.path.startswith(gas_http.PREFIX):
            return gas_http.dispatch(self,handler)
        if handler.path.startswith(focus_http.PREFIX):
            return focus_http.dispatch(self,handler)
        request_id = uuid.uuid4().hex
        principal = None
        route = "unknown"
        status = 200
        code = "OK"
        try:
            if len(handler.path) > 8192 or any(ord(ch) < 32 for ch in handler.path):
                raise ApiError(400, "INVALID_REQUEST")
            url = urlsplit(handler.path)
            if url.scheme or url.netloc or url.fragment:
                raise ApiError(400, "INVALID_REQUEST")
            path = url.path
            if path == "/api/v1/health":
                route = "health"
            elif path == "/api/v1/session":
                route = "session"
            elif path == "/api/v1/spatial_objects":
                route = "spatial_objects"
            elif path == "/api/v1/business_records":
                route = "business_records"
            elif path.startswith("/api/v1/business_records/"):
                route = "business_record"
            else:
                raise ApiError(404, "NOT_FOUND")
            if handler.command not in ("GET", "HEAD"):
                raise ApiError(405, "METHOD_NOT_ALLOWED")
            if (
                handler.headers.get("Transfer-Encoding")
                or handler.headers.get("Content-Length", "0") != "0"
            ):
                raise ApiError(400, "INVALID_REQUEST")
            if route == "health":
                self.query(url.query, [])
                result = {
                    "service": "XNBY Zhumadian API",
                    "version": "0.3.0",
                    "status": "running",
                }
            else:
                headers = handler.headers.get_all("Authorization", [])
                if (
                    len(headers) != 1
                    or not headers[0].startswith("Bearer ")
                    or len(headers[0]) > 16400
                ):
                    raise ApiError(401, "UNAUTHENTICATED")
                claims = self.jwt.verify(headers[0][7:])
                principal = self.policy.principal(claims)
                if route == "session":
                    self.query(url.query, [])
                    result = {
                        "subject": principal.subject,
                        "tenant": principal.tenant,
                        "permissions": sorted(principal.permissions),
                        "enterprises": sorted(principal.enterprises),
                        "allEnterprises": principal.all_enterprises,
                        "publicSpatial": principal.public_spatial,
                        "policyVersion": principal.policy_version,
                        "expiresAt": claims["exp"],
                        "gasWorkflow": self.gas is not None,
                        "focusMaterials": self.focus is not None and callable(getattr(self.focus,"add_material",None)),
                    }
                elif route == "spatial_objects":
                    result = self.store.spatial(
                        principal,
                        self.query(
                            url.query,
                            [
                                "topic",
                                "category",
                                "enterpriseId",
                                "search",
                                "offset",
                                "limit",
                            ],
                        ),
                    )
                elif route == "business_records":
                    result = self.store.business(
                        principal,
                        self.query(
                            url.query,
                            [
                                "objectType",
                                "sourceSystem",
                                "enterpriseId",
                                "search",
                                "offset",
                                "limit",
                            ],
                        ),
                    )
                else:
                    self.query(url.query, [])
                    segments = path.split("/")[4:]
                    if len(segments) != 3 or any(
                        re.search(r"%(?![0-9a-fA-F]{2})", s) for s in segments
                    ):
                        raise ApiError(404, "NOT_FOUND")
                    try:
                        record_key = tuple(
                            text(
                                unquote(s, encoding="utf-8", errors="strict"), 256, True
                            )
                            for s in segments
                        )
                    except (ValueError, UnicodeError):
                        raise ApiError(400, "INVALID_REQUEST") from None
                    result = self.store.business(principal, {}, record_key)
            body = {"requestId": request_id, **result}
            if principal:
                body["policyVersion"] = principal.policy_version
                effective = {
                    "subject": principal.subject,
                    "tenant": principal.tenant,
                    "permissions": sorted(principal.permissions),
                    "enterprises": sorted(principal.enterprises),
                    "allEnterprises": principal.all_enterprises,
                    "publicSpatial": principal.public_spatial,
                    "policyVersion": principal.policy_version,
                    "publicSpatialIds": (
                        sorted(self.store.public) if principal.public_spatial else []
                    ),
                }
                body["authorizationVersion"] = hashlib.sha256(
                    json.dumps(
                        effective,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()
        except ApiError as error:
            status, code = error.status, error.code
            body = {"requestId": request_id, "error": code}
        except Exception:
            status, code = 503, "SERVICE_UNAVAILABLE"
            body = {"requestId": request_id, "error": code}
        try:
            self.audit(request_id, route, status, principal, code)
        except ApiError:
            status = 503
            body = {"requestId": request_id, "error": "AUDIT_UNAVAILABLE"}
        raw = json.dumps(
            body, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
        handler.send_response(status)
        for k, v in {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(raw)),
            "Cache-Control": "no-store",
            "Vary": "Authorization",
            "X-Content-Type-Options": "nosniff",
            "X-Request-Id": request_id,
        }.items():
            handler.send_header(k, v)
        if status == 401:
            handler.send_header("WWW-Authenticate", "Bearer")
        if status == 405:
            handler.send_header("Allow", "GET, HEAD")
        handler.end_headers()
        if handler.command != "HEAD":
            handler.wfile.write(raw)


class Handler(BaseHTTPRequestHandler):
    server_version = "XNBY"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionError, TimeoutError):
            pass

    def do_GET(self):
        self.server.service.dispatch(self)

    do_HEAD = do_POST = do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_GET


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, service):
        self.service = service
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(address, Handler)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", type=int, default=8780)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be 1..65535")
    try:
        service = Service(args.config)
    except Exception:
        parser.exit(
            2, "API configuration invalid or unavailable; no service started.\n"
        )
    server = Server(("127.0.0.1", args.port), service)
    print(
        f"XNBY API 0.3 listening on http://127.0.0.1:{args.port}/api/v1/health",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
