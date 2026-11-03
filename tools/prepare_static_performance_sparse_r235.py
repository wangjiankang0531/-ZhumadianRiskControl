"""Six-path static update, strict composition negatives and real file recovery."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';W=R/'work/user_feedback_20261031';OLD=W/'r36-native-history-candidate-r2/bundle';O=W/'r37-static-performance-r1';D=R/'Document/Deployment/public_test_static_performance_r37_20261103'
assert not O.exists()
sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode();J=lambda p:json.loads(p.read_bytes())
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
source=T/'original_public_test_update_r37_static_20261103.py';spec=importlib.util.spec_from_file_location('r37static',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
oldraw=(OLD/'payload/release-manifest.json').read_bytes();oldqraw=(OLD/'payload/payload-manifest.json').read_bytes();old=J(OLD/'payload/release-manifest.json');q=J(OLD/'payload/payload-manifest.json');assert sha(oldraw)=='daaf0be2b1cb17eab4640b7388901a0f00c1b920cfe2260c4d060234230fb853'
paths={'tools/original_project_branding.py':T/'original_project_branding_r229.py','deploy/iis_original/App_Code/XnbyReferenceProxy.cs':T/'frontend/static_performance_r229/XnbyReferenceProxy.cs','iis/App_Code/XnbyReferenceProxy.cs':T/'frontend/static_performance_r229/XnbyReferenceProxy.cs','tools/original_public_test_update.py':source}
bodies={n:p.read_bytes()for n,p in paths.items()};new=copy.deepcopy(old);new[m.R37_STATIC_FIELD]=copy.deepcopy(m.R37_STATIC_CONTRACT);new.update(publicTestRevision='20261103-R37-static-initial-load-performance',publicAccepted=False)
for n,b in bodies.items():new['controllerFiles'][n]=sha(b)
bodies['payload-manifest.json']=oldqraw;bodies['release-manifest.json']=enc(new)
plan=copy.deepcopy(J(OLD/'update-manifest.json'));oldproxy='deploy/iis_original/App_Code/XnbyReferenceProxy.cs';actual='iis/App_Code/XnbyReferenceProxy.cs'
plan.update(updateId='20261103-R37-static-performance-from-exact-R36',acceptedOldReleases={sha(oldraw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=old['payloadManifestSHA256'],newReleaseSHA256=sha(bodies['release-manifest.json']),oldPayloadFiles={},legacyEntrySHA256={actual:[old['controllerFiles'][oldproxy]]},removedFrontendFiles={},iisProxySHA256=old['controllerFiles'][oldproxy],files={n:{'bytes':len(b),'SHA256':sha(b)}for n,b in bodies.items()})
assert len(bodies)==6 and len(new['controllerFiles'])==22 and not any(n.startswith(('frontend/','private/','UserData/','payload/'))for n in paths)
def resolve(name,pin):
 candidates=[OLD/'payload'/name,W/'r35-personal-workflow-candidate-r1/contract-Application'/name,A/name,R/'_g/Application'/name]
 for p in candidates:
  if p.is_file()and sha(p.read_bytes())==pin:return p
 raise ValueError('UNRESOLVED_ORIGINAL_SOURCE:'+name)
baseline={n:resolve(n,pin).read_bytes()for n,pin in old['controllerFiles'].items() if n in paths}
baseline.update({actual:resolve(oldproxy,old['controllerFiles'][oldproxy]).read_bytes(),'payload-manifest.json':oldqraw,'release-manifest.json':oldraw})
assert set(baseline)==set(bodies)
peak=(sum(map(len,baseline.values()))+sum(map(len,bodies.values())))*12;assert peak<128*1024**2 and shutil.disk_usage(R).free>peak+1024**3
O.mkdir();bundle=O/'bundle';app=O/'contract-Application'
for n,b in bodies.items():put(bundle/'payload'/n,b)
put(bundle/'update-manifest.json',enc(plan));put(app/'release-manifest.json',oldraw);put(app/'payload-manifest.json',oldqraw)
for n,b in baseline.items():put(app/n,b)
assert m.static_performance_bundle_contract(app,bundle,plan,old,new,q)
cases=[]
def negative(label,mutate):
 p,o,n,payload=map(copy.deepcopy,[plan,old,new,q]);mutate(p,o,n,payload)
 try:accepted=m.static_performance_bundle_contract(app,bundle,p,o,n,payload)
 except ValueError as e:cases.append({'case':label,'refused':str(e)});return
 raise AssertionError('BAD_STATIC_COMPOSITION_ACCEPTED:'+label)
negative('missing-static-descriptor',lambda p,o,n,q:n.pop(m.R37_STATIC_FIELD))
for key in ['revision','onlyPublicStaticGETHEADNegotiatesGzip','encodedResponseBytesPreserved','contentEncodingAndVaryForwarded','successfulHashedAssetsImmutable','htmlBusinessErrorsAndNonHashedResourcesNotLongCached','businessPayloadAuthDatabaseAndPrivateConfigurationUnchanged']:
 negative('descriptor-'+key,lambda p,o,n,q,k=key:n[m.R37_STATIC_FIELD].__setitem__(k,False))
for key in paths:
 negative('wrong-candidate-control-'+key,lambda p,o,n,q,k=key:n['controllerFiles'].__setitem__(k,'0'*64))
negative('wrong-retained-controller',lambda p,o,n,q:n['controllerFiles'].__setitem__(m.R23_CONTROLLER,'0'*64))
negative('wrong-old-updater',lambda p,o,n,q:o['controllerFiles'].__setitem__('tools/original_public_test_update.py','0'*64))
for key in ['payload/business/application.jar',m.R31_NATIVE_CLASS,next(k for k in q['files']if k.startswith('frontend/emergency_pc/')),'private/server-configuration.json']:
 negative('changed-retained-payload-'+key,lambda p,o,n,q,k=key:q['files'][k].__setitem__('sha256','0'*64))
negative('extra-accepted-release',lambda p,o,n,q:p['acceptedOldReleases'].__setitem__('0'*64,{}))
negative('wrong-existing-IIS-proxy',lambda p,o,n,q:p.__setitem__('iisProxySHA256','0'*64))
negative('extra-legacy-entry',lambda p,o,n,q:p['legacyEntrySHA256'].__setitem__('iis/web.config',['0'*64]))
negative('wrong-existing-IIS-legacy-pin',lambda p,o,n,q:p['legacyEntrySHA256'].__setitem__(actual,['0'*64]))
negative('unexpected-frontend-write',lambda p,o,n,q:p['files'].__setitem__('frontend/emergency_pc/new.js',{'bytes':1,'SHA256':'0'*64}))
negative('unexpected-removal',lambda p,o,n,q:p['removedFrontendFiles'].__setitem__('frontend/emergency_pc/old.js',{}))
negative('unexpected-old-payload-adaptation',lambda p,o,n,q:p['oldPayloadFiles'].__setitem__('payload/business/application.jar',{}))
negative('missing-required-IIS-write',lambda p,o,n,q:p['files'].pop(actual))
negative('wrong-static-file-transport',lambda p,o,n,q:p['files'][actual].__setitem__('SHA256','0'*64))
negative('wrong-updater-transport',lambda p,o,n,q:p['files']['tools/original_public_test_update.py'].__setitem__('SHA256','0'*64))
negative('drop-original-history',lambda p,o,n,q:n.pop(m.R36_HISTORY_FIELD))
negative('premature-full-acceptance',lambda p,o,n,q:n.__setitem__('publicAccepted',True))
negative('wrong-static-revision',lambda p,o,n,q:n.__setitem__('publicTestRevision','other'))
put(D/'composition-negative-cases.json',enc(cases))
changes={n:{'before':sha(baseline[n]),'after':sha(b)}for n,b in bodies.items()};results=[]
for label,trigger in [('normal',None),('first-write',1),('IIS-source-write',oldproxy),('live-IIS-write',actual),('branding-write','tools/original_project_branding.py'),('updater-write','tools/original_public_test_update.py'),('payload-manifest-write','payload-manifest.json'),('release-pointer-write','release-manifest.json')]:
 case=O/'transactions'/label;app=case/'Application'
 for n,b in baseline.items():put(app/n,b)
 m.backup_code(app,case/'before',changes);count=[0];caught=False
 def after(n):
  count[0]+=1
  if n==trigger or count[0]==trigger:raise RuntimeError('OWN_STATIC_FAULT')
 try:m.replace_code(app,bundle,changes,after_each=after)
 except RuntimeError as e:assert str(e)=='OWN_STATIC_FAULT'and trigger is not None;caught=True
 assert caught==(trigger is not None)
 if trigger is None:assert all((app/n).read_bytes()==b for n,b in bodies.items())
 m.restore_code(app,case/'before',changes);assert all((app/n).read_bytes()==b for n,b in baseline.items())
 results.append({'scenario':label,'allSixOriginalFilesRestored':True,'writesBeforeRestore':count[0]})
case=O/'transactions/foreign-drift';app=case/'Application'
for n,b in baseline.items():put(app/n,b)
m.backup_code(app,case/'before',changes);put(app/actual,b'own unrelated edit\n');snap={n:sha((app/n).read_bytes())for n in bodies}
try:m.restore_code(app,case/'before',changes)
except ValueError as e:assert str(e).startswith('ROLLBACK_FILE_DRIFT:')
else:raise AssertionError('FOREIGN_IIS_EDIT_OVERWRITTEN')
assert snap=={n:sha((app/n).read_bytes())for n in bodies}
proof={'passed':True,'writes':6,'removals':0,'negativeCompositionCases':len(cases),'allNegativeCasesRefused':True,'normalAndFaultRecoveryCases':results,'foreignIISDriftRefusedBeforeAnyRestore':True,'allPayloadRowsAndOriginalBusinessFrontendsPrivateConfigUnchanged':True,'newUpdaterSHA256':sha(source.read_bytes()),'newReleaseSHA256':plan['newReleaseSHA256'],'updateManifestSHA256':sha((bundle/'update-manifest.json').read_bytes()),'oldReleaseSHA256':sha(oldraw),'fullProgramPreflightPassed':False,'publicUploadedOrInstalled':False}
put(O/'changes.json',enc(changes));put(D/'composition-and-recovery.json',enc(proof));print(json.dumps({k:v for k,v in proof.items()if k!='normalAndFaultRecoveryCases'}))
