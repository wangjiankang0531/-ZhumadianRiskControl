"""Independent cache protocol verification; test data stays in temporary folders."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromNames(['tools.test_native_cache_policy','tools.test_native_cache_http'])
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
