"""Bounded loopback integration of original dedicated Vue components.

Independent candidate database and explicit test identities. Not public ingress
or enterprise IAM. Unsupported reference APIs return 501, never empty success.
"""
from contextlib import closing
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from http.cookies import SimpleCookie,CookieError
from pathlib import Path
from urllib.parse import parse_qs,urlsplit,unquote
import argparse,html,json,mimetypes,secrets,sys,threading
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.reference_access import AccessGate
from services.reference_errors import DemoError
from services.replica_risk_units import ProjectDirectory,RiskPrincipal,RiskUnitStore

SESSION='XNBY_REPLICA_SESSION';CHALLENGE='XNBY_REPLICA_LOGIN';CSRF='XNBY_REPLICA_CSRF'
BASE='/hiddenInvestigate/riskAnalysisUnit'

def menu(identity,title,path,component,*,parent='root',visible='1',children=None):
 return dict(id=identity,fullName=title,enCode=identity,parentId=parent,icon='AppstoreOutlined',hasChildren=bool(children),urlAddress=component,path=path,visible=visible,children=children or [],type=1,propertyJson='{}',systemId='safety')

def profile(principal,directory):
 directory.require(principal,'read');u=directory.users[principal.subject]
 routes=[menu('risk-unit','安全风险单元',BASE,BASE,parent='prevention')]
 buttons=[menu('risk-'+kind,title,BASE+'/'+kind,BASE+'/info',parent='risk-unit',visible='0') for kind,title in [('add','风险分析单元-新增'),('edit','风险分析单元-编辑'),('detail','风险分析单元-详情')]]
 root=menu('prevention','双重预防管理','/hiddenInvestigate','',children=routes)
 return dict(userInfo=dict(userId=principal.subject,userAccount=principal.subject,userName=u['name'],organizeId=directory.project,organizeName='驻马店复刻候选项目',departmentId='',departmentName='',roleName='独立联调测试',roleIds=[],isAdministrator=False,headIcon='',signImg='',systemId='safety'),menuList=[root],permissionList=[dict(modelId='risk-unit',moduleName='安全风险单元',button=buttons,column=[],resource=[],form=[])])

class Server(ThreadingHTTPServer):
 daemon_threads=True
 def __init__(self,*args,**kwargs):self.slots=threading.BoundedSemaphore(16);super().__init__(*args,**kwargs)
 def process_request(self,request,address):
  if not self.slots.acquire(False):self.shutdown_request(request);return
  try:super().process_request(request,address)
  except Exception:self.slots.release();raise
 def process_request_thread(self,*args):
  try:super().process_request_thread(*args)
  finally:self.slots.release()

class Handler(BaseHTTPRequestHandler):
 def setup(self):super().setup();self.connection.settimeout(10)
 def log_message(self,*args):pass
 def end_headers(self):
  self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','same-origin');self.send_header('X-Frame-Options','DENY')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'")
  super().end_headers()
 def respond(self,status,raw,kind='application/json; charset=utf-8',headers=()):
  if isinstance(raw,dict):raw=json.dumps(raw,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
  for k,v in headers:self.send_header(k,v)
  self.end_headers();self.wfile.write(raw)
 def cookie(self,name,value,*,http=True,age=1800):return ('Set-Cookie',f'{name}={value}; Path=/; Max-Age={age}; SameSite=Strict'+('; HttpOnly' if http else ''))
 def ingress(self):
  if self.headers.get_all('Host',[])!=[self.server.authority]:raise DemoError(403,'访问主机无效')
  if not self.path.startswith('/') or self.path.startswith('//'):raise DemoError(400,'请求路径无效')
  try:
   cookies=SimpleCookie();cookies.load(self.headers.get('Cookie',''))
  except CookieError:raise DemoError(400,'Cookie 无效')
  self.cookies=cookies;self.token=cookies[SESSION].value if SESSION in cookies else '';self.session=self.server.gate.session(self.token)
  parsed=urlsplit(self.path);self.route=parsed.path;self.params=parse_qs(parsed.query,keep_blank_values=True,max_num_fields=32)
  if any(len(v)!=1 for v in self.params.values()):raise DemoError(400,'参数不能重复')
  self.params={k:v[0] for k,v in self.params.items()}
 def trusted(self,write=False):
  if not self.session:raise DemoError(401,'请登录独立候选环境')
  grant=self.server.identities.get(self.session['user'])
  if not grant:raise DemoError(403,'候选账号未配置')
  principal=RiskPrincipal(self.server.directory.project,self.session['user'],frozenset(grant['permissions']),frozenset(grant['departments']),self.server.policy_version)
  self.server.directory.require(principal,'read')
  if write and (self.headers.get_all('Origin',[])!=[self.server.origin] or self.headers.get_all('X-XNBY-CSRF',[])!=[self.session['csrf']]):raise DemoError(403,'操作来源或 CSRF 无效')
  return principal
 def body(self,form=False):
  if self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length',[]))!=1:raise DemoError(400,'请求长度无效')
  try:length=int(self.headers['Content-Length'])
  except ValueError:raise DemoError(400,'请求长度无效')
  if not 0<length<=16384:raise DemoError(413,'请求大小无效')
  expected='application/x-www-form-urlencoded' if form else 'application/json'
  if self.headers.get('Content-Type','').split(';')[0]!=expected:raise DemoError(415,'请求类型无效')
  raw=self.rfile.read(length)
  if len(raw)!=length:raise DemoError(400,'请求不完整')
  if form:
   value=parse_qs(raw.decode(),keep_blank_values=True,max_num_fields=4)
   if set(value)!={'username','password','csrf'} or any(len(v)!=1 for v in value.values()):raise DemoError(400,'登录字段无效')
   return {k:v[0] for k,v in value.items()}
  def pairs(items):
   result={}
   for k,v in items:
    if k in result:raise ValueError('Duplicate JSON key')
    result[k]=v
   return result
  value=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))
  if not isinstance(value,dict):raise DemoError(400,'请求需为对象')
  return value
 def success(self,data):return self.respond(200,dict(code=200,msg='操作成功',data=data))
 def dispatch(self,write=False):
  try:
   self.ingress()
   # Browsers request this independently of the login document. Redirecting
   # it to login would rotate the challenge cookie after the form rendered.
   if self.route=='/favicon.ico':raise DemoError(404,'资源不存在')
   if self.route=='/candidate/login':return self.login(write)
   if self.route=='/candidate/logout':
    self.trusted(True)
    if not write:raise DemoError(405,'退出需 POST')
    self.server.gate.logout(self.token);return self.respond(303,b'',headers=[('Location','/candidate/login'),self.cookie(SESSION,'',age=0),self.cookie(CSRF,'',http=False,age=0)])
   if not self.session and not self.route.startswith('/replica-api/'):
    return self.respond(303,b'',headers=[('Location','/candidate/login')])
   p=self.trusted(write);d=self.server.directory;s=self.server.store;r=self.route;q=self.params
   if r.startswith('/replica-api/'):
    endpoint=r[len('/replica-api'):]
    if not write:
     if endpoint=='/jnpf/oauth/CurrentUser':return self.success(profile(p,d))
     if endpoint=='/jnpf/permission/Organize/getTree/'+d.project:
      nodes={i:dict(id=i,fullName=x['name'],hasChildren=False,children=[]) for i,x in d.departments.items() if i in p.departments};roots=[]
      for i,n in nodes.items():
       parent=d.departments[i]['parent']
       if parent in nodes:nodes[parent]['children'].append(n);nodes[parent]['hasChildren']=True
       else:roots.append(n)
      return self.success(dict(list=[dict(id=d.project,fullName='驻马店候选项目',children=roots)]))
     if endpoint=='/jnpf/system/DictionaryData/getInfo':
      if q!={'dictType':'safetycode','dictItemType':'riskLevel'}:raise DemoError(501,'此字典尚未适配')
      return self.success([dict(enCode=k,fullName=v) for k,v in d.risk_levels.items()])
     if endpoint=='/serv/riskLevel/getPage':
      filters={k:v for k,v in q.items() if k not in ('current','size')};return self.success(s.query(p,d,filters,int(q.get('current','1')),int(q.get('size','10'))))
     if endpoint=='/serv/riskLevel/getById':return self.success(s.get(p,d,q.get('id')))
     if endpoint=='/serv/riskLevel/removeById':raise DemoError(405,'删除需 POST、版本和 CSRF')
    else:
     if endpoint=='/jnpf/permission/Users/getDepartmentIdByUserList':
      if q.get('organizeId') not in p.departments:raise DemoError(403,'不允许访问此部门人员')
      return self.success([dict(id=u['id'],realName=u['name']) for u in d.users.values() if u['enabled'] and q['organizeId'] in u['departments']])
     value=self.body()
     if endpoint in ('/serv/riskLevel/save','/serv/riskLevel/updateById'):
      identity=value.pop('id',None);revision=value.pop('revision',None)
      if endpoint.endswith('/save') and (identity is not None or revision is not None):raise DemoError(400,'新增不接受现有版本')
      if endpoint.endswith('/updateById') and (not identity or revision is None):raise DemoError(400,'编辑缺少标识或版本')
      return self.success(s.save(p,d,self.headers.get('Idempotency-Key'),value,identity=identity,revision=revision))
     if endpoint=='/serv/riskLevel/removeById':
      if set(value)!={'id','revision'}:raise DemoError(400,'删除字段无效')
      return self.success(s.delete(p,d,self.headers.get('Idempotency-Key'),value['id'],value['revision']))
    raise DemoError(501,'此原站接口尚未适配，未执行业务操作')
   if write:raise DemoError(405,'此资源不支持 POST')
   if r=='/safety/login':return self.respond(303,b'',headers=[('Location','/candidate/login')])
   if not r.startswith('/safety/'):raise DemoError(404,'资源不存在')
   relative=unquote(r[len('/safety/'):]);path=(self.server.static/relative).resolve()
   if not path.is_relative_to(self.server.static) or '\\' in relative:raise DemoError(404,'资源不存在')
   if not Path(relative).suffix:path=self.server.static/'index.html'
   if not path.is_file() or path.suffix.lower() not in ('.html','.js','.css','.svg','.png','.jpg','.jpeg','.gif','.webp','.ico','.woff','.woff2','.ttf'):raise DemoError(404,'资源不存在')
   return self.respond(200,path.read_bytes(),mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
  except DemoError as e:self.respond(e.status,dict(code=e.status,msg=e.message))
  except (ValueError,TypeError,UnicodeError):self.respond(400,dict(code=400,msg='请求格式无效'))
  except Exception:self.respond(500,dict(code=500,msg='候选服务异常，操作未确认'))
 def login(self,write):
  if write:
   if self.headers.get_all('Origin',[])!=[self.server.origin]:raise DemoError(403,'登录来源无效')
   value=self.body(True);challenge=self.cookies[CHALLENGE].value if CHALLENGE in self.cookies else ''
   entry=self.server.gate.challenges.get(challenge)
   check=dict(challengeCookiePresent=bool(challenge),challengeKnown=bool(entry),csrfMatched=bool(entry and secrets.compare_digest(entry['csrf'],value['csrf'])),knownTestAccount=value['username'] in self.server.gate.users)
   token,error=self.server.gate.login(challenge,value['csrf'],value['username'],value['password'])
   if error:
    # Local diagnostics intentionally omit all form values, cookies and hashes.
    sys.stderr.write(json.dumps(dict(event='candidate-login-failed',checks=check,reason=error))+'\n');sys.stderr.flush()
    raise DemoError(429 if error=='limited' else 401,'候选登录失败')
   session=self.server.gate.session(token)
   return self.respond(303,b'',headers=[('Location','/safety'+BASE),self.cookie(SESSION,token),self.cookie(CSRF,session['csrf'],http=False),self.cookie(CHALLENGE,'',age=0)])
  challenge=self.server.gate.challenge()
  if not challenge:raise DemoError(429,'登录请求较多')
  token,csrf=challenge
  raw=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>驻马店原组件独立联调登录</title><style>body{{font:16px system-ui;background:#edf1f6}}main{{width:420px;margin:10vh auto;padding:30px;background:white;border-radius:12px}}label{{display:block;margin:20px 0}}input{{padding:10px;width:90%}}button{{padding:12px;background:#5156ec;color:white;border:0}}p{{line-height:1.7}}</style><main><h1>驻马店原组件独立联调</h1><p>仅风险分析单元接口接入测试库。其它原组件尚未适配；地图、Excel及正式组织认证待验收。</p><form method="post" action="/candidate/login"><input type="hidden" name="csrf" value="{html.escape(csrf)}"><label>测试账号<input name="username" required autocomplete="username"></label><label>测试密码<input name="password" type="password" required autocomplete="current-password"></label><button>登录独立测试环境</button></form></main></html>'''.encode()
  return self.respond(200,raw,'text/html; charset=utf-8',[self.cookie(CHALLENGE,token,age=300)])
 def do_GET(self):self.dispatch()
 def do_POST(self):self.dispatch(True)

def make_server(config,static,database,port=0):
 if set(config)!={'users','directory','identities','policyVersion'}:raise ValueError('Invalid candidate config')
 gate=AccessGate(config['users']);d=ProjectDirectory(**config['directory'])
 for name,grant in config['identities'].items():
  if name not in gate.users or name not in d.users or set(grant)!={'permissions','departments'} or not set(grant['departments'])<=d.departments.keys():raise ValueError('Invalid candidate identity')
 static=Path(static).resolve()
 if not (static/'index.html').is_file():raise ValueError('Build the dedicated frontend first')
 server=Server(('127.0.0.1',port),Handler);server.authority='127.0.0.1:'+str(server.server_port);server.origin='http://'+server.authority;server.gate=gate;server.directory=d;server.identities=config['identities'];server.policy_version=config['policyVersion'];server.static=static;server.store=RiskUnitStore(database);return server

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--static',type=Path,required=True);p.add_argument('--database',type=Path,required=True);p.add_argument('--port',type=int,default=0);p.add_argument('--seconds',type=int,default=1800);a=p.parse_args()
 if not 60<=a.seconds<=3600:raise ValueError('Candidate duration must be 60..3600 seconds')
 s=make_server(json.loads(a.config.read_text('utf-8')),a.static,a.database,a.port);timer=threading.Timer(a.seconds,s.shutdown);timer.daemon=True;timer.start();print(json.dumps(dict(url=s.origin+'/candidate/login',seconds=a.seconds,mode='isolated-candidate')),flush=True)
 try:s.serve_forever()
 finally:s.server_close();timer.cancel()
