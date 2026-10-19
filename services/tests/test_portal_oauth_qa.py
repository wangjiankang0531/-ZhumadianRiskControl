import base64, hashlib, http.client, json, threading, unittest
from urllib.parse import urlencode, urlsplit, parse_qs
from services.tests import test_api as fixture
from tools.authenticated_portal_server import PortalServer
from tools.serve_business_portal_qa import QAHandler, configure_fixture


class PortalOAuthQATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.ApiTests.setUpClass()

    def setUp(self):
        self.probe = fixture.ApiTests()
        self.probe.setUp()
        configure_fixture(self.probe)
        c = {
            "schema": "xnby.portal.config.v1",
            "mode": "authenticated",
            "development": True,
            "oauth": {
                "issuer": "https://qa.identity.invalid",
                "clientId": "qa-client",
                "authorizationEndpoint": "http://127.0.0.1/authorize",
                "tokenEndpoint": "http://127.0.0.1/token",
                "scope": "spatial:read business:read",
            },
        }
        self.server = PortalServer(
            ("127.0.0.1", 0), self.probe.server.server_port, c, QAHandler
        )
        self.server.app_origin = f"http://127.0.0.1:{self.server.server_port}"
        self.server.probe = self.probe
        self.server.qa_lock = threading.Lock()
        self.server.transactions = {}
        self.server.codes = {}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.verifier = "A" * 64
        self.challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(self.verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.probe.tearDown()

    def request(self, path, method="GET", values=None, origin=True):
        c = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        headers = {"Accept": "application/json"}
        body = None
        if values is not None:
            body = urlencode(values)
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        if origin:
            headers["Origin"] = self.server.app_origin
        try:
            c.request(method, path, body=body, headers=headers)
            r = c.getresponse()
            raw = r.read()
            return r.status, raw, dict(r.getheaders())
        finally:
            c.close()

    def authorization(self):
        params = {
            "response_type": "code",
            "client_id": "qa-client",
            "redirect_uri": self.server.app_origin + "/",
            "scope": "spatial:read business:read",
            "state": "QA-STATE",
            "code_challenge": self.challenge,
            "code_challenge_method": "S256",
        }
        status, raw, _ = self.request("/qa/oauth/authorize?" + urlencode(params))
        self.assertEqual(status, 200)
        self.assertIn(b"/qa/oauth/selection.js", raw)
        return next(iter(self.server.transactions))

    def select(self):
        transaction = self.authorization()
        status, raw, _ = self.request(
            "/qa/oauth/select",
            "POST",
            {"transaction": transaction, "subject": "QA-A", "lifetime": "300"},
        )
        self.assertEqual(status, 200)
        callback = json.loads(raw)["redirect"]
        q = parse_qs(urlsplit(callback).query)
        self.assertEqual(q["state"], ["QA-STATE"])
        self.assertEqual(q["iss"], ["https://qa.identity.invalid"])
        return q["code"][0]

    def exchange(self, code, verifier=None):
        return self.request(
            "/qa/oauth/token",
            "POST",
            {
                "grant_type": "authorization_code",
                "client_id": "qa-client",
                "redirect_uri": self.server.app_origin + "/",
                "code": code,
                "code_verifier": verifier or self.verifier,
            },
        )

    def test_pkce_code_exchange_and_one_use_only(self):
        code = self.select()
        status, raw, _ = self.exchange(code)
        self.assertEqual(status, 200)
        token = json.loads(raw)["access_token"]
        claims = self.probe.service.jwt.verify(token)
        self.assertEqual(claims["sub"], "QA-A")
        self.assertEqual(self.exchange(code)[0], 400)

    def test_wrong_pkce_verifier_and_untrusted_origin_rejected(self):
        code = self.select()
        self.assertEqual(self.exchange(code, "B" * 64)[0], 400)
        self.assertEqual(
            self.request(
                "/qa/oauth/select",
                "POST",
                {"transaction": "unknown", "subject": "QA-A", "lifetime": "300"},
                origin=False,
            )[0],
            403,
        )

    def test_redirect_and_client_are_pinned(self):
        q = {
            "response_type": "code",
            "client_id": "qa-client",
            "redirect_uri": "https://attacker.invalid/",
            "state": "QA",
            "code_challenge": self.challenge,
            "code_challenge_method": "S256",
        }
        self.assertEqual(self.request("/qa/oauth/authorize?" + urlencode(q))[0], 400)

    def test_expired_code_and_unknown_identity_rejected(self):
        code = self.select()
        self.server.codes[code]["at"] -= 61
        self.assertEqual(self.exchange(code)[0], 400)
        transaction = self.authorization()
        self.assertEqual(
            self.request(
                "/qa/oauth/select",
                "POST",
                {
                    "transaction": transaction,
                    "subject": "PRODUCTION-ADMIN",
                    "lifetime": "300",
                },
            )[0],
            400,
        )


    def test_portal_callback_and_requested_scope_bound_to_code(self):
        params={'response_type':'code','client_id':'qa-client','redirect_uri':self.server.app_origin+'/portal.html','scope':'focus:read','state':'QA-PORTAL','code_challenge':self.challenge,'code_challenge_method':'S256'}
        self.assertEqual(self.request('/qa/oauth/authorize?'+urlencode(params))[0],200)
        transaction=next(iter(self.server.transactions))
        status,raw,_=self.request('/qa/oauth/select','POST',{'transaction':transaction,'subject':'QA-A','lifetime':'300'});self.assertEqual(status,200)
        callback=json.loads(raw)['redirect'];self.assertEqual(urlsplit(callback).path,'/portal.html')
        code=parse_qs(urlsplit(callback).query)['code'][0]
        self.assertEqual(self.exchange(code)[0],400)
        # A mismatched redirect consumes the code; a fresh transaction can exchange correctly.
        self.assertEqual(self.request('/qa/oauth/authorize?'+urlencode(params))[0],200)
        transaction=next(iter(self.server.transactions));status,raw,_=self.request('/qa/oauth/select','POST',{'transaction':transaction,'subject':'QA-A','lifetime':'300'})
        code=parse_qs(urlsplit(json.loads(raw)['redirect']).query)['code'][0]
        status,raw,_=self.request('/qa/oauth/token','POST',{'grant_type':'authorization_code','client_id':'qa-client','redirect_uri':self.server.app_origin+'/portal.html','code':code,'code_verifier':self.verifier})
        self.assertEqual(status,200,raw);claims=self.probe.service.jwt.verify(json.loads(raw)['access_token']);self.assertEqual(claims['scope'],'focus:read')


    def test_gas_callback_and_scope_keep_pkce_and_exact_redirect_binding(self):
        params={'response_type':'code','client_id':'qa-client','redirect_uri':self.server.app_origin+'/gas.html','scope':'gas:read gas:verify','state':'QA-GAS','code_challenge':self.challenge,'code_challenge_method':'S256'}
        self.assertEqual(self.request('/qa/oauth/authorize?'+urlencode(params))[0],200)
        transaction=next(iter(self.server.transactions));status,raw,_=self.request('/qa/oauth/select','POST',{'transaction':transaction,'subject':'QA-A','lifetime':'300'});self.assertEqual(status,200);callback=json.loads(raw)['redirect'];self.assertEqual(urlsplit(callback).path,'/gas.html');code=parse_qs(urlsplit(callback).query)['code'][0]
        status,raw,_=self.request('/qa/oauth/token','POST',{'grant_type':'authorization_code','client_id':'qa-client','redirect_uri':self.server.app_origin+'/gas.html','code':code,'code_verifier':self.verifier});self.assertEqual(status,200,raw);claims=self.probe.service.jwt.verify(json.loads(raw)['access_token']);self.assertEqual(claims['scope'],'gas:read gas:verify');self.assertEqual(self.exchange(code)[0],400)
        params['scope']='gas:approve';self.assertEqual(self.request('/qa/oauth/authorize?'+urlencode(params))[0],400)

if __name__ == "__main__":
    unittest.main()
