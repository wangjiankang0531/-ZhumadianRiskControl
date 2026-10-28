from pathlib import Path
import os,sys,tempfile,time,unittest
if os.name=='nt':
    from serve_original_server_release import Child,regular_tree_path,wait_for,require_children_running

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

    def test_ready_poll_preserves_live_state_and_polls_each_child_once(self):
        class Process:
            pid=123
            calls=0
            def poll(self):self.calls+=1;return None
        class Live:
            name='synthetic-live'
            process=Process()
        child=Live();state={'ready':True}
        require_children_running([child],state)
        self.assertEqual(child.process.calls,1);self.assertEqual(state,{'ready':True})

    def test_first_zero_exit_is_saved_before_other_owned_child_cleanup(self):
        with tempfile.TemporaryDirectory(prefix='owned-ready-exit-') as temp:
            root=Path(temp)
            first=Child('synthetic-first',[sys.executable,'-I','-B','-c','pass'],root,dict(os.environ))
            other=Child('synthetic-other',[sys.executable,'-I','-B','-c','import time; time.sleep(30)'],root,dict(os.environ))
            state={'ready':True}
            try:
                self.assertEqual(first.process.wait(timeout=5),0)
                self.assertIsNone(other.process.poll())
                with self.assertRaisesRegex(AssertionError,'OWN_COMPONENT_EXITED_AFTER_READY'):
                    require_children_running([first,other],state)
                self.assertEqual(state['unexpectedChildExits'],[{'component':'synthetic-first','PID':first.process.pid,'exitCode':0}])
                observed=state['unexpectedChildExitObservedAt'];snapshot=list(state['unexpectedChildExits'])
                other.close_job();other.process.wait(timeout=5)
                with self.assertRaisesRegex(AssertionError,'OWN_COMPONENT_EXITED_AFTER_READY'):
                    require_children_running([first,other],state)
                self.assertEqual(state['unexpectedChildExits'],snapshot)
                self.assertEqual(state['unexpectedChildExitObservedAt'],observed)
                self.assertTrue(state['ready'])  # Historical ready flag keeps its original meaning.
            finally:
                for child in [other,first]:
                    child.close_job()
                    if child.process.poll() is None:child.process.kill()
                    child.process.wait(timeout=5);child.thread.join(timeout=3)

    def test_real_nonzero_exit_is_recorded_without_log_or_command_content(self):
        with tempfile.TemporaryDirectory(prefix='owned-nonzero-exit-') as temp:
            child=Child('synthetic-seven',[sys.executable,'-I','-B','-c','raise SystemExit(7)'],Path(temp),dict(os.environ))
            state={}
            try:
                self.assertEqual(child.process.wait(timeout=5),7)
                with self.assertRaisesRegex(AssertionError,'OWN_COMPONENT_EXITED_AFTER_READY'):
                    require_children_running([child],state)
                row=state['unexpectedChildExits'][0]
                self.assertEqual(row,{'component':'synthetic-seven','PID':child.process.pid,'exitCode':7})
                self.assertEqual(set(state),{'unexpectedChildExits','unexpectedChildExitObservedAt'})
            finally:child.close_job();child.thread.join(timeout=3)

if __name__=='__main__':unittest.main()
