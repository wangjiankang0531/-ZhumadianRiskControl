"""Check the actual frozen transport and simulated HTTP boundaries, with all network denied."""
from pathlib import Path
import ast,copy,gzip,hashlib,importlib.util,io,json,re,socket,subprocess,sys,tempfile,zipfile
from unittest.mock import patch
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_home_supervision_r47_20261104';T=D/'delivery'
F=R/'work/sv929/Application';B=R/'work/unified-home-supervision-r928/bundle'
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
spec=importlib.util.spec_from_file_location('r47_frozen_delivery',T/'deploy_home_supervision_r47.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=J(D/'delivery-manifest.json');prep=J(D/'preparation-r932.json');assert sha((D/'delivery-manifest.json').read_bytes())==prep['manifestSHA256']
assert (D/'delivery-manifest.json').read_bytes()==(T/'delivery-manifest.json').read_bytes()
assert set(f.name for f in T.iterdir())==set(manifest['files'])|{'delivery-manifest.json'}
for n,p in manifest['files'].items():b=(T/n).read_bytes();assert len(b)==p['bytes']and sha(b)==p['sha256']
archive=T/m.ARCHIVE_NAME;assert sha(archive.read_bytes())==m.ARCHIVE_SHA
assert sha((T/'original_public_test_base_r46.py').read_bytes())==m.CORE_SHA
base=next(iter(m.BASES.values()));old=next(iter(m.BASES));failures=[]

def reject(name,fn):
 try:fn()
 except (ValueError,KeyError,FileExistsError,FileNotFoundError,zipfile.BadZipFile):failures.append(name);return
 raise AssertionError('DID_NOT_REJECT:'+name)

def forbidden(*a,**k):raise AssertionError('REAL_PROCESS_OR_NETWORK_FORBIDDEN')

with patch.object(subprocess,'Popen',forbidden),patch.object(socket,'create_connection',forbidden):
 with tempfile.TemporaryDirectory(prefix='home-supervision-transport-r933-',dir=V)as temp:
  temp=Path(temp);stage=temp/'extract'
  with zipfile.ZipFile(archive)as z:
   selected=m.validate_archive(z,base);assert len(selected['files'])==11 and not selected['removedFrontendFiles'];members={i.filename:z.read(i)for i in z.infolist()}
  m.extract_selected_archive(archive,stage,base)
  assert {p.relative_to(stage).as_posix()for p in stage.rglob('*')if p.is_file()}=={'web.config','update-manifest.json'}|{'payload/'+n for n in selected['files']}|{n for n in members if n.startswith('base-r46/')}
  for n,p in selected['files'].items():b=(stage/'payload'/n).read_bytes();assert len(b)==p['bytes']and sha(b)==p['SHA256']
  reject('existing-extraction-stage',lambda:m.extract_selected_archive(archive,stage,base))
  def mutated(case,mutate):
   rows=list(members.items());rows=mutate(rows);f=temp/(case+'.zip')
   with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED)as z:
    for n,b in rows:z.writestr(n,b)
   def invoke():
    with zipfile.ZipFile(f)as z:m.validate_archive(z,base)
   reject(case,invoke)
  mutated('extra-archive-member',lambda x:x+[('unexpected.txt',b'x')])
  mutated('parent-traversal',lambda x:x+[('../escape',b'x')])
  mutated('windows-colon-member',lambda x:x+[('C:/escape',b'x')])
  mutated('duplicate-member',lambda x:x+[x[0]])
  mutated('missing-member',lambda x:x[:-1])
  mutated('corrupted-payload',lambda x:[(n,b+b'x'if n.startswith('payload/frontend/')else b)for n,b in x])
  mutated('changed-fixed-manifest',lambda x:[(n,b+b' 'if n.endswith('update-manifest.json')else b)for n,b in x])
  mutated('changed-inner-home-manifest',lambda x:[(n,b+b' 'if n=='base-r46/update-manifest.json'else b)for n,b in x])
  mutated('changed-frozen-core-payload',lambda x:[(n,b+b' 'if n=='payload/tools/original_public_test_base_r46.py'else b)for n,b in x])
  for field,value in [('targetApplication','C:/elsewhere'),('gatewayPort',1),('updateId','foreign'),('acceptedOldReleases',{}),('newReleaseSHA256','0'*64),('files',{}),('removedFrontendFiles',{'foreign':{}})]:
   plan=copy.deepcopy(selected);plan[field]=value;raw=(json.dumps(plan)+'\n').encode();rows={**members,'variants/r45/update-manifest.json':raw}
   f=temp/('semantic-'+field+'.zip')
   with zipfile.ZipFile(f,'w')as z:
    for n,b in rows.items():z.writestr(n,b)
   adjusted={**base,'manifestSHA256':sha(raw)}
   def invoke():
    with zipfile.ZipFile(f)as z:m.validate_archive(z,adjusted)
   # The pin may be adjusted only in this test's BASES, never on disk.
   with patch.object(m,'BASES',{old:adjusted}):reject('semantic-'+field,invoke)
  app=temp/'app';(app/'tools').mkdir(parents=True)
  original_release=(R/'work/original-backend-bootstrap-r847/r36/bundle/payload/release-manifest.json').read_bytes()
  (app/'release-manifest.json').write_bytes(original_release)
  (app/'tools/original_public_test_update.py').write_bytes((R/'Application/tools/original_public_test_update_r45_bootstrap_r847.py').read_bytes())
  assert m.select_installed_base(app)==(old,base)
  (app/'tools/original_public_test_update.py').write_bytes(b'foreign');reject('wrong-installed-updater',lambda:m.select_installed_base(app))
  (app/'release-manifest.json').write_bytes(b'foreign');reject('unknown-installed-release',lambda:m.select_installed_base(app))
  record={'oldReleaseSHA256':old,'newReleaseSHA256':m.NEW,'updateId':base['updateId'],'attempt':str(m.APP/'UserData/OriginalPublicUpdates'/('a'*32))}
  assert m.recovery_guard(record)==base
  for field,val in [('oldReleaseSHA256','0'*64),('newReleaseSHA256','0'*64),('updateId','foreign'),('attempt',str(m.APP/'UserData/foreign'/('a'*32))),('attempt',str(m.APP/'UserData/OriginalPublicUpdates/not-a-run'))]:
   reject('recovery-'+field+'-'+str(len(failures)),lambda:m.recovery_guard({**record,field:val}))
  static={}
  for path,pin in m.STATIC_EXPECTED.items():
   if path.startswith('/zhumadian/emergency/'):n='frontend/emergency_pc/'+path.split('/branding-20261025/',1)[1]
   else:n='frontend/security_pc/'+path.split('/branding-20261025/',1)[1]
   src=B/'payload'/n
   if not src.exists():src=F/n
   b=src.read_bytes()
   if n.endswith('assets/js/index-DOC7mNwT.js'):
    # Existing server-side sub_filter changes the wire representation. Apply the
    # actual pinned branding directives in a single source scan, not a product edit.
    specb=importlib.util.spec_from_file_location('r917_original_branding',F/'tools/original_project_branding.py');brand=importlib.util.module_from_spec(specb);specb.loader.exec_module(brand)
    replacements={}
    for line in brand.static_directives(brand.PROJECT_NAME):
     if line.startswith('sub_filter '):
      parts=re.findall(r'"(?:\\.|[^"\\])*"',line);assert len(parts)==2
      before,after=[json.loads(x).encode('utf8')for x in parts];replacements[before]=after
    pattern=re.compile(b'|'.join(re.escape(x)for x in replacements));b=pattern.sub(lambda match:replacements[match.group()],b)
   assert len(b)==pin['decodedBytes']and sha(b)==pin['decodedSHA256'],path
   static[path]=b
  for path,pin in m.STATIC_EXPECTED.items():
   b=static[path];encoding=pin.get('encoding','gzip');headers={'cache-control':'public, max-age=31536000, immutable','content-type':pin.get('mime','application/javascript')}
   if encoding=='gzip':headers.update({'content-encoding':'gzip','vary':'Accept-Encoding'});body=gzip.compress(b)
   else:body=b
   assert m.validate_static_response(path,encoding,200,headers,body)['decodedContentMatched']
   reject('bad-response-content-'+path.rsplit('/',1)[-1],lambda:m.validate_static_response(path,encoding,200,headers,body+b'x')) if encoding=='identity' else None
   reject('bad-response-cache-'+path.rsplit('/',1)[-1],lambda:m.validate_static_response(path,encoding,200,{**headers,'cache-control':'no-store'},body))
   reject('bad-response-status-'+path.rsplit('/',1)[-1],lambda:m.validate_static_response(path,encoding,503,headers,body))
   if 'mime'in pin:reject('bad-mime-'+pin['mime'],lambda:m.validate_static_response(path,encoding,200,{**headers,'content-type':'application/octet-stream'},body))
  responses=[]
  class Response:
   status=200
   def __init__(self,path,accept):self.path=path;self.accept=accept
   def getheaders(self):
    if self.path not in static:return [('Cache-Control','no-store')]
    p=m.STATIC_EXPECTED[self.path];h=[('Cache-Control','public, max-age=31536000, immutable'),('Content-Type',p.get('mime','application/javascript'))]
    if self.accept=='gzip':h +=[('Content-Encoding','gzip'),('Vary','Accept-Encoding')]
    return h
   def read(self,bound):
    if self.path not in static:
     root=B/'payload/frontend/security_pc/index.html'if self.path=='/zhumadian/home'else F/'frontend/emergency_pc/index.html'
     return pattern.sub(lambda match:replacements[match.group()],root.read_bytes())
    b=static[self.path];return gzip.compress(b)if self.accept=='gzip'else b
  class Connection:
   def __init__(self,*a,**k):pass
   def request(self,method,path,headers):responses.append((path,headers['Accept-Encoding']));self.response=Response(path,headers['Accept-Encoding'])
   def getresponse(self):return self.response
   def close(self):pass
  class SSLContext:
   def wrap_socket(self,*a,**k):return object()
  class Runtime:
   R37_STATIC_CONTRACT={'files':{'iis/App_Code/XnbyReferenceProxy.cs':{'sha256':'a'*64}}}
   def ingress_preflight(self,*a):return {},'127.0.0.1'
   def write_json(self,p,v):p.write_text(json.dumps(v))
  import http.client,ssl
  with patch.object(http.client,'HTTPConnection',Connection),patch.object(socket,'create_connection',lambda *a,**k:object()),patch.object(ssl,'create_default_context',SSLContext):
   m.verify_static_gateway_and_iis(Runtime(),temp,{})
  result=J(temp/'server-static-performance-result.json');assert result['passed']and len(result['checks'])==22 and len(responses)==22
  m.write_scoped_result(temp,'preflight-passed',base,old);scoped=J(temp/'r47-scoped-result.json');assert scoped['schema']=='xnby.r47.scoped-deployment-result.v1'and not scoped['credentialsSessionsBusinessRowsRuntimeUUIDOrRawLogsIncluded']
  (temp/'r47-scoped-result.json').write_text('{"schema":"foreign"}')
  reject('foreign-scoped-result-refuse-overwrite',lambda:m.write_scoped_result(temp,'deploy-complete',base,old))
  # The wrapper's original execution order is unchanged except version string labels.
  tree=ast.parse((T/'deploy_home_supervision_r47.py').read_text('utf8'));main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');src=ast.unparse(main)
  assert src.index('candidate_runtime_pool_preflight')<src.index('m.apply_update')and src.index('verify_candidate_mapper_configuration')<src.index('m.apply_update')
  assert 'POSTCHECK_UPDATE_RECORD_DRIFT_REFUSE_ROLLBACK'in src and 'm.rollback_latest(APP)'in src
report={'schema':'xnby.r47.transport-acceptance.v1','passed':True,'transportFiles':9,'transportBytes':prep['transportBytes'],'manifestSHA256':prep['manifestSHA256'],
 'archiveMembers':21,'exactExtractedFiles':21,'allPayloadAndTransportPinsMatched':True,'negativeCases':failures,'negativeCaseCount':len(failures),
 'simulatedGatewayAndIISTLSResponseCases':22,'realNetworkOrProcessOrDatabaseUsed':False,'actualPublicTLSOrIISAccepted':False,
 'actualCoreNormalAndFourthWriteRecoveryEvidence':'unified_home_supervision_r928_20261104/verified-files-r929.json',
 'preflightBeforeApplyOrderAndConditionalRollbackRetained':True,'temporaryExtractionAndMutationFilesRemoved':True,'publicChanged':False}
(D/'verified-transport-r933.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(report))
