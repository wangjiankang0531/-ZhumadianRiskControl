"""Explicit synthetic OAuth+PKCE manual QA; cannot load production identity configuration."""

import argparse, base64, hashlib, html, json, secrets, sys, threading, time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit, urlencode

sys.path.insert(0, str(Path(__file__).parents[1]))
from services.tests.test_api import ApiTests
from services.api import Service
from services.auth import PERMISSIONS
from services.data import fingerprint
from tools.authenticated_portal_server import PortalServer, PortalHandler
from tools.landscape_web_server import ROOT


class QAHandler(PortalHandler):
    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/qa/oauth/selection.js":
            raw = b"document.querySelectorAll('form').forEach(form=>form.addEventListener('submit',async event=>{event.preventDefault();const button=form.querySelector('button');button.disabled=true;try{const response=await fetch(form.action,{method:'POST',credentials:'omit',redirect:'error',headers:{'Content-Type':'application/x-www-form-urlencoded','Accept':'application/json'},body:new URLSearchParams(new FormData(form)).toString()});const result=await response.json();if(!response.ok||!result.redirect)throw Error('QA_LOGIN_FAILED');location.assign(result.redirect);}catch{button.disabled=false;document.getElementById('qa-note').textContent='Login failed. Please return to the application and try again.';}}));"
            self.send_response(200)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if route == "/qa/oauth/authorize":
            try:
                q = parse_qs(
                    urlsplit(self.path).query, strict_parsing=True, max_num_fields=12
                )
                if set(q) - {
                    "response_type",
                    "client_id",
                    "redirect_uri",
                    "scope",
                    "state",
                    "code_challenge",
                    "code_challenge_method",
                    "prompt",
                } or any(len(v) != 1 for v in q.values()):
                    raise ValueError()
                q = {k: v[0] for k, v in q.items()}
                if (
                    q.get("response_type") != "code"
                    or q.get("client_id") != "qa-client"
                    or q.get("redirect_uri") not in (self.server.app_origin + "/",self.server.app_origin + "/portal.html",self.server.app_origin + "/gas.html")
                    or q.get("code_challenge_method") != "S256"
                    or not q.get("scope") or not set(q["scope"].split()) <= PERMISSIONS
                    or len(q.get("state", "")) > 128
                    or not q.get("state")
                    or len(q.get("code_challenge", "")) != 43
                ):
                    raise ValueError()
                transaction = secrets.token_urlsafe(32)
                with self.server.qa_lock:
                    self.server.transactions = {
                        k: v
                        for k, v in self.server.transactions.items()
                        if time.time() - v["at"] < 300
                    }
                    if len(self.server.transactions) > 128:
                        raise ValueError()
                    self.server.transactions[transaction] = {
                        "parameters": q,
                        "at": time.time(),
                    }
                page = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="referrer" content="no-referrer"><title>信能本源 · 独立联调验收</title><style>body{font-family:Microsoft YaHei,sans-serif;background:#101b29;color:#e8eff8;margin:40px;max-width:660px}button{background:#193e51;color:#70e3ed;border:1px solid #406374;border-radius:8px;padding:15px;margin:7px}p{line-height:1.8;color:#adc1d2}</style><h1>独立联调验收</h1><p>此页面使用临时合成账号和数据，验证统一登录跳转、PKCE 和企业权限。没有连接生产身份平台，也不收集密码。</p>'
                for subject, label, life in [
                    ("QA-A", "验收 A 企业", 300),
                    ("QA-B", "验收 B 企业", 300),
                    ("QA-PUBLIC", "验收公共点位账号", 300),
                    ("QA-FEEDBACK", "模拟A企业 · 反馈人员", 300),
                    ("QA-READER", "模拟A企业 · 只读人员", 300),
                    ("QA-A", "验收 A 企业 · 15秒有效", 15),
                ]:
                    if life==300:label=getattr(self.server,'qa_role_labels',{}).get(subject,label)
                    page += f'<form method="post" action="/qa/oauth/select"><input type="hidden" name="transaction" value="{html.escape(transaction)}"><input type="hidden" name="subject" value="{subject}"><input type="hidden" name="lifetime" value="{life}"><button>{label}</button></form>'
                raw = (
                    page
                    + '<p id="qa-note" role="alert"></p><script src="/qa/oauth/selection.js" defer></script></html>'
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            except (ValueError, KeyError):
                return self.output(400, {"error": "QA_AUTH_REQUEST_INVALID"})
        if route == "/qa/status":
            return self.output(
                200,
                {
                    "stage": "XNBY business portal QA 0.7",
                    "synthetic": True,
                    "productionIdentityConnected": False,
                },
            )
        return super().do_GET()

    def do_POST(self):
        route = urlsplit(self.path).path
        if route not in ("/qa/oauth/select", "/qa/oauth/token"):
            return super().do_POST()
        if self.headers.get("Origin") != self.server.app_origin or self.headers.get(
            "Transfer-Encoding"
        ):
            return self.output(403, {"error": "QA_ORIGIN_REQUIRED"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 1 <= size <= 8192:
                raise ValueError()
            q = parse_qs(
                self.rfile.read(size).decode("utf-8"),
                strict_parsing=True,
                max_num_fields=8,
            )
            if any(len(v) != 1 for v in q.values()):
                raise ValueError()
            q = {k: v[0] for k, v in q.items()}
            if route.endswith("/select"):
                if (
                    set(q) != {"transaction", "subject", "lifetime"}
                    or q["subject"] not in ("QA-A", "QA-B", "QA-PUBLIC", "QA-FEEDBACK", "QA-READER")
                    or q["lifetime"] not in ("15", "300")
                ):
                    raise ValueError()
                with self.server.qa_lock:
                    transaction = self.server.transactions.pop(q["transaction"], None)
                if not transaction or time.time() - transaction["at"] > 300:
                    raise ValueError()
                code = secrets.token_urlsafe(32)
                with self.server.qa_lock:
                    self.server.codes = {
                        k: v
                        for k, v in self.server.codes.items()
                        if time.time() - v["at"] < 60
                    }
                    if len(self.server.codes) > 128:
                        raise ValueError()
                    self.server.codes[code] = {
                        "parameters": transaction["parameters"],
                        "subject": q["subject"],
                        "lifetime": int(q["lifetime"]),
                        "at": time.time(),
                    }
                params = transaction["parameters"]
                callback = (
                    params["redirect_uri"]
                    + "?"
                    + urlencode(
                        {
                            "code": code,
                            "state": params["state"],
                            "iss": "https://qa.identity.invalid",
                        }
                    )
                )
                if self.headers.get("Accept") == "application/json":
                    return self.output(200, {"redirect": callback})
                self.send_response(303)
                self.send_header("Location", callback)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if (
                set(q)
                != {"grant_type", "client_id", "redirect_uri", "code_verifier", "code"}
                or q["grant_type"] != "authorization_code"
                or q["client_id"] != "qa-client"
                or q["redirect_uri"] not in (self.server.app_origin + "/",self.server.app_origin + "/portal.html",self.server.app_origin + "/gas.html")
            ):
                raise ValueError()
            with self.server.qa_lock:
                record = self.server.codes.pop(q["code"], None)
            if not record or q["redirect_uri"] != record["parameters"]["redirect_uri"] or time.time() - record["at"] > 60:
                raise ValueError()
            challenge = (
                base64.urlsafe_b64encode(
                    hashlib.sha256(q["code_verifier"].encode("ascii")).digest()
                )
                .rstrip(b"=")
                .decode()
            )
            if (
                len(q["code_verifier"]) < 43
                or challenge != record["parameters"]["code_challenge"]
            ):
                raise ValueError()
            now = int(time.time())
            lifetime = record["lifetime"]
            token = self.server.probe.token(
                record["subject"],
                iat=now,
                exp=now + lifetime,
                jti=secrets.token_urlsafe(16),
                scope=record["parameters"]["scope"],
            )
            return self.output(
                200,
                {"access_token": token, "token_type": "Bearer", "expires_in": lifetime},
            )
        except (ValueError, KeyError, UnicodeError):
            return self.output(400, {"error": "QA_AUTH_EXCHANGE_INVALID"})


def configure_fixture(probe, focus_path=None):
    a = probe.layers["layers"][0]["features"][0]
    b = probe.layers["layers"][0]["features"][1]
    public = probe.layers["layers"][0]["features"][2]
    a.update(name="独立验收 · A企业", positions=[[-520, -2240, 65]])
    b.update(name="独立验收 · B企业计量位置", positions=[[-100, -2240, 65]])
    public.update(
        name="独立验收 · 公共区域",
        type="region",
        positions=[
            [-620, -2300, 65],
            [-480, -2300, 65],
            [-480, -2160, 65],
            [-620, -2160, 65],
        ],
    )
    road = {
        "id": "qa-road-a",
        "name": "独立验收 · A企业道路",
        "type": "line",
        "positions": [[-520, -2240, 65], [-340, -2240, 65], [-340, -2120, 65]],
        "business": {
            "sourceSystem": "QA",
            "objectType": "road",
            "businessId": "road-a",
            "enterpriseId": "A",
        },
        "style": {"pattern": "dash", "color": "#FBBF24", "widthPx": 5},
    }
    probe.layers["layers"][0]["features"] = [a, b, public, road]
    for record in probe.records["records"]:
        record["name"] = "独立验收 · " + record["enterpriseId"] + "企业台账"
        record["attributes"] = [
            {"label": "数据用途", "value": "合成联调验收，非正式监管数据"}
        ]
    probe.records["records"].append(
        {
            "sourceSystem": "QA",
            "objectType": "road",
            "businessId": "road-a",
            "enterpriseId": "A",
            "name": "独立验收 · A企业道路记录",
            "updatedAt": probe.records["exportedAt"],
            "attributes": [{"label": "数据用途", "value": "合成联调验收"}],
        }
    )
    if focus_path is not None:
        for owner,point in [("A",[-380,-2110,65]),("B",[-190,-2110,65])]:
            probe.layers["layers"][0]["features"].append({"id":"qa-focus-"+owner.lower(),"name":"模拟"+owner+"企业重点问题位置","type":"point","positions":[point],"business":{"sourceSystem":"QA","objectType":"hidden-danger","businessId":"focus-"+owner.lower(),"enterpriseId":owner},"style":{"icon":"warning","color":"#F97316"}})
    from services.focus import FocusStore
    from services.focus_demo import seed
    probe.service.focus=FocusStore(focus_path or probe.root/"focus.sqlite")
    seed(probe.service.focus,{owner:"qa-focus-"+owner.lower() for owner in ("A","B")} if focus_path is not None else {})
    for person in probe.policy["principals"]:
        if person["subject"] in ("QA-A","QA-B","QA-ADMIN"):
            person["permissions"] += ["focus:read","focus:track"]
    probe.policy["principals"] += [
        {"subject":"QA-FEEDBACK","enabled":True,"permissions":["spatial:read","business:read","focus:read","focus:feedback"],"enterprises":["A"]},
        {"subject":"QA-READER","enabled":True,"permissions":["spatial:read","business:read","focus:read"],"enterprises":["A"]}]
    probe.write("policy.json",probe.policy)
    probe.write("layers.json", probe.layers)
    probe.write("business.json", probe.records)
    catalog = {
        "schema": "xnby.spatial.catalog.v1",
        "scene": "zhumadian",
        "layerFingerprint": fingerprint(probe.layers),
        "exportedAt": probe.records["exportedAt"],
        "objects": [
            {"spatialId": "b", "category": "energy-meter", "themes": ["energy"]},
            {"spatialId": "public", "category": "public-area"},
        ],
    }
    probe.write("spatial.json", catalog)
    probe.service.store.paths["spatial"] = probe.root / "spatial.json"
    if focus_path is not None:
        from services.layers import LayerRepository
        repository=LayerRepository(focus_path)
        try:version=repository.get("QA")["revision"]
        except Exception:version=0
        repository.import_bytes("QA","default",json.dumps(probe.layers,ensure_ascii=False).encode("utf-8"),version)
        probe.service.store.layer_repository=repository
        probe.service.store.layer_document="default"
        probe.service.store.layer_tenant="QA"



def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8790)
    a = p.parse_args()
    if not 1 <= a.port <= 65535:
        p.error("invalid port")
    ApiTests.setUpClass()
    probe = ApiTests()
    probe.setUp()
    try:
        configure_fixture(probe, ROOT / "work/focus_qa/focus.sqlite")
        origin = f"http://127.0.0.1:{a.port}"
        c = {
            "schema": "xnby.portal.config.v1",
            "mode": "authenticated",
            "development": True,
            "oauth": {
                "issuer": "https://qa.identity.invalid",
                "clientId": "qa-client",
                "authorizationEndpoint": origin + "/qa/oauth/authorize",
                "tokenEndpoint": origin + "/qa/oauth/token",
                "scope": "spatial:read business:read focus:read focus:track focus:feedback",
            },
        }
        QAHandler.python = ROOT / "runtime/python/python.exe"
        if not QAHandler.python.exists():
            QAHandler.python = (
                Path.home()
                / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
            )
        server = PortalServer(
            ("127.0.0.1", a.port), probe.server.server_port, c, QAHandler
        )
        server.app_origin = origin
        server.probe = probe
        server.qa_lock = threading.Lock()
        server.transactions = {}
        server.codes = {}
        print(f"XNBY SYNTHETIC QA ONLY http://127.0.0.1:{a.port}/", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    finally:
        probe.tearDown()


if __name__ == "__main__":
    main()
