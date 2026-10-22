"""Persistence and cross-type invariants of synthetic work reservations."""
import copy,json,sqlite3,tempfile,unittest,threading,http.client
from contextlib import closing
from pathlib import Path
from services.reference_demo import DemoStore,DemoError,MODULES
from services.reference_work_forms import TYPES,SCHEMA_ID,synthetic_form,catalog_schema
from tools.serve_reference_demo import make_server

class WorkFormTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'work.sqlite';self.store=DemoStore(self.path)
 def tearDown(self):self.tmp.cleanup()
 def save(self,form,action='submit',identity=None,revision=None):
  return self.store.save_work_form(form,'模拟企业乙','独立合成验收',action,identity,revision)
 def test_eight_types_persist_actual_fields_and_people(self):
  expected={'动火作业':'动火地点及部位','受限空间作业':'受限空间内原有介质名称','盲板抽堵作业':'盲板位置图及编号','高处作业':'作业高度','吊装作业':'吊物质量(t)','临时用电作业':'工作电压','动土作业':'作业范围、内容、方式','断路作业':'断路地段示意图及相关说明'}
  for i,kind in enumerate(TYPES,1):
   form=synthetic_form(i);result=self.save(form);record=result['record']
   self.assertEqual(record['workForm']['jobType'],kind);self.assertIn(expected[kind],record['workForm']['values'])
   self.assertEqual(record['state'],'待核验');self.assertEqual(record['fields']['作业类型'],kind)
   self.assertEqual(result['detailFields'],{});self.assertEqual(result['events'][0]['kind'],'work_simulated_submit')
   reloaded=DemoStore(self.path).detail('work-reservation',record['id'])['record']
   self.assertEqual(record,reloaded)
  kinds={r['fields']['作业类型'] for page in (1,2) for r in self.store.list('work-reservation',page=page)['records'] if r['id'].startswith('DEMO-WORK-')}
  self.assertEqual(kinds,set(TYPES))
 def test_partial_draft_edit_cas_and_submit(self):
  form=dict(schema=SCHEMA_ID,jobType='高处作业',values={},people={});r=self.save(form,'draft')['record']
  self.assertEqual(r['state'],'草稿')
  with self.assertRaises(DemoError):self.store.change('work-reservation',r['id'],1,'不得绕过完整性检查')
  edited=self.save(synthetic_form(4),'draft',r['id'],1)['record'];self.assertEqual(edited['revision'],2)
  with self.assertRaises(DemoError) as error:self.save(synthetic_form(1),'submit',r['id'],1)
  self.assertEqual(error.exception.status,409)
  result=self.save(edited['workForm'],'submit',r['id'],2);self.assertEqual(result['record']['revision'],3)
  self.assertEqual([e['revision'] for e in result['events']],[1,2,3])
  with self.assertRaises(DemoError):self.save(edited['workForm'],'draft',r['id'],3)
 def test_validation_failures_leave_no_records_or_events(self):
  variants=[]
  for value in ('NaN','Infinity','-1','0','nonsense'):
   f=synthetic_form(4);f['values']['作业高度']=value;variants.append(f)
  f=synthetic_form(1);f['values']['工作电压']='12';variants.append(f)
  f=synthetic_form(1);f['values']['动火级别']='低';variants.append(f)
  f=synthetic_form(2);f['people']['基层单位监护人']=[];variants.append(f)
  f=synthetic_form(1);f['people']['作业人员'][0]['联系方式']='';variants.append(f)
  f=synthetic_form(1);f['values']['实施结束时间']=f['values']['实施开始时间'];variants.append(f)
  f=synthetic_form(1);f['values']['作业内容']='长'*201;variants.append(f)
  f=synthetic_form(1);f['people']['作业人员']*=13;variants.append(f)
  for f in variants:
   with self.assertRaises(DemoError):self.save(f)
  self.assertEqual(self.store.list('work-reservation')['total'],12)
  with closing(self.store.connect()) as db:self.assertEqual(db.execute("SELECT COUNT(*) FROM demo_events WHERE entity='work-reservation'").fetchone()[0],12)
 def test_utc_comparison_and_backup_restore(self):
  form=synthetic_form(1);form['values'].update({'实施开始时间':'2026-10-18T10:00:00+08:00','实施结束时间':'2026-10-18T03:00:00Z'})
  r=self.save(form)['record'];self.assertEqual(r['workForm']['values']['实施开始时间'],'2026-10-18T02:00:00+00:00')
  backup=Path(self.tmp.name)/'restored.sqlite'
  with closing(self.store.connect()) as source,closing(sqlite3.connect(backup)) as target:source.backup(target)
  restored=DemoStore(backup).detail('work-reservation',r['id']);self.assertEqual(restored['record'],r)
  self.assertEqual(len(restored['events']),1)
 def test_legacy_fixture_upgrade_is_idempotent_and_preserves_data(self):
  identity='DEMO-WORK-RESERVATION-001'
  with closing(self.store.connect()) as db:
   row=db.execute('SELECT payload FROM demo_records WHERE entity=? AND id=?',('work-reservation',identity)).fetchone();payload=json.loads(row[0]);del payload['workForm'];payload['note']='保留原模拟备注';payload['fields']['自定义旧字段']='旧值'
   db.execute('UPDATE demo_records SET payload=? WHERE entity=? AND id=?',(json.dumps(payload),'work-reservation',identity));db.commit()
  r=DemoStore(self.path).detail('work-reservation',identity);self.assertEqual(r['record']['note'],'保留原模拟备注');self.assertEqual(r['record']['fields']['自定义旧字段'],'旧值');self.assertEqual(r['record']['revision'],2)
  again=DemoStore(self.path).detail('work-reservation',identity);self.assertEqual(r,again)
 def test_generic_create_cannot_bypass_typed_schema(self):
  with self.assertRaises(DemoError):self.store.create('work-reservation',{c:'模拟' for c in MODULES['work-reservation']['columns']},'模拟企业甲','')
 def test_launcher_forks_live_wal_once_without_overwriting_new_edits(self):
  from tools.launch_reference_demo import backup_previous_demo
  root=Path(self.tmp.name)/'ReferenceWeb_0.8.7';old=root.parent/'ReferenceWeb_0.8.6/Assets/Demo/reference_demo.sqlite';old.parent.mkdir(parents=True)
  with closing(sqlite3.connect(old)) as source:
   source.execute('PRAGMA journal_mode=WAL');source.execute('CREATE TABLE proof(value TEXT)');source.execute("INSERT INTO proof VALUES ('old-live-wal')");source.commit()
   target=root/'Assets/Demo/reference_demo.sqlite';backup_previous_demo(root,target)
   with closing(sqlite3.connect(target)) as new:
    self.assertEqual(new.execute('SELECT value FROM proof').fetchone()[0],'old-live-wal');new.execute("UPDATE proof SET value='new-team-edit'");new.commit()
   backup_previous_demo(root,target)
   with closing(sqlite3.connect(target)) as new:self.assertEqual(new.execute('SELECT value FROM proof').fetchone()[0],'new-team-edit')
   self.assertEqual(source.execute('SELECT value FROM proof').fetchone()[0],'old-live-wal')
 def test_http_contract(self):
  static=Path(self.tmp.name)/'static';static.mkdir();server=make_server(0,static,self.path);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
  try:
   with self.assertRaises(OSError):make_server(server.server_port,static,self.path)
   host='127.0.0.1:'+str(server.server_port);client=http.client.HTTPConnection(host)
   client.request('GET','/api/demo/catalog');response=client.getresponse();catalog=json.loads(response.read());self.assertEqual(len(catalog['workFormSchema']['types']),8);self.assertEqual(catalog['version'],'0.9.0')
   body=json.dumps(dict(form=synthetic_form(8),enterprise='模拟企业甲',note='',action='submit',identity=None,revision=None))
   client.request('POST','/api/demo/work-reservation',body,{'Content-Type':'application/json','Origin':'http://'+host,'X-XNBY-Demo':catalog['token']});response=client.getresponse();value=json.loads(response.read());self.assertEqual(response.status,200);self.assertEqual(value['record']['workForm']['jobType'],'断路作业')
   client.request('POST','/api/demo/work-reservation',body,{'Content-Type':'application/json','Origin':'http://evil.invalid','X-XNBY-Demo':catalog['token']});response=client.getresponse();response.read();self.assertEqual(response.status,403);client.close()
  finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
