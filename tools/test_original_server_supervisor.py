from pathlib import Path
import os,sys,tempfile,time,unittest
if os.name=='nt':
    from serve_original_server_release import Child,regular_tree_path,wait_for

@unittest.skipUnless(os.name=='nt','Windows server supervisor')
class Supervisor(unittest.TestCase):
    def test_log_is_bounded_and_original_child_exits_normally(self):
        with tempfile.TemporaryDirectory(prefix='owned-server-log-') as temp:
            root=Path(temp)
            child=Child('synthetic',[sys.executable,'-B','-c','import os; os.write(1,b"x"*2097152); os.write(1,b"TAIL-END")'],root,dict(os.environ))
            try:
                self.assertEqual(child.process.wait(timeout=5),0);child.thread.join(timeout=3);self.assertFalse(child.thread.is_alive())
                data=(root/'synthetic.private.log').read_bytes();self.assertEqual(len(data),1024*1024);self.assertTrue(data.endswith(b'TAIL-END'));self.assertEqual(child.job.limit_flags,8192)
            finally:child.close_job()
    def test_owned_path_traversal_rejected(self):
        with self.assertRaises(ValueError):regular_tree_path(Path('D:/q/Application/../outside'),Path('D:/q/Application'))
    def test_external_path_rejected(self):
        with self.assertRaises(ValueError):regular_tree_path(Path('C:/Windows/file'),Path('D:/q/Application'))
    def test_wait_reports_real_child_exit(self):
        class Process:
            def poll(self):return 9
        class Exited:process=Process()
        with self.assertRaisesRegex(RuntimeError,'OWN_COMPONENT_EXITED'):wait_for(lambda:False,[Exited()],1,'synthetic')
    def test_wait_timeout_without_process_mutation(self):
        with self.assertRaisesRegex(RuntimeError,'OWN_COMPONENT_TIMEOUT'):wait_for(lambda:False,[],.01,'synthetic')

if __name__=='__main__':unittest.main()
