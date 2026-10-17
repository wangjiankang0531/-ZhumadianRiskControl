import http.client, json, threading, unittest
from pathlib import Path
from services.tests import test_api as fixture
from tools.authenticated_portal_server import PortalServer, public_configuration


class PortalGatewayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ApiTests.setUpClass()

    def setUp(self):
        self.probe = fixture.ApiTests()
        self.probe.setUp()
        c = {
            "schema": "xnby.portal.config.v1",
            "mode": "authenticated",
            "oauth": {
                "issuer": "https://qa.identity.invalid",
                "clientId": "qa-client",
                "authorizationEndpoint": "https://qa.identity.invalid/authorize",
                "tokenEndpoint": "https://qa.identity.invalid/token",
                "scope": "spatial:read business:read",
            },
        }
        self.server = PortalServer(("127.0.0.1", 0), self.probe.server.server_port, c)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.probe.tearDown()

    def request(self, path, token=None, method="GET"):
        c = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            c.request(
                method,
                path,
                headers={} if not token else {"Authorization": "Bearer " + token},
            )
            r = c.getresponse()
            return r.status, r.read(), dict(r.getheaders())
        finally:
            c.close()

    def test_same_origin_authorized_proxy(self):
        status, raw, h = self.request("/api/v1/business_records", self.probe.token())
        self.assertEqual(status, 200)
        d = json.loads(raw)
        self.assertEqual(d["total"], 1)
        self.assertEqual(d["items"][0]["businessId"], "a")
        self.assertIn("no-store", h["Cache-Control"])
        self.assertEqual(h["Referrer-Policy"], "no-referrer")

    def test_proxy_without_token_and_cross_enterprise_denied(self):
        self.assertEqual(self.request("/api/v1/spatial_objects")[0], 401)
        self.assertEqual(
            self.request(
                "/api/v1/business_records/QA/enterprise/b", self.probe.token()
            )[0],
            404,
        )

    def test_raw_file_and_source_routes_not_available(self):
        for path in (
            "/layers/default.json",
            "/business/default.json",
            "/spatial/default.json",
            "/layers/sample.json",
            "/business/%64efault.json",
            "/services/examples/api.example.json",
            "/../README.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.request(path)[0], 404)

    def test_configuration_public_and_no_credential_fields(self):
        status, raw, h = self.request("/application/config.json")
        self.assertEqual(status, 200)
        c = json.loads(raw)
        self.assertEqual(c["mode"], "authenticated")
        self.assertNotIn("clientSecret", c["oauth"])
        self.assertIn("frame-ancestors 'none'", h["Content-Security-Policy"])

    def test_head_and_mutations(self):
        status, raw, h = self.request(
            "/api/v1/session", self.probe.token(), method="HEAD"
        )
        self.assertEqual(status, 200)
        self.assertEqual(raw, b"")
        self.assertGreater(int(h["Content-Length"]), 0)
        self.assertEqual(
            self.request("/api/v1/session", self.probe.token(), method="POST")[0], 405
        )

    def test_only_internal_cache_release_post_is_permitted(self):
        path="/api/lod-lease/"+"a"*32+"/release"
        self.assertEqual(self.request(path,method="POST")[0],204)
        for method in ["PUT","PATCH","DELETE","OPTIONS"]:
            self.assertEqual(self.request(path,method=method)[0],405)
        self.assertEqual(self.request("/layers/default.json",method="POST")[0],405)

    def test_configuration_rejects_secrets_and_external_insecure_urls(self):
        p = self.probe.root / "portal.json"
        c = self.server.portal_config.copy()
        c["clientSecret"] = "TEST"
        self.probe.write("portal.json", c)
        with self.assertRaises(ValueError):
            public_configuration(p)
        c = self.server.portal_config.copy()
        c["oauth"] = dict(
            c["oauth"], tokenEndpoint="http://outside.example.invalid/token"
        )
        self.probe.write("portal.json", c)
        with self.assertRaises(ValueError):
            public_configuration(p)


    def configure_focus(self):
        from services.api import Service
        for actor in self.probe.policy['principals']:
            if actor['subject']=='QA-A':actor['permissions'] += ['focus:read','focus:track']
        self.probe.write('policy.json',self.probe.policy)
        self.probe.config['businessDatabase']='focus.sqlite';self.probe.write('config.json',self.probe.config)
        self.probe.server.service=Service(self.probe.root/'config.json')

    def focus_post(self,origin=True,**overrides):
        import uuid
        payload={'enterpriseId':'A','sourceSystem':'GATEWAY-TEST','sourceId':uuid.uuid4().hex,'title':'合成网关验收','description':'模拟','level':'major','flags':['major'],'dueDate':None}
        headers={'Content-Type':'application/json','Idempotency-Key':uuid.uuid4().hex,'Authorization':'Bearer '+self.probe.token(scope='focus:read focus:track')}
        if origin:headers['Origin']=self.server.app_origin
        headers.update(overrides)
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            c.request('POST','/api/v1/focus_issues',json.dumps(payload).encode(),headers)
            r=c.getresponse();return r.status,json.loads(r.read())
        finally:c.close()

    def test_focus_write_proxy_origin_and_authenticated_scope(self):
        self.configure_focus()
        self.assertEqual(self.focus_post(origin=False)[0],403)
        self.assertEqual(self.focus_post(Origin='https://outside.invalid')[0],403)
        self.assertEqual(self.focus_post(Authorization='')[0],401)
        self.assertEqual(self.focus_post(Authorization='Bearer '+self.probe.token())[0],403)
        status,data=self.focus_post();self.assertEqual(status,200,data)
        with self.probe.server.service.focus.transaction() as db:self.assertEqual(db.execute('SELECT count(*) FROM issues').fetchone()[0],1)

    def test_focus_write_proxy_rejects_oversize_and_non_json(self):
        self.configure_focus()
        self.assertEqual(self.focus_post(**{'Content-Length':'32769'})[0],413)
        self.assertEqual(self.focus_post(**{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.focus_post(**{'Idempotency-Key':''})[0],400)
        with self.probe.server.service.focus.transaction() as db:self.assertEqual(db.execute('SELECT count(*) FROM issues').fetchone()[0],0)

    def test_configured_https_origin_survives_reverse_proxy_and_ignores_host(self):
        self.configure_focus();self.server.app_origin='https://risk.example.invalid'
        self.assertEqual(self.focus_post(Host='attacker.invalid')[0],200)
        self.assertEqual(self.focus_post(Origin='https://attacker.invalid',Host='attacker.invalid')[0],403)

    def test_authenticated_handler_cannot_serve_database_raw_snapshot(self):
        from tools.authenticated_portal_server import PortalHandler
        from services.layers import LayerRepository
        previous=PortalHandler.layer_repository
        try:
            PortalHandler.layer_repository=LayerRepository(self.probe.root/'raw.sqlite')
            PortalHandler.layer_repository.import_bytes('zhumadian','default',json.dumps(self.probe.layers).encode(),0)
            self.assertEqual(self.request('/layers/default.json')[0],404)
        finally:PortalHandler.layer_repository=previous

    def test_public_origin_must_be_trusted_https_origin(self):
        path=self.probe.root/'portal.json'
        for origin in ['http://risk.example.invalid','https://risk.example.invalid/route','https://u:p@risk.example.invalid','https://risk.example.invalid?x=1']:
            self.probe.write('portal.json',dict(self.server.portal_config,publicOrigin=origin))
            with self.assertRaises(ValueError):public_configuration(path)
        self.probe.write('portal.json',dict(self.server.portal_config,publicOrigin='https://risk.example.invalid'))
        self.assertEqual(public_configuration(path)['publicOrigin'],'https://risk.example.invalid')


if __name__ == "__main__":
    unittest.main()
