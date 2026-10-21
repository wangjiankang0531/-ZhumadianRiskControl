import struct,unittest,subprocess,queue
from types import SimpleNamespace
from unittest.mock import patch
from osgb_stdio_worker import frame_extent,StdioWorker
class Framing(unittest.TestCase):
 def test_explicit_frames_and_control_zero_payload(self):
  for magic in (b'ZMDWRK01',b'ZMDERR01',b'ZMDOSGB1',b'ZMDGEO01',b'ZMDROI01'):
   self.assertEqual(frame_extent(magic+struct.pack('<QQ',30,0 if magic in (b'ZMDWRK01',b'ZMDERR01') else 4)),(30,0 if magic in (b'ZMDWRK01',b'ZMDERR01') else 4))
 def test_unbounded_unknown_and_truncated_frames_are_rejected(self):
  for p in (b'',b'UNKNOWN1'+struct.pack('<QQ',30,4),b'ZMDGEO01'+struct.pack('<QQ',1048577,4),b'ZMDOSGB1'+struct.pack('<QQ',30,134217729),b'ZMDWRK01'+struct.pack('<QQ',30,1),b'ZMDERR01'+struct.pack('<QQ',0,0)):
   with self.assertRaises(ValueError):frame_extent(p)
 def test_process_start_failure_is_held_without_second_create_attempt(self):
  worker=StdioWorker('unstarted.exe','Data')
  with patch('osgb_stdio_worker.subprocess.Popen',side_effect=PermissionError('locked')) as start:
   with self.assertRaises(PermissionError):worker.request('node',None)
   with self.assertRaisesRegex(RuntimeError,'no automatic restart'):worker.request('node',None)
   self.assertEqual(start.call_count,1);self.assertEqual(worker.starts,1);self.assertTrue(worker.failed)
  worker.close();self.assertTrue(worker.closed)
 def test_source_store_closes_an_owned_reader_after_its_executor(self):
  from test_source_memory_store import Catalog,Reader
  from readonly_source_memory_store import MemorySourceStore
  reader=Reader();closed=[];reader.close=lambda:closed.append(True);store=MemorySourceStore(Catalog(),reader);store.close();self.assertEqual(closed,[True])
class ExitAudit(unittest.TestCase):
 class Process:
  pid=123
  def __init__(self,exit_after_wait=None):self.code=None;self.after=exit_after_wait;self.kills=0;self.waits=[];self.stdin=SimpleNamespace(close=lambda:None,write=lambda b:len(b),flush=lambda:None)
  def poll(self):return self.code
  def wait(self,timeout):
   self.waits.append(timeout)
   if self.code is not None:return self.code
   if self.after is None:raise subprocess.TimeoutExpired('fake',timeout)
   self.code=self.after;return self.code
  def kill(self):self.kills+=1;self.code=1
 def worker(self,code=None):
  w=StdioWorker('never-start.exe','Data');w.process=self.Process(code);return w
 def test_eof_records_natural_ntstatus_before_owner_cleanup(self):
  w=self.worker(-1073741819);w.phase='response';w.handshake_complete=True;w.responses.put(EOFError('stdout closed'))
  with self.assertRaisesRegex(RuntimeError,'frame failed'):w._response()
  audit=w.audit();self.assertEqual(audit['nativeExitHex'],'0xC0000005');self.assertEqual(audit['failure']['phase'],'response');self.assertFalse(audit['ownerTerminated']);self.assertEqual(w.process.kills,0);self.assertEqual(w.process.waits[0],.25)
  w.close();self.assertEqual(w.audit()['phase'],'closed');self.assertEqual(w.audit()['failure'],audit['failure'])
 def test_live_child_after_eof_is_held_and_owner_code_is_not_mislabeled_native(self):
  w=self.worker();w.phase='handshake';w.responses.put(EOFError('closed'))
  with self.assertRaises(RuntimeError):w._response()
  audit=w.audit();self.assertIsNone(audit['nativeExitCode']);self.assertTrue(audit['ownerTerminated']);self.assertEqual(audit['cleanupExitCode'],1);self.assertEqual(audit['failure']['phase'],'handshake')
  with self.assertRaisesRegex(RuntimeError,'no automatic restart'):w.request('node',None)
  self.assertEqual(w.process.kills,1);w.close()
 def test_write_and_response_attempts_are_distinct_from_successful_requests(self):
  w=self.worker(7);w.handshake_complete=True;w._start=lambda:None;w.responses.put(EOFError('closed'))
  with self.assertRaises(RuntimeError):w.request('node',None)
  self.assertEqual(w.audit()['attemptedRequests'],1);self.assertEqual(w.requests,0);self.assertEqual(w.audit()['failure']['phase'],'response');self.assertEqual(w.audit()['nativeExitCode'],7);w.close()
 def test_initial_spawn_failure_captures_phase_without_leaking_message_or_retrying(self):
  w=StdioWorker('never-start.exe','Data');error=OSError('private path not copied to audit');error.winerror=225
  with patch('osgb_stdio_worker.subprocess.Popen',side_effect=error) as start:
   with self.assertRaises(OSError):w.request('node',None)
   with self.assertRaisesRegex(RuntimeError,'no automatic restart'):w.request('node',None)
   self.assertEqual(start.call_count,1)
  self.assertEqual(w.audit()['failure'],{'phase':'launch','type':'OSError','winerror':225});self.assertNotIn('private path',str(w.audit()));w.close()
 def test_success_marks_ready_and_increments_both_attempt_and_success(self):
  w=self.worker();w.handshake_complete=True;w._start=lambda:None;w.responses.put(b'frame')
  self.assertEqual(w.request('node',None),b'frame');self.assertEqual(w.audit()['phase'],'ready');self.assertEqual(w.attempted_requests,1);self.assertEqual(w.requests,1);w.process.code=0;w.close();self.assertEqual(w.audit()['nativeExitCode'],0)

if __name__=='__main__':unittest.main()
