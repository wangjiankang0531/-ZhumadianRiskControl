import array,math,random,struct,unittest
from unittest.mock import patch
import osgb_memory_reader as reader

class SourceFloatValidationTests(unittest.TestCase):
 def compare(self,raw):
  expected=all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',raw));self.assertEqual(reader.finite_source_float32(memoryview(raw)),expected)
 def test_extreme_finite_float32_values_and_cancellation_remain_valid(self):
  words=[0,0x80000000,1,0x80000001,0x007fffff,0x807fffff,0x00800000,0x80800000,0x7f7fffff,0xff7fffff]
  self.compare(b''.join(struct.pack('<I',word) for word in words)*5000)
 def test_every_nonfinite_class_is_rejected_at_block_edges(self):
  for word in [0x7f800000,0xff800000,0x7fc00000,0xffc00000,0x7f800001,0xff800001]:
   for at in [0,16383,16384,32767]:
    raw=bytearray(struct.pack('<f',1)*32768);struct.pack_into('<I',raw,at*4,word);self.compare(raw)
 def test_opposite_infinities_cannot_cancel_into_a_valid_sum(self):self.compare(struct.pack('<II',0x7f800000,0xff800000))
 def test_deterministic_random_bit_patterns_agree_with_scalar_validation(self):
  randomizer=random.Random(20261028)
  for _ in range(20):self.compare(b''.join(struct.pack('<I',randomizer.getrandbits(32)) for i in range(2000)))
 def test_validator_scratch_input_is_bounded_to_64KiB(self):
  factory=array.array;seen=[]
  class BoundedArray:
   itemsize=4
   def __init__(self,kind):self.value=factory(kind)
   def frombytes(self,data):seen.append(len(data));self.assert_bound(data);self.value.frombytes(data)
   def assert_bound(self,data):assert len(data)<=65536
   def byteswap(self):self.value.byteswap()
   def __iter__(self):return iter(self.value)
  raw=struct.pack('<f',1)*100000
  with patch.object(reader.array,'array',BoundedArray):self.assertTrue(reader.finite_source_float32(memoryview(raw)))
  self.assertGreater(len(seen),1);self.assertLessEqual(max(seen),65536)
 def test_partial_float_bytes_refuse_instead_of_ignoring_tail(self):
  for raw in [b'x',b'xx',b'xxx',b'\0'*5]:
   with self.assertRaises(ValueError):reader.finite_source_float32(memoryview(raw))

if __name__=='__main__':unittest.main()
