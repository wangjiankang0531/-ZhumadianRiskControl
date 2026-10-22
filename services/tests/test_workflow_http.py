import http.client,json,tempfile,threading,time,unittest,uuid
from pathlib import Path
from services.reference_access import AccessGate,COOKIE
from tools.serve_reference_demo import make_server
from tools.serve_reference_public import PublicHandler

class WorkflowHTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  for name in ('business.html','mobile.html','mobile.webmanifest'):(self.root/name).write_text('workflow static',encoding='utf-8')
  self.server=make_server(0,self.root,self.root/'legacy-demo.sqlite',handler_type=PublicHandler)
  self.server.public_config={'prefix':'/zhumadian/','origin':'https://www.joinlinksmart.com','proxyKey':'a'*64}
  self.server.access_gate=AccessGate({name:dict(salt='11'*24,digest='22'*32) for name in ('reporter','executor','reviewer')})
  for user in self.server.access_gate.users:self.server.access_gate.sessions[user+'-session']=dict(user=user,csrf='test-csrf',expires=time.monotonic()+300)
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
 def req(self,path,body=None,user='reporter',headers=None):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
  h={'X-XNBY-Ingress':'a'*64,'X-XNBY-Public-Origin':'https://www.joinlinksmart.com'}
  if user:h['Cookie']=COOKIE+'='+user+'-session'
  if body is not None:h.update({'Origin':'https://www.joinlinksmart.com','Content-Type':'application/json','X-XNBY-Demo':self.server.demo_token})
  h.update(headers or {});c.request('POST' if body is not None else 'GET','/zhumadian/'+path,json.dumps(body) if body is not None else None,h);r=c.getresponse();raw=r.read();status=r.status;c.close()
  try:return status,json.loads(raw)
  except ValueError:return status,raw.decode()
 def test_new_h5_and_all_workflow_routes_require_existing_login(self):
  self.assertEqual(self.req('mobile.html',user=None)[0],303)
  self.assertEqual(self.req('api/demo/workflow-catalog',user=None)[0],401)
  self.assertEqual(self.req('mobile.html')[0],200)
  for name in ('catalog','summary','records','resources'):self.assertEqual(self.req('api/demo/workflow-'+name)[0],200)
 def test_public_actor_comes_from_cookie_not_client_header(self):
  code,value=self.req('api/demo/workflow-catalog',headers={'X-XNBY-Business-Actor':'executor'})
  self.assertEqual(code,200);self.assertEqual(value['user'],'reporter');self.assertEqual(value['fixtureCount'],0)
 def test_real_http_record_persists_and_writes_reject_bad_origin_or_token(self):
  form=dict(kind='hazard',title='HTTP验收',enterprise='验收单位',location='验收地点',description='HTTP实际事务验证')
  body=dict(requestId=uuid.uuid4().hex,form=form)
  self.assertEqual(self.req('api/demo/workflow-create',body,headers={'Origin':'https://wrong.invalid'})[0],403)
  self.assertEqual(self.req('api/demo/workflow-create',body,headers={'X-XNBY-Demo':'wrong'})[0],403)
  code,value=self.req('api/demo/workflow-create',body);self.assertEqual(code,200);identity=value['record']['id']
  self.assertEqual(value['record']['reporter'],'reporter');self.assertEqual(self.req('api/demo/workflow-detail?id='+identity,user='executor')[1]['record']['id'],identity)
  command=dict(requestId=uuid.uuid4().hex,identity=identity,revision=1,action='dispatch',data=dict(note='HTTP派发',assignee='executor',reviewer='reviewer',dueDate='2099-01-01'))
  self.assertEqual(self.req('api/demo/workflow-command',command,user='executor')[0],403)
  self.assertEqual(self.req('api/demo/workflow-command',command)[0],200)
  self.assertEqual(self.req('api/demo/workflow-records?mine=1',user='executor')[1]['total'],1)
  self.assertEqual(self.req('api/demo/workflow-records?mine=1',user='reviewer')[1]['total'],0)
 def test_sidecar_not_legacy_fixture_database_and_queries_are_bounded(self):
  self.assertNotEqual(self.server.workflow_store.path,self.server.store.path)
  self.assertEqual(self.req('api/demo/workflow-summary')[1]['total'],0)
  for query in ('?page=zero','?mine=2','?page=1&page=2','?kind=unknown','?unexpected=1'):self.assertEqual(self.req('api/demo/workflow-records'+query)[0],400)
  self.assertEqual(self.req('api/demo/workflow-detail?id=missing')[0],404)

 def test_material_upload_beyond_old_128k_boundary_and_exact_download(self):
  import base64
  form=dict(kind='hazard',title='HTTP材料验收',enterprise='验收单位',location='验收地点',description='原字节保存验证')
  code,created=self.req('api/demo/workflow-create',dict(requestId=uuid.uuid4().hex,form=form));self.assertEqual(code,200)
  raw=b'%PDF-1.4\n%'+b'x'*140000+b'\n%%EOF';identity=created['record']['id']
  body=dict(requestId=uuid.uuid4().hex,identity=identity,revision=1,name='evidence.pdf',mediaType='application/pdf',base64Data=base64.b64encode(raw).decode(),description='超过旧128KiB门槛的材料测试')
  self.assertEqual(self.req('api/demo/workflow-material',body,user=None)[0],401)
  code,saved=self.req('api/demo/workflow-material',body);self.assertEqual(code,200);material=saved['materials'][0]
  code,download=self.req('api/demo/workflow-material?id='+identity+'&materialId='+material['id']);self.assertEqual(code,200);self.assertEqual(download.encode(),raw)

if __name__=='__main__':unittest.main()
