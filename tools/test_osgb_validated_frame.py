import hashlib,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import osgb_v80_memory_frame as frame
from osgb_memory_reader import parse_frame
from osgb_v80_source_reader import PinnedOSGBDataReader
from test_osgb_v80_data_reader import fixture

class ValidatedFrameTests(unittest.TestCase):
 def setUp(self):self.raw,self.expected=fixture();self.node='Tile_1/Tile_1_L19_0uuuu.osgb'
 def test_parsed_result_is_the_same_complete_descriptor_and_original_payload(self):
  packed,audit=frame.build_frame(self.raw,self.node);expected,payload=parse_frame(packed,self.node,len(self.raw));actual,view=frame.build_parsed_frame(self.raw,self.node)
  self.assertEqual(actual,expected);self.assertEqual(bytes(view),bytes(payload));self.assertTrue(view.readonly);self.assertIsInstance(view.obj,bytes);self.assertEqual(audit['frameSHA256'],hashlib.sha256(packed).hexdigest())
  mesh=actual['meshes'][0];self.assertEqual(bytes(view[mesh['positions']['offset']:mesh['positions']['offset']+mesh['positions']['bytes']]),self.expected['positions'])
  with self.assertRaises(TypeError):view[0]=0
 def test_both_entry_points_perform_exactly_one_complete_validation(self):
  for entry in (frame.build_frame,frame.build_parsed_frame):
   with self.subTest(entry=entry.__name__),patch.object(frame,'parse_frame',wraps=parse_frame) as checked:entry(self.raw,self.node);self.assertEqual(checked.call_count,1)
 def test_validator_rejection_is_not_bypassed_by_the_parsed_entry(self):
  for entry in (frame.build_frame,frame.build_parsed_frame):
   with self.subTest(entry=entry.__name__),patch.object(frame,'parse_frame',side_effect=ValueError('rejected complete frame')) as checked:
    with self.assertRaisesRegex(ValueError,'rejected complete frame'):entry(self.raw,self.node)
    self.assertEqual(checked.call_count,1)
 def test_malformed_geometry_and_invalid_budget_still_fail_closed(self):
  bad,_=fixture(indices=(0,1,99))
  for entry in (frame.build_frame,frame.build_parsed_frame):
   for raw,maximum in ((bad,128*1048576),(self.raw,1),(self.raw,True),(bytearray(self.raw),128*1048576)):
    with self.subTest(entry=entry.__name__,maximum=maximum),self.assertRaises((ValueError,TypeError)):entry(raw,self.node,maximum)
 def setup_reader(self):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)/'Data';(root/'Tile_1').mkdir(parents=True);source=root/'Tile_1/Tile_1_L19_0uuuu.osgb';source.write_bytes(self.raw);reader=PinnedOSGBDataReader(root);pin={'bytes':len(self.raw),'sha256':hashlib.sha256(self.raw).hexdigest()};return reader,source,pin
 def test_pinned_reader_consumes_the_validated_result_once_without_native_launch(self):
  reader,source,pin=self.setup_reader();before=source.read_bytes(),source.stat().st_mtime_ns
  with patch('subprocess.run',side_effect=AssertionError('No native reader')),patch.object(frame,'parse_frame',wraps=parse_frame) as checked:desc,payload=reader(1,source.name,pin)
  self.assertEqual(checked.call_count,1);self.assertEqual(desc['triangles'],1);self.assertTrue(payload.readonly);self.assertEqual(before,(source.read_bytes(),source.stat().st_mtime_ns))
 def test_postdecode_original_source_change_is_still_rejected(self):
  reader,source,pin=self.setup_reader();original=frame.build_parsed_frame
  def changed(*args,**kwargs):
   value=original(*args,**kwargs);source.write_bytes(self.raw[:-1]+bytes([self.raw[-1]^1]));return value
  with patch.object(frame,'build_parsed_frame',side_effect=changed),self.assertRaisesRegex(ValueError,'changed during decode'):reader(1,source.name,pin)
 def test_postdecode_reader_code_change_is_still_rejected(self):
  reader,source,pin=self.setup_reader();original=frame.build_parsed_frame;bad=source.parent/'changed.py';bad.write_text('changed','utf-8')
  def changed(*args,**kwargs):
   value=original(*args,**kwargs);reader.code['reader']=bad;return value
  with patch.object(frame,'build_parsed_frame',side_effect=changed),self.assertRaisesRegex(ValueError,'implementation changed'):reader(1,source.name,pin)

if __name__=='__main__':unittest.main()
