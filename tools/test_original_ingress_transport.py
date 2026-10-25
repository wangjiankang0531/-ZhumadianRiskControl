"""Use real loopback HTTP/TLS to exercise installer transport and trust checks."""
from pathlib import Path
import contextlib, http.server, os, shutil, socket, ssl, subprocess, tempfile, threading, unittest, types, xml.etree.ElementTree as ET
from unittest.mock import patch, Mock
import install_original_server_ingress as installer

class TLSFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='ingress-tls-')
        cls.root = Path(cls.temp.name)
        openssl = shutil.which('openssl') or str(Path(shutil.which('git')).parent.parent / 'usr/bin/openssl.exe')
        cls.cert = cls.root / 'localhost-test.crt'
        cls.key = cls.root / 'localhost-test.key'
        result = subprocess.run([openssl, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
            '-subj', '/CN=www.joinlinksmart.com', '-addext', 'subjectAltName=DNS:www.joinlinksmart.com',
            '-keyout', str(cls.key), '-out', str(cls.cert)], capture_output=True, timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode:
            cls.temp.cleanup()
            raise RuntimeError('Owned test certificate generation failed')
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    @contextlib.contextmanager
    def endpoint(self, tls=False, status=200):
        seen = []
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                seen.append((self.path, self.headers.get('Host')))
                body = b'original-ingress-owned-transport-fixture'
                self.send_response(status); self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        if tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(self.cert, self.key)
            context.set_servername_callback(lambda sock, name, ctx: seen.append(('SNI', name)))
            server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval': .05}, daemon=True)
        thread.start()
        try: yield server.server_port, seen
        finally: server.shutdown(); server.server_close(); thread.join(timeout=5)

    @contextlib.contextmanager
    def route_tls_to(self, port):
        # Keep tls_local and HTTPConnection real. Route only its fixed 443
        # socket to an ephemeral loopback fixture; retain hostname verification.
        real_connect = socket.create_connection
        def connect(address, timeout):
            self.assertEqual(address, ('127.0.0.1', 443))
            return real_connect(('127.0.0.1', port), timeout=timeout)
        with patch.object(installer.socket, 'create_connection', side_effect=connect): yield

class Transport(TLSFixture):
    def test_plain_http_helper_reaches_real_loopback_endpoint(self):
        with self.endpoint() as (port, seen):
            self.assertEqual(installer.http(port, '/zhumadian/home'),
                (200, b'original-ingress-owned-transport-fixture'))
            self.assertEqual(seen, [('/zhumadian/home', '127.0.0.1:' + str(port))])

    def test_tls_helper_preserves_sni_host_and_verified_response(self):
        trusted = ssl.create_default_context(cafile=str(self.cert))
        with self.endpoint(tls=True) as (port, seen), self.route_tls_to(port), \
                patch.object(installer.ssl, 'create_default_context', return_value=trusted):
            self.assertTrue(trusted.check_hostname)
            self.assertEqual(trusted.verify_mode, ssl.CERT_REQUIRED)
            self.assertEqual(installer.tls_local('127.0.0.1', '/zhumadian/'),
                (200, b'original-ingress-owned-transport-fixture'))
            self.assertEqual(seen, [('SNI', 'www.joinlinksmart.com'), ('/zhumadian/', 'www.joinlinksmart.com')])

    def test_tls_helper_rejects_untrusted_certificate(self):
        with self.endpoint(tls=True) as (port, seen), self.route_tls_to(port):
            with self.assertRaises(ssl.SSLCertVerificationError):
                installer.tls_local('127.0.0.1', '/zhumadian/')
            self.assertNotIn(('/zhumadian/', 'www.joinlinksmart.com'), seen)

    def test_tls_helper_rejects_wrong_certificate_hostname(self):
        trusted = ssl.create_default_context(cafile=str(self.cert))
        with self.endpoint(tls=True) as (port, seen), self.route_tls_to(port), \
                patch.object(installer.ssl, 'create_default_context', return_value=trusted), \
                patch.object(installer, 'HOST', 'wrong-host.invalid'):
            with self.assertRaises(ssl.SSLCertVerificationError):
                installer.tls_local('127.0.0.1', '/zhumadian/')
            self.assertFalse(any(path == '/zhumadian/' for path, host in seen))

class Preflight(TLSFixture):
    @contextlib.contextmanager
    def environment(self):
        # Exercise preflight itself. Only machine configuration prerequisites
        # are fixtures; TLS, HTTPConnection, SNI and hostname checking remain real.
        xml = ET.fromstring('<configuration><system.webServer><globalModules>'
            '<add name="WebSocketModule" /></globalModules></system.webServer>'
            '<system.applicationHost><sites><site><application><virtualDirectory physicalPath="'
            + str(installer.IIS_ROOT) + '" /></application><bindings><binding protocol="https" '
            'bindingInformation="*:443:www.joinlinksmart.com" /></bindings></site></sites>'
            '</system.applicationHost></configuration>')
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(installer, 'regular', side_effect=lambda p: p))
            stack.enter_context(patch.object(Path, 'resolve', lambda p, strict=False: p))
            stack.enter_context(patch.object(Path, 'is_file', return_value=True))
            stack.enter_context(patch.object(shutil, 'disk_usage', return_value=types.SimpleNamespace(free=20*1024**3)))
            stack.enter_context(patch.object(installer.winreg, 'OpenKey', return_value=Mock(__enter__=Mock(), __exit__=Mock(return_value=False))))
            stack.enter_context(patch.object(installer.winreg, 'QueryValueEx', return_value=(528040, 4)))
            stack.enter_context(patch.object(installer.ET, 'parse', return_value=ET.ElementTree(xml)))
            child = stack.enter_context(patch.object(installer.subprocess, 'Popen'))
            run = stack.enter_context(patch.object(installer.subprocess, 'run'))
            yield
            child.assert_not_called(); run.assert_not_called()

    def check_status(self, status, accepted):
        report = {}
        trusted = ssl.create_default_context(cafile=str(self.cert))
        with self.endpoint(tls=True, status=status) as (port, seen), self.route_tls_to(port), self.environment(), \
                patch.object(installer.ssl, 'create_default_context', return_value=trusted):
            if accepted:
                self.assertEqual(installer.preflight(Path('C:/Zdm/Application'), installer.IIS_ROOT, report), '127.0.0.1')
                self.assertTrue(report['existingSiteTLSVerified'])
            else:
                with self.assertRaisesRegex(RuntimeError, 'EXISTING_SITE_TLS_PREFLIGHT_FAILED'):
                    installer.preflight(Path('C:/Zdm/Application'), installer.IIS_ROOT, report)
                self.assertNotIn('existingSiteTLSVerified', report)
            self.assertEqual(seen, [('SNI', installer.HOST), ('/zhumadian/', installer.HOST)])
        return report

    def test_actual_303_verified_redirect_is_accepted(self):
        report = self.check_status(303, True)
        self.assertEqual(report['existingSiteHTTPSChecks'], [{'address':'127.0.0.1','httpStatus':303}])

    def test_other_supported_success_and_redirect_statuses_are_accepted(self):
        for status in (200, 301, 302, 307, 308):
            with self.subTest(status=status): self.check_status(status, True)

    def test_authentication_and_server_error_statuses_remain_rejected(self):
        for status in (401, 403, 500):
            with self.subTest(status=status):
                report = self.check_status(status, False)
                self.assertEqual(report['existingSiteHTTPSChecks'], [{'address':'127.0.0.1','httpStatus':status}])

    def test_untrusted_certificate_remains_rejected_and_is_reported(self):
        report = {}
        with self.endpoint(tls=True) as (port, seen), self.route_tls_to(port), self.environment():
            with self.assertRaisesRegex(RuntimeError, 'EXISTING_SITE_TLS_PREFLIGHT_FAILED'):
                installer.preflight(Path('C:/Zdm/Application'), installer.IIS_ROOT, report)
        self.assertNotIn('existingSiteTLSVerified', report)
        self.assertEqual(report['existingSiteHTTPSChecks'][0]['errorType'], 'SSLCertVerificationError')
        self.assertFalse(any(path == '/zhumadian/' for path, host in seen))

if __name__ == '__main__': unittest.main()
