import http.server,json,threading,unittest
from unittest.mock import patch
from tools import launch_selected_release as launch
from tools.test_release_catalog import CatalogTests


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.fixture=CatalogTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.fixture.choose('new',0);self.catalog=self.fixture.catalog
        self.rootPatch=patch.object(launch,'ROOT',self.fixture.root);self.rootPatch.start();self.addCleanup(self.rootPatch.stop)
        self.viewer=b'new';self.plan=self.catalog.plan('web');self.health={'application':'xnby.landscape.web.v1',**launch.identity(self.plan)}
        owner=self
        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps(owner.health).encode() if self.path=='/api/health' else owner.viewer)
        self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.close)
    def close(self):self.server.shutdown();self.server.server_close();self.thread.join()
    def reuse(self,page='scene'):
        with patch.object(launch.webbrowser,'open') as browser:
            code=launch.launch_web(self.catalog,self.server.server_port,page,True);browser.assert_not_called();return code
    def test_matching_version_data_and_viewer_reuses(self):self.assertEqual(self.reuse(),0)
    def test_portal_reuses_the_same_selected_service(self):self.assertEqual(self.reuse('portal'),0)
    def test_same_version_wrong_data_rejected(self):
        self.health['dataBinding']='wrong'
        with self.assertRaisesRegex(RuntimeError,'端口'):self.reuse()
        self.assertFalse((self.fixture.root/'work/release_logs').exists())
    def test_same_identity_wrong_viewer_rejected(self):
        self.viewer=b'other'
        with self.assertRaisesRegex(RuntimeError,'端口'):self.reuse()
    def test_unadapted_legacy_service_is_not_silently_reused(self):
        del self.health['controller']
        with self.assertRaisesRegex(RuntimeError,'端口'):self.reuse()
    def test_binding_uses_installation_paths_and_survives_save(self):
        first=launch.binding(self.plan['selected']);self.fixture.layers.write_text('edited')
        self.assertEqual(first,launch.binding(self.plan['selected']))
    def test_explicit_qa_entry_uses_selected_runtime_and_separate_port(self):
        import sys
        with patch.object(sys,'argv',['launch_selected_release.py','--state',str(self.catalog.state),'--kind','qa','--port','8812','--no-browser']),patch.object(launch.subprocess,'call',return_value=0) as call:
            self.assertEqual(launch.main(),0)
            command=call.call_args.args[0]
            self.assertIn(str(self.fixture.root/'Packages/new/tools/launch_business_portal_qa.py'),command)
            self.assertEqual(command[command.index('--port')+1],'8812')
            self.assertIn('--no-browser',command)
    def test_startup_revision_change_refuses_before_importing_server(self):
        with self.assertRaisesRegex(RuntimeError,'Selection changed'):
            launch.serve(self.catalog,999,self.server.server_port)


if __name__=='__main__':unittest.main()
