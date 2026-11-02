import os,tempfile,unittest
from pathlib import Path
import original_third_party_frontend_compat as m

class ThirdPartyFrontendTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='third-party-form-',dir=Path(tempfile.gettempdir()).resolve());self.root=Path(self.tmp.name).resolve()
        self.reference=self.root/'reference';self.project=self.root/'project';self.raw=(Path(os.environ['ORIGINAL_THIRD_PARTY_REFERENCE'])/m.RELATIVE).read_bytes()
        for folder in (self.reference,self.project):p=folder/m.RELATIVE;p.parent.mkdir(parents=True);p.write_bytes(self.raw)
    def tearDown(self):self.tmp.cleanup()
    def test_unknown_source_refused(self):
        with self.assertRaisesRegex(ValueError,'PINNED_ORIGINAL'):m.transform(self.raw+b'\n')
    def test_one_field_only_and_required_retained(self):
        out,r=m.transform(self.raw);self.assertTrue(r['originalRequiredDateDictionaryAttachmentAndCallbackPreserved']);self.assertTrue(r['noSilentTruncation']);self.assertEqual(r['maximumUnicodeCodePoints'],16)
        before=self.raw.decode().replace('\r\n','\n');after=out.decode().replace('\r\n','\n')
        self.assertEqual(before[:before.index('    { el: "input", prop: "licenceName",')],after[:after.index('    {\n      el: "input",')])
        anchor='    {\n      el: "select",';self.assertEqual(before[before.index(anchor):],after[after.index(anchor):])
    def test_restore_success(self):
        with m.third_party_credentials_override(self.project,self.reference) as receipt:self.assertEqual((self.project/m.RELATIVE).read_bytes(),m.transform(self.raw)[0]);self.assertEqual((self.reference/m.RELATIVE).read_bytes(),self.raw)
        self.assertTrue(receipt['sourceFileRestored']);self.assertEqual((self.project/m.RELATIVE).read_bytes(),self.raw)
    def test_restore_failure(self):
        with self.assertRaisesRegex(RuntimeError,'OWN_BUILD_FAILED'):
            with m.third_party_credentials_override(self.project,self.reference):raise RuntimeError('OWN_BUILD_FAILED')
        self.assertEqual((self.project/m.RELATIVE).read_bytes(),self.raw)
    def test_same_root_refused(self):
        with self.assertRaisesRegex(ValueError,'DISTINCT_THIRD_PARTY'):
            with m.third_party_credentials_override(self.reference,self.reference):self.fail()
    def test_nested_root_refused(self):
        (self.reference/'nested').mkdir()
        with self.assertRaisesRegex(ValueError,'DISTINCT_THIRD_PARTY'):
            with m.third_party_credentials_override(self.reference/'nested',self.reference):self.fail()
    def test_hardlink_refused(self):
        p=self.project/m.RELATIVE;p.unlink();os.link(self.reference/m.RELATIVE,p)
        with self.assertRaisesRegex(ValueError,'DISTINCT_REGULAR'):
            with m.third_party_credentials_override(self.project,self.reference):self.fail()
    def test_build_copy_drift_refused(self):
        p=self.project/m.RELATIVE;p.write_bytes(self.raw+b'\n')
        with self.assertRaisesRegex(ValueError,'COPY_DRIFT'):
            with m.third_party_credentials_override(self.project,self.reference):self.fail()
        self.assertEqual(p.read_bytes(),self.raw+b'\n')
    def test_external_change_preserved(self):
        p=self.project/m.RELATIVE
        with self.assertRaisesRegex(ValueError,'EXTERNAL_EDIT'):
            with m.third_party_credentials_override(self.project,self.reference):p.write_bytes(b'OWN_EDIT')
        self.assertEqual(p.read_bytes(),b'OWN_EDIT')

if __name__=='__main__':unittest.main()
