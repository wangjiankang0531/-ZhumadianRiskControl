import io,subprocess,unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from tools import build_zhumadian_stage_asset as worker

class WorkerStartupTests(unittest.TestCase):
 def check(self,results):
  with patch.object(worker.subprocess,'run',side_effect=results) as run,patch.object(worker.time,'sleep') as sleep,patch.object(worker,'set_windows_error_mode',return_value=77),patch.object(worker,'restore_windows_error_mode') as restore,redirect_stdout(io.StringIO()):
   try:worker.run_hidden(['known-exporter'],Path('.'),{},'test')
   finally:restore.assert_called_once_with(77)
   return run.call_count,sleep.call_count
 def result(self,code):return subprocess.CompletedProcess([],code,stdout='')
 def test_success_has_no_retry(self):self.assertEqual(self.check([self.result(0)]),(1,0))
 def test_nt_sharing_conflict_recovers(self):self.assertEqual(self.check([self.result(0xc0000043),self.result(0)]),(2,1))
 def test_createprocess_sharing_conflict_recovers(self):
  error=OSError('busy');error.winerror=32;self.assertEqual(self.check([error,self.result(0)]),(2,1))
 def test_sharing_retries_are_bounded(self):
  with self.assertRaisesRegex(worker.StageAssetError,'failed with exit code'):self.check([self.result(0xc0000043)]*4)
 def test_malware_detection_is_never_retried(self):
  error=OSError('blocked');error.winerror=225
  with self.assertRaisesRegex(worker.StageAssetError,'could not start'):self.check([error])
 def test_access_denial_is_never_retried(self):
  with self.assertRaisesRegex(worker.StageAssetError,'failed with exit code'):self.check([self.result(0xc0000022)])
 def test_decode_failure_is_never_retried(self):
  with self.assertRaisesRegex(worker.StageAssetError,'failed with exit code'):self.check([self.result(1)])

if __name__=='__main__':unittest.main()
