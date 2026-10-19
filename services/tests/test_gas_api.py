"""Actual JWT/policy/API/gateway gas workflow requests, isolated sources and SQLite only."""
import base64,hashlib,http.client,json,threading,unittest,uuid
from services.tests import test_api as fixture
from services.tests.test_gas_domain import SOURCE,LOCATION
from services.tests.test_gas_repository import PDF
from services.api import Service
from services.auth import PERMISSIONS
from tools.authenticated_portal_server import PortalServer

class GasApiTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.ApiTests.setUpClass()
 def setUp(self):
  self.p=fixture.ApiTests();self.p.setUp();gas=['gas:read','gas:ingest','gas:verify','gas:cooperate','gas:handoff']
  for row in self.p.policy['principals']:row['permissions']+=gas
  self.p.policy['principals'] += [{'subject':subject,'enabled':True,'permissions':permissions,'enterprises':companies,'publicSpatial':True,'allEnterprises':False} for subject,permissions,companies in [('QA-SOURCE',['gas:read','gas:ingest'],[]),('QA-RESULT',['gas:read','gas:ingest'],[]),('QA-READER',['gas:read'],[]),('QA-FEEDBACK',['gas:read','gas:cooperate'],['A'])]]
  self.p.write('policy.json',self.p.policy);self.p.config['businessDatabase']='gas.sqlite';self.p.config['gas']={'sourceSystem':'QA-MONITOR','sourceSubjects':['QA-SOURCE'],'emergencySystem':'QA-EMERGENCY','resultSubjects':['QA-RESULT']};self.p.write('config.json',self.p.config);self.p.server.service=Service(self.p.root/'config.json');self.service=self.p.server.service;self.source={**SOURCE,'spatialId':'public'}
 def tearDown(self):self.p.tearDown()
 def call(self,path='',method='GET',payload=None,subject='QA-A',key=None,token=None,headers=None):
  h={}
  if payload is not None:h={'Content-Type':'application/json','Idempotency-Key':key or uuid.uuid4().hex}
  h.update(headers or {});auth=token if token is not None else self.p.token(subject,scope=' '.join(sorted(PERMISSIONS)))
  return self.p.request('/api/v1/gas_alerts'+path,auth,method,h,None if payload is None else json.dumps(payload).encode())
 def create(self):
  status,data,_=self.call(method='POST',payload=self.source,subject='QA-SOURCE');self.assertEqual(status,200,data);return data['event']
 def move(self,event,action,extra,subject='QA-A',**options):return self.call('/'+event['id']+'/'+action,'POST',{'revision':event['revision'],**extra},subject,**options)
 def verify(self,event,**patch):return self.move(event,'verify',{'conclusion':'continue','note':'合成核实','verifiedAt':SOURCE['observedAt'],'location':LOCATION,'materialRefs':[],**patch})
 def upload(self,event,subject='QA-A',**patch):return self.move(event,'materials',{'name':'synthetic.pdf','mediaType':'application/pdf','base64':base64.b64encode(PDF).decode(),'description':'合成气体材料','scope':'public','enterpriseId':None,**patch},subject)
 def test_session_capability_and_token_scope_cannot_expand_server_policy(self):
  status,session,_=self.p.request('/api/v1/session',self.p.token('QA-A',scope=' '.join(PERMISSIONS)));self.assertEqual(status,200);self.assertTrue(session['gasWorkflow']);self.assertIn('gas:verify',session['permissions'])
  event=self.create();self.assertEqual(self.call('/'+event['id'],subject='QA-ADMIN')[0],404);self.assertEqual(self.call('/'+event['id'],token=self.p.token('QA-A',scope='spatial:read'))[0],403)
  self.assertEqual(self.verify(event)[0],200);self.assertEqual(self.move(event,'classify',{'classification':'persistent','note':'合成'},'QA-READER')[0],403)
 def test_authenticated_source_and_fixed_result_adapter_enforced(self):
  self.assertEqual(self.call(method='POST',payload=self.source)[0],403);event=self.create();code,data,_=self.verify(event);event=data['event'];code,data,_=self.move(event,'handoff-request',{'requestId':'c'*32,'reason':'合成转办'});self.assertEqual(code,200,data);event=data['event']
  result={'requestId':'c'*32,'externalSystem':'QA-EMERGENCY','externalId':'QA-X','state':'completed','note':'合成完成'};self.assertEqual(self.move(event,'handoff-result',result,'QA-SOURCE')[0],403);code,data,_=self.move(event,'handoff-result',result,'QA-RESULT');self.assertEqual(code,200,data);self.assertEqual(data['event']['handoff']['state'],'completed');self.assertEqual(self.move(data['event'],'archive',{'note':'合成归档'})[0],200)
 def test_missing_private_and_removed_spatial_points_refused(self):
  self.assertEqual(self.call(method='POST',payload={**self.source,'spatialId':'missing'},subject='QA-SOURCE')[0],404)
  self.p.config['data']['publicSpatialIds']=['public','a'];self.p.write('config.json',self.p.config);self.p.server.service=Service(self.p.root/'config.json');self.assertEqual(self.call(method='POST',payload={**self.source,'spatialId':'a'},subject='QA-SOURCE')[0],404)
  event=self.create();self.p.layers['layers'][0]['features']=[f for f in self.p.layers['layers'][0]['features'] if f['id']!='public'];self.p.write('layers.json',self.p.layers);self.assertEqual(self.call('/'+event['id'])[0],404);self.assertEqual(self.call()[1]['total'],0)
 def test_permission_revocation_and_idempotency_replay_reauthorized(self):
  event=self.create();key=uuid.uuid4().hex;body={'revision':1,'classification':'persistent','note':'合成分类'};self.assertEqual(self.call('/'+event['id']+'/classify','POST',body,key=key)[0],200);self.assertTrue(self.call('/'+event['id']+'/classify','POST',body,key=key)[1]['replayed'])
  self.p.policy['principals'][0]['publicSpatial']=False;self.p.write('policy.json',self.p.policy);self.assertEqual(self.call('/'+event['id']+'/classify','POST',body,key=key)[0],404);self.assertEqual(self.call()[1]['total'],0)
 def test_private_materials_binary_headers_and_filtered_history(self):
  event=self.create();code,data,_=self.upload(event,'QA-FEEDBACK',scope='enterprise',enterpriseId='A');self.assertEqual(code,200,data);event=data['event'];material=data['material'];route='/api/v1/gas_alerts/'+event['id']+'/materials/'+material['id'];token=self.p.token('QA-A',scope=' '.join(PERMISSIONS));c=http.client.HTTPConnection('127.0.0.1',self.p.server.server_port,timeout=10)
  try:c.request('GET',route,headers={'Authorization':'Bearer '+token});r=c.getresponse();self.assertEqual(r.status,200);self.assertEqual(r.read(),PDF);self.assertEqual(r.getheader('X-XNBY-Material-SHA256'),hashlib.sha256(PDF).hexdigest());self.assertIn('attachment;',r.getheader('Content-Disposition'));self.assertEqual(r.getheader('Cache-Control'),'no-store')
  finally:c.close()
  self.assertEqual(self.call('/'+event['id']+'/materials',subject='QA-READER')[1]['total'],0);history=self.call('/'+event['id']+'/history',subject='QA-READER')[1];self.assertEqual(history['items'][-1]['kind'],'restricted');self.assertNotIn(material['id'],json.dumps(history));self.assertEqual(self.call('/'+event['id']+'/materials/'+material['id'],subject='QA-READER')[0],404);self.assertEqual(self.verify(event,materialRefs=[material['id']])[0],200)
 def test_history_pagination_and_invalid_routes_queries_methods(self):
  event=self.create();event=self.verify(event)[1]['event'];code,history,_=self.call('/'+event['id']+'/history?limit=1&offset=1');self.assertEqual(code,200);self.assertEqual(history['total'],2);self.assertEqual([r['revision'] for r in history['items']],[2]);self.assertEqual(history['revision'],2)
  for route in ['?limit=101','?limit=1&limit=2','?fake=1','/'+event['id']+'?offset=1','/'+event['id']+'/materials?limit=1']:self.assertEqual(self.call(route)[0],400,route)
  self.assertEqual(self.call('/'+event['id']+'/verify')[0],405);self.assertEqual(self.call('/'+event['id'],'POST',{})[0],405);self.assertEqual(self.call('/'+event['id']+'/claim','POST',{})[0],404);self.assertEqual(self.call('/%2e%2e')[0],404)
 def test_material_limits_slots_and_corrupt_server_bytes_are_unavailable(self):
  event=self.create();slots=self.service.gas.http_material_slots;slots.acquire();slots.acquire()
  try:self.assertEqual(self.upload(event)[0],429)
  finally:slots.release();slots.release()
  self.assertEqual(self.upload(event,name='../bad.pdf')[0],400);code,data,_=self.upload(event);self.assertEqual(code,200,data);material=data['material']
  with self.service.gas.transaction(write=True) as db:db.execute('UPDATE gas_materials SET payload=?',(b'X'*len(PDF),))
  self.assertEqual(self.call('/'+event['id']+'/materials/'+material['id'])[0],503);self.assertEqual(self.verify(data['event'],materialRefs=[material['id']])[0],503)
 def test_no_optin_no_workflow_and_invalid_config_refused(self):
  config=dict(self.p.config);del config['gas'];self.p.write('disabled.json',config);self.p.server.service=Service(self.p.root/'disabled.json');self.assertEqual(self.call()[0],503)
  for patch in [{'sourceSubjects':['QA-RESULT']},{'resultSubjects':'QA-RESULT'},{'extra':True}]:
   self.p.write('bad.json',{**self.p.config,'gas':{**self.p.config['gas'],**patch}})
   with self.assertRaises(ValueError):Service(self.p.root/'bad.json')
 def test_write_audit_failure_and_database_failure_do_not_commit(self):
  event=self.create();self.service.audit_file=self.p.root;self.assertEqual(self.verify(event)[0],503)
  with self.service.gas.transaction() as db:self.assertEqual(db.execute('SELECT revision FROM gas_alerts').fetchone()[0],1)
  self.service.audit_file=self.p.root/'audit.jsonl'
  with self.service.gas.transaction(write=True) as db:db.execute("CREATE TRIGGER fail_gas_history BEFORE INSERT ON gas_history BEGIN SELECT RAISE(ABORT,'synthetic'); END")
  self.assertEqual(self.verify(event)[0],503)
  with self.service.gas.transaction() as db:self.assertEqual(db.execute('SELECT revision FROM gas_alerts').fetchone()[0],1)
  audit=(self.p.root/'audit.jsonl').read_text('utf8');self.assertNotIn('Bearer',audit);self.assertNotIn('合成核实',audit)

 def test_invalid_authentication_framing_duplicate_json_and_large_body_refused(self):
  event=self.create();route='/api/v1/gas_alerts/'+event['id']+'/classify';token=self.p.token('QA-A',scope=' '.join(PERMISSIONS))
  def raw(body,headers):
   c=http.client.HTTPConnection('127.0.0.1',self.p.server.server_port,timeout=10)
   try:
    c.putrequest('POST',route)
    for name,value in headers:c.putheader(name,value)
    c.endheaders(body);r=c.getresponse();return r.status,r.read()
   finally:c.close()
  normal=[('Authorization','Bearer '+token),('Content-Type','application/json'),('Idempotency-Key',uuid.uuid4().hex)]
  self.assertEqual(raw(b'{}',normal+[('Content-Length','2'),('Content-Length','2')])[0],400)
  self.assertEqual(raw(b'{}',normal+[('Content-Length','2'),('Transfer-Encoding','chunked')])[0],400)
  body=b'{"revision":1,"revision":1}'
  self.assertEqual(raw(body,normal+[('Content-Length',str(len(body)))])[0],400)
  self.assertEqual(raw(b'{}',normal+[('Content-Length','2'),('Authorization','Bearer '+token)])[0],401)
  self.assertEqual(raw(b'',normal+[('Content-Length','32769')])[0],413)
  self.assertEqual(self.call(token='invalid-token')[0],401)
  with self.service.gas.transaction() as db:self.assertEqual(db.execute('SELECT revision FROM gas_alerts').fetchone()[0],1)

 def test_scoped_literal_search_status_and_classification_filters(self):
  event=self.create();event=self.verify(event)[1]['event'];second={**self.source,'sourceEventId':'QA-%_LITERAL','area':'合成区域二'};self.assertEqual(self.call(method='POST',payload=second,subject='QA-SOURCE')[0],200)
  self.assertEqual(self.call('?status=verified')[1]['total'],1);self.assertEqual(self.call('?status=attention')[1]['total'],1);self.assertEqual(self.call('?search=%25_')[1]['total'],1);self.assertEqual(self.call('?classification=needs-verification')[1]['total'],2);self.assertEqual(self.call('?status=bad')[0],400);self.assertEqual(self.call('?classification=bad')[0],400)

class GasGatewayTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):GasApiTests.setUpClass()
 def setUp(self):
  self.f=GasApiTests();self.f.setUp();self.event=self.f.create();self.gateway=PortalServer(('127.0.0.1',0),self.f.p.server.server_port,{'oauth':{'tokenEndpoint':'https://qa.identity.invalid/token'}});self.thread=threading.Thread(target=self.gateway.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.gateway.shutdown();self.gateway.server_close();self.thread.join();self.f.tearDown()
 def request(self,path,body=None,origin=None,subject='QA-A',method=None):
  token=self.f.p.token(subject,scope=' '.join(PERMISSIONS));headers={'Authorization':'Bearer '+token}
  if body is not None:headers.update({'Origin':origin or self.gateway.app_origin,'Content-Type':'application/json','Idempotency-Key':uuid.uuid4().hex})
  c=http.client.HTTPConnection('127.0.0.1',self.gateway.server_port,timeout=10)
  try:c.request(method or ('POST' if body is not None else 'GET'),'/api/v1/gas_alerts'+path,None if body is None else json.dumps(body).encode(),headers);r=c.getresponse();return r.status,r.read(),dict(r.getheaders())
  finally:c.close()
 def test_same_origin_restriction_large_material_and_binary_roundtrip(self):
  raw=b'%PDF-1.7\n'+b'Q'*65536+b'\n%%EOF';body={'revision':1,'name':'gas.pdf','mediaType':'application/pdf','base64':base64.b64encode(raw).decode(),'description':'合成材料','scope':'public','enterpriseId':None};route='/'+self.event['id']+'/materials';self.assertEqual(self.request(route,body,origin='https://outside.invalid')[0],403);code,encoded,_=self.request(route,body);self.assertEqual(code,200,encoded);result=json.loads(encoded);code,download,headers=self.request(route+'/'+result['material']['id']);self.assertEqual(code,200);self.assertEqual(download,raw);self.assertEqual(headers['X-XNBY-Authorization-Version'],result['authorizationVersion']);self.assertIn('attachment;',headers['Content-Disposition']);self.assertEqual(headers['Cache-Control'],'no-store')
 def test_gateway_does_not_expose_worker_routes_and_bounds_material_slots(self):
  self.assertEqual(self.request('/'+self.event['id']+'/claim',{},method='POST')[0],405);slots=self.gateway.material_slots;slots.acquire();slots.acquire()
  try:self.assertEqual(self.request('/'+self.event['id']+'/materials')[0],429)
  finally:slots.release();slots.release()

if __name__=='__main__':unittest.main()
