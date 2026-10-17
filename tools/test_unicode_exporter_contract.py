"""Unicode exporter contracts keep source access independent of Windows junction creation."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import build_zhumadian_stage_asset as stage


class UnicodeExporterContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'原始数据';self.source.mkdir();self.alias=self.root/'zmd_source'
        self.exe=self.root/'ht_osgb_exporter.exe';self.exe.write_bytes(b'test exporter bytes')
        self.cap=self.root/'ht_osgb_exporter.capabilities.json'
        self.contract={'schema':'xnby.osgb.exporter.v1','exe_sha256':hashlib.sha256(self.exe.read_bytes()).hexdigest(),'unicode_source_paths':True}
    def tearDown(self):self.temp.cleanup()
    def test_matching_contract_reads_original_path_without_subprocess(self):
        self.cap.write_text(json.dumps(self.contract))
        with patch.object(stage.subprocess,'run',side_effect=AssertionError('No junction command may run')):
            self.assertEqual(stage.ensure_ascii_source_alias(self.source,self.alias,self.exe),self.source)
        self.assertFalse(self.alias.exists())
    def test_stale_binary_and_false_capability_fail_without_fallback(self):
        for patch_value in [{'exe_sha256':'0'*64},{'unicode_source_paths':False},{'schema':'unknown'}]:
            self.cap.write_text(json.dumps(dict(self.contract,**patch_value)))
            with self.subTest(patch_value=patch_value),patch.object(stage.subprocess,'run',side_effect=AssertionError('No implicit fallback')):
                with self.assertRaises(stage.StageAssetError):stage.ensure_ascii_source_alias(self.source,self.alias,self.exe)
    def test_corrupt_capability_is_rejected(self):
        self.cap.write_text('{')
        with self.assertRaises(stage.StageAssetError):stage.ensure_ascii_source_alias(self.source,self.alias,self.exe)
    def test_linked_capability_is_rejected(self):
        outside=self.root/'outside.json';outside.write_text(json.dumps(self.contract))
        try:self.cap.symlink_to(outside)
        except OSError as error:self.skipTest(str(error))
        try:
            with self.assertRaises(stage.StageAssetError):stage.ensure_ascii_source_alias(self.source,self.alias,self.exe)
            self.assertTrue(outside.exists())
        finally:self.cap.unlink()


if __name__=='__main__':unittest.main()