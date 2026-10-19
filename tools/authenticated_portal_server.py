"""Loopback same-origin gateway for configured OAuth/public-client portal integration."""

import argparse, http.client, http.server, json, re, sys, threading
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).parents[1]))
from services.common import read_json, fields, text
from services.focus_materials import MATERIAL_JSON_LIMIT
from tools.landscape_web_server import Handler as LandscapeHandler, ROOT


def public_configuration(path):
    c = read_json(path, 16384)
    fields(c, ["schema", "mode", "oauth", "development", "publicOrigin"], ["schema", "mode", "oauth"])
    if (
        c["schema"] != "xnby.portal.config.v1"
        or c["mode"] != "authenticated"
        or type(c.get("development", False)) is not bool
    ):
        raise ValueError("invalid portal configuration")
    if "publicOrigin" in c:
        u=urlsplit(c["publicOrigin"])
        if u.scheme!="https" or not u.hostname or u.username or u.password or u.path or u.query or u.fragment:
            raise ValueError("publicOrigin must be a pinned HTTPS origin")
    o = c["oauth"]
    fields(
        o,
        ["issuer", "clientId", "authorizationEndpoint", "tokenEndpoint", "scope"],
        ["issuer", "clientId", "authorizationEndpoint", "tokenEndpoint", "scope"],
    )
    for name, value in o.items():
        text(value, 2048)
    for name in ("issuer", "authorizationEndpoint", "tokenEndpoint"):
        u = urlsplit(o[name])
        if (
            u.username
            or u.password
            or u.fragment
            or u.query
            or not u.hostname
            or u.scheme != "https"
            and not (
                name != "issuer"
                and c.get("development")
                and u.scheme == "http"
                and u.hostname in ("127.0.0.1", "localhost", "::1")
            )
        ):
            raise ValueError("invalid OAuth URL")
    return c


class PortalHandler(LandscapeHandler):
    allow_local_layer_database=False
    def log_message(self, *args):
        pass  # Callback query codes and Authorization are never logged.

    def output(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def proxy(self):
        material=re.fullmatch(r'/api/v1/focus_issues/[a-f0-9]{32}/materials(?:/[a-f0-9]{32})?',urlsplit(self.path).path)
        slot=None
        if material:
            if not self.server.material_slots.acquire(blocking=False):return self.output(429,{'error':'MATERIAL_BUSY'})
            slot=self.server.material_slots
        try:return self._proxy_body()
        finally:
            if slot is not None:slot.release()

    def _proxy_body(self):
        mutation = self.command == "POST" and re.fullmatch(r"/api/v1/focus_issues(?:/[a-f0-9]{32}/(?:feedback|track|review|archive|reopen|materials))?",urlsplit(self.path).path)
        if self.command not in ("GET", "HEAD") and not mutation:
            return self.output(405, {"error": "METHOD_NOT_ALLOWED"})
        body = None
        if mutation:
            if self.headers.get_all("Origin",[]) != [self.server.app_origin]:
                return self.output(403,{"error":"ORIGIN_REQUIRED"})
            sizes = self.headers.get_all("Content-Length",[])
            if self.headers.get("Transfer-Encoding") or len(sizes)!=1 or not re.fullmatch(r"[0-9]{1,8}",sizes[0]):
                return self.output(400,{"error":"INVALID_REQUEST"})
            material_upload=bool(re.fullmatch(r'/api/v1/focus_issues/[a-f0-9]{32}/materials',urlsplit(self.path).path))
            if not 1<=int(sizes[0])<=(MATERIAL_JSON_LIMIT if material_upload else 32768):return self.output(413,{"error":"BODY_TOO_LARGE"})
            if material_upload and (len(self.headers.get_all('Authorization',[]))!=1 or not self.headers['Authorization'].startswith('Bearer ') or len(self.headers['Authorization'])>16400):return self.output(401,{'error':'UNAUTHENTICATED'})
            if self.headers.get_all("Content-Type",[]) not in (["application/json"],["application/json; charset=utf-8"]):
                return self.output(415,{"error":"JSON_REQUIRED"})
            if len(self.headers.get_all("Idempotency-Key",[]))!=1:return self.output(400,{"error":"IDEMPOTENCY_KEY_REQUIRED"})
            body=self.rfile.read(int(sizes[0]))
            if len(body)!=int(sizes[0]):return self.output(400,{"error":"INVALID_REQUEST"})
        elif self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length","0")!="0":
            return self.output(400,{"error":"INVALID_REQUEST"})
        headers = self.headers.get_all("Authorization", [])
        if len(headers) > 1:
            return self.output(401, {"error": "UNAUTHENTICATED"})
        if headers and len(headers[0]) > 16400:
            return self.output(401, {"error": "UNAUTHENTICATED"})
        forwarded = {"Accept": "application/json"}
        if headers:
            forwarded["Authorization"] = headers[0]
        if mutation:
            forwarded.update({"Content-Type":"application/json","Idempotency-Key":self.headers["Idempotency-Key"]})
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.api_port, timeout=15
        )
        try:
            connection.request("POST" if mutation else "GET", self.path, body=body, headers=forwarded)
            response = connection.getresponse()
            data = response.read(16 * 1048576 + 1)
            if len(data) > 16 * 1048576:
                return self.output(503, {"error": "DATA_TOO_LARGE"})
            self.send_response(response.status)
            for name in ("Content-Type", "WWW-Authenticate", "X-Request-Id", "Allow", "Content-Disposition", "X-XNBY-Material-SHA256", "X-XNBY-Authorization-Version", "Retry-After"):
                value = response.getheader(name)
                if value:
                    self.send_header(name, value)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Vary", "Authorization")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)
        except (OSError, http.client.HTTPException):
            self.output(503, {"error": "CONNECTION_FAILED"})
        finally:
            connection.close()

    def do_GET(self):
        route = unquote(urlsplit(self.path).path)
        if route == "/application/config.json":
            return self.output(200, self.server.portal_config)
        if route.startswith("/api/v1/"):
            return self.proxy()
        return super().do_GET()

    def do_HEAD(self):
        route = unquote(urlsplit(self.path).path)
        if route == "/application/config.json":
            return self.output(200, self.server.portal_config)
        if route.startswith("/api/v1/"):
            return self.proxy()
        return super().do_HEAD()

    def do_POST(self):
        if self.command=="POST" and re.fullmatch(r"/api/v1/focus_issues(?:/[a-f0-9]{32}/(?:feedback|track|review|archive|reopen|materials))?",urlsplit(self.path).path):
            return self.proxy()
        if self.command == "POST" and re.fullmatch(r"/api/lod-lease/[0-9a-f]{32}/release",urlsplit(self.path).path):
            return super().do_POST()
        return self.output(405, {"error": "METHOD_NOT_ALLOWED"})

    do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_POST

    def translate_path(self, path):
        route = unquote(urlsplit(path).path).lstrip("/")
        if route.startswith(("layers/", "business/", "spatial/")):
            return str(ROOT / "work/portal_file_route_disabled")
        return super().translate_path(path)

    def end_headers(self):
        endpoint = urlsplit(self.server.portal_config["oauth"]["tokenEndpoint"])
        token_origin = f"{endpoint.scheme}://{endpoint.netloc}"
        self.send_header(
            "Content-Security-Policy",
            f"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self' {token_origin}; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        http.server.SimpleHTTPRequestHandler.end_headers(self)


class PortalServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, api_port, configuration, handler=PortalHandler):
        self.material_slots=threading.BoundedSemaphore(2)
        self.api_port = api_port
        self.portal_config = configuration
        super().__init__(address, handler)
        self.app_origin = configuration.get("publicOrigin",f"http://127.0.0.1:{self.server_port}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--portal-config", required=True)
    p.add_argument("--api-port", type=int, default=8780)
    p.add_argument("--port", type=int, default=8781)
    a = p.parse_args()
    if not 1 <= a.port <= 65535 or not 1 <= a.api_port <= 65535:
        p.error("invalid port")
    try:
        c = public_configuration(Path(a.portal_config))
    except Exception:
        p.exit(2, "Portal OAuth configuration invalid or unavailable.\n")
    handler = PortalHandler
    handler.python = ROOT / "runtime/python/python.exe"
    if not handler.python.exists():
        handler.python = (
            Path.home()
            / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
        )
    server = PortalServer(("127.0.0.1", a.port), a.api_port, c)
    print(f"XNBY authenticated portal http://127.0.0.1:{a.port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
