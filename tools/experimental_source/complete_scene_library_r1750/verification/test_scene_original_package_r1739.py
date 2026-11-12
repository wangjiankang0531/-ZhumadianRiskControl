"""Actual HTTP authorization, durable CAS, rollback and cross-language scene validation."""
from pathlib import Path
import copy,hashlib,http.client,http.server,importlib.util,json,os,secrets,subprocess,sys,threading,time
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;W=R/'work/scene-library-origin-tests-r1739';P=R/'work/scene-file-frontend-r1735/backend';D=R/'Document/Deployment/scene_library_original_package_r1737_20261107';sys.path.insert(0,str(P))
from services.scene_projects import SceneProjectRepository,validate_scene_project,checked_catalog,configured_scene_repository,validate_scene_settings,ROUTE
from services.project_files import ProjectFileRepository
from services.common import ApiError
from services.layer_sync_server import LayerSyncServer,OriginalPlatformAccess,empty_document
from services.layer_sync_identity import account_key,ACCOUNT_HEADER
CATALOG={'schema':'xnby.scene-model-library.v1','models':[{'id':'synthetic-asset-a','sha256':'a'*64,'name':'合成模型'}]}
def document():return{'schema':'xnby.scene-project.v2','scene':'zhumadian','landscape':empty_document(),'models':[{'id':'instance-a','assetId':'synthetic-asset-a','name':'合成实例','assetSHA256':'a'*64,'anchor':[0,0,1.25],'scale':.01,'rotationDegrees':30,'visible':True}],'lighting':{'intensity':1.8,'azimuth':135,'textures':True,'shadows':True,'targetModelId':'instance-a'}}
def J(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if '--cas-child'in sys.argv:
 value=json.loads(sys.stdin.buffer.read(65536));assert value['gate']=='OWN_SCENE_CAS_R1739';root=Path(value['root']);assert root==W/'state/scenes';repo=SceneProjectRepository(root,CATALOG)
 while not(W/'state/release-cas-children').exists():time.sleep(.01)
 doc=document();doc['models'][0]['anchor'][0]=value['number']
 try:repo.save('shared.scene.json',doc,value['expected']);result={'saved':True}
 except ApiError as e:assert e.status==409;result={'saved':False,'conflict':True}
 print(json.dumps(result));raise SystemExit(0)
assert sys.stdin.buffer.readline(100)==b'OWN_SCENE_BACKEND_R1739\n';STATE=W/'state';assert not STATE.exists();STATE.mkdir(parents=True);checks=[]
def mark(name):checks.append({'case':name,'passed':True})
def refused(fn,code=None):
 try:fn()
 except(ValueError,ApiError)as e:
  if code is not None:assert getattr(e,'code',str(e))==code,(type(e).__name__,str(e))
  return
 raise AssertionError('EXPECTED_REFUSAL')
catalog=checked_catalog(CATALOG);base=document();validate_scene_project(base,catalog)
cases=[{'name':'modern','document':base}];legacy=copy.deepcopy(base);legacy['schema']='xnby.scene-project.v1';legacy['models'][0]={k:v for k,v in legacy['models'][0].items()if k not in ['assetId','name']};legacy['models'][0]['id']='synthetic-asset-a';legacy['lighting']['targetModelId']='synthetic-asset-a';cases.append({'name':'legacy','document':legacy});empty=copy.deepcopy(base);empty['models']=[];empty['lighting']['targetModelId']=None;cases.append({'name':'empty','document':empty})
def variant(name,fn):
 d=copy.deepcopy(base);fn(d);cases.append({'name':name,'document':d})
variant('duplicate-id',lambda d:d['models'].append(copy.deepcopy(d['models'][0])))
variant('wrong-version',lambda d:d['models'][0].update(assetSHA256='b'*64))
variant('unknown-asset',lambda d:d['models'][0].update(assetId='unknown'))
variant('field-injection',lambda d:d.update(untrusted='ignored?'))
variant('bool-intensity',lambda d:d['lighting'].update(intensity=True))
variant('invalid-target',lambda d:d['lighting'].update(targetModelId='absent'))
variant('bool-visible',lambda d:d['models'][0].update(visible=1))
variant('bool-coordinate',lambda d:d['models'][0].update(anchor=[True,0,0]))
variant('coordinate-outside',lambda d:d['models'][0].update(anchor=[100001,0,0]))
variant('negative-scale',lambda d:d['models'][0].update(scale=-1))
variant('rotation-outside',lambda d:d['models'][0].update(rotationDegrees=360001))
variant('empty-name',lambda d:d['models'][0].update(name=''))
variant('control-name',lambda d:d['models'][0].update(name='bad\x00name'))
variant('astral-name-at-limit',lambda d:d['models'][0].update(name='😀'*60))
variant('astral-name-over-limit',lambda d:d['models'][0].update(name='😀'*61))
variant('legacy-extra-modern-fields',lambda d:d.update(schema='xnby.scene-project.v1'))
variant('bad-landscape',lambda d:d['landscape'].update(scene='elsewhere'))
variant('missing-model-field',lambda d:d['models'][0].pop('scale'))
variant('model-limit',lambda d:d.update(models=[{**d['models'][0],'id':'instance-'+str(i)}for i in range(1025)]))
variant('JS-permits-NEL-name',lambda d:d['models'][0].update(name='\u0085name'))
variant('JS-trims-BOM-name',lambda d:d['models'][0].update(name='\ufeffname'))
python=[]
for row in cases:
 try:validate_scene_project(row['document'],catalog);python.append(True)
 except ValueError:python.append(False)
p=subprocess.run(['D:/Program Files/nodejs/node.exe',str(V/'check_scene_schema_r1739.mjs')],input=json.dumps({'gate':'OWN_SCENE_SCHEMA_R1739','catalog':CATALOG,'cases':cases},ensure_ascii=False).encode(),capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert p.returncode==0
node=json.loads(p.stdout)['results'];assert python==node,list(zip([x['name']for x in cases],python,node));assert sum(python)==5;mark('actual-Node-receiver-and-Python-schema-parity-'+str(len(cases)))
repo=SceneProjectRepository(STATE/'scenes',CATALOG);name='shared.scene.json';saved=repo.save(name,base,None);assert saved['changed']and repo.get(name)['document']==base;mark('complete-v2-landscape-model-lighting-snapshot-roundtrip')
assert repo.save(name,base,saved['sha256'])['changed']is False;mark('same-content-idempotent-with-exact-CAS')
refused(lambda:repo.save(name,base,None),'PROJECT_FILE_REVISION_CONFLICT');assert repo.get(name)['sha256']==saved['sha256'];mark('create-CAS-refuses-overwrite')
for filename in ['../escape.scene.json','plain.json','CON.scene.json','bad/scene.scene.json','a.scene.JSON']:
 refused(lambda:repo.save(filename,base,None))
mark('scene-filenames-require-valid-fixed-root-scene-extension')
invalid=copy.deepcopy(base);invalid['models'][0]['assetSHA256']='b'*64;refused(lambda:repo.save(name,invalid,saved['sha256']));assert repo.get(name)['document']==base;mark('unavailable-model-version-keeps-entire-prior-scene')
repo.save('legacy.scene.json',legacy,None);assert repo.get('legacy.scene.json')['document']==legacy;repo.save('empty.scene.json',empty,None);assert repo.get('empty.scene.json')['document']==empty;mark('legacy-v1-and-empty-v2-lossless-persistence')
readback=SceneProjectRepository(STATE/'scenes',CATALOG);assert readback.get(name)['document']==base;mark('new-repository-instance-reads-durable-scene')
original=sha(STATE/'scenes'/name)
import services.project_files as files_module
prior_replace=files_module.os.replace
def fail_replace(*args):raise OSError('OWN_SYNTHETIC_REPLACE_FAILURE')
files_module.os.replace=fail_replace
try:
 nextdoc=copy.deepcopy(base);nextdoc['models'][0]['anchor'][0]=1
 try:repo.save(name,nextdoc,saved['sha256'])
 except OSError:pass
 else:raise AssertionError('REPLACE_FAILURE_NOT_EXERCISED')
finally:files_module.os.replace=prior_replace
assert sha(STATE/'scenes'/name)==original and not list((STATE/'scenes').glob('*.pending'));mark('actual-replace-failure-keeps-old-whole-file-and-removes-pending')
children=[]
for number in range(4):
 child=subprocess.Popen([sys.executable,'-X','utf8','-I','-B',str(Path(__file__)),'--cas-child'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW);children.append(child);child.stdin.write(json.dumps({'gate':'OWN_SCENE_CAS_R1739','root':str(STATE/'scenes'),'expected':saved['sha256'],'number':number+10}).encode());child.stdin.close();child.stdin=None
(STATE/'release-cas-children').write_text('same-expected-CAS',encoding='ascii');results=[]
for child in children:
 while child.poll()is None:child.wait()
 out,err=child.communicate();assert child.returncode==0,err.decode()[-1000:];results.append(json.loads(out))
assert sum(row['saved']for row in results)==1 and sum(row.get('conflict',False)for row in results)==3;assert repo.get(name)['document']['models'][0]['anchor'][0]in range(10,14);mark('four-actual-processes-one-CAS-winner-three-conflicts-no-lost-update')
layers=ProjectFileRepository(STATE/'dlg-files');layers.save('layers.json',base['landscape'],None);assert layers.get('layers.json')['document']==base['landscape'];refused(lambda:layers.save('scene.json',base,None));mark('legacy-DLG-file-library-default-contract-unchanged')
tokens={secrets.token_urlsafe(20):'writer',secrets.token_urlsafe(20):'reader',secrets.token_urlsafe(20):'denied'};keys={role:'Bearer '+token for token,role in tokens.items()};subjects={r:'own-scene-'+r for r in ['writer','reader','denied']};state={'revoked':False,'checks':0};first=threading.Event()
class Platform(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  role=tokens.get(self.headers.get('Authorization','')[7:]);state['checks']+=1;first.set()
  if role is None:status=401;value={'code':401}
  else:status=200;value={'code':200,'data':{'userInfo':{'userId':subjects[role],'roleIds':['denied'if state['revoked']and role=='writer'else role],'isAdministrator':False}}}
  raw=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
platform=http.server.ThreadingHTTPServer(('127.0.0.1',0),Platform);pt=threading.Thread(target=platform.serve_forever);pt.start();access=OriginalPlatformAccess(platform.server_port,read_roles=['reader'],write_roles=['writer']);server=LayerSyncServer(0,None,access,project_files=layers,scene_projects=repo,origin='http://127.0.0.1:19091');server_thread=threading.Thread(target=server.serve_forever);handles=[];original_request=server.process_request_thread
def observed_request(*args):handles.append(threading.current_thread());return original_request(*args)
server.process_request_thread=observed_request;server_thread.start()
def request(method,path=ROUTE,role='writer',payload=None,extra=None,raw=None):
 headers={'Authorization':keys[role],ACCOUNT_HEADER:account_key(subjects[role]),'Origin':'http://127.0.0.1:19091'}
 if payload is not None:raw=json.dumps(payload,ensure_ascii=False).encode();headers['Content-Type']='application/json'
 if extra:
  for k,v in extra.items():
   if v is None:headers.pop(k,None)
   else:headers[k]=v
 conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
 try:conn.request(method,path,body=raw,headers=headers);response=conn.getresponse();body=response.read();return response.status,json.loads(body)if body else None
 finally:conn.close()
try:
 assert request('GET',role='reader')[0]==200;assert request('HEAD',role='reader')==(200,None);mark('actual-original-access-adapter-reader-GET-HEAD-scene-list')
 assert request('GET',extra={'Authorization':None})[0]==401;assert request('GET',role='denied')[0]==403;assert request('GET',extra={ACCOUNT_HEADER:'0'*64})[0]==403;assert request('GET',extra={'Origin':'https://invalid.example'})[0]==403;mark('actual-HTTP-missing-login-role-account-binding-origin-denied')
 current=repo.get(name);payload={'name':name,'expectedSHA256':current['sha256'],'document':base};assert request('POST',payload=payload,role='reader')[0]==403;assert repo.get(name)['sha256']==current['sha256'];mark('reader-cannot-write-and-prior-file-kept')
 status,value=request('POST',payload=payload);assert status==200 and value['changed'];assert request('GET',ROUTE+'/shared.scene.json',role='reader')[1]['document']==base;mark('actual-authenticated-complete-scene-HTTP-save-and-read');assert request('GET',extra={'Origin':'https://www.joinlinksmart.com'})[0]==403;mark('configured-loopback-Origin-forwarded-only-exact-trusted-origin-accepted')
 assert request('POST',payload=payload)[0]==409;mark('actual-HTTP-stale-CAS-is-409')
 assert request('POST',ROUTE+'/shared.scene.json',payload=payload)[0]==405;assert request('GET',ROUTE+'?other=1')[0]==404;assert request('GET',ROUTE+'/%2e%2e%2fescape.scene.json')[0]==422;mark('method-query-encoded-traversal-rejected')
 assert request('POST',raw=b'{"name":"x","name":"y"}',extra={'Content-Type':'application/json'})[0]==422;assert request('POST',payload=payload,extra={'Content-Type':'text/plain'})[0]==415;mark('duplicate-JSON-member-and-wrong-content-type-denied')
 before=repo.get(name);payload['expectedSHA256']=before['sha256'];wire=json.dumps(payload).encode();first.clear();c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10);c.putrequest('POST',ROUTE)
 for k,v in {'Authorization':keys['writer'],ACCOUNT_HEADER:account_key(subjects['writer']),'Content-Type':'application/json','Content-Length':str(len(wire))}.items():c.putheader(k,v)
 c.endheaders();assert first.wait(5);state['revoked']=True;c.send(wire);reply=c.getresponse();reply.read();c.close();assert reply.status==403 and repo.get(name)['sha256']==before['sha256'];state['revoked']=False;mark('actual-revocation-during-upload-rechecked-before-persistence')
 assert request('GET','/v2/project/files',role='reader')[0]==200;mark('existing-DLG-file-HTTP-route-unchanged')
finally:
 server.shutdown();server.server_close();server_thread.join()
 for handle in handles:handle.join()
 platform.shutdown();platform.server_close();pt.join();assert not server_thread.is_alive()and not pt.is_alive()and all(not h.is_alive()for h in handles)
catalog_file=STATE/'catalog.json';catalog_file.write_text(json.dumps(CATALOG),encoding='utf8');config={'sceneProjectsRoot':str(STATE/'configured-scenes'),'sceneModelCatalog':str(catalog_file),'sceneModelCatalogSHA256':sha(catalog_file)};configured=configured_scene_repository(config,STATE/'unused-layer-state',STATE/'unused-run-state');assert configured.list()['files']==[];mark('explicit-separate-directory-and-pinned-catalog-configured')
refused(lambda:validate_scene_settings({'sceneProjectsRoot':str(STATE/'partial')}));bad=dict(config,sceneModelCatalogSHA256='0'*64);refused(lambda:configured_scene_repository(bad,STATE/'unused-layer-state',STATE/'unused-run-state'));overlap=dict(config,sceneProjectsRoot=str(STATE));refused(lambda:configured_scene_repository(overlap,STATE/'unused-layer-state',STATE/'unused-run-state'));mark('partial-settings-catalog-drift-and-root-overlap-refused')
proof={'passed':True,'checks':checks,'crossLanguageCases':len(cases),'actualConcurrentCASProcesses':4,'actualCASWinners':1,'actualCASConflicts':3,'sameOriginalPlatformAccessImplementation':True,'identityUpstreamSyntheticNotActualJava':True,'actualAuthenticatedHTTPServerUsed':True,'allServerAndRequestThreadsJoined':True,'noTokensOrAuthHeadersWritten':True,'newSyntheticSceneStateOnly':True,'originalDLGFileContractKept':True,'publicUpdated':False,'originalSixOrEightParentIntegrationAccepted':False,'frontendSceneCloudUIAccepted':False,'actualIIS_TLSAccepted':False}
(D/'actual-backend-proof-r1739.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'checks':len(checks),'crossLanguageCases':len(cases),'CASProcesses':4,'CASWinners':1,'CASConflicts':3,'allHTTPThreadsJoined':True}))
