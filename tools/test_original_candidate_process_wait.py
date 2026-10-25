import subprocess
import unittest
from original_candidate_process_wait import finish_owned_process

class Process:
    def __init__(self, code=None, error=None): self.returncode=code; self.error=error; self.terminated=False
    def poll(self): return self.returncode
    def terminate(self): self.terminated=True
    def wait(self, timeout):
        if self.error: raise self.error
        self.returncode=1

class WaitTest(unittest.TestCase):
    def test_timeout_records_failure_and_allows_remaining_components(self):
        p=Process(error=subprocess.TimeoutExpired(['owned-test'],15))
        r=finish_owned_process(p,'Platform')
        self.assertFalse(r['ownPlatformExited']); self.assertTrue(r['failed']); self.assertTrue(p.terminated)
        self.assertEqual(r['ownPlatformStopErrorType'],'TimeoutExpired')
        remaining=Process(0); r.update(finish_owned_process(remaining,'Redis'))
        self.assertTrue(r['ownRedisExited']); self.assertEqual(r['ownRedisExitCode'],0)
    def test_already_exited_preserves_code(self):
        p=Process(0); r=finish_owned_process(p,'Business')
        self.assertEqual(r['ownBusinessExitCode'],0); self.assertFalse(p.terminated)
    def test_os_error_does_not_claim_exit(self):
        r=finish_owned_process(Process(error=OSError('owned-fixture')),'Platform')
        self.assertFalse(r['ownPlatformExited']); self.assertTrue(r['failed'])
    def test_successful_termination_is_not_natural_exit(self):
        r=finish_owned_process(Process(),'Business')
        self.assertTrue(r['ownBusinessTerminated']); self.assertEqual(r['ownBusinessExitCode'],1)
    def test_not_started(self):
        r=finish_owned_process(None,'Business'); self.assertTrue(r['ownBusinessExited']); self.assertIsNone(r['ownBusinessExitCode'])


class RecoveryReceiptTest(unittest.TestCase):
    def setUp(self):
        import tempfile,json,hashlib
        from pathlib import Path
        self.tmp=tempfile.TemporaryDirectory(prefix='own-recovery-fixture-'); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.path=self.root/'recovery_after_controller_failure.json'
        log=b'own synthetic log: Redis is now ready to exit, bye bye...'
        (self.root/'redis.private.log').write_bytes(log)
        (self.root/'ready.json').write_text(json.dumps({'ownerId':'own-fixture','ownRedisPID':123}))
        self.receipt={'ownerId':'own-fixture','ownRedisPID':123,'ownMySQLExited':True,'ownMySQLExitCode':0,'ownRedisExited':True,'ownRedisExitCode':None,
            'recoveredAfterControllerFailure':True,'failed':True,'controllerShutdownException':'TimeoutExpired','allPreviousPIDsAbsent':True,
            'allThreeOwnerLocksAcquiredAndReleased':True,'redisExitCodeObserved':False,'redisGracefulShutdownLogSHA256':hashlib.sha256(log).hexdigest()}
    def validate(self):
        from original_candidate_process_wait import validate_previous_database_shutdown
        validate_previous_database_shutdown(self.receipt,self.path)
    def test_explicit_recovery_keeps_exit_code_unknown(self):
        self.validate(); self.assertIsNone(self.receipt['ownRedisExitCode']); self.assertTrue(self.receipt['failed'])
    def test_unstopped_or_unlocked_or_wrong_owner_is_rejected(self):
        for key,value in [('allPreviousPIDsAbsent',False),('allThreeOwnerLocksAcquiredAndReleased',False),('ownerId','other-run'),('ownMySQLExitCode',1)]:
            old=self.receipt[key]; self.receipt[key]=value
            with self.assertRaises(AssertionError): self.validate()
            self.receipt[key]=old
    def test_changed_shutdown_log_is_rejected(self):
        (self.root/'redis.private.log').write_bytes(b'changed')
        with self.assertRaises(AssertionError): self.validate()
    def test_plain_unknown_exit_is_rejected(self):
        self.receipt['recoveredAfterControllerFailure']=False
        with self.assertRaises(AssertionError): self.validate()

if __name__=='__main__': unittest.main()
