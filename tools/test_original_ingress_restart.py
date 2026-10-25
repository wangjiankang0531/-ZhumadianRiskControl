"""Exercise real installer/rollback file flow with simulated process and TLS edges.

No IIS, database, original backend, browser, or native process is started.
"""
from pathlib import Path
import contextlib,hashlib,json,os,subprocess,sys,tempfile,unittest
from unittest.mock import patch,Mock
if os.name!='nt':raise unittest.SkipTest('Windows installer process boundary contract')
import install_original_server_ingress as installer
from original_iis_cutover import apply

class SocketFixture:
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def setsockopt(self,*args):pass
    def bind(self,*args):pass

class RestartOwnership(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ingress-restart-')
        self.base=Path(self.tmp.name).resolve();self.app=self.base/'Application';self.app.mkdir()
        self.iis=self.base/'iis';(self.iis/'App_Code').mkdir(parents=True)
        self.data=self.app/'UserData/OriginalDeployment';self.data.mkdir(parents=True)
        self.old_run=self.app/'UserData/OriginalServer/runs/j1';self.old_run.mkdir(parents=True)
        self.new_run=self.old_run.parent/'j2';self.new_run.mkdir()
        self.current=self.old_run.parent.parent/'current-run.json'
        self.release='8fb77ca1-c206-4690-8509-cc6285704d01'
        self.old_pid=42001;self.new_pid=42002;self.icon=b'<svg xmlns="http://www.w3.org/2000/svg"/>'
        manifest=self.app/'release-manifest.json';manifest.write_text(json.dumps({'schema':'zhumadian.original.server.release.v1','releaseId':self.release,'controllerFiles':{}}))
        self.pin=hashlib.sha256(manifest.read_bytes()).hexdigest()
        icon=self.app/'deploy/branding/zhumadian-emergency.svg';icon.parent.mkdir(parents=True);icon.write_bytes(self.icon)
        source=self.app/'deploy/iis_original/App_Code/XnbyReferenceProxy.cs';source.parent.mkdir(parents=True);source.write_bytes(b'// inert compiler fixture')
        key='b'*64
        template='<configuration><appSettings><add key="XnbyIngressKey" value="REPLACE_WITH_PRIVATE_64_HEX_KEY" /></appSettings></configuration>'
        (source.parent.parent/'web.config.template').write_text(template)
        self.old={'web.config':b'<configuration>old fixture</configuration>','App_Code/XnbyReferenceProxy.cs':b'// old fixture'}
        self.new={'web.config':template.replace('REPLACE_WITH_PRIVATE_64_HEX_KEY',key).encode(),'App_Code/XnbyReferenceProxy.cs':source.read_bytes()}
        for rel,data in self.old.items():(self.iis/rel).write_bytes(data)
        self.backup=self.data/'first-deployment/iis-backup';apply(self.iis,self.backup,self.new,lambda:True)
        self.active_path=self.data/'active-deployment.private.json'
        self.old_binding={'releaseId':self.release,'backup':str(self.backup),'controllerPID':self.old_pid,'run':str(self.old_run)}
        self.active_path.write_text(json.dumps(self.old_binding))
        self.old_ready={'releaseId':self.release,'controllerPID':self.old_pid,'run':str(self.old_run),'ready':True}
        self.new_ready=dict(self.old_ready,controllerPID=self.new_pid,run=str(self.new_run))
        self.current.write_text(json.dumps(self.old_ready));self.alive={self.new_pid};self.foreign_during_validate=False
        self.compiler_calls=0;self.launches=0
    def tearDown(self):self.tmp.cleanup()
    def process_start(self,*args,**kwargs):
        self.launches+=1;self.current.write_text(json.dumps(self.new_ready))
        process=Mock();process.pid=self.new_pid;process.poll.return_value=None;return process
    def compiler(self,*args,**kwargs):
        self.compiler_calls+=1;return subprocess.CompletedProcess(args[0],0,b'',b'')
    def http(self,port,route):return (200,b'{"code":200}' if route.endswith('getLoginConfig') else b'<html>fixture</html>')
    def tls(self,address,route):
        if self.foreign_during_validate:
            self.active_path.write_bytes(b'concurrent operator fixture');self.foreign_during_validate=False
        return (200,self.icon) if route.endswith('.svg') else self.http(0,route)
    @contextlib.contextmanager
    def environment(self,rollback=False):
        argv=['installer','--application',str(self.app),'--release-manifest-sha256',self.pin]+(['--rollback'] if rollback else [])
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(sys,'argv',argv))
            stack.enter_context(patch.object(installer,'IIS_ROOT',self.iis))
            stack.enter_context(patch.object(installer,'preflight',return_value='127.0.0.1'))
            stack.enter_context(patch.object(installer,'owned_controller',side_effect=lambda pid,app,pin:pid in self.alive))
            stack.enter_context(patch.object(installer,'http',side_effect=self.http))
            stack.enter_context(patch.object(installer,'tls_local',side_effect=self.tls))
            stack.enter_context(patch.object(installer.subprocess,'run',side_effect=self.compiler))
            stack.enter_context(patch.object(installer.subprocess,'Popen',side_effect=self.process_start))
            stack.enter_context(patch.object(installer.socket,'socket',return_value=SocketFixture()))
            yield
    def assert_iis_unchanged(self,before):
        for rel,(raw,mtime) in before.items():
            self.assertEqual((self.iis/rel).read_bytes(),raw)
            self.assertEqual((self.iis/rel).stat().st_mtime_ns,mtime)
    def snapshot_iis(self):return {rel:((self.iis/rel).read_bytes(),(self.iis/rel).stat().st_mtime_ns) for rel in self.new}
    def test_restart_updates_rollback_owner_without_rewriting_iis(self):
        before=self.snapshot_iis()
        with self.environment():installer.main()
        binding=json.loads(self.active_path.read_bytes())
        self.assertEqual(binding['controllerPID'],self.new_pid)
        self.assertEqual(binding['run'],str(self.new_run));self.assertEqual(binding['backup'],str(self.backup))
        self.assertEqual(self.launches,1);self.assert_iis_unchanged(before)
    def test_rollback_after_restart_stops_new_owner_and_restores_old_entry(self):
        with self.environment():installer.main()
        with self.environment(rollback=True):installer.main()
        self.assertTrue((self.new_run/'stop-requested.txt').is_file())
        self.assertFalse((self.old_run/'stop-requested.txt').exists())
        for rel,raw in self.old.items():self.assertEqual((self.iis/rel).read_bytes(),raw)
    def test_live_same_owner_is_idempotent(self):
        self.alive={self.old_pid};before=self.active_path.read_bytes();mtime=self.active_path.stat().st_mtime_ns
        before_iis=self.snapshot_iis()
        with self.environment():installer.main()
        self.assertEqual(self.launches,0);self.assertEqual(self.active_path.read_bytes(),before)
        self.assertEqual(self.active_path.stat().st_mtime_ns,mtime);self.assert_iis_unchanged(before_iis)
    def test_concurrent_binding_edit_is_not_overwritten(self):
        self.current.write_text(json.dumps(self.new_ready));self.foreign_during_validate=True
        before=self.snapshot_iis()
        with self.environment(),self.assertRaisesRegex(ValueError,'DEPLOYMENT_OWNER_CHANGED'):installer.main()
        self.assertEqual(self.active_path.read_bytes(),b'concurrent operator fixture')
        self.assert_iis_unchanged(before);self.assertEqual(self.launches,0)
    def test_run_outside_owned_runs_is_refused(self):
        outside=self.base/'outside-run';outside.mkdir();self.new_ready['run']=str(outside)
        self.current.write_text(json.dumps(self.new_ready));before=self.active_path.read_bytes()
        with self.environment(),self.assertRaisesRegex(ValueError,'OWNED_READY_CONTROLLER_REQUIRED'):installer.main()
        self.assertEqual(self.active_path.read_bytes(),before);self.assertEqual(self.launches,0)

if __name__=='__main__':unittest.main()
