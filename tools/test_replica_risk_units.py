"""Isolated risk-unit contract, authorization, transaction and recovery checks."""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
import json,sqlite3,tempfile,threading,unittest,uuid
from services.replica_risk_units import RiskPrincipal,ProjectDirectory,RiskUnitStore,SCHEMA,canonical
from services.reference_errors import DemoError

GRANTS=frozenset('risk-unit:'+v for v in ('create','read','update','delete','export','audit'))
def key():return uuid.uuid4().hex
def directory(project='p'):
 return ProjectDirectory(project,[{'id':'d1','name':'一部'},{'id':'d2','name':'二部'}],[{'id':'a','name':'测试管理员','departments':['d1','d2']},{'id':'u1','name':'测试甲','departments':['d1']},{'id':'u2','name':'测试乙','departments':['d2']},{'id':'off','name':'停用测试','departments':['d1'],'enabled':False}],[{'code':'red','name':'重大风险'},{'code':'blue','name':'低风险'}],'directory-1')

class RiskTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'risk.sqlite';self.s=RiskUnitStore(self.path);self.d=directory();self.p=RiskPrincipal('p','a',GRANTS,frozenset(['d1','d2']),'policy-1')
 def form(self,**kw):return dict(departmentId='d1',department='一部',personId='u1',person='测试甲',analysisObject='合成测试装置',analysisUnit='合成测试单元',riskLevel='red',coordinate='114.025,32.98',**kw)
 def fail(self,status,fn,*args,**kw):
  with self.assertRaises(DemoError) as c:fn(*args,**kw)
  self.assertEqual(c.exception.status,status)
 def counts(self):
  with closing(self.s.connect()) as db:return [db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('rp_risk_units','rp_risk_events','rp_risk_requests','rp_risk_outbox')]
 def create(self):return self.s.save(self.p,self.d,key(),self.form())
 def test_persistence_actor_dictionary_and_outbox(self):
  r=self.create();self.assertEqual((r['revision'],r['createBy'],r['coordinateSystem']),(1,'a','待核实'));self.assertEqual(self.counts(),[1,1,1,1]);self.assertEqual(RiskUnitStore(self.path).get(self.p,self.d,r['id']),r)
  with closing(self.s.connect()) as db:
   x=db.execute('SELECT * FROM rp_risk_outbox').fetchone();self.assertEqual((x['state'],x['event']),('pending','risk-unit.create'));self.assertEqual(json.loads(x['payload'])['record'],r)
 def test_reject_required_unknown_and_invalid_fields_atomically(self):
  for field in ('department','person','analysisObject','analysisUnit','riskLevel','coordinate'):
   v=self.form();v[field]='';self.fail(400,self.s.save,self.p,self.d,key(),v)
  for field,value in [('riskLevel','not-configured'),('actor','someone'),('departmentId',[]),('coordinateSystem','EPSG:random')]:
   v=self.form();v[field]=value;self.fail(400,self.s.save,self.p,self.d,key(),v)
  self.assertEqual(self.counts(),[0,0,0,0])
 def test_coordinate_range_nonfinite_and_underflow_rejected(self):
  for v in ('NaN,1','Infinity,1','181,1','1,91','1e-100000000,0','1,2,3','一,二','1.0000000000001,2'):
   form=self.form();form['coordinate']=v;self.fail(400,self.s.save,self.p,self.d,key(),form)
  for v in ('-180,-90','+180,90','.12,-.4'):
   form=self.form();form['coordinate']=v;self.assertEqual(self.s.save(self.p,self.d,key(),form)['coordinate'],v)
 def test_person_department_and_disabled_user_rejected(self):
  for name,identity in [('测试乙','u2'),('停用测试','off')]:
   v=self.form();v.update(person=name,personId=identity);self.fail(400,self.s.save,self.p,self.d,key(),v)
  self.fail(403,self.s.query,replace(self.p,subject='off'),self.d)
 def test_duplicate_display_names_need_stable_identity(self):
  d=ProjectDirectory('p',[{'id':'d1','name':'同名部'},{'id':'d2','name':'同名部'}],[{'id':'a','name':'同名人','departments':['d1','d2']},{'id':'b','name':'同名人','departments':['d1']}],[{'code':'red','name':'重大风险'}],'dir-2')
  f=self.form();f.update(department='同名部',person='同名人',personId='a');self.assertEqual(self.s.save(self.p,d,key(),f)['departmentId'],'d1')
  for omitted in ('departmentId','personId'):
   v=dict(f);v.pop(omitted);self.fail(400,self.s.save,self.p,d,key(),v)
 def test_directory_cycles_and_invalid_memberships(self):
  with self.assertRaises(ValueError):ProjectDirectory('p',[{'id':'d','name':'部','parent':'d'}],[],[{'code':'r','name':'红'}],'v')
  with self.assertRaises(ValueError):ProjectDirectory('p',[],[{'id':'a','name':'甲','departments':['missing']}],[{'code':'r','name':'红'}],'v')
 def test_project_and_department_isolation(self):
  r=self.create();p=replace(self.p,departments=frozenset(['d2']));self.assertEqual(self.s.query(p,self.d)['total'],0);self.fail(404,self.s.get,p,self.d,r['id']);self.fail(403,self.s.save,p,self.d,key(),self.form())
  p=replace(self.p,project='other');self.assertEqual(self.s.query(p,directory('other'))['total'],0);self.fail(404,self.s.get,p,directory('other'),r['id'])
  self.fail(403,self.s.get,p,self.d,r['id'])
 def test_empty_scope_and_grant_enforcement(self):
  r=self.create();p=replace(self.p,departments=frozenset());self.assertEqual(self.s.query(p,self.d)['records'],[]);self.fail(404,self.s.get,p,self.d,r['id'])
  p=replace(self.p,permissions=frozenset(['risk-unit:read']));self.fail(403,self.s.delete,p,self.d,key(),r['id'],1);self.fail(403,self.s.query,p,self.d,export=True)
 def test_exact_replay_no_duplicate_and_conflict(self):
  k=key();r=self.s.save(self.p,self.d,k,self.form());self.assertEqual(self.s.save(self.p,self.d,k,self.form()),r);self.assertEqual(self.counts(),[1,1,1,1]);f=self.form();f['analysisUnit']='另一个';self.fail(409,self.s.save,self.p,self.d,k,f)
 def test_scope_revoked_replay_does_not_disclose_old_response(self):
  k=key();r=self.s.save(self.p,self.d,k,self.form());f=self.form();f.update(departmentId='d2',department='二部',personId='u2',person='测试乙');self.s.save(self.p,self.d,key(),f,identity=r['id'],revision=1)
  # Original request form remains allowed, but its record has moved outside this principal's current scope.
  p=replace(self.p,departments=frozenset(['d1']));self.fail(404,self.s.save,p,self.d,k,self.form())
 def test_old_snapshot_scope_checked_after_move(self):
  k=key();r=self.s.save(self.p,self.d,k,self.form());f=self.form();f.update(departmentId='d2',department='二部',personId='u2',person='测试乙');self.s.save(self.p,self.d,key(),f,identity=r['id'],revision=1)
  p=replace(self.p,departments=frozenset(['d2']));self.fail(403,self.s.save,p,self.d,k,self.form())
 def test_optimistic_concurrent_updates(self):
  r=self.create();barrier=threading.Barrier(2)
  def save(n):
   f=self.form();f['analysisUnit']=str(n);barrier.wait()
   try:return self.s.save(self.p,self.d,key(),f,identity=r['id'],revision=1)['revision']
   except DemoError as e:return e.status
  with ThreadPoolExecutor(2) as pool:results=list(pool.map(save,[1,2]))
  self.assertEqual(sorted(results),[2,409]);self.assertEqual(self.counts(),[1,2,2,2])
 def test_soft_delete_history_and_replay(self):
  r=self.create();k=key();deleted=self.s.delete(self.p,self.d,k,r['id'],1);self.assertTrue(deleted['deleted']);self.assertEqual(deleted['revision'],2);self.fail(404,self.s.get,self.p,self.d,r['id']);self.assertEqual(self.s.query(self.p,self.d)['total'],0);self.assertEqual(self.s.delete(self.p,self.d,k,r['id'],1),deleted);self.assertEqual([v['action'] for v in self.s.history(self.p,self.d,r['id'])],['create','delete'])
 def test_stale_version_and_boolean_revision(self):
  r=self.create();self.s.save(self.p,self.d,key(),self.form(),identity=r['id'],revision=1);self.fail(409,self.s.delete,self.p,self.d,key(),r['id'],1);self.fail(400,self.s.delete,self.p,self.d,key(),r['id'],True)
 def test_outbox_failure_rolls_back_everything(self):
  with closing(self.s.connect()) as db:db.execute("CREATE TRIGGER fail_outbox BEFORE INSERT ON rp_risk_outbox BEGIN SELECT RAISE(ABORT,'injected'); END")
  with self.assertRaises(sqlite3.IntegrityError):self.create()
  self.assertEqual(self.counts(),[0,0,0,0])
 def test_history_corruption_detected_without_repair(self):
  r=self.create()
  with closing(self.s.connect()) as db:db.execute("UPDATE rp_risk_events SET sha256='broken'")
  self.fail(503,self.s.history,self.p,self.d,r['id'])
  with closing(self.s.connect()) as db:self.assertEqual(db.execute('SELECT sha256 FROM rp_risk_events').fetchone()[0],'broken')
 def test_replay_tampering_detected(self):
  k=key();self.s.save(self.p,self.d,k,self.form())
  with closing(self.s.connect()) as db:
   row=json.loads(db.execute('SELECT result FROM rp_risk_requests').fetchone()[0]);row['analysisObject']='篡改';db.execute('UPDATE rp_risk_requests SET result=?',(canonical(row),))
  self.fail(503,self.s.save,self.p,self.d,k,self.form())
 def test_literal_filters_and_pagination(self):
  for value in ('百分%号','下划_线',"引号'测试"):
   f=self.form();f['analysisObject']=value;self.s.save(self.p,self.d,key(),f)
  self.assertEqual(self.s.query(self.p,self.d,{'analysisObject':'%'})['total'],1);self.assertEqual(len(self.s.query(self.p,self.d,current=2,size=2)['records']),1);self.assertEqual(len(self.s.query(self.p,self.d,export=True)['records']),3)
  self.fail(400,self.s.query,self.p,self.d,{'where':'1=1'});self.fail(400,self.s.query,self.p,self.d,current=True)
 def test_online_backup_restore_all_relations(self):
  r=self.create();self.s.save(self.p,self.d,key(),self.form(),identity=r['id'],revision=1);self.s.delete(self.p,self.d,key(),r['id'],2);self.create();backup=Path(self.tmp.name)/'restored.sqlite'
  with closing(self.s.connect()) as source,closing(sqlite3.connect(backup)) as dest:source.backup(dest)
  restored=RiskUnitStore(backup)
  with closing(self.s.connect()) as source,closing(restored.connect()) as dest:
   for t in ('rp_risk_units','rp_risk_events','rp_risk_requests','rp_risk_outbox'):self.assertEqual([tuple(r) for r in source.execute('SELECT * FROM '+t+' ORDER BY rowid')],[tuple(r) for r in dest.execute('SELECT * FROM '+t+' ORDER BY rowid')])
   self.assertEqual(dest.execute('PRAGMA integrity_check').fetchone()[0],'ok');self.assertEqual(dest.execute('PRAGMA foreign_key_check').fetchall(),[])
  self.assertEqual(len(restored.history(self.p,self.d,r['id'])),3)
 def test_foreign_schema_and_unknown_version_no_repair(self):
  for name,sql in [('foreign','CREATE TABLE user_records(id TEXT)'),('future','PRAGMA user_version=99'),('partial','PRAGMA user_version=1; CREATE TABLE rp_risk_units(id TEXT)')]:
   path=Path(self.tmp.name)/(name+'.sqlite')
   with closing(sqlite3.connect(path)) as db:db.executescript(sql)
   before=path.read_bytes()
   with self.assertRaises(ValueError):RiskUnitStore(path)
   self.assertEqual(path.read_bytes(),before)

if __name__=='__main__':unittest.main(verbosity=2)
