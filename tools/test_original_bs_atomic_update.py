"""Exercise actual sparse loader/apply/rollback for the exact added class scope."""
import sys,unittest
from pathlib import Path
sys.path.insert(1,'D:/Project/Zhumadian/Application/tools')
import build_original_bs_atomic_update as m
import test_original_work_reservation_update as prior
prior.adapt_updater=m.adapt_updater

class CombinedClassTests(unittest.TestCase):
    def setUp(self):
        self.fx=prior.ReservationUpdateTests();self.fx.setUp();self.u=self.fx.u;self.app=self.fx.app;self.bundle=self.fx.bundle
        for name in (m.THIRD,m.OBSERVER):
            self.u.atomic(self.bundle/'payload'/name,b'own-class')
            p=self.u.read(self.bundle/'payload/payload-manifest.json');p['files'][name]={'bytes':9,'sha256':self.u.sha(self.bundle/'payload'/name)};self.u.write_json(self.bundle/'payload/payload-manifest.json',p)
        self.fx.new.update(thirdPartyCredentialsCandidate=m.THIRD_REVISION,workTransactionObservationCandidate=m.OBSERVER_REVISION);self.fx.release()
    def tearDown(self):self.fx.tearDown()
    def test_exact_three_classes(self):self.assertTrue({m.RESERVATION,m.THIRD,m.OBSERVER}.issubset(self.fx.load()[2]))
    def test_third_revision_required(self):
        self.fx.new.pop('thirdPartyCredentialsCandidate');self.fx.release()
        with self.assertRaisesRegex(ValueError,'EXPLICIT_THIRD_PARTY_CREDENTIALS'):self.fx.load()
    def test_observer_revision_required(self):
        self.fx.new.pop('workTransactionObservationCandidate');self.fx.release()
        with self.assertRaisesRegex(ValueError,'EXPLICIT_WORK_TRANSACTION_OBSERVER'):self.fx.load()
    def test_third_wrong_payload_hash(self):
        p=self.u.read(self.bundle/'payload/payload-manifest.json');p['files'][m.THIRD]['sha256']='0'*64;self.u.write_json(self.bundle/'payload/payload-manifest.json',p);self.fx.release()
        with self.assertRaisesRegex(ValueError,'THIRD_PARTY_CREDENTIALS_CLASS_PAYLOAD_PIN'):self.fx.load()
    def test_observer_missing_payload(self):
        p=self.u.read(self.bundle/'payload/payload-manifest.json');p['files'].pop(m.OBSERVER);self.u.write_json(self.bundle/'payload/payload-manifest.json',p);self.fx.release()
        with self.assertRaisesRegex(ValueError,'WORK_TRANSACTION_OBSERVER_CLASS_PAYLOAD_PIN'):self.fx.load()
    def test_neighboring_third_service_rejected(self):
        self.u.atomic(self.bundle/'payload'/m.THIRD.replace('ThirdPartyUnitInfoServiceImpl','OtherServiceImpl'),b'own-class');self.fx.refresh()
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_UPDATE_PATH'):self.fx.load()
    def test_real_code_rollback_keeps_data(self):
        changes=self.fx.load()[2];before={p:(self.app/p).read_bytes() for p in ('release-manifest.json','payload-manifest.json')};backup=self.fx.root/'backup';self.u.backup_code(self.app,backup,changes);self.u.replace_code(self.app,self.bundle,changes)
        self.assertTrue(all((self.app/n).is_file() for n in (m.RESERVATION,m.THIRD,m.OBSERVER)));self.u.restore_code(self.app,backup,changes)
        self.assertTrue(all(not (self.app/n).exists() for n in (m.RESERVATION,m.THIRD,m.OBSERVER)))
        for name,raw in before.items():self.assertEqual((self.app/name).read_bytes(),raw)
        for name in ('private/OWN_CANARY','UserData/OriginalServer/database/OWN_CANARY','UserData/Uploads/OWN_CANARY'):self.assertEqual((self.app/name).read_bytes(),b'KEEP_SYNTHETIC')

if __name__=='__main__':
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(prior.ReservationUpdateTests),unittest.defaultTestLoader.loadTestsFromTestCase(CombinedClassTests)])
    result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())
