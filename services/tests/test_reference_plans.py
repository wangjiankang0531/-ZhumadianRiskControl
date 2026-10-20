"""Business lifecycle, immutable old publication, CAS, migration and restore evidence."""
import copy,json,sqlite3,tempfile,unittest,threading,http.client
from pathlib import Path
from contextlib import closing
from services.reference_demo import DemoStore,DemoError,SCHEMA
from services.reference_plans import SCHEMA_ID,FIELDS,REVIEW_FIELDS,PLAN_TABLES,CATEGORIES
from tools.serve_reference_demo import make_server

def form():
 return dict(schema=SCHEMA_ID,values={k:('2026-10-20' if k=='compiledDate' else CATEGORIES[0] if k=='category' else '模拟'+label) for k,label in FIELDS.items()},steps=[dict(title='接报研判',department='模拟指挥组',content='模拟确认事件并通知现场处置组')])
def review():
 return {k:('2026-10-20' if k.endswith('Date') else '否' if k=='notified' else '模拟'+label) for k,label in REVIEW_FIELDS.items()}
class PlanTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'qa.sqlite';self.store=DemoStore(self.path)
 def tearDown(self):self.tmp.cleanup()
 def save(self,f=None,action='submit',r=None):
  return self.store.save_plan(f or form(),'模拟企业甲','合成验收',action,r['id'] if r else None,r['revision'] if r else None)
 def action(self,v,action,review_value=None):
  return self.store.plan_action(v['record']['id'],v['record']['revision'],action,'模拟'+action,review_value)
 def published(self):return self.action(self.action(self.save(),'approve',review()),'publish')
 def test_review_publish_revise_keeps_old_active_until_new_publish(self):
  v=self.published();identity=v['record']['id'];old=copy.deepcopy(v['plan']['versions'][0]);self.assertEqual(v['plan']['publishedVersion'],1)
  revised=self.action(v,'revise');self.assertEqual(revised['plan']['publishedVersion'],1);self.assertEqual(revised['plan']['currentVersion'],2)
  self.assertEqual(revised['plan']['versions'][1],old)
  f=form();f['values']['name']='模拟新版预案';v=self.save(f,r=revised['record'])
  approved=self.action(v,'approve',review());self.assertEqual(approved['plan']['publishedVersion'],1)
  result=self.action(approved,'publish');self.assertEqual(result['plan']['publishedVersion'],2)
  history=result['plan']['versions'][1];self.assertEqual(history['status'],'historical');self.assertEqual(history['form'],old['form']);self.assertEqual(history['reviews'],old['reviews']);self.assertEqual(history['publishedAt'],old['publishedAt'])
  self.assertEqual([e['revision'] for e in result['events']],list(range(1,8)))
  self.assertEqual(DemoStore(self.path).detail('plans',identity),result)
 def test_cas_and_illegal_transition_are_atomic(self):
  v=self.save();identity=v['record']['id']
  with self.assertRaises(DemoError):self.action(v,'publish')
  self.assertEqual(self.store.detail('plans',identity),v)
  approved=self.action(v,'approve',review())
  with self.assertRaises(DemoError) as error:self.action(v,'approve',review())
  self.assertEqual(error.exception.status,409);self.assertEqual(self.store.detail('plans',identity),approved)
  for method in [lambda:self.store.change('plans',identity,2,'绕过'),lambda:self.store.create('plans',{},'模拟企业甲','绕过')]:
   with self.assertRaises(DemoError):method()
 def test_rejected_form_snapshot_survives_edit_and_review_json_order(self):
  v=self.save();r=review();r=dict(reversed(list(r.items())))
  v=self.action(v,'reject',r);snapshot=copy.deepcopy(v['plan']['versions'][0]['reviews'][0])
  f=form();f['values']['name']='修订后的模拟草稿';v=self.save(f,'draft',v['record'])
  self.assertEqual(v['plan']['versions'][0]['reviews'][0],snapshot)
  self.assertEqual(snapshot['review_date'],'2026-10-20');self.assertEqual(snapshot['opinion'],'模拟评审意见')
  self.assertNotEqual(snapshot['reviewed_form'],v['plan']['versions'][0]['form'])
 def test_draft_validation_and_entity_ownership(self):
  empty=dict(schema=SCHEMA_ID,values={},steps=[]);v=self.save(empty,'draft')
  with self.assertRaises(DemoError):self.save(empty,'submit',v['record'])
  before=self.store.detail('plans',v['record']['id'])
  with self.assertRaises(DemoError):self.store.save_plan(form(),'模拟企业乙','归属不可改','draft',v['record']['id'],1)
  self.assertEqual(self.store.detail('plans',v['record']['id']),before)
  for bad in ('2026-02-30','2026-1-1','x'):
   f=form();f['values']['compiledDate']=bad
   with self.assertRaises(DemoError):self.save(f)
  f=form();f['steps'][0]['content']=''
  with self.assertRaises(DemoError):self.save(f)
  with self.assertRaises(DemoError):self.store.plan_action(v['record']['id'],True,'publish','说明',None)
 def test_concurrent_revision_only_one_commit(self):
  v=self.save();results=[];barrier=threading.Barrier(2)
  def run():
   barrier.wait()
   try:self.action(v,'approve',review());results.append(200)
   except DemoError as error:results.append(error.status)
  threads=[threading.Thread(target=run) for _ in range(2)]
  for t in threads:t.start()
  for t in threads:t.join()
  self.assertEqual(sorted(results),[200,409]);self.assertEqual(len(self.store.detail('plans',v['record']['id'])['events']),2)
 def test_backup_restore_normalized_rows_and_review_bytes(self):
  v=self.action(self.published(),'revise');target=Path(self.tmp.name)/'restored.sqlite'
  with closing(self.store.connect()) as src,closing(sqlite3.connect(target)) as dst:src.backup(dst)
  restored=DemoStore(target);self.assertEqual(restored.detail('plans',v['record']['id']),v)
  for table in PLAN_TABLES+('demo_records','demo_events'):
   with closing(self.store.connect()) as src,closing(restored.connect()) as dst:self.assertEqual([tuple(r) for r in src.execute('SELECT * FROM '+table)],[tuple(r) for r in dst.execute('SELECT * FROM '+table)])
 def test_v1_upgrade_preserves_old_seed_records_and_does_not_fabricate_approval(self):
  legacy=Path(self.tmp.name)/'v1.sqlite'
  with closing(sqlite3.connect(legacy)) as db:
   db.executescript(SCHEMA.split('CREATE TABLE IF NOT EXISTS demo_plan_versions')[0]);db.execute('PRAGMA user_version=1');db.commit()
  store=DemoStore(legacy);r=store.detail('plans','DEMO-PLANS-003');self.assertIsNone(r['plan']);self.assertEqual(r['record']['state'],'已发布')
  self.assertEqual(len(r['events']),1)
  with closing(store.connect()) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],3);self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(),[])
  self.assertEqual(DemoStore(legacy).detail('plans',r['record']['id']),r)
class PlanHTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.server=make_server(0,root,root/'qa.sqlite');self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
 def req(self,path,body=None,authorized=True):
  port=self.server.server_port;c=http.client.HTTPConnection('127.0.0.1',port,timeout=5);headers={'Content-Type':'application/json'}
  if authorized:headers.update({'Origin':f'http://127.0.0.1:{port}','X-XNBY-Demo':self.server.demo_token})
  c.request('POST' if body is not None else 'GET','/api/demo/'+path,json.dumps(body) if body is not None else None,headers);r=c.getresponse();raw=json.loads(r.read());c.close();return r.status,raw
 def test_http_auth_and_full_workflow_contract(self):
  code,catalog=self.req('catalog');self.assertEqual(code,200);self.assertEqual(catalog['planSchema']['schema'],SCHEMA_ID);self.assertEqual(catalog['demoSchemaVersion'],3)
  body=dict(form=form(),enterprise='模拟企业甲',note='HTTP模拟',action='submit',identity=None,revision=None)
  self.assertEqual(self.req('plan',body,False)[0],403)
  code,result=self.req('plan',body);self.assertEqual(code,200);r=result['record']
  action=dict(identity=r['id'],revision=1,action='approve',note='模拟HTTP通过',review=review())
  self.assertEqual(self.req('plan-action',action)[0],200);self.assertEqual(self.req('plan-action',action)[0],409)
  action.update(revision=2,action='publish',review=None)
  self.assertEqual(self.req('plan-action',action)[1]['plan']['publishedVersion'],1)
  self.assertEqual(self.req('plan-action',{**action,'unknown':True})[0],400)
 def test_generated_models_match_real_ddl_and_are_deterministic(self):
  from tools.generate_reference_demo_docs import generate
  root=Path(self.tmp.name);a=root/'a';b=root/'b';model=generate(a);generate(b)
  self.assertEqual(model['version'],3);self.assertEqual(len(model['tables']),9)
  for file in a.iterdir():self.assertEqual(file.read_bytes(),(b/file.name).read_bytes())
  self.assertEqual(model['tables']['demo_plan_reviews']['mysqlTypes']['reviewed_form'],'LONGBLOB')
  self.assertTrue(model['tables']['demo_plan_heads']['foreignKeys'])
if __name__=='__main__':unittest.main()
