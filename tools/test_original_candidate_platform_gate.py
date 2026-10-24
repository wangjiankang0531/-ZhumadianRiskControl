from pathlib import Path
import tempfile
import unittest
from original_candidate_platform_gate import allowed_ports,require_semantics_pair,wait_for_platform

class Process:
 def __init__(self,code=None):self.code=code
 def poll(self):return self.code
class PlatformGateTests(unittest.TestCase):
 def test_source_and_pin_are_explicit_pair(self):
  self.assertFalse(require_semantics_pair(None,None));self.assertTrue(require_semantics_pair(Path('source'),'a'*64))
  for config,pin in ((None,'a'*64),(Path('source'),None),(Path('source'),'wrong')):
   with self.assertRaises(ValueError):require_semantics_pair(config,pin)
 def test_only_exact_distinct_owned_ports_are_allowed(self):
  self.assertEqual(allowed_ports(33060,33061),'33060,33061');self.assertEqual(allowed_ports(33060,33061,33062),'33060,33061,33062')
  for p in ((33060,33060,None),(33060,33061,9),(33060,33061,65536),(True,33061,None)):
   with self.assertRaises(ValueError):allowed_ports(*p)
 def test_ready_file_does_not_replace_main_return_and_verified_bootstrap(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'own-platform-http-port.txt').write_text('33062');(r/'own-platform-ready.txt').write_text('ready')
   with self.assertRaises(TimeoutError):wait_for_platform(r,Process(),[],timeout=0)
   (r/'original-platform-main-returned.txt').write_text('returned')
   with self.assertRaises(RuntimeError):wait_for_platform(r,Process(),[],timeout=0)
 def fixture(self,root):
  (root/'own-platform-http-port.txt').write_text('33062');(root/'original-platform-main-returned.txt').write_text('returned');(root/'bootstrap-rehydration-observation.properties').write_text('originalBootstrapMethodCompleted=true\noutsideBootstrapCriticalFieldsSignaturePreserved=true\n')
 def test_verified_main_and_live_dependencies_release_business_gate(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);self.assertEqual(wait_for_platform(root,Process(),[Process(),Process()],timeout=0),33062)
 def test_platform_or_dependency_exit_cannot_release_business(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root)
   for platform,dep in ((Process(0),Process()),(Process(),Process(1))):
    with self.assertRaises(RuntimeError):wait_for_platform(root,platform,[dep],timeout=0)
 def test_failure_receipt_and_invalid_port_are_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);self.fixture(root);receipt=root/'bootstrap-rehydration-observation.properties';receipt.write_text('failureClass=fixture.Failure\n')
   with self.assertRaises(RuntimeError):wait_for_platform(root,Process(),[],timeout=0)
   self.fixture(root);(root/'own-platform-http-port.txt').write_text('9')
   with self.assertRaises(RuntimeError):wait_for_platform(root,Process(),[],timeout=0)
if __name__=='__main__':unittest.main()
