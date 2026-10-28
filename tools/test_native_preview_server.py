"""HTTP/lifecycle contract checks with tiny fixtures; not a landscape rendering test."""
from pathlib import Path
from urllib.request import build_opener,ProxyHandler,Request
from urllib.error import HTTPError
import unittest,tempfile,subprocess,sys,time,json,hashlib

class PreviewServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='preview server ');self.root=Path(self.tmp.name)
        self.bundle=self.root/'bundle';self.resources=self.root/'resources';self.project=self.root/'project.json';self.state=self.root/'state.json'
        for rel in ['web/index.html','web/viewer.js','web/source-gain-worker.js']:
            file=self.bundle/rel;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'fixture')
        for rel in ['data/showcase/zhumadian_native_hierarchy.json','assets/landscape/icons.png','assets/showcase/runtime/zhumadian/context/context_fused.gltf','assets/showcase/runtime/zhumadian/context/context_fused.bin','assets/showcase/runtime/zhumadian/context/context_colormatched.jpg','assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf','assets/showcase/runtime/zhumadian/full/zhumadian_full.bin','assets/showcase/runtime/zhumadian/full/zhumadian_full_atlas.jpg','assets/showcase/runtime/zhumadian/full/base_lod_quality.json']:
            file=self.resources/rel;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(b'not-rendered-http-fixture')
        self.project.write_bytes(b'{"revision":1}');(self.root/'secret.txt').write_bytes(b'MUST_NOT_BE_SERVED')
        self.script=Path(__file__).with_name('serve_native_preview.py')
        self.args=[sys.executable,'-I','-B',str(self.script),'--bundle',str(self.bundle),'--resources',str(self.resources),'--layers',str(self.project),'--state',str(self.state),'--no-browser']
        self.flags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0
        self.process=subprocess.Popen(self.args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=self.flags)
        deadline=time.monotonic()+5
        while not self.state.exists():
            if self.process.poll() is not None:raise AssertionError('Server exited before ready')
            if time.monotonic()>deadline:raise AssertionError('Server readiness timeout')
            time.sleep(.02)
        self.saved=json.loads(self.state.read_text(encoding='utf-8'));self.url='http://127.0.0.1:'+str(self.saved['port']);self.http=build_opener(ProxyHandler({}))
    def request(self,path,method='GET',headers=None):
        try:
            response=self.http.open(Request(self.url+path,method=method,data=b'' if method=='POST' else None,headers=headers or {}),timeout=3)
        except HTTPError as error:response=error
        with response:return response.status,response.read(),response.headers
    def stop(self):
        p=subprocess.run([sys.executable,'-I','-B',str(self.script),'--stop','--state',str(self.state)],capture_output=True,timeout=5,creationflags=self.flags)
        self.assertEqual(p.returncode,0);self.process.wait(timeout=5)
    def tearDown(self):
        try:
            if self.process.poll() is None:self.stop()
            self.assertEqual(self.process.returncode,0)
            if self.process.stderr:self.process.stderr.close()
        finally:self.tmp.cleanup()
    def test_reads_latest_project_without_mutation_or_cache(self):
        status,data,headers=self.request('/layers/default.json');self.assertEqual(status,200);self.assertEqual(data,b'{"revision":1}');self.assertEqual(headers['Cache-Control'],'no-store')
        self.project.write_bytes(b'{"revision":2}')
        self.assertEqual(self.request('/layers/default.json')[:2],(200,b'{"revision":2}'))
        self.assertEqual(self.project.read_bytes(),b'{"revision":2}')
    def test_traversal_and_source_files_are_not_exposed(self):
        for path in ['/%2e%2e/secret.txt','/serve_native_preview.py','/state.json']:
            status,body,_=self.request(path);self.assertEqual(status,404);self.assertNotIn(b'MUST_NOT_BE_SERVED',body)
    def test_foreign_host_is_rejected(self):
        self.assertEqual(self.request('/__preview__/health',headers={'Host':'unrelated.invalid'})[0],403)
    def test_stop_requires_control_and_same_origin(self):
        self.assertEqual(self.request('/__preview__/stop','POST')[0],403)
        self.assertEqual(self.request('/__preview__/stop','POST',{'X-Preview-Key':self.saved['controlKey'],'Origin':'https://unrelated.invalid'})[0],403)
        self.assertEqual(self.request('/__preview__/health')[0],200)
    def test_duplicate_start_reuses_existing_owner(self):
        before=self.state.read_bytes();p=subprocess.run(self.args,capture_output=True,timeout=5,creationflags=self.flags)
        self.assertEqual(p.returncode,0);self.assertEqual(self.state.read_bytes(),before);self.assertIsNone(self.process.poll())
    def test_owned_stop_exits_without_changing_project(self):
        before=self.project.read_bytes();self.stop();state=json.loads(self.state.read_text(encoding='utf-8'))
        self.assertTrue(state['stopped']);self.assertNotIn('controlKey',state);self.assertEqual(self.project.read_bytes(),before)

if __name__=='__main__':unittest.main()
