import hashlib
import http.client
import http.server
import json
from pathlib import Path
import tempfile
import threading
import unittest
from tools import landscape_web_server as web


class ReleaseHealthTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        class Handler(web.Handler):
            def log_message(self,*args):pass
        Handler.root=self.root
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()
    def health(self):
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
        try:
            c.request('GET','/api/health');r=c.getresponse();self.assertEqual(r.status,200);return json.loads(r.read())
        finally:c.close()
    def write(self,version):
        p=self.root/'package.json';p.write_text(json.dumps({'editorVersion':version,'webVersion':'0.8.5','apiVersion':'0.3.0'}));return hashlib.sha256(p.read_bytes()).hexdigest()
    def test_version_and_exact_manifest_are_reported(self):
        digest=self.write('0.9.7');release=self.health()['release']
        self.assertEqual(release,{'editorVersion':'0.9.7','webVersion':'0.8.5','apiVersion':'0.3.0','manifestSha256':digest})
    def test_same_server_tracks_atomically_replaced_manifest(self):
        first=self.write('0.9.7');self.assertEqual(self.health()['release']['manifestSha256'],first)
        p=self.root/'package.pending.json';p.write_text(json.dumps({'editorVersion':'0.9.8'}));p.replace(self.root/'package.json')
        self.assertNotEqual(self.health()['release']['manifestSha256'],first)
        self.assertEqual(self.health()['release']['editorVersion'],'0.9.8')
    def test_data_binding_is_reported_without_revealing_paths(self):
        self.server.RequestHandlerClass.data_binding=web.layer_data_binding(self.root/'layers.json',self.root/'data.sqlite')
        health=self.health()
        self.assertEqual(len(health['dataBinding']),64)
        self.assertNotIn(str(self.root),json.dumps(health))
    def test_data_binding_is_independent_of_manifest_identity(self):
        self.write('0.9.7');handler=self.server.RequestHandlerClass
        handler.data_binding=web.layer_data_binding(self.root/'a.json',self.root/'db.sqlite');first=self.health()
        handler.data_binding=web.layer_data_binding(self.root/'b.json',self.root/'db.sqlite');second=self.health()
        self.assertEqual(first['release'],second['release']);self.assertNotEqual(first['dataBinding'],second['dataBinding'])
    def test_source_server_without_release_keeps_legacy_health_shape(self):
        self.assertEqual(self.health(),{'application':'xnby.landscape.web.v1','scene':'zhumadian'})


if __name__=='__main__':unittest.main()