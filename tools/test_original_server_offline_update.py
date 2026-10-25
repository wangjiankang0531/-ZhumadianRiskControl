from pathlib import Path
import hashlib,json,os,tempfile,unittest,uuid
from unittest.mock import patch
if os.name!='nt':raise unittest.SkipTest('Windows server byte-lock contract')
import apply_original_server_offline_update as update

class OfflineUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='offline-controller-update-');self.root=Path(self.tmp.name).resolve()
        self.app=self.root/'Application';self.bundle=self.root/'bundle';self.app.mkdir();self.bundle.mkdir()
        self.before={rel:('old '+rel).encode() for rel in update.FILES if rel!='release-manifest.json'}
        self.after={rel:('new '+rel).encode() for rel in self.before}
        stable=self.app/'tools/stable.py';stable.parent.mkdir();stable.write_bytes(b'stable')
        base={'schema':'zhumadian.original.server.release.v1','releaseId':str(uuid.uuid4()),'payloadManifestSHA256':'e'*64,
              'controllerFiles':{rel:update.sha(self.before[rel]) for rel in update.CONTROLLERS}}
        base['controllerFiles']['tools/stable.py']=update.sha(b'stable')
        revised=dict(base,controllerFiles=dict(base['controllerFiles']))
        for rel in update.CONTROLLERS:revised['controllerFiles'][rel]=update.sha(self.after[rel])
        self.before['release-manifest.json']=json.dumps(base).encode();self.after['release-manifest.json']=json.dumps(revised).encode()
        self.spec={'schema':'zhumadian.original.offline-update.v1','updateId':str(uuid.uuid4()),'releaseId':base['releaseId'],
                   'baseReleaseManifestSHA256':update.sha(self.before['release-manifest.json']),
                   'updatedReleaseManifestSHA256':update.sha(self.after['release-manifest.json']),
                   'files':{rel:{'before':update.sha(self.before[rel]),'after':update.sha(self.after[rel]),'bytes':len(self.after[rel])} for rel in update.FILES}}
        for rel in update.FILES:
            p=self.app/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(self.before[rel])
            p=self.bundle/'payload'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(self.after[rel])
        self.manifest=self.bundle/'update-manifest.json';self.save_spec()
    def save_spec(self):self.manifest.write_text(json.dumps(self.spec));self.pin=update.sha(self.manifest.read_bytes())
    def tearDown(self):self.tmp.cleanup()
    def apply(self):return update.apply_update(self.app,self.manifest,self.pin)
    def assert_before(self):
        for rel,raw in self.before.items():self.assertEqual((self.app/rel).read_bytes(),raw)
    def prepare_next_delta(self):
        self.apply()
        guard=self.app/'UserData/OriginalServer/offline-update.private.json'
        prior=json.loads(guard.read_bytes())
        self.before={rel:(self.app/rel).read_bytes() for rel in update.FILES}
        self.after={rel:('third '+rel).encode() for rel in update.FILES if rel!='release-manifest.json'}
        revised=json.loads(self.before['release-manifest.json'])
        for rel in update.CONTROLLERS:revised['controllerFiles'][rel]=update.sha(self.after[rel])
        self.after['release-manifest.json']=json.dumps(revised).encode()
        self.spec=dict(self.spec,updateId=str(uuid.uuid4()),previousReservation=prior,
            baseReleaseManifestSHA256=update.sha(self.before['release-manifest.json']),
            updatedReleaseManifestSHA256=update.sha(self.after['release-manifest.json']),
            files={rel:{'before':update.sha(self.before[rel]),'after':update.sha(self.after[rel]),'bytes':len(self.after[rel])} for rel in update.FILES})
        for rel,raw in self.after.items():(self.bundle/'payload'/rel).write_bytes(raw)
        self.save_spec()
        return guard,prior
    def test_exact_successor_before_initialization_keeps_prior_backup(self):
        guard,prior=self.prepare_next_delta()
        result=self.apply();self.assertTrue(result['applied']);self.assertFalse(result['databaseOpened'])
        self.assertEqual(json.loads(guard.read_bytes())['updateId'],self.spec['updateId'])
        self.assertNotEqual(prior['updateId'],self.spec['updateId'])
        for rel,raw in self.after.items():self.assertEqual((self.app/rel).read_bytes(),raw)
        self.assertEqual(len(list((self.app/'UserData/OriginalOfflineUpdate').glob('*/result.json'))),2)
    def test_successor_without_exact_prior_reservation_is_refused(self):
        guard,prior=self.prepare_next_delta();self.spec.pop('previousReservation');self.save_spec()
        with self.assertRaisesRegex(ValueError,'OTHER_OFFLINE_UPDATE_RESERVATION'):self.apply()
        self.assert_before();self.assertEqual(json.loads(guard.read_bytes()),prior)
    def test_successor_with_changed_prior_pin_is_refused(self):
        guard,prior=self.prepare_next_delta();self.spec['previousReservation']=dict(prior,patchSHA256='f'*64);self.save_spec()
        with self.assertRaisesRegex(ValueError,'OTHER_OFFLINE_UPDATE_RESERVATION'):self.apply()
        self.assert_before();self.assertEqual(json.loads(guard.read_bytes()),prior)
    def test_apply_and_idempotent_after_runtime_initialization(self):
        result=self.apply();self.assertTrue(result['applied']);self.assertFalse(result['runtimeStarted']);self.assertFalse(result['iisChanged'])
        for rel,raw in self.after.items():self.assertEqual((self.app/rel).read_bytes(),raw)
        (self.app/'UserData/OriginalServer/installation.json').write_bytes(b'initialized fixture')
        self.assertTrue(self.apply()['alreadyApplied'])
        self.assertEqual((self.app/'UserData/OriginalServer/installation.json').read_bytes(),b'initialized fixture')
    def test_initialized_base_refused_without_touching_data(self):
        d=self.app/'UserData/OriginalServer';d.mkdir(parents=True);(d/'installation.json').write_bytes(b'keep test data')
        with self.assertRaisesRegex(ValueError,'INITIALIZED_SERVER'):self.apply()
        self.assert_before();self.assertEqual(list(d.iterdir()),[d/'installation.json'])
    def test_changed_payload_refused_before_reservation(self):
        (self.bundle/'payload'/update.CONTROLLERS[0]).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'PAYLOAD_CHANGED'):self.apply()
        self.assert_before();self.assertFalse((self.app/'UserData').exists())
    def test_changed_patch_manifest_refused(self):
        self.manifest.write_bytes(self.manifest.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'MANIFEST_CHANGED'):self.apply()
        self.assert_before()
    def test_controller_byte_lock_blocks_offline_mutation(self):
        import msvcrt
        d=self.app/'UserData/OriginalServer';d.mkdir(parents=True)
        with (d/'server-owner.lock').open('w+b') as lock:
            lock.write(b'0');lock.flush();lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            with self.assertRaises(OSError):self.apply()
            self.assert_before();self.assertFalse((d/'offline-update.private.json').exists())
    def test_changed_installed_controller_refused(self):
        (self.app/update.CONTROLLERS[0]).write_bytes(b'operator edit')
        with self.assertRaisesRegex(ValueError,'BASE_CONTROLLER_DRIFT'):self.apply()
        self.assertEqual((self.app/update.CONTROLLERS[0]).read_bytes(),b'operator edit')
        self.assertFalse((self.app/'UserData').exists())
    def test_partial_write_failure_restores_all_old_bytes(self):
        real=update.atomic;calls=0
        def fail_once(p,raw):
            nonlocal calls;calls+=1
            if calls==4:raise OSError('owned write fixture failure')
            return real(p,raw)
        with patch.object(update,'atomic',side_effect=fail_once),self.assertRaisesRegex(OSError,'fixture failure'):self.apply()
        self.assert_before()
        reports=list((self.app/'UserData/OriginalOfflineUpdate').glob('*/result.json'))
        self.assertEqual(len(reports),1);self.assertTrue(json.loads(reports[0].read_bytes())['rolledBack'])
    def test_unrelated_concurrent_edit_is_retained(self):
        real=update.atomic;calls=0;foreign=self.app/update.CONTROLLERS[0]
        def edit_once(p,raw):
            nonlocal calls;calls+=1
            if calls==4:foreign.write_bytes(b'operator edit during update');raise OSError('concurrent fixture')
            return real(p,raw)
        with patch.object(update,'atomic',side_effect=edit_once),self.assertRaisesRegex(OSError,'concurrent fixture'):self.apply()
        self.assertEqual(foreign.read_bytes(),b'operator edit during update')
        reports=list((self.app/'UserData/OriginalOfflineUpdate').glob('*/result.json'))
        self.assertTrue(json.loads(reports[0].read_bytes())['concurrentEditDetected'])
    def test_extra_or_parent_path_is_refused(self):
        self.spec['files']['../outside']={'before':'a'*64,'after':'b'*64,'bytes':1};self.save_spec()
        with self.assertRaisesRegex(ValueError,'EXACT_CONTROLLER_DELTA'):self.apply()
        self.assert_before();self.assertFalse((self.app/'UserData').exists())

if __name__=='__main__':unittest.main()
