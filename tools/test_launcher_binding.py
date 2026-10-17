import hashlib
import http.server
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from tools.landscape_web_server import layer_data_binding


class LauncherBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); (self.root/'tools').mkdir()
        source=Path(__file__).with_name('launch_landscape_web.py')
        self.script=self.root/'tools/launch_landscape_web.py'; self.script.write_bytes(source.read_bytes())
        self.layers=self.root/'layers.json';self.layers.write_text('{}');self.db=self.root/'layers.sqlite'
        self.viewer=b'known viewer'; self.manifest=json.dumps({'files':[{'path':'apps/landscape_web/dist/viewer.js','sha256':hashlib.sha256(self.viewer).hexdigest()}]}).encode()
        (self.root/'package.json').write_bytes(self.manifest)
        owner=self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.end_headers()
                self.wfile.write(json.dumps(owner.health).encode() if self.path=='/api/health' else owner.viewer)
        self.health={'application':'xnby.landscape.web.v1','release':{'manifestSha256':hashlib.sha256(self.manifest).hexdigest()},'dataBinding':layer_data_binding(self.layers,self.db)}
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def run_launcher(self):
        return subprocess.run([sys.executable,'-X','utf8',str(self.script),'--no-browser','--port',str(self.server.server_port),'--layers',str(self.layers),'--layer-database',str(self.db)],capture_output=True,timeout=10)
    def test_matching_version_and_binding_reuses_service(self):
        self.assertEqual(self.run_launcher().returncode,0)
    def test_same_version_other_database_is_refused(self):
        self.health['dataBinding']=layer_data_binding(self.layers,self.db.with_name('other.sqlite'))
        result=self.run_launcher();self.assertNotEqual(result.returncode,0)
        self.assertIn('端口'.encode(),result.stderr);self.assertFalse((self.root/'work/web_logs').exists())
    def test_same_version_other_layers_is_refused(self):
        self.health['dataBinding']=layer_data_binding(self.layers.with_name('other.json'),self.db)
        self.assertNotEqual(self.run_launcher().returncode,0)
    def test_legacy_health_without_binding_is_not_reused_when_explicit(self):
        del self.health['dataBinding'];self.assertNotEqual(self.run_launcher().returncode,0)
    def test_saving_same_file_does_not_change_binding(self):
        first=layer_data_binding(self.layers,self.db);self.layers.write_text('{"edited":true}')
        self.assertEqual(layer_data_binding(self.layers,self.db),first)


if __name__=='__main__':unittest.main()
