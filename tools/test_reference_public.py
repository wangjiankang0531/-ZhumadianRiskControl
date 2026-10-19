"""Exercise the real HTTP adapter and SQLite with an isolated test database."""
import http.client
import json
import re
import secrets
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from services.reference_access import AccessGate, password_record
from tools.serve_reference_public import make_public_server, validate_config


class PublicHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = 'Only-For-Local-QA-' + secrets.token_hex(12)
        cls.record = password_record(cls.password)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.static = root/'static'
        self.static.mkdir()
        for name in ('reference-demo.html', 'reference-demo.css', 'reference-demo.js'):
            (self.static/name).write_text('QA-' + name)
        with socket.socket() as s:
            s.bind(('127.0.0.1', 0))
            port = s.getsockname()[1]
        self.config = dict(schema='xnby.reference.public.v1', origin='https://www.joinlinksmart.com', prefix='/zhumadian/', port=port, proxyKey=secrets.token_hex(32), users={'tester':self.record})
        self.database = root/'synthetic.sqlite'
        self.server = make_public_server(self.config, self.static, self.database)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def request(self, path, method='GET', body=None, headers=None, ingress=True):
        base = {'X-XNBY-Ingress':self.config['proxyKey'], 'X-XNBY-Public-Origin':self.config['origin']} if ingress else {}
        base.update(headers or {})
        c = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=8)
        c.request(method, path, body, base)
        r = c.getresponse()
        result = r.status, r.getheaders(), r.read()
        c.close()
        return result

    def login(self, password=None):
        status, headers, raw = self.request('/zhumadian/auth/login')
        self.assertEqual(status, 200)
        cookie = next(value.split(';')[0] for key,value in headers if key.lower() == 'set-cookie')
        csrf = re.search(rb'name="csrf" value="([^"]+)"', raw).group(1).decode()
        form = urlencode(dict(username='tester', password=password or self.password, csrf=csrf))
        return self.request('/zhumadian/auth/login', 'POST', form, {'Origin':self.config['origin'],'Cookie':cookie,'Content-Type':'application/x-www-form-urlencoded'})

    def session(self):
        status, headers, raw = self.login()
        self.assertEqual(status, 303)
        cookies = [value for key,value in headers if key.lower() == 'set-cookie']
        session = next(value for value in cookies if value.startswith('XNBY_TEST_SESSION='))
        for attr in ('Secure','HttpOnly','SameSite=Strict','Path=/zhumadian/'):
            self.assertIn(attr, session)
        return session.split(';')[0]

    def test_authenticated_record_date_scope_matches_list_summary_and_blocks_bad_range(self):
        cookie=self.session();headers={'Cookie':cookie}
        query=urlencode(dict(entity='special-work',enterprise='模拟企业甲',dateFrom='2026-10-13',dateTo='2026-10-15'))
        status,_,raw=self.request('/zhumadian/api/demo/records?'+query,headers=headers)
        self.assertEqual(status,200);listing=json.loads(raw);self.assertEqual(listing['total'],2);self.assertEqual(sum(listing['counts'].values()),2)
        status,_,raw=self.request('/zhumadian/api/demo/summary?'+query,headers=headers)
        self.assertEqual(status,200);self.assertEqual(json.loads(raw)['total'],2)
        self.assertEqual(self.request('/zhumadian/api/demo/records?entity=special-work&dateFrom=2026-02-30',headers=headers)[0],400)
        self.assertEqual(self.request('/zhumadian/api/demo/records?'+query)[0],401)

    def test_every_resource_requires_fixed_ingress_and_login(self):
        for path in ('/zhumadian/', '/zhumadian/reference-demo.js', '/zhumadian/api/demo/catalog'):
            self.assertEqual(self.request(path, ingress=False)[0], 403)
        self.assertEqual(self.request('/api/demo/catalog')[0], 404)
        self.assertEqual(self.request('/zhumadian/')[0], 303)
        self.assertEqual(self.request('/zhumadian/reference-demo.js')[0], 401)
        self.assertEqual(self.request('/zhumadian/api/demo/health')[0], 401)
        self.assertEqual(self.request('/zhumadian/auth/login', headers={'X-XNBY-Ingress':'0'*64})[0], 403)
        self.assertEqual(self.request('/zhumadian/auth/login', headers={'Host':'bad.test'})[0], 403)

    def test_login_cookie_catalog_and_business_flow(self):
        cookie = self.session()
        headers = {'Cookie':cookie}
        status, _, raw = self.request('/zhumadian/api/demo/catalog', headers=headers)
        self.assertEqual(status, 200)
        catalog = json.loads(raw)
        self.assertEqual(catalog['deployment']['mode'], 'public-business')
        self.assertEqual(catalog['deployment']['user'], 'tester')
        self.assertEqual(len(catalog['modules']), 82)
        query = '/zhumadian/api/demo/records?entity=hidden-danger&id=DEMO-HIDDEN-DANGER-001'
        status, _, raw = self.request(query, headers=headers)
        self.assertEqual(status, 200)
        before = json.loads(raw)['record']
        value = dict(entity='hidden-danger', id=before['id'], revision=before['revision'], note='PUBLIC-ADAPTER-QA synthetic only')
        body = json.dumps(value)
        write = dict(headers, **{'Content-Type':'application/json', 'Origin':self.config['origin'], 'X-XNBY-Demo':catalog['token']})
        self.assertEqual(self.request('/zhumadian/api/demo/transition','POST',body,write)[0], 200)
        status, _, raw = self.request(query, headers=headers)
        self.assertEqual(json.loads(raw)['record']['revision'], before['revision']+1)
        self.assertEqual(self.request('/zhumadian/api/demo/transition','POST',body,dict(write, Origin='https://bad.test'))[0],403)
        self.assertEqual(self.request('/zhumadian/api/demo/transition','POST',body,dict(write, **{'X-XNBY-Demo':'wrong'}))[0],403)

    def test_logout_invalidates_session(self):
        cookie = self.session()
        status, _, raw = self.request('/zhumadian/api/demo/catalog', headers={'Cookie':cookie})
        csrf = json.loads(raw)['deployment']['csrf']
        endpoint = '/zhumadian/auth/logout'
        h = {'Cookie':cookie,'Origin':self.config['origin']}
        self.assertEqual(self.request(endpoint,'POST',headers=h)[0],403)
        status, headers, _ = self.request(endpoint,'POST',headers=dict(h, **{'X-XNBY-CSRF':csrf}))
        self.assertEqual(status,204)
        self.assertIn('Max-Age=0', next(v for k,v in headers if k.lower()=='set-cookie'))
        self.assertEqual(self.request('/zhumadian/api/demo/catalog',headers={'Cookie':cookie})[0],401)

    def test_native_login_form_keeps_same_origin_and_rejects_null_origin(self):
        status, headers, raw = self.request('/zhumadian/auth/login')
        self.assertEqual(status, 200)
        self.assertEqual(next(v for k,v in headers if k.lower() == 'referrer-policy'), 'same-origin')
        self.assertIn(b'method="post"', raw)
        self.assertEqual(self.request('/zhumadian/auth/login','POST','x=1',{'Origin':'null','Content-Type':'application/x-www-form-urlencoded'})[0],403)

    def test_wrong_password_and_cross_origin_login_rejected(self):
        self.assertEqual(self.login('wrong-password')[0],401)
        self.assertEqual(self.request('/zhumadian/auth/login','POST','x=1',{'Origin':'https://bad.test'})[0],403)
        self.assertEqual(self.request('/zhumadian/auth/login','POST','x=1',{'Origin':self.config['origin'],'Content-Type':'application/json'})[0],415)

    def test_no_private_config_or_path_alias_exposure(self):
        cookie = self.session()
        for path in ('config/public.json','../config/public.json','%2e%2e/config/public.json','data/synthetic.sqlite','web.config'):
            self.assertEqual(self.request('/zhumadian/'+path,headers={'Cookie':cookie})[0],404)
        self.assertEqual(self.request('/zhumadian/reference-demo.js',headers={'Cookie':cookie})[2],b'QA-reference-demo.js')


class GateTests(unittest.TestCase):
    def test_one_time_challenge_expiry_and_restart(self):
        password = 'Isolated-Session-Expiry-Password'
        now = [0]
        users = {'tester':password_record(password)}
        gate = AccessGate(users, clock=lambda:now[0])
        challenge, csrf = gate.challenge()
        token, error = gate.login(challenge,csrf,'tester',password)
        self.assertIsNone(error)
        self.assertIsNotNone(gate.session(token))
        self.assertEqual(gate.login(challenge,csrf,'tester',password),(None,'invalid'))
        self.assertIsNone(AccessGate(users).session(token))
        now[0] = 28_801
        self.assertIsNone(gate.session(token))
        challenge, csrf = gate.challenge()
        now[0] += 301
        self.assertEqual(gate.login(challenge,csrf,'tester',password),(None,'invalid'))

    def test_config_and_passwords_fail_closed(self):
        for value in ('short', 'x'*129):
            with self.assertRaises(ValueError):password_record(value)
        for users in ({},{'admin':{'password':'plaintext'}},{'../bad':{'salt':'0'*48,'digest':'0'*64}}):
            with self.assertRaises(ValueError):AccessGate(users)
        base = dict(schema='xnby.reference.public.v1',origin='http://example.test',prefix='/zhumadian/',port=18873,proxyKey='0'*64,users={'tester':{'salt':'0'*48,'digest':'0'*64}})
        with self.assertRaises(ValueError):validate_config(base)
        with self.assertRaises(ValueError):validate_config(dict(base,origin='https://example.test',prefix='/'))

    def test_challenges_bounded_and_bad_csrf_does_not_hash(self):
        gate = AccessGate({'tester':{'salt':'0'*48,'digest':'0'*64}})
        challenge, csrf = gate.challenge()
        self.assertEqual(gate.login(challenge,'bad','tester','irrelevant'),(None,'invalid'))
        for _ in range(128):gate.challenge()
        self.assertIsNone(gate.challenge())


if __name__ == '__main__':unittest.main()
