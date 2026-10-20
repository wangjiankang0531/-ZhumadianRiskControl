"""Attachment ownership, revision binding, historical availability, limits and raw restore."""
import base64,copy,hashlib,http.client,json,sqlite3,tempfile,threading,unittest
from contextlib import closing
from pathlib import Path
from services.reference_demo import DemoStore,DemoError
from services.reference_plan_materials import MAX_BYTES,MAX_ACTIVE,MATERIAL_TABLES
from services.tests.test_reference_plans import form,review
from tools.serve_reference_demo import make_server
PDF=b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF'
class MaterialTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'qa.sqlite';self.store=DemoStore(self.path)
 def tearDown(self):self.tmp.cleanup()
 def draft(self):return self.store.save_plan(form(),'模拟企业甲','模拟编制','draft',None,None)
 def add(self,v,raw=PDF,name='模拟预案.pdf'):
  r=v['record'];return self.store.add_plan_material(r['id'],r['revision'],name,'application/pdf',base64.b64encode(raw).decode(),'合成附件验收')
 def action(self,v,action):return self.store.plan_action(v['record']['id'],v['record']['revision'],action,'模拟'+action,review() if action in ('approve','reject') else None)
 def submit(self,v):return self.store.save_plan(v['plan']['versions'][0]['form'],'模拟企业甲','提交模拟评审','submit',v['record']['id'],v['record']['revision'])
 def test_review_reference_survives_rejection_and_draft_unlink(self):
  v=self.add(self.draft());mid=v['plan']['versions'][0]['materials'][0]['material_id'];identity=v['record']['id']
  self.assertEqual(self.store.plan_material(identity,1,mid)[0],PDF)
  v=self.action(self.submit(v),'reject');rr=v['record']['revision'];snapshot=copy.deepcopy(v['plan']['versions'][0]['reviews'][0])
  v=self.store.remove_plan_material(identity,rr,mid);self.assertEqual(v['plan']['versions'][0]['materials'],[])
  self.assertEqual(v['plan']['versions'][0]['reviews'][0],snapshot)
  with self.assertRaises(DemoError):self.store.plan_material(identity,1,mid)
  self.assertEqual(self.store.plan_material(identity,1,mid,rr)[0],PDF)
  self.assertEqual(snapshot['reviewed_form']['materials'][0]['sha256'],hashlib.sha256(PDF).hexdigest())
 def test_published_old_attachment_unchanged_when_revised(self):
  v=self.add(self.draft());mid=v['plan']['versions'][0]['materials'][0]['material_id'];v=self.action(self.action(self.submit(v),'approve'),'publish')
  with self.assertRaises(DemoError):self.add(v)
  with self.assertRaises(DemoError):self.store.remove_plan_material(v['record']['id'],v['record']['revision'],mid)
  v=self.action(v,'revise');self.assertEqual(v['plan']['versions'][0]['materials'],v['plan']['versions'][1]['materials'])
  v=self.store.remove_plan_material(v['record']['id'],v['record']['revision'],mid)
  self.assertEqual(self.store.plan_material(v['record']['id'],1,mid)[0],PDF)
  with closing(self.store.connect()) as db:self.assertEqual(db.execute('SELECT count(*) FROM demo_plan_materials').fetchone()[0],1)
 def test_plan_ownership_stale_revision_bad_metadata_and_tamper(self):
  v=self.draft();added=self.add(v);mid=added['plan']['versions'][0]['materials'][0]['material_id'];other=self.draft()
  with self.assertRaises(DemoError) as e:self.add(v)
  self.assertEqual(e.exception.status,409)
  with self.assertRaises(DemoError):self.store.plan_material(other['record']['id'],1,mid)
  for name in ('../x.pdf','x.pdf\r\nInjected: yes','x.pdf.exe','x\u202epdf.pdf'):
   with self.assertRaises(DemoError):self.add(added,name=name)
  with self.assertRaises(DemoError):self.add(added,raw=b'not a PDF')
  with self.assertRaises(DemoError):self.add(added,raw=b'%PDF-'+b' '*MAX_BYTES+b'%%EOF')
  with closing(self.store.connect()) as db:db.execute('UPDATE demo_plan_materials SET sha256=?',('0'*64,));db.commit()
  with self.assertRaises(DemoError) as e:self.store.plan_material(added['record']['id'],1,mid)
  self.assertEqual(e.exception.status,503)
 def test_capacity_and_parallel_cas_leave_single_audited_write(self):
  v=self.draft();results=[];barrier=threading.Barrier(2)
  def upload():
   barrier.wait()
   try:self.add(v);results.append(200)
   except DemoError as e:results.append(e.status)
  threads=[threading.Thread(target=upload) for _ in range(2)]
  for t in threads:t.start()
  for t in threads:t.join()
  self.assertEqual(sorted(results),[200,409]);v=self.store.detail('plans',v['record']['id'])
  for _ in range(MAX_ACTIVE-1):v=self.add(v)
  with self.assertRaises(DemoError):self.add(v)
  self.assertEqual(len(self.store.detail('plans',v['record']['id'])['events']),MAX_ACTIVE+1)
 def test_retained_payload_budget_counts_unlinked_history(self):
  v=self.draft();large=b'%PDF-'+b' '*(MAX_BYTES-10)+b'%%EOF';self.assertEqual(len(large),MAX_BYTES)
  for _ in range(16):
   v=self.add(v,raw=large);mid=v['plan']['versions'][0]['materials'][0]['material_id'];v=self.store.remove_plan_material(v['record']['id'],v['record']['revision'],mid)
  with self.assertRaises(DemoError) as error:self.add(v)
  self.assertEqual(error.exception.status,409)
  with closing(self.store.connect()) as db:self.assertEqual(db.execute('SELECT sum(bytes) FROM demo_plan_materials').fetchone()[0],32*1048576)
 def test_restore_all_blobs_links_and_v2_upgrade_preserves_rows(self):
  v=self.add(self.draft());v=self.action(self.submit(v),'approve');target=Path(self.tmp.name)/'restored.sqlite'
  with closing(self.store.connect()) as src,closing(sqlite3.connect(target)) as dst:src.backup(dst)
  restored=DemoStore(target);self.assertEqual(restored.detail('plans',v['record']['id']),v)
  with closing(self.store.connect()) as src,closing(restored.connect()) as dst:
   for table in MATERIAL_TABLES:self.assertEqual([tuple(r) for r in src.execute('SELECT * FROM '+table)],[tuple(r) for r in dst.execute('SELECT * FROM '+table)])
   self.assertEqual(dst.execute('PRAGMA foreign_key_check').fetchall(),[])
  legacy=Path(self.tmp.name)/'legacy_v2.sqlite';empty=self.draft()
  with closing(sqlite3.connect(legacy)) as db:
   # Material-free layout exactly matches v2; migration adds tables without rewriting rows.
   from services.reference_demo import SCHEMA
   db.executescript(SCHEMA.split('CREATE TABLE IF NOT EXISTS demo_plan_materials')[0]);db.execute('PRAGMA user_version=2');db.commit()
  DemoStore(legacy)
  with closing(sqlite3.connect(legacy)) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3)
class MaterialHTTPTests(unittest.TestCase):
 def test_upload_download_headers_and_protected_scope(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);server=make_server(0,root,root/'qa.sqlite');thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   try:
    v=server.store.save_plan(form(),'模拟企业甲','模拟编制','draft',None,None);identity=v['record']['id'];port=server.server_port;headers={'Origin':f'http://127.0.0.1:{port}','X-XNBY-Demo':server.demo_token,'Content-Type':'application/json'}
    body=dict(identity=identity,revision=1,name='模拟预案.pdf',mediaType='application/pdf',base64Data=base64.b64encode(PDF).decode(),description='HTTP原字节验收')
    c=http.client.HTTPConnection('127.0.0.1',port,timeout=5);c.request('POST','/api/demo/plan-material',json.dumps(body),headers);r=c.getresponse();v=json.loads(r.read());self.assertEqual(r.status,200);mid=v['plan']['versions'][0]['materials'][0]['material_id']
    c.request('GET',f'/api/demo/plan-material?id={identity}&version=1&materialId={mid}');r=c.getresponse();self.assertEqual(r.status,200);self.assertEqual(r.read(),PDF);self.assertEqual(r.getheader('Content-Type'),'application/octet-stream');self.assertTrue(r.getheader('Content-Disposition').startswith('attachment; filename*='));self.assertEqual(r.getheader('X-Content-Type-Options'),'nosniff')
    c.request('GET',f'/api/demo/plan-material?id={identity}&version=999&materialId={mid}');r=c.getresponse();self.assertEqual(r.status,404);r.read();c.close()
   finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main()
