from pathlib import Path
from contextlib import closing
import base64,hashlib,sqlite3,tempfile,unittest,uuid
from services.business_workflow import WorkflowStore,DemoError
RAW=b'%PDF-1.4\n% Workflow test evidence\n%%EOF'

class MaterialTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=WorkflowStore(Path(self.tmp.name)/'workflow.sqlite');self.users=['reporter','executor','reviewer','observer']
  self.d=self.store.create('reporter',self.users,uuid.uuid4().hex,dict(kind='hazard',title='材料验收',enterprise='验收单位',location='测试位置',description='材料原字节及审计测试'))
 def tearDown(self):self.tmp.cleanup()
 def upload(self,d=None,key=None,actor='reporter',raw=RAW,name='evidence.pdf'):
  d=d or self.d
  return self.store.add_material(actor,self.users,key or uuid.uuid4().hex,d['record']['id'],d['record']['revision'],name,'application/pdf',base64.b64encode(raw).decode(),'测试附件说明')
 def test_immutable_original_bytes_and_case_revision_audit(self):
  d=self.upload();m=d['materials'][0];raw,meta=self.store.material('reviewer',self.users,d['record']['id'],m['id'])
  self.assertEqual(raw,RAW);self.assertEqual(meta['sha256'],hashlib.sha256(RAW).hexdigest());self.assertEqual(d['record']['revision'],2);self.assertEqual(d['events'][-1]['action'],'material');self.assertEqual(d['tasks'][-1]['status'],'pending')
  with self.assertRaises(DemoError):self.store.material('reporter',self.users,'other-case',m['id'])
 def test_replay_single_blob_and_changed_payload_conflict(self):
  key=uuid.uuid4().hex;d=self.upload(key=key);again=self.upload(key=key);self.assertEqual(d['materials'],again['materials'])
  with self.assertRaises(DemoError):self.upload(key=key,raw=RAW.replace(b'test',b'case'))
  with closing(self.store.connect()) as db:self.assertEqual(db.execute('SELECT count(*) FROM wf_materials').fetchone()[0],1)
 def test_invalid_type_path_capacity_and_foreign_actor_are_rejected(self):
  for name in ('../bad.pdf','bad.exe'):
   with self.assertRaises(DemoError):self.upload(name=name)
  with self.assertRaises(DemoError):self.upload(actor='observer')
  with self.assertRaises(DemoError):self.upload(raw=b'not a pdf')
  d=self.d
  for _ in range(8):d=self.upload(d)
  with self.assertRaises(DemoError):self.upload(d)
  self.assertEqual(self.store.detail('reporter',self.users,d['record']['id'])['record']['revision'],9)
 def test_corrupt_blob_is_detected_without_repair(self):
  d=self.upload();m=d['materials'][0]
  with closing(self.store.connect()) as db:db.execute('UPDATE wf_materials SET payload=? WHERE id=?',(b'x'*len(RAW),m['id']));db.commit()
  with self.assertRaises(DemoError) as error:self.store.material('reporter',self.users,d['record']['id'],m['id'])
  self.assertEqual(error.exception.status,503)
  with closing(self.store.connect()) as db:self.assertEqual(bytes(db.execute('SELECT payload FROM wf_materials').fetchone()[0]),b'x'*len(RAW))

if __name__=='__main__':unittest.main()
