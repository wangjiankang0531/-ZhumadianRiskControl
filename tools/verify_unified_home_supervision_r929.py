"""Run the actual frozen R46 inner validator and R47 extension on code-only files.

No service/network/SQL; immutable program hardlinks, atomic tampering and restore.
Private manifest identity is adapted solely to this owned fixture.
"""
from pathlib import Path
from unittest.mock import patch
import copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/unified_home_supervision_r928_20261104';B=R/'work/unified-home-supervision-r928/bundle';O=R/'work/sv929'
J=lambda p:json.loads(p.read_bytes());enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
cache={}
def sha(p):
 p=Path(p);s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
 if key not in cache:
  with p.open('rb')as f:cache[key]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[key]
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not O.exists()and shutil.disk_usage(R).free>2*1024**3+256*1024**2
prepared=J(D/'prepared-r928.json');runtime=V/'original_public_test_home_supervision_r47_r928.py';assert sha(runtime)==prepared['runtimeSHA256']
w=load('unified_supervision_r929',runtime);m=w.runtime()
public=R/'work/original-backend-bootstrap-r847/r36/bundle/payload';old=J(public/'release-manifest.json');payload=J(public/'payload-manifest.json')
sourceplan=J(R/'Document/Deployment/r45_owned_backend_r848_20261104/full-source-and-restore-plan.private.json')
required={n:p for n,p in payload['files'].items()if not n.startswith(('private/','UserData/','Assets/','seed/'))}
for n,h in old['controllerFiles'].items():required.setdefault(n,{'bytes':sourceplan['sources'][n]['bytes'],'sha256':h})
sources={n:Path(sourceplan['sources'][n]['source'])for n in required}
assert all(pin(p)==required[n]for n,p in sources.items())
O.mkdir();put(O/'own-code-fixture.marker',b'r47-frozen-core-file-test-no-services\n');app=O/'Application';app.mkdir();logical=0
touched=set(J(B/'update-manifest.json')['files'])
for i,(n,p)in enumerate(sources.items(),1):
 q=app/n;q.parent.mkdir(parents=True,exist_ok=True)
 if n in touched:q.write_bytes(p.read_bytes())
 else:os.link(p,q)
 logical+=p.stat().st_size
 if i%5000==0:print(json.dumps({'phase':'reference-frozen-R45-programs','files':i}),flush=True)
put(app/'private/server-configuration.json',(G/'private/server-configuration.json').read_bytes())
payload['files']['private/server-configuration.json']=pin(app/'private/server-configuration.json');raw_payload=enc(payload);old['payloadManifestSHA256']=hashlib.sha256(raw_payload).hexdigest();raw_old=enc(old)
put(app/'payload-manifest.json',raw_payload);put(app/'release-manifest.json',raw_old);oldsha=hashlib.sha256(raw_old).hexdigest()
inner=J(B/'base-r46/update-manifest.json');inner_payload=J(B/'base-r46/payload/payload-manifest.json');inner_release=J(B/'base-r46/payload/release-manifest.json')
inner_payload['files']['private/server-configuration.json']=payload['files']['private/server-configuration.json'];ipraw=enc(inner_payload);inner_release['payloadManifestSHA256']=hashlib.sha256(ipraw).hexdigest();irraw=enc(inner_release)
accepted={oldsha:{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}}
inner.update(targetApplication=app.as_posix(),gatewayPort=23456,acceptedOldReleases=accepted,basePayloadManifestSHA256=old['payloadManifestSHA256'],newReleaseSHA256=hashlib.sha256(irraw).hexdigest(),newPayloadManifestSHA256=inner_release['payloadManifestSHA256'])
iraws={'payload-manifest.json':ipraw,'release-manifest.json':irraw}
bundle=O/'bundle'
for n,p in inner['files'].items():
 b=iraws[n]if n in iraws else(B/'base-r46/payload'/n).read_bytes()
 if n in iraws:inner['files'][n]={'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()}
 put(bundle/'base-r46/payload'/n,b)
put(bundle/'base-r46/update-manifest.json',enc(inner))
plan=J(B/'update-manifest.json');next_payload=w.expected_payload(inner_payload);npraw=enc(next_payload);next_release=w.expected_release(inner_release,hashlib.sha256(npraw).hexdigest());nrraw=enc(next_release)
plan.update(targetApplication=app.as_posix(),gatewayPort=23456,acceptedOldReleases=accepted,basePayloadManifestSHA256=old['payloadManifestSHA256'],newReleaseSHA256=hashlib.sha256(nrraw).hexdigest(),newPayloadManifestSHA256=next_release['payloadManifestSHA256'])
plan[w.OUTER_FIELD]['manifestSHA256']=sha(bundle/'base-r46/update-manifest.json')
raws={'payload-manifest.json':npraw,'release-manifest.json':nrraw}
for n,p in plan['files'].items():
 b=raws[n]if n in raws else(B/'payload'/n).read_bytes()
 if n in raws:plan['files'][n]={'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()}
 put(bundle/'payload'/n,b)
put(bundle/'update-manifest.json',enc(plan));manifestsha=sha(bundle/'update-manifest.json')
m.R46_HOME_BASE_RELEASE_SHA=oldsha;m.R46_HOME_BASE_PAYLOAD_SHA=old['payloadManifestSHA256']
negative=[]
def reject(name,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError,FileNotFoundError,TypeError):negative.append(name);return
 raise AssertionError('REJECTION_REQUIRED:'+name)
def check():return m.load_bundle(app,bundle,manifestsha,expected_target=app,expected_port=23456)
basepins={n:pin(app/n)for n in [*sources,'private/server-configuration.json','payload-manifest.json','release-manifest.json']}
with patch('subprocess.Popen',side_effect=AssertionError('NO_PROCESS_IN_R929')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK_IN_R929')):
 checked,actualold,changes=check();assert actualold==oldsha and len(changes)==11 and len(plan['files'])==11
 pool=m.candidate_runtime_pool_preflight(app,bundle,checked);assert pool['supervisionModuleAndInitializerPreflightPassed']and pool['originalMapperPreflight']['passed']
 assert w.declared(next_release)and not w.declared(old)and m.controller_pin_for(old)==old['controllerFiles'][w.CONTROLLER]and m.controller_pin_for(next_release)==next_release['controllerFiles'][w.CONTROLLER]
 assert m.pool_control_pins(old)[w.CONTROLLER]['sha256']==old['controllerFiles'][w.CONTROLLER]and m.pool_control_pins(next_release)[w.CONTROLLER]==w.PINS[w.CONTROLLER]
 for label,fault in [('normal',False),('fourth-write',True)]:
  backup=O/(label+'-before');m.backup_code(app,backup,changes);seen=[]
  def after(n):
   seen.append(n)
   if fault and len(seen)==4:raise OSError('OWN_R929_FOURTH_WRITE')
  try:m.replace_code(app,bundle,changes,after_each=after)
  except OSError as e:assert fault and str(e)=='OWN_R929_FOURTH_WRITE'
  else:assert not fault and sha(app/'release-manifest.json')==plan['newReleaseSHA256']and all(sha(app/n)==p['SHA256']for n,p in plan['files'].items())
  m.restore_code(app,backup,changes);assert all(pin(app/n)==p for n,p in basepins.items())and all(not(app/n).exists()for n,c in changes.items()if c['before']is None)
 reject('wrong-manifest-pin',lambda:m.load_bundle(app,bundle,'0'*64,expected_target=app,expected_port=23456))
 reject('wrong-target',lambda:m.load_bundle(app,bundle,manifestsha,expected_target=O/'Foreign',expected_port=23456))
 # Actual file corruption, always detach hardlinks atomically.
 for name,path in [('inner-manifest',bundle/'base-r46/update-manifest.json'),('home-css',bundle/'payload/frontend/security_pc/assets/css/xnby-home-transfer-162b8ebe4004d78f.css'),('module',bundle/'payload'/w.DESCRIPTOR['file']),('helper',bundle/'payload'/w.HELPER),('retained-original-jar',app/'payload/business/application.jar')]:
  good=path.read_bytes();m.atomic(path,b'foreign');reject('corrupt-'+name,check);m.atomic(path,good)
 # Exercise the actual outer loader with a recomputed transport pin, never alter production functions.
 original_plan=(bundle/'update-manifest.json').read_bytes()
 for name,key,value in [('extra-write','files',{**plan['files'],'private/foreign.json':{'bytes':0,'SHA256':'0'*64}}),('remove-path','removedFrontendFiles',{'frontend/security_pc/index.html':{}}),('legacy-write','legacyEntrySHA256',{'foreign':[]}),('foreign-update-id','updateId','20261104-r47-home-supervision-from-r99')]:
  changed=copy.deepcopy(plan);changed[key]=value;m.atomic(bundle/'update-manifest.json',enc(changed));freshsha=sha(bundle/'update-manifest.json')
  reject(name,lambda:m.load_bundle(app,bundle,freshsha,expected_target=app,expected_port=23456));m.atomic(bundle/'update-manifest.json',original_plan)
 assert all(pin(app/n)==p for n,p in basepins.items())
assert all(pin(p)==required[n]for n,p in sources.items()),'SHARED_ORIGINAL_SOURCE_CHANGED'
proof={'schema':'xnby.r47.frozen-core-file-acceptance.v1','passed':True,'fullInstalledProgramSources':len(sources),'logicalSharedBytesNotPhysicalCopies':logical,
 'writes':11,'removals':0,'actualFrozenCoreAndInnerCompleteValidatorUsed':True,'productionFunctionBodiesNotModifiedForFixture':True,'onlyFixturePrivateIdentityConstantsAdapted':True,
 'normalReplacementAndRestorePassed':True,'fourthWriteFailureAndRestorePassed':True,'oldAndNewHistoryPoolControllerPinsSelectedByRelease':True,
 'moduleAndOriginalJarAndConfigurationPreflightBeforeDowntimePassed':True,'negativeCases':negative,'originalSourceAndBaseHashesPreserved':True,
 'processNetworkOrDatabaseUsed':False,'fixtureCleanupPending':True,'publicChanged':False,'fullCloneReady':False}
(D/'verified-files-r929.json').write_bytes(enc(proof));print(json.dumps(proof))
