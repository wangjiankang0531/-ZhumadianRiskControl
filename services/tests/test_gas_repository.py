"""Real isolated SQLite transactions, revisions, scopes and durable delivery leases."""
import base64,concurrent.futures,hashlib,json,sqlite3,tempfile,unittest,uuid
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from pathlib import Path
from services.auth import Principal
from services.common import ApiError
from services.gas_repository import GasRepository,digest
from services.tests.test_gas_domain import SOURCE,LOCATION,ALL

PDF=b'%PDF-1.4\nSynthetic public gas evidence\n%%EOF\n'
class GasRepositoryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'gas.sqlite';self.now=datetime(2026,10,19,3,0,tzinfo=timezone.utc);self.points=frozenset({'PUBLIC-POINT'})
  self.op=Principal('QA-OP','QA',ALL,frozenset({'A','B'}),True,True,'qa-policy-v1');self.source=replace(self.op,subject='QA-SOURCE');self.result=replace(self.op,subject='QA-RESULT')
  self.a=replace(self.op,subject='QA-A',permissions=frozenset({'gas:read','gas:cooperate'}),enterprises=frozenset({'A'}),all_enterprises=False);self.b=replace(self.a,subject='QA-B',enterprises=frozenset({'B'}));self.reader=replace(self.a,subject='QA-READER',permissions=frozenset({'gas:read'}),enterprises=frozenset())
  self.store=self.open();self.event=self.store.ingest(self.source,self.points,SOURCE,uuid.uuid4().hex)['event']
 def tearDown(self):self.temp.cleanup()
 def open(self):return GasRepository(self.path,source_system='QA-MONITOR',source_subjects=['QA-SOURCE'],emergency_system='QA-EMERGENCY',result_subjects=['QA-RESULT'],clock=lambda:self.now.isoformat())
 def error(self,code,fn):
  with self.assertRaises(ApiError) as e:fn()
  self.assertEqual(e.exception.code,code)
 def move(self,action,body,actor=None,key=None):
  result=self.store.mutate(actor or self.op,self.points,self.event['id'],action,{'revision':self.event['revision'],**body},key or uuid.uuid4().hex);self.event=result['event'];return result
 def verify(self,refs=None):return self.move('verify',{'conclusion':'continue','note':'合成现场核实','verifiedAt':self.now.isoformat(),'location':LOCATION,'materialRefs':refs or []})
 def pending(self,request_id=None):
  self.verify();self.request_id=request_id or uuid.uuid4().hex;self.move('handoff-request',{'requestId':self.request_id,'reason':'合成应急转办'});return self.request_id
 def upload(self,actor=None,scope='public',enterprise=None,key=None,**patch):
  body={'revision':self.event['revision'],'name':'合成材料.pdf','mediaType':'application/pdf','base64':base64.b64encode(PDF).decode(),'description':'合成现场材料','scope':scope,'enterpriseId':enterprise,**patch};out=self.store.add_material(actor or self.op,self.points,self.event['id'],body,key or uuid.uuid4().hex);self.event=out['event'];return out
 def counts(self):
  with self.store.transaction() as db:return {t:db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('gas_alerts','gas_history','gas_requests','gas_outbox','gas_materials','gas_delivery_attempts')}
 def test_restart_preserves_exact_source_and_public_scope(self):
  self.store=self.open();actual=self.store.detail(self.reader,self.points,self.event['id']);self.assertEqual(actual['source']['document'],SOURCE);self.assertEqual(actual['source']['document']['concentration'],'12.5000');self.assertEqual(self.store.list(self.reader,self.points)['total'],1)
  for actor,points in [(replace(self.op,tenant='OTHER'),self.points),(replace(self.op,public_spatial=False),self.points),(self.op,frozenset())]:self.error('NOT_FOUND',lambda:self.store.detail(actor,points,self.event['id']));self.assertEqual(self.store.list(actor,points)['total'],0)
 def test_source_and_result_identities_are_pinned_and_separate(self):
  self.error('SOURCE_ADAPTER_FORBIDDEN',lambda:self.store.ingest(self.op,self.points,SOURCE,uuid.uuid4().hex));self.error('SOURCE_SYSTEM_CONFLICT',lambda:self.store.ingest(self.source,self.points,{**SOURCE,'sourceSystem':'UNTRUSTED'},uuid.uuid4().hex))
  unconfigured=GasRepository(Path(self.temp.name)/'unconfigured.sqlite');self.error('SOURCE_ADAPTER_NOT_CONFIGURED',lambda:unconfigured.ingest(self.source,self.points,SOURCE,uuid.uuid4().hex))
  with self.assertRaises(ValueError):GasRepository(Path(self.temp.name)/'bad.sqlite',source_subjects=['SAME'],result_subjects=['SAME'])
  self.pending();result={'requestId':self.request_id,'externalSystem':'QA-EMERGENCY','externalId':'QA-X','state':'accepted','note':'合成回执'};self.error('RESULT_ADAPTER_FORBIDDEN',lambda:self.move('handoff-result',result,self.source));self.error('RESULT_SYSTEM_CONFLICT',lambda:self.move('handoff-result',{**result,'externalSystem':'FAKE'},self.result))
 def test_source_duplicate_key_and_revision_are_independent(self):
  key=uuid.uuid4().hex;source={**SOURCE,'sourceEventId':'ANOMALY-2'};one=self.store.ingest(self.source,self.points,source,key);again=self.store.ingest(self.source,self.points,source,key);self.assertTrue(again['replayed']);self.assertEqual(one['event']['id'],again['event']['id'])
  self.error('IDEMPOTENCY_CONFLICT',lambda:self.store.ingest(self.source,self.points,{**source,'area':'different'},key));self.error('SOURCE_ALREADY_REGISTERED',lambda:self.store.ingest(self.source,self.points,source,uuid.uuid4().hex))
  body={'source':{**SOURCE,'sourceRevision':2,'unit':'ppm','concentration':'1250.00','trend':[]}};self.move('source-update',body,self.source);self.assertEqual(self.event['source']['document']['unit'],'ppm');self.error('SOURCE_REVISION_CONFLICT',lambda:self.move('source-update',body,self.source))
 def test_idempotent_replay_rechecks_current_point_and_command_permissions(self):
  key=uuid.uuid4().hex;body={'revision':1,'classification':'persistent','note':'合成分类'};self.store.mutate(self.op,self.points,self.event['id'],'classify',body,key)
  replay=self.store.mutate(self.op,self.points,self.event['id'],'classify',body,key);self.assertTrue(replay['replayed']);self.assertEqual(replay['committedRevision'],2)
  self.error('NOT_FOUND',lambda:self.store.mutate(self.op,frozenset(),self.event['id'],'classify',body,key));self.error('FORBIDDEN',lambda:self.store.mutate(replace(self.op,permissions=frozenset({'gas:read'})),self.points,self.event['id'],'classify',body,key))
  self.error('IDEMPOTENCY_CONFLICT',lambda:self.store.mutate(self.op,self.points,self.event['id'],'classify',{**body,'note':'changed'},key))
 def test_material_bytes_same_revision_journal_and_restart(self):
  self.verify();self.assertIsNotNone(self.event['verification']);upload=self.upload();meta=upload['material'];self.assertIsNone(self.event['verification']);self.assertEqual(meta['revision'],self.event['revision']);self.store=self.open()
  actual,raw=self.store.material(self.reader,self.points,self.event['id'],meta['id']);self.assertEqual(raw,PDF);self.assertEqual(actual,meta);self.assertEqual(meta['sha256'],hashlib.sha256(PDF).hexdigest());self.assertEqual(self.store.history(self.op,self.points,self.event['id'])[-1]['data']['material'],meta)
  self.verify([meta['id']]);self.assertEqual(self.event['verification']['materialRefs'],[meta['id']]);self.move('classify',{'classification':'persistent','note':'新增分类重新核实'});self.assertIsNone(self.event['verification'])
 def test_private_materials_and_history_refs_do_not_cross_enterprises(self):
  a=self.upload(self.a,'enterprise','A')['material'];b=self.upload(self.b,'enterprise','B')['material'];self.verify([a['id'],b['id']])
  self.assertEqual(self.store.materials(self.a,self.points,self.event['id'])['items'],[a]);self.error('NOT_FOUND',lambda:self.store.material(self.a,self.points,self.event['id'],b['id']))
  projection=self.store.detail(self.a,self.points,self.event['id']);self.assertEqual(projection['verification']['materialRefs'],[a['id']]);history=self.store.history(self.a,self.points,self.event['id']);self.assertEqual(history[2]['kind'],'restricted');self.assertNotIn(b['id'],json.dumps(history));self.assertEqual(history[-1]['data']['materialRefs'],[a['id']]);self.assertEqual(self.store.materials(self.reader,self.points,self.event['id'])['total'],0)
 def test_private_upload_replay_revocation_and_metadata_injection_refused(self):
  self.error('FORBIDDEN',lambda:self.upload(self.a));self.error('NOT_FOUND',lambda:self.upload(self.a,'enterprise','B'));self.error('MATERIAL_UPLOAD_REQUIRED',lambda:self.move('material',{'material':{}}))
  key=uuid.uuid4().hex;revision=self.event['revision'];meta=self.upload(self.a,'enterprise','A',key)['material'];replay=self.upload(self.a,'enterprise','A',key,revision=revision);self.assertTrue(replay['replayed']);self.assertEqual(replay['material'],meta)
  self.error('NOT_FOUND',lambda:self.upload(replace(self.a,enterprises=frozenset()),'enterprise','A',key,revision=revision));self.assertEqual(self.counts()['gas_materials'],1)
 def test_material_refs_bind_event_and_corruption_is_refused(self):
  meta=self.upload()['material'];other=self.store.ingest(self.source,self.points,{**SOURCE,'sourceEventId':'OTHER'},uuid.uuid4().hex)['event'];self.event=other;self.error('NOT_FOUND',lambda:self.verify([meta['id']]))
  self.event=self.store.list(self.op,self.points)['items'][-1]
  # Select the owning event explicitly rather than relying on row order.
  with self.store.transaction() as db:owner=db.execute('SELECT event_id FROM gas_materials').fetchone()[0]
  self.event=self.store.detail(self.op,self.points,owner)
  with self.store.transaction(write=True) as db:db.execute('UPDATE gas_materials SET payload=?',(b'X'*len(PDF),))
  with self.assertRaises(ValueError):self.store.material(self.op,self.points,owner,meta['id'])
  with self.assertRaises(ValueError):self.verify([meta['id']])
 def test_material_failure_rolls_back_all_four_tables(self):
  before=self.counts();revision=self.event['revision']
  with self.store.transaction(write=True) as db:db.execute("CREATE TRIGGER fail_material BEFORE INSERT ON gas_materials BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
  with self.assertRaises(sqlite3.IntegrityError):self.upload()
  self.assertEqual(self.counts(),before);self.assertEqual(self.store.detail(self.op,self.points,self.event['id'])['revision'],revision)
 def test_outbox_failure_rolls_back_snapshot_history_and_key(self):
  self.verify();before=self.counts();revision=self.event['revision']
  with self.store.transaction(write=True) as db:db.execute("CREATE TRIGGER fail_outbox BEFORE INSERT ON gas_outbox BEGIN SELECT RAISE(ABORT,'synthetic failure'); END")
  with self.assertRaises(sqlite3.IntegrityError):self.move('handoff-request',{'requestId':uuid.uuid4().hex,'reason':'合成'})
  self.assertEqual(self.counts(),before);self.assertEqual(self.store.detail(self.op,self.points,self.event['id'])['revision'],revision)
 def test_concurrent_revision_has_exactly_one_commit(self):
  def call(_):
   try:self.store.mutate(self.op,self.points,self.event['id'],'classify',{'revision':1,'classification':'persistent','note':'合成并发'},uuid.uuid4().hex);return 200
   except ApiError as e:return e.status
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:codes=list(pool.map(call,range(2)))
  self.assertEqual(sorted(codes),[200,409]);self.assertEqual(self.counts()['gas_history'],2);self.assertEqual(self.counts()['gas_requests'],2)
 def test_sent_transport_is_not_business_acceptance_and_survives_restart(self):
  request=self.pending();claim=self.store.claim(self.op,self.points,request);self.assertEqual(digest(claim['package']),claim['packageSHA256']);self.store=self.open();sent=self.store.finish_delivery(self.op,self.points,request,claim['leaseToken'],sent=True);self.assertEqual(sent['deliveryState'],'awaiting-result');self.assertEqual(self.store.detail(self.op,self.points,self.event['id'])['handoff']['state'],'pending-delivery')
  self.error('DELIVERY_NOT_DUE',lambda:self.store.claim(self.op,self.points,request));self.error('DELIVERY_LEASE_CONFLICT',lambda:self.store.finish_delivery(self.op,self.points,request,claim['leaseToken'],sent=True))
  self.move('handoff-result',{'requestId':request,'externalSystem':'QA-EMERGENCY','externalId':'QA-X','state':'accepted','note':'合成接收'},self.result);self.assertEqual(self.event['handoff']['state'],'accepted')
  with self.store.transaction() as db:self.assertEqual(db.execute('SELECT delivery_state FROM gas_outbox').fetchone()[0],'accepted');self.assertEqual(db.execute('SELECT outcome FROM gas_delivery_attempts').fetchone()[0],'sent')
 def test_expired_lease_cannot_finish_new_attempt(self):
  request=self.pending();old=self.store.claim(self.op,self.points,request,lease_seconds=5);self.error('DELIVERY_NOT_DUE',lambda:self.store.claim(self.op,self.points,request));self.now+=timedelta(seconds=6);new=self.store.claim(self.op,self.points,request);self.assertEqual(new['attempt'],2)
  self.error('DELIVERY_LEASE_CONFLICT',lambda:self.store.finish_delivery(self.op,self.points,request,old['leaseToken'],sent=True));self.store.finish_delivery(self.op,self.points,request,new['leaseToken'],sent=False,error_code='QA_TIMEOUT')
  self.error('DELIVERY_NOT_DUE',lambda:self.store.claim(self.op,self.points,request));self.now+=timedelta(minutes=1);third=self.store.claim(self.op,self.points,request);self.assertEqual(third['attempt'],3)
  with self.store.transaction() as db:self.assertEqual([r[0] for r in db.execute('SELECT outcome FROM gas_delivery_attempts ORDER BY attempt')],['expired','failed','inflight'])
 def test_ten_failed_deliveries_stop_without_new_attempts(self):
  request=self.pending()
  for i in range(10):
   claim=self.store.claim(self.op,self.points,request);response=self.store.finish_delivery(self.op,self.points,request,claim['leaseToken'],sent=False,error_code='QA_UNAVAILABLE');self.now+=timedelta(hours=2)
  self.assertEqual(response['deliveryState'],'failed');self.error('DELIVERY_NOT_DUE',lambda:self.store.claim(self.op,self.points,request));self.assertEqual(self.counts()['gas_delivery_attempts'],10)
 def test_revoked_scope_cannot_claim_or_finish_and_callback_closes_lease(self):
  request=self.pending();self.error('NOT_FOUND',lambda:self.store.claim(self.op,frozenset(),request));claim=self.store.claim(self.op,self.points,request);self.error('FORBIDDEN',lambda:self.store.finish_delivery(self.reader,self.points,request,claim['leaseToken'],sent=True))
  self.move('handoff-result',{'requestId':request,'externalSystem':'QA-EMERGENCY','externalId':'QA-X','state':'completed','note':'合成完成'},self.result);self.error('DELIVERY_LEASE_CONFLICT',lambda:self.store.finish_delivery(self.op,self.points,request,claim['leaseToken'],sent=True))
  with self.store.transaction() as db:self.assertEqual(db.execute('SELECT outcome FROM gas_delivery_attempts').fetchone()[0],'acknowledged')
 def test_request_id_unique_across_events_and_all_past_rounds(self):
  request=self.pending();self.move('handoff-result',{'requestId':request,'externalSystem':'QA-EMERGENCY','externalId':'QA-X','state':'completed','note':'合成完成'},self.result)
  self.move('source-update',{'source':{**SOURCE,'sourceRevision':2}},self.source);self.verify();second=uuid.uuid4().hex;self.move('handoff-request',{'requestId':second,'reason':'第二轮'});self.move('handoff-result',{'requestId':second,'externalSystem':'QA-EMERGENCY','externalId':'QA-Y','state':'completed','note':'第二轮完成'},self.result);self.verify();before=self.counts();self.error('HANDOFF_IDENTITY_REUSED',lambda:self.move('handoff-request',{'requestId':request,'reason':'不能复用历史ID'}));self.assertEqual(self.counts(),before)
  self.event=self.store.ingest(self.source,self.points,{**SOURCE,'sourceEventId':'OTHER'},uuid.uuid4().hex)['event'];self.verify();self.error('HANDOFF_IDENTITY_REUSED',lambda:self.move('handoff-request',{'requestId':second,'reason':'不能跨事件复用'}))
 def test_cooperation_projection_and_generic_history_keep_ownership(self):
  body={'enterpriseId':'A','state':'following','activities':['pipeline'],'statement':'企业甲合成说明','measures':'甲合成措施'};self.move('cooperate',body,self.a);self.assertEqual(self.store.detail(self.b,self.points,self.event['id'])['cooperation'],{});history=self.store.history(self.b,self.points,self.event['id']);self.assertEqual(history[-1]['kind'],'restricted');self.assertNotIn('甲合成',json.dumps(history,ensure_ascii=False))

if __name__=='__main__':unittest.main()
