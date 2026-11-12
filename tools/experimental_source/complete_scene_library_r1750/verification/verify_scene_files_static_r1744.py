"""Actual loopback original Nginx serves complete host bundle and pinned scene assets."""
from pathlib import Path
import hashlib,http.client,importlib.util,json,re,socket,subprocess,sys,time
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';V=Path(__file__).parent
W=R/'work/scene-fine-auth-stage-r1743';D=R/'Document/Deployment/scene_fine_auth_stage_r1743_20261107';O=W/'nginx-r1744'
def J(p):return json.loads(Path(p).read_bytes())
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not O.exists() and J(D/'prepared-scene-fine-auth-stage-r1743.json')['passed']
scene=module('static1480',V/'original_scene_model_static_routes_r1560.py')
source=W/'gateway-source-r1744';assert not source.exists()
for n in ['tools/prepare_original_frontend_gateway.py','tools/original_project_branding.py','tools/original_header_branding.py','deploy/branding/zhumadian-emergency.svg']:
 p=R/'work/unified-attachment-r49-r1361/payload'/n
 if not p.is_file():p=G/n
 target=source/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
sys.path.insert(0,str(source/'tools'));gateway=module('gateway1484',source/'tools/prepare_original_frontend_gateway.py')
assets=J(W/'scene-readonly-assets.private.json');descriptor=J(W/'scene-descriptor.json');rows=scene.preflight(W/'payload',descriptor,assets)
roots={k:G/'frontend'/k for k in ['security_pc','emergency_pc','mobile','bigscreen']};roots['security_pc']=W/'payload/frontend/security_pc';roots['tiles']=G/'map'
if not roots['tiles'].is_dir():roots['tiles']=G/'frontend/tiles'
assert roots['tiles'].is_dir()
with socket.socket()as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
assert port not in [8767,18891,18892]

gateway.prepare(O,G/'runtime/nginx',roots,port,base_path='/zhumadian',public_origin='https://www.joinlinksmart.com',project_name='驻马店重大风险防控')
config=O/'nginx.conf';before=config.read_bytes();after=scene.insert(before,rows)
policy=module('private_asset_policy1691',R/'work/scene-file-frontend-r1735/support/original_scene_asset_policy.py');after=policy.protect(after,rows,'/_xnby_original_scene_read_auth')
sys.path.insert(0,str(V))
from test_scene_read_auth_r1577 import start_fixture,TOKEN
original_auth_state,original_auth_port,close_original_auth=start_fixture()
anchor=b' location = /zhumadian/api { return 404; }';assert after.count(anchor)==1
internal=(' location = /_xnby_original_scene_read_auth { internal; proxy_pass http://127.0.0.1:'+str(original_auth_port)+'/v2/project/scene-read; proxy_pass_request_body off; proxy_set_header Content-Length ""; proxy_set_header Authorization $http_authorization; proxy_set_header Origin $http_origin; proxy_set_header Cookie ""; proxy_connect_timeout 3s; proxy_read_timeout 8s; }\n').encode()
after=after.replace(anchor,internal+anchor);config.write_bytes(after)
exe=G/'runtime/nginx/nginx.exe';cmd=[str(exe),'-p',str(O)+'/', '-c',str(config)]
test=subprocess.run([*cmd,'-t'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);(O/'config-check.private.log').write_bytes(test.stdout+test.stderr);
if test.returncode!=0:close_original_auth();raise AssertionError('ACTUAL_NGINX_CONFIG_REJECTED')
out=(O/'nginx.private.log').open('xb')
try:p=subprocess.Popen(cmd,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
except BaseException:close_original_auth();out.close();raise
checks=[];failure=None
brand=module('brand_expected1493',source/'tools/original_project_branding.py')
patterns=[]
for line in brand.static_directives('驻马店重大风险防控'):
 if line.startswith('sub_filter '):
  # The actual original function emits two JSON-compatible quoted literals.
  decoder=json.JSONDecoder();left,used=decoder.raw_decode(line[len('sub_filter '):]);remaining=line[len('sub_filter ')+used:].strip();right,used=decoder.raw_decode(remaining);assert remaining[used:]==';';patterns.append((left.encode(),right.encode()))
substitutions={a.lower():b for a,b in patterns};regex=re.compile(b'|'.join(re.escape(a)for a,b in patterns),re.I)
def expected_served(q):
 if q.relative_to(security).as_posix()=='assets/png/logo-CQaY_L7K.png':return(source/'deploy/branding/zhumadian-emergency.svg').read_bytes()
 raw=q.read_bytes()
 return regex.sub(lambda m:substitutions[m.group().lower()],raw)if q.suffix in['.html','.js','.json']else raw

def check(v,n):
 checks.append({'case':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def request(route,method='GET',headers=None,maximum=12*1048576,authorized=True,body=None):
 c=http.client.HTTPConnection('127.0.0.1',port,timeout=10)
 try:
  c.request(method,route,body=body,headers={**({'Authorization':TOKEN}if authorized else{}),**(headers or{})});res=c.getresponse();body=res.read(maximum+1);assert len(body)<=maximum;return res.status,dict(res.getheaders()),body
 finally:c.close()
try:
 deadline=time.monotonic()+15
 while True:
  assert p.poll()is None,'NGINX_EXITED_BEFORE_LISTEN'
  try:request('/zhumadian/scene/');break
  except OSError:
   if time.monotonic()>deadline:raise
   time.sleep(.05)
 # Entire full compiler bundle and all four retained served overlays, not only new chunks.
 security=W/'payload/frontend/security_pc';files=[q for q in security.rglob('*')if q.is_file()]
 for q in files:
  route='/zhumadian/'+q.relative_to(security).as_posix();status,h,b=request(route)
  expected=expected_served(q);check(status==200 and b==expected,'complete-original-frontend-file-'+q.relative_to(security).as_posix())
 for row in rows:
  if row['route'].removeprefix(scene.PREFIX)in assets:continue
  status,h,b=request(row['route']);q=Path(row['file'])
  check(status==200 and hashlib.sha256(b).hexdigest()==sha(q) and h.get('X-Content-Type-Options')=='nosniff','exact-scene-static-'+row['route'].removeprefix(scene.PREFIX))
  if q.suffix in ['.js','.html']:check(h.get('Content-Type','').startswith('text/javascript'if q.suffix=='.js'else'text/html'),'scene-executable-mime-'+row['route'].removeprefix(scene.PREFIX))
 for n,row in assets.items():
  status,h,b=request(scene.PREFIX+n,'HEAD');check(status==200 and not b and int(h['Content-Length'])==row['bytes'],'readonly-gis-head-'+n)
 model_names=sorted(n for n in assets if n.startswith('model-library/'));check(len(model_names)==29,'exact-29-declared-model-routes')
 for name in model_names:
  row=assets[name];status,h,b=request(scene.PREFIX+name,maximum=32*1048576)
  check(status==200 and len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']and b[:4]==b'glTF'and int.from_bytes(b[4:8],'little')==2 and int.from_bytes(b[8:12],'little')==len(b)and h.get('Content-Type','').startswith('model/gltf-binary'),'complete-exact-self-contained-GLB-'+name)
 status,h,b=request(scene.PREFIX+'model-library/catalog.json');catalog=json.loads(b);check(status==200 and len(catalog['models'])==29 and all('/'not in r['sourceFile']and '\\'not in r['sourceFile']and ':'not in r['sourceFile']for r in catalog['models']),'public-model-catalog-keeps-only-source-basename')
 for name in ['model-library/','model-library/unknown.glb','model-library/private.json','model-library/../private/server-configuration.json']:
  status,h,b=request(scene.PREFIX+name);check(status==404,'no-model-directory-alias-'+name)
 binary='assets/showcase/runtime/zhumadian/full/zhumadian_full.bin';source=Path(assets[binary]['path'])
 for start in [0,source.stat().st_size-4096]:
  status,h,b=request(scene.PREFIX+binary,headers={'Range':f'bytes={start}-{start+4095}'},maximum=4096)
  with source.open('rb')as f:f.seek(start);expected=f.read(4096)
  check(status==206 and b==expected and h.get('Content-Range')==f'bytes {start}-{start+4095}/{source.stat().st_size}','real-gis-byte-range-'+str(start))
 for route in ['private/server-configuration.json','layers/default.json','layers/sample.json','api/not-installed','point-symbols/system/not-a-symbol.png','other/index.html']:
  status,h,b=request(scene.PREFIX+route);check(status==404,'unknown-scene-file-no-spa-or-local-dlg-fallback-'+route)
 status,h,b=request('/zhumadian/api/jnpf/oauth/CurrentUser');check(status==503,'original-unavailable-api-route-preserved-no-synthetic-login')
 private_rows=[r for r in rows if r['route'].removeprefix(scene.PREFIX)in policy.PRIVATE_GIS or r['route'].startswith(scene.PREFIX+'model-library/')];check(len(private_rows)==38,'all-38-declared-private-resource-routes')
 for row in private_rows:
  for method in ['GET','HEAD']:
   status,h,b=request(row['route'],method,authorized=False);check(status==401 and h.get('Cache-Control')=='no-store','anonymous-private-'+method+'-'+row['route'].removeprefix(scene.PREFIX))
 original_auth_state['mode']='denied'
 for row in private_rows:
  status,h,b=request(row['route']);check(status==403 and h.get('Cache-Control')=='no-store','ungranted-private-'+row['route'].removeprefix(scene.PREFIX))
 original_auth_state['mode']='reader'
 sample=scene.PREFIX+'assets/showcase/runtime/zhumadian/full/zhumadian_full.bin'
 status,h,b=request(sample,headers={'Range':'bytes=0-15'},authorized=False);check(status==401,'anonymous-range-cannot-retrieve-source')
 status,h,b=request(sample,headers={'Authorization':'synthetic-invalid'});check(status==401,'invalid-token-source-refused')
 status,h,b=request(sample,headers={'Origin':'https://foreign.invalid'});check(status==403,'foreign-origin-source-refused')
 for method in ['POST','PUT','DELETE','OPTIONS']:
  status,h,b=request(sample,method);check(status==405,'private-no-write-'+method)
 for suffix in ['?','?view=1','?token=invalid']:
  status,h,b=request(sample+suffix);check(status==400,'private-query-refused-'+suffix)
 status,h,b=request(sample,headers={'Content-Length':'1'},body=b'x');check(status==400,'private-get-body-refused')
 original_auth_state['allowed']=False;status,h,b=request(sample);check(status==401,'private-revocation-next-request-refused');original_auth_state['allowed']=True
 original_auth_state['mode']='unavailable';status,h,b=request(sample);check(status==500,'private-auth-upstream-outage-fails-closed');original_auth_state['mode']='reader'
 status,h,b=request(sample,'HEAD');check(status==200 and not b and h.get('Cache-Control')=='no-store','private-auth-restored-without-nginx-restart')
 check(original_auth_state['readRows']==0,'authorization-did-not-read-project-data-rows')
 check(scene.insert(before,None)==before,'optional-no-scene-byte-preserving')
 for code,operation in [('duplicate-route',lambda:scene.insert(before,[rows[0],rows[0]])),('nginx-path-injection',lambda:scene.insert(before,[{**rows[0],'file':'D:/x"; return 200;'}])),('second-insertion',lambda:scene.insert(after,rows)),('missing-scene-descriptor',lambda:scene.preflight(W/'payload',None,assets))]:
  try:operation()
  except ValueError:check(True,'rejected-'+code)
  else:check(False,'rejected-'+code)
 for n,row in assets.items():check(sha(row['path'])==row['sha256'],'readonly-gis-source-kept-'+n)
except BaseException as e:failure={'class':type(e).__name__,'message':str(e)[:220]};print(json.dumps({'failed':True,**failure}),flush=True)
finally:
 if p.poll()is None:
  stop=subprocess.run([*cmd,'-s','quit'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
  assert stop.returncode==0,'NORMAL_NGINX_QUIT_REJECTED_RETAIN_PROCESS'
 while p.poll()is None:
  try:p.wait(timeout=15)
  except subprocess.TimeoutExpired:print(json.dumps({'sameOwnedNginxStillLive':True,'forceTerminationUsed':False}),flush=True)
 out.close();close_original_auth()
 result={'passed':failure is None and p.returncode==0,'checks':checks,'failure':failure,'fullFrontendFiles':len(files)if'files'in globals()else 0,'normalNginxExitCode':p.returncode,'forceTerminationUsed':False,'GISCopiedOrModified':False,'syntheticLoginUsed':False,'syntheticCurrentUserHTTPFixture':True,'actualJavaCurrentUserUsed':False,'allOriginalAuthThreadsNormallyJoined':True,'all38PrivateAssetRoutesAuthenticated':True,'normalSDKHostBrowserAccepted':False,'publicDeployed':False}
 (D/'actual-static-gateway-r1744.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:v for k,v in result.items()if k!='checks'}),flush=True)
if failure:raise SystemExit(1)
