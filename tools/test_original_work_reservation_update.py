"""Verify the exact service whitelist, payload identity and real file rollback."""
from pathlib import Path
import importlib.util, json, tempfile, unittest
from build_original_work_reservation_update import adapt_updater, CLASS, REVISION

class ReservationUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='zmd-reservation-update-');self.root=Path(self.temp.name)
        raw=Path(__file__).with_name('original_public_test_update.py').read_bytes()
        self.patched=adapt_updater(raw);module_path=self.root/'updater.py';module_path.write_bytes(self.patched)
        spec=importlib.util.spec_from_file_location('own_reservation_updater',module_path)
        self.u=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.u)
        self.app=self.root/'Application';self.app.mkdir();self.bundle=self.root/'bundle';self.bundle.mkdir()
        old_payload={'releaseId':'OWN_SYNTHETIC','files':{}}
        self.u.write_json(self.app/'payload-manifest.json',old_payload)
        old={'releaseId':'OWN_SYNTHETIC','controllerFiles':{},'payloadManifestSHA256':self.u.sha(self.app/'payload-manifest.json')}
        self.u.write_json(self.app/'release-manifest.json',old)
        self.u.atomic(self.bundle/'payload'/CLASS,b'own-class')
        self.u.write_json(self.bundle/'payload/payload-manifest.json',{'releaseId':'OWN_SYNTHETIC','files':{CLASS:{'bytes':9,'sha256':self.u.sha(self.bundle/'payload'/CLASS)}}})
        self.new=dict(old,reservationEndTimeCandidate=REVISION,payloadManifestSHA256=self.u.sha(self.bundle/'payload/payload-manifest.json'))
        self.u.write_json(self.bundle/'payload/release-manifest.json',self.new)
        self.plan={'schema':'zhumadian.public-test-update.v1','targetApplication':self.app.as_posix(),'gatewayPort':18891,'releaseId':'OWN_SYNTHETIC','databaseUploadsCredentialsGISOrDependenciesIncluded':False,'acceptedOldReleases':{self.u.sha(self.app/'release-manifest.json'):{'controllerFiles':{},'payloadManifestSHA256':old['payloadManifestSHA256']}},'basePayloadManifestSHA256':old['payloadManifestSHA256'],'newPayloadManifestSHA256':self.new['payloadManifestSHA256'],'newReleaseSHA256':self.u.sha(self.bundle/'payload/release-manifest.json'),'oldPayloadFiles':{},'legacyEntrySHA256':{},'removedFrontendFiles':{},'files':{}}
        self.refresh()
        for rel in ('private/OWN_CANARY','UserData/OriginalServer/database/OWN_CANARY','UserData/Uploads/OWN_CANARY'):
            self.u.atomic(self.app/rel,b'KEEP_SYNTHETIC')
    def tearDown(self):self.temp.cleanup()
    def refresh(self):
        for p in (self.bundle/'payload').rglob('*'):
            if p.is_file():self.plan['files'][p.relative_to(self.bundle/'payload').as_posix()]={'bytes':p.stat().st_size,'SHA256':self.u.sha(p)}
    def release(self):
        self.new['payloadManifestSHA256']=self.u.sha(self.bundle/'payload/payload-manifest.json')
        self.u.write_json(self.bundle/'payload/release-manifest.json',self.new)
        self.plan['newPayloadManifestSHA256']=self.new['payloadManifestSHA256'];self.plan['newReleaseSHA256']=self.u.sha(self.bundle/'payload/release-manifest.json');self.refresh()
    def load(self):
        self.u.write_json(self.bundle/'update-manifest.json',self.plan)
        return self.u.load_bundle(self.app,self.bundle,self.u.sha(self.bundle/'update-manifest.json'),expected_target=self.app,expected_port=18891)
    def test_exact_override_accepted(self):
        self.assertEqual(set(self.load()[2]),{CLASS,'payload-manifest.json','release-manifest.json'})
    def test_neighbouring_service_rejected(self):
        self.u.atomic(self.bundle/'payload'/CLASS.replace('WorkReservationBaseServiceImpl','OtherServiceImpl'),b'x');self.refresh()
        with self.assertRaisesRegex(ValueError,'UNEXPECTED_UPDATE_PATH'):self.load()
    def test_explicit_revision_required(self):
        self.new.pop('reservationEndTimeCandidate');self.release()
        with self.assertRaisesRegex(ValueError,'EXPLICIT_RESERVATION_END_TIME_CANDIDATE'):self.load()
    def test_payload_entry_required(self):
        payload=self.u.read(self.bundle/'payload/payload-manifest.json');payload['files'].pop(CLASS);self.u.write_json(self.bundle/'payload/payload-manifest.json',payload);self.release()
        with self.assertRaisesRegex(ValueError,'RESERVATION_END_TIME_CLASS_PAYLOAD_PIN'):self.load()
    def test_wrong_class_hash_rejected(self):
        payload=self.u.read(self.bundle/'payload/payload-manifest.json');payload['files'][CLASS]['sha256']='0'*64;self.u.write_json(self.bundle/'payload/payload-manifest.json',payload);self.release()
        with self.assertRaisesRegex(ValueError,'RESERVATION_END_TIME_CLASS_PAYLOAD_PIN'):self.load()
    def test_apply_and_rollback_only_owned_code(self):
        changes=self.load()[2];old={n:(self.app/n).read_bytes() for n in ('payload-manifest.json','release-manifest.json')}
        backup=self.root/'backup';self.u.backup_code(self.app,backup,changes);self.u.replace_code(self.app,self.bundle,changes)
        self.assertTrue((self.app/CLASS).is_file());self.u.restore_code(self.app,backup,changes);self.assertFalse((self.app/CLASS).exists())
        for n,raw in old.items():self.assertEqual((self.app/n).read_bytes(),raw)
        for rel in ('private/OWN_CANARY','UserData/OriginalServer/database/OWN_CANARY','UserData/Uploads/OWN_CANARY'):self.assertEqual((self.app/rel).read_bytes(),b'KEEP_SYNTHETIC')
    def test_changed_updater_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'PINNED_INSTALLED_UPDATER'):adapt_updater(self.patched)

if __name__=='__main__':unittest.main()
