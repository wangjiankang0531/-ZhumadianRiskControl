"""Real HTTP session and original component API contract checks on loopback."""
from contextlib import closing
from pathlib import Path
import http.client,json,re,tempfile,threading,unittest,uuid
from services.reference_access import password_record
from tools.serve_replica_candidate import make_server,SESSION,CSRF

PASSWORD='Synthetic-Loopback-Only-2026'
def config():
 return {'users':{'tester':password_record(PASSWORD)},'directory':{'project':'zhumadian-project','version':'synthetic-dir-1','departments':[{'id':'d1','name':'合成测试部门'}],'users':[{'id':'tester','name':'合成测试人员','departments':['d1']}],'risk_levels':[{'code':'red','name':'重大风险'}]},'identities':{'tester':{'permissions':['risk-unit:'+v for v in ('create','read','update','delete','export','audit')],'departments':['d1']}},'policyVersion':'synthetic-policy-1'}

class HTTPTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.cfg=config()
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);root=Path(self.tmp.name);(root/'index.html').write_text('<h1>candidate-test</h1>');self.s=make_server(self.cfg,root,root/'test.sqlite');threading.Thread(target=self.s.serve_forever,daemon=True).start();self.addCleanup(self.s.server_close);self.addCleanup(self.s.shutdown);self.cookies={};self.csrf=''
 def req(self,method,path,body=None,headers=None):
  h={'Host':self.s.authority}
  if self.cookies:h['Cookie']='; '.join(k+'='+v for k,v in self.cookies.items())
  if headers:h.update(headers)
  with closing(http.client.HTTPConnection('127.0.0.1',self.s.server_port,timeout=5)) as c:
   c.request(method,path,body,h);r=c.getresponse();raw=r.read();hh=r.getheaders()
  for k,v in hh:
   if k.lower()=='set-cookie':a=v.split(';')[0].split('=',1);self.cookies[a[0]]=a[1]
  return r.status,dict(hh),raw
 def login(self):
  from urllib.parse import urlencode
  status,h,body=self.req('GET','/candidate/login');self.assertEqual(status,200);csrf=re.search(b'name="csrf" value="([^"]+)"',body)[1].decode();form=urlencode(dict(username='tester',password=PASSWORD,csrf=csrf));status,h,_=self.req('POST','/candidate/login',form,{'Origin':self.s.origin,'Content-Type':'application/x-www-form-urlencoded'});self.assertEqual(status,303);self.csrf=self.cookies[CSRF]
 def post(self,path,value,**extra):return self.req('POST','/replica-api'+path,json.dumps(value),{'Origin':self.s.origin,'X-XNBY-CSRF':self.csrf,'Content-Type':'application/json','Idempotency-Key':uuid.uuid4().hex,**extra})
 def form(self):return dict(departmentId='d1',department='合成测试部门',personId='tester',person='合成测试人员',analysisObject='HTTP合成装置',analysisUnit='HTTP合成单元',riskLevel='red',coordinate='114,33')
 def test_no_session_static_and_api_denied(self):
  self.assertEqual(self.req('GET','/safety/hiddenInvestigate/riskAnalysisUnit')[0],303);self.assertEqual(self.req('GET','/replica-api/jnpf/oauth/CurrentUser')[0],401)
 def test_login_csrf_not_authentication(self):
  self.cookies[CSRF]='forged';self.assertEqual(self.req('GET','/replica-api/jnpf/oauth/CurrentUser')[0],401)
 def test_favicon_never_rotates_login_challenge(self):
  from urllib.parse import urlencode
  _,_,body=self.req('GET','/candidate/login');csrf=re.search(b'name="csrf" value="([^"]+)"',body)[1].decode();before=dict(self.cookies)
  status,h,_=self.req('GET','/favicon.ico');self.assertEqual(status,404);self.assertNotIn('Set-Cookie',h);self.assertEqual(self.cookies,before)
  form=urlencode(dict(username='tester',password=PASSWORD,csrf=csrf));self.assertEqual(self.req('POST','/candidate/login',form,{'Origin':self.s.origin,'Content-Type':'application/x-www-form-urlencoded'})[0],303)
 def test_current_user_org_dictionary_contract(self):
  self.login();status,_,body=self.req('GET','/replica-api/jnpf/oauth/CurrentUser');data=json.loads(body)['data'];self.assertEqual(data['userInfo']['userId'],'tester');self.assertEqual(len(data['permissionList'][0]['button']),3)
  status,_,body=self.req('GET','/replica-api/jnpf/permission/Organize/getTree/zhumadian-project');self.assertEqual(json.loads(body)['data']['list'][0]['children'][0]['id'],'d1')
  self.assertEqual(self.req('GET','/replica-api/jnpf/system/DictionaryData/getInfo?dictType=safetycode&dictItemType=riskLevel')[0],200)
  self.assertEqual(self.post('/jnpf/permission/Users/getDepartmentIdByUserList?organizeId=d1',{})[0],200)
 def test_save_update_cas_and_delete_post(self):
  self.login();status,_,body=self.post('/serv/riskLevel/save',self.form());self.assertEqual(status,200);r=json.loads(body)['data'];f=self.form();f.update(id=r['id'],revision=1);self.assertEqual(self.post('/serv/riskLevel/updateById',f)[0],200);self.assertEqual(self.post('/serv/riskLevel/updateById',f)[0],409);self.assertEqual(self.req('GET','/replica-api/serv/riskLevel/removeById?id='+r['id'])[0],405);self.assertEqual(self.post('/serv/riskLevel/removeById',dict(id=r['id'],revision=2))[0],200)
 def test_wrong_origin_csrf_and_actor_rejected(self):
  self.login();self.assertEqual(self.post('/serv/riskLevel/save',self.form(),Origin='http://other.invalid')[0],403);self.assertEqual(self.post('/serv/riskLevel/save',self.form(),**{'X-XNBY-CSRF':'forged'})[0],403);f=self.form();f['actor']='admin';self.assertEqual(self.post('/serv/riskLevel/save',f)[0],400)
 def test_unsupported_apis_explicit_and_no_side_effect(self):
  self.login();self.assertEqual(self.req('GET','/replica-api/serv/riskLevel/export')[0],501);self.assertEqual(self.post('/serv/work/save',{})[0],501)
  self.assertEqual(self.s.store.query(self._principal(),self.s.directory)['total'],0)
 def _principal(self):
  from services.replica_risk_units import RiskPrincipal
  return RiskPrincipal('zhumadian-project','tester',frozenset(self.cfg['identities']['tester']['permissions']),frozenset(['d1']),'p')
 def test_static_traversal_host_and_logout(self):
  self.login();self.assertEqual(self.req('GET','/safety/%2e%2e/test.sqlite')[0],404);self.assertEqual(self.req('GET','/safety/hiddenInvestigate/riskAnalysisUnit')[0],200);self.assertEqual(self.req('GET','/safety/',headers={'Host':'evil.invalid'})[0],403)
  self.assertEqual(self.req('POST','/candidate/logout','{}',{'Origin':self.s.origin,'X-XNBY-CSRF':self.csrf,'Content-Type':'application/json'})[0],303);self.assertEqual(self.req('GET','/replica-api/jnpf/oauth/CurrentUser')[0],401)

if __name__=='__main__':unittest.main(verbosity=2)
