import hashlib
from pathlib import Path
import tempfile
import unittest
from prepare_original_bigscreen_lifecycle import (KIND, class_member, document,
    selection_requested, validate_shape, verify_class_pins)


class LifecycleSelectionTests(unittest.TestCase):
    def test_optional_selection_is_not_a_silent_override(self):
        self.assertFalse(selection_requested(None,None))
        self.assertTrue(selection_requested(Path('receipt.json'),'a'*64))
        for args in ((None,'a'*64),(Path('receipt.json'),None),(Path('receipt.json'),'invalid')):
            with self.subTest(args=args),self.assertRaises(ValueError):selection_requested(*args)

    def test_only_lifecycle_bytecode_members_are_accepted(self):
        self.assertEqual(class_member('xnby/replica/CandidateLifecycleObservation.class'),
                         'xnby/replica/CandidateLifecycleObservation.class')
        for value in ('../other.class','xnby/replica/OriginalBigscreenProcessBoundary.class',
                      '/xnby/replica/CandidateLifecycleObservation.class',
                      'xnby/replica/CandidateLifecycleObservation.class/../other',
                      r'xnby\replica\CandidateLifecycleObservation.class'):
            with self.subTest(value=value),self.assertRaises(ValueError):class_member(value)

    def valid(self):
        return {'kind':KIND,'checks':5,'ownExitCode':0,'eventConstructorArity':3,
                'originalApplicationStarted':False,'nativeCodeExecuted':False,'databaseConnected':False}

    def test_requires_actual_success_with_no_original_app_or_database(self):
        validate_shape(self.valid())
        for key,value in [('kind','other'),('checks',4),('ownExitCode',1),('eventConstructorArity',2),
                          ('originalApplicationStarted',True),('nativeCodeExecuted',True),('databaseConnected',True)]:
            r=self.valid();r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate_shape(r)

    def test_class_drift_and_bad_pins_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix='own-lifecycle-test-') as tmp:
            root=Path(tmp);name='xnby/replica/CandidateLifecycleObservation.class';p=root/name
            p.parent.mkdir(parents=True);p.write_bytes(b'own synthetic class bytes; never executed')
            pins={name:hashlib.sha256(p.read_bytes()).hexdigest()};verify_class_pins(root,pins)
            p.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'CLASS_CHANGED'):verify_class_pins(root,pins)
            with self.assertRaises(ValueError):verify_class_pins(root,{name:'bad'})
            with self.assertRaises(ValueError):verify_class_pins(root,{})

    def test_duplicate_receipt_keys_do_not_override_a_failed_proof(self):
        with tempfile.TemporaryDirectory(prefix='own-lifecycle-json-') as tmp:
            p=Path(tmp)/'receipt.json';p.write_text('{"checks":0,"checks":5}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'DUPLICATE'):document(p)


if __name__=='__main__':unittest.main()
