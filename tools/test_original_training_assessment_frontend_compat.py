import os,tempfile,unittest
from pathlib import Path
import original_training_assessment_frontend_compat as m

class ExamFrontendTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='exam-form-',dir=Path(tempfile.gettempdir()).resolve());self.root=Path(self.temp.name).resolve()
        self.raw=(Path(os.environ['ORIGINAL_EXAM_REFERENCE'])/m.RELATIVE).read_bytes();self.project=self.root/'project';self.reference=self.root/'reference'
        for folder in [self.project,self.reference]:p=folder/m.RELATIVE;p.parent.mkdir(parents=True);p.write_bytes(self.raw)
    def tearDown(self):self.temp.cleanup()
    def test_exact_two_changes_and_all_other_fields_preserved(self):
        out,receipt=m.transform(self.raw);before=self.raw.decode().replace('\r\n','\n');after=out.decode().replace('\r\n','\n')
        self.assertEqual(after,before.replace(m.DATE_OLD,m.DATE_NEW,1).replace(m.USERS_OLD,m.USERS_NEW,1))
        self.assertTrue(receipt['requiredFieldsAndOriginalCallbackPreserved']);self.assertFalse(receipt['schemaAPIAndPermissionChanges'])
    def test_unknown_source_refused(self):
        with self.assertRaisesRegex(ValueError,'PINNED_ORIGINAL'):m.transform(self.raw+b'\n')
    def test_restore_after_success(self):
        with m.training_assessment_override(self.project,self.reference) as r:self.assertEqual((self.project/m.RELATIVE).read_bytes(),m.transform(self.raw)[0]);self.assertEqual((self.reference/m.RELATIVE).read_bytes(),self.raw)
        self.assertTrue(r['sourceFileRestored']);self.assertEqual((self.project/m.RELATIVE).read_bytes(),self.raw)
    def test_restore_after_build_error(self):
        with self.assertRaisesRegex(RuntimeError,'OWN_BUILD_ERROR'):
            with m.training_assessment_override(self.project,self.reference):raise RuntimeError('OWN_BUILD_ERROR')
        self.assertEqual((self.project/m.RELATIVE).read_bytes(),self.raw)
    def test_same_and_nested_roots_refused(self):
        for p in [self.reference,self.reference/'nested']:
            p.mkdir(exist_ok=True)
            with self.assertRaisesRegex(ValueError,'DISTINCT_EXAM'):
                with m.training_assessment_override(p,self.reference):self.fail()
    def test_hardlink_refused(self):
        p=self.project/m.RELATIVE;p.unlink();os.link(self.reference/m.RELATIVE,p)
        with self.assertRaisesRegex(ValueError,'DISTINCT_REGULAR'):
            with m.training_assessment_override(self.project,self.reference):self.fail()
    def test_drift_refused_without_overwrite(self):
        p=self.project/m.RELATIVE;p.write_bytes(self.raw+b'\n')
        with self.assertRaisesRegex(ValueError,'COPY_DRIFT'):
            with m.training_assessment_override(self.project,self.reference):self.fail()
        self.assertEqual(p.read_bytes(),self.raw+b'\n')
    def test_external_edit_preserved(self):
        p=self.project/m.RELATIVE
        with self.assertRaisesRegex(ValueError,'EXTERNAL_EDIT'):
            with m.training_assessment_override(self.project,self.reference):p.write_bytes(b'OWN_EDIT')
        self.assertEqual(p.read_bytes(),b'OWN_EDIT')
if __name__=='__main__':unittest.main()
