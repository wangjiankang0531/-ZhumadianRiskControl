import concurrent.futures,json,sqlite3,tempfile,unittest,uuid
from contextlib import closing
from pathlib import Path
from services.business_workflow import WorkflowStore,DemoError

class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'workflow.sqlite';self.s=WorkflowStore(self.path);self.users=['reporter','executor','reviewer'];self.actor='reporter'
 def tearDown(self):self.tmp.cleanup()
 def create(self,kind='hazard',**extra):
  if kind=='event' and 'coordinates' not in extra:extra['coordinates']=dict(longitude=0,latitude=0,system='WGS84')
  form=dict(kind=kind,title='测试业务闭环',enterprise='验收企业',location='仓储区',description='由验收人员明确录入的业务内容',**extra)
  return self.s.create('reporter',self.users,uuid.uuid4().hex,form)
 def command(self,d,action,actor='reporter',**data):
  return self.s.command(actor,self.users,uuid.uuid4().hex,d['record']['id'],d['record']['revision'],action,dict(note='验收处理说明',**data))
 def assigned(self,kind='hazard',**extra):
  return self.command(self.create(kind,**extra),'submit' if kind=='work' else 'dispatch',assignee='executor',reviewer='reviewer',dueDate='2099-01-01')
 def correct(self,d):return self.command(d,'correct','executor',department='安全管理组',actualDate='2026-10-22',reason='设备维护不足',description='已完成更换及现场检查',cost='12.50')
 def test_no_fixture_counts_and_persistence(self):
  self.assertEqual(self.s.summary('reporter',self.users)['total'],0)
  d=self.create();reopened=WorkflowStore(self.path);self.assertEqual(reopened.detail('reporter',self.users,d['record']['id']),d)
  self.assertEqual(reopened.summary('reporter',self.users)['counts'],{'hazard':1})
 def test_hazard_assign_rectify_reject_and_close_updates_todos(self):
  d=self.assigned();self.assertEqual(self.s.summary('executor',self.users)['pending'],1)
  d=self.correct(d);self.assertEqual(d['record']['state'],'review');self.assertEqual(len(d['corrections']),1)
  self.assertEqual(self.s.summary('executor',self.users)['pending'],0);self.assertEqual(self.s.summary('reviewer',self.users)['pending'],1)
  d=self.command(d,'reject','reviewer');d=self.correct(d);d=self.command(d,'approve','reviewer')
  self.assertEqual(d['record']['state'],'closed');self.assertEqual(len(d['corrections']),2)
  self.assertEqual([e['revision'] for e in d['events']],list(range(1,7)));self.assertEqual(self.s.summary('reviewer',self.users)['pending'],0)
 def test_actor_cannot_spoof_or_self_review_and_bad_write_is_atomic(self):
  d=self.create()
  with self.assertRaises(DemoError):self.command(d,'dispatch',assignee='executor',reviewer='executor',dueDate='2099-01-01')
  self.assertEqual(self.s.detail('reporter',self.users,d['record']['id'])['record']['revision'],1)
  with self.assertRaises(DemoError):self.command(d,'dispatch','executor',assignee='executor',reviewer='reviewer',dueDate='2099-01-01')
  with self.assertRaises(DemoError):self.s.summary('foreign',self.users)
 def test_idempotent_replay_returns_current_record_and_content_conflict(self):
  key=uuid.uuid4().hex;form=dict(kind='event',title='验收事件',enterprise='验收企业',location='园区',description='现场上报内容',coordinates=dict(longitude=0,latitude=0,system='WGS84'))
  d=self.s.create('reporter',self.users,key,form);self.assertEqual(self.s.create('reporter',self.users,key,form)['record']['id'],d['record']['id'])
  with self.assertRaises(DemoError):self.s.create('reporter',self.users,key,{**form,'title':'变更内容'})
  self.assertEqual(self.s.summary('reporter',self.users)['total'],1)
 def test_concurrent_same_revision_has_one_winner(self):
  d=self.assigned()
  def submit(_):
   try:self.correct(d);return 200
   except DemoError as e:return e.status
  with concurrent.futures.ThreadPoolExecutor(2) as pool:codes=list(pool.map(submit,range(2)))
  self.assertEqual(sorted(codes),[200,409])
  self.assertEqual(len(self.s.detail('executor',self.users,d['record']['id'])['corrections']),1)
 def test_inspection_all_points_required_and_abnormal_creates_linked_hazard(self):
  d=self.assigned('inspection',points=[dict(name='储罐阀门',standard='无跑冒滴漏'),dict(name='消防通道',standard='通道畅通')])
  with self.assertRaises(DemoError):self.command(d,'finish','executor')
  d=self.command(d,'point','executor',position=0,result='abnormal');issue=d['points'][0]['issue_id'];self.assertTrue(issue)
  h=self.s.detail('executor',self.users,issue);self.assertEqual(h['record']['parent_id'],d['record']['id']);self.assertEqual(h['record']['state'],'reported')
  with self.assertRaises(DemoError):self.command(d,'point','executor',position=0,result='normal')
  d=self.command(d,'point','executor',position=1,result='normal');d=self.command(d,'finish','executor');d=self.command(d,'approve','reviewer');self.assertEqual(d['record']['state'],'closed')
 def test_work_cannot_start_without_measures_briefing_and_applicable_gas(self):
  d=self.assigned('work',workType='动火作业');d=self.command(d,'approve','reviewer')
  with self.assertRaises(DemoError):self.command(d,'start','executor')
  d=self.command(d,'measure','executor');d=self.command(d,'brief','executor')
  with self.assertRaises(DemoError):self.command(d,'start','executor')
  d=self.command(d,'gas','executor');d=self.command(d,'start','executor');d=self.command(d,'finish','executor');d=self.command(d,'approve','reviewer');self.assertEqual(d['record']['state'],'closed');self.assertEqual(len(d['checks']),3)
 def test_event_resource_reservations_are_atomic_and_must_return_before_close(self):
  stock=self.s.create_resource('reporter',self.users,uuid.uuid4().hex,dict(name='应急物资',category='装备',warehouse='应急库',unit='套',quantity=3))['records'][0]
  d=self.assigned('event');d=self.command(d,'reserve','executor',resourceId=stock['id'],quantity=2)
  self.assertEqual(self.s.resources('reporter',self.users)['records'][0]['available'],1)
  other=self.assigned('event')
  with self.assertRaises(DemoError):self.command(other,'reserve','executor',resourceId=stock['id'],quantity=2)
  d=self.command(d,'resolve','executor')
  with self.assertRaises(DemoError):self.command(d,'approve','reviewer')
  d=self.command(d,'reject','reviewer');d=self.command(d,'return','executor',resourceId=stock['id']);d=self.command(d,'resolve','executor');d=self.command(d,'approve','reviewer');self.assertEqual(d['record']['state'],'closed');self.assertEqual(self.s.resources('reporter',self.users)['records'][0]['available'],3)
 def test_resource_register_replay_does_not_duplicate_stock(self):
  key=uuid.uuid4().hex;form=dict(name='物资A',category='装备',warehouse='应急库',unit='套',quantity=3)
  self.s.create_resource('reporter',self.users,key,form);self.s.create_resource('reporter',self.users,key,form);self.assertEqual(len(self.s.resources('reporter',self.users)['records']),1)
 def test_invalid_fields_dates_money_and_literal_search(self):
  with self.assertRaises(DemoError):self.create('work',workType='未知类别')
  with self.assertRaises(DemoError):self.create('inspection',points=[])
  with self.assertRaises(DemoError):self.create(dueDate='2026-02-30')
  d=self.assigned()
  with self.assertRaises(DemoError):self.command(d,'correct','executor',department='安全组',actualDate='2026-10-22',reason='原因',description='情况',cost='NaN')
  self.assertEqual(self.s.list('reporter',self.users,q="' OR 1=1 --")['total'],0)
 def test_coordinates_preserve_declared_system_and_reject_invalid_or_missing_event_position(self):
  d=self.create('event',coordinates=dict(longitude=0,latitude=0,system='GCJ02'));self.assertEqual(d['record']['details']['coordinates']['system'],'GCJ02')
  for coordinates in (dict(longitude=181,latitude=0,system='WGS84'),dict(longitude=0,latitude=91,system='WGS84'),dict(longitude=float('nan'),latitude=0,system='WGS84'),dict(longitude=True,latitude=0,system='WGS84'),dict(longitude=0,latitude=0,system='unknown')):
   with self.assertRaises(DemoError):self.create('hazard',coordinates=coordinates)
  with self.assertRaises(DemoError):self.s.create('reporter',self.users,uuid.uuid4().hex,dict(kind='event',title='无坐标事件',enterprise='测试',location='测试',description='测试'))
 def test_reference_withdrawal_clears_old_todo_and_keeps_audit(self):
  d=self.assigned();d=self.command(d,'withdraw')
  self.assertEqual(d['record']['state'],'reported');self.assertEqual(d['record']['assignee'],'')
  self.assertEqual(self.s.summary('executor',self.users)['pending'],0)
  self.assertEqual(self.s.summary('reporter',self.users)['pending'],1)
  self.assertEqual(d['events'][-1]['action'],'withdraw')
  d=self.command(d,'dispatch',assignee='executor',reviewer='reviewer',dueDate='2099-01-01');d=self.correct(d);d=self.command(d,'reject','reviewer')
  self.assertNotIn('withdraw',self.s.detail('reporter',self.users,d['record']['id'])['actions'])
  with self.assertRaises(DemoError):self.command(d,'withdraw')
 def test_reference_prevention_and_explicit_review_history_survive_rejection(self):
  d=self.assigned();d=self.command(d,'correct','executor',department='维护组',actualDate='2026-10-22',reason='密封老化',description='更换密封并复测',cost='25.00',preventiveMeasures='每周检查密封状态')
  self.assertEqual(d['corrections'][0]['preventive_measures'],'每周检查密封状态')
  d=self.command(d,'reject','reviewer');d=self.correct(d);d=self.command(d,'approve','reviewer')
  self.assertEqual([x['result'] for x in d['reviews']],['return','pass'])
  self.assertEqual([x['actor'] for x in d['reviews']],['reviewer','reviewer'])
  self.assertEqual(len(d['corrections']),2)
 def test_reference_investigation_child_preserves_standard_source_and_coordinates(self):
  coords=dict(longitude=114.1,latitude=33.1,system='CGCS2000')
  d=self.assigned('investigation',points=[dict(name='安全出口',standard='出口畅通')],coordinates=coords)
  d=self.command(d,'point','executor',position=0,result='abnormal');h=self.s.detail('executor',self.users,d['points'][0]['issue_id'])
  self.assertEqual(h['record']['details']['source'],'隐患排查')
  self.assertEqual(h['record']['details']['checkStandard'],'出口畅通')
  self.assertEqual(h['record']['details']['coordinates'],coords)
  self.assertEqual(self.s.catalog('reporter',self.users)['referenceRevision'],'20261022-r2')
 def test_reference_event_category_and_dynamic_overdue_not_state_override(self):
  d=self.create('event',eventType='验收事件类别',dueDate='2000-01-01')
  self.assertEqual(d['record']['details']['eventType'],'验收事件类别');self.assertTrue(d['record']['isOverdue'])
  self.assertEqual(d['record']['state'],'triage')
 def test_v1_copy_migration_preserves_rows_blobs_and_original_backup(self):
  import hashlib
  d=self.correct(self.assigned());old=Path(self.tmp.name)/'old-v1.sqlite'
  sql=(Path(__file__).parent/'fixtures/workflow_v1.sql').read_text('utf-8')
  with closing(sqlite3.connect(old)) as dst,closing(self.s.connect()) as src:
   dst.executescript(sql)
   for row in dst.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
    name=row[0];cols=[r[1] for r in dst.execute('PRAGMA table_info('+name+')')]
    data=[tuple(x) for x in src.execute('SELECT '+','.join(cols)+' FROM '+name)]
    dst.executemany('INSERT INTO '+name+' ('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',data)
   dst.commit();self.assertEqual(dst.execute('PRAGMA user_version').fetchone()[0],1)
  backup=Path(self.tmp.name)/'immutable-v1.sqlite';backup.write_bytes(old.read_bytes());digest=hashlib.sha256(backup.read_bytes()).hexdigest()
  migrated=WorkflowStore(old);value=migrated.detail('executor',self.users,d['record']['id'])
  self.assertEqual(value['record'],d['record']);self.assertEqual(value['events'],d['events']);self.assertEqual(value['corrections'][0]['cost'],'12.50');self.assertEqual(value['corrections'][0]['preventive_measures'],'');self.assertEqual(value['reviews'],[])
  with closing(migrated.connect()) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],2);self.assertEqual(list(db.execute('PRAGMA foreign_key_check')),[])
  self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(),digest)
 def test_backup_restore_all_relations_and_foreign_keys(self):
  hazard=self.correct(self.assigned())
  import base64
  self.s.add_material('reporter',self.users,uuid.uuid4().hex,hazard['record']['id'],hazard['record']['revision'],'evidence.pdf','application/pdf',base64.b64encode(b'%PDF-1.4\n%%EOF').decode(),'备份材料原字节')
  inspection=self.assigned('inspection',points=[dict(name='检查点',standard='检查标准')]);self.command(inspection,'point','executor',position=0,result='abnormal')
  work=self.command(self.assigned('work',workType='高处作业'),'approve','reviewer');self.command(work,'measure','executor')
  stock=self.s.create_resource('reporter',self.users,uuid.uuid4().hex,dict(name='应急物资',category='装备',warehouse='库房',unit='套',quantity=5))['records'][0];self.command(self.assigned('event'),'reserve','executor',resourceId=stock['id'],quantity=2)
  backup=Path(self.tmp.name)/'backup.sqlite'
  with closing(self.s.connect()) as src,closing(sqlite3.connect(backup)) as dst:src.backup(dst)
  restored=WorkflowStore(backup)
  with closing(self.s.connect()) as src,closing(restored.connect()) as dst:
   names=[r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
   for name in names:
    expected=list(src.execute('SELECT * FROM '+name));self.assertTrue(expected,name);self.assertEqual(expected,list(dst.execute('SELECT * FROM '+name)))
   self.assertEqual(list(dst.execute('PRAGMA foreign_key_check')),[])

if __name__=='__main__':unittest.main()
