import struct,unittest
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
if __name__=='__main__':unittest.main()
