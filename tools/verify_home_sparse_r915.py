"""Actual new bundle loader and frozen core file recovery on a code-only fixture.

Private configuration/manifest identity is adapted only for this owned fixture.
All retained shipped program bytes are referenced via immutable hardlinks.
"""
from pathlib import Path
from unittest.mock import patch
import copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application'
D=R/'Document/Deployment/home_sparse_update_r914_20261104';B=R/'work/home-sparse-r914/bundle';O=R/'work/hf915';assert not O.exists()
J=lambda p:json.loads(p.read_bytes());enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
cache={}
def sha(p):
 p=Path(p);st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
 if key not in cache:
  with p.open('rb')as f:cache[key]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[key]
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prepared=J(D/'prepared-sparse-r914.json');runtime=V/'original_public_test_update_home_r46_r914.py';assert sha(runtime)==prepared['runtimeSHA256']
m=load('home_sparse_real_core_r915',runtime)
pub=R/'work/original-backend-bootstrap-r847/r36/bundle/payload';old=J(pub/'release-manifest.json');payload=J(pub/'payload-manifest.json')
sourceplan=J(R/'Document/Deployment/r45_owned_backend_r848_20261104/full-source-and-restore-plan.private.json')
required={n:p for n,p in payload['files'].items()if not n.startswith(('private/','UserData/','Assets/','seed/'))}
for n,h in old['controllerFiles'].items():
 if n not in required:required[n]={'bytes':sourceplan['sources'][n]['bytes'],'sha256':h}
sources={}
for n,p in required.items():
 src=Path(sourceplan['sources'][n]['source']);assert pin(src)==p,'RETAINED_PUBLIC_PROGRAM_SOURCE_DRIFT:'+n;sources[n]=src
assert shutil.disk_usage(R).free>2*1024**3+128*1024**2
O.mkdir();app=O/'Application';app.mkdir();put(O/'own-code-fixture.marker',b'home-r46-static-files-only-no-services\n')
touched=set(prepared['writePaths']);logical=0
for i,(n,src)in enumerate(sources.items(),1):
 dst=app/n;dst.parent.mkdir(parents=True,exist_ok=True)
 if n in touched:dst.write_bytes(src.read_bytes())
 else:os.link(src,dst)
 logical+=src.stat().st_size
 if i%5000==0:print(json.dumps({'phase':'reference-frozen-programs','files':i}),flush=True)
# Adapt just the owned fixture's private configuration pin and resulting manifests.
put(app/'private/server-configuration.json',(G/'private/server-configuration.json').read_bytes())
payload['files']['private/server-configuration.json']=pin(app/'private/server-configuration.json')
rawoldpayload=enc(payload);old['payloadManifestSHA256']=hashlib.sha256(rawoldpayload).hexdigest();rawold=enc(old)
put(app/'payload-manifest.json',rawoldpayload);put(app/'release-manifest.json',rawold)
fakeoldsha=hashlib.sha256(rawold).hexdigest()
nextpayload=J(B/'payload/payload-manifest.json');nextrelease=J(B/'payload/release-manifest.json');plan=J(B/'update-manifest.json')
nextpayload['files']['private/server-configuration.json']=payload['files']['private/server-configuration.json']
rawpayload=enc(nextpayload);nextrelease['payloadManifestSHA256']=hashlib.sha256(rawpayload).hexdigest();rawrelease=enc(nextrelease)
plan.update(targetApplication=app.as_posix(),gatewayPort=23456,acceptedOldReleases={fakeoldsha:{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
 basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=nextrelease['payloadManifestSHA256'],newReleaseSHA256=hashlib.sha256(rawrelease).hexdigest())
raws={'payload-manifest.json':rawpayload,'release-manifest.json':rawrelease}
bundle=O/'bundle'
for n,p in plan['files'].items():
 raw=raws[n]if n in raws else(B/'payload'/n).read_bytes()
 if n in raws:plan['files'][n]={'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest()}
 put(bundle/'payload'/n,raw)
put(bundle/'update-manifest.json',enc(plan));manifest_sha=sha(bundle/'update-manifest.json')
# Only these identity constants are adapted; no production function body is patched.
m.R46_HOME_BASE_RELEASE_SHA=fakeoldsha;m.R46_HOME_BASE_PAYLOAD_SHA=old['payloadManifestSHA256']
negative=[]
def rejected(name,f):
 try:f()
 except (ValueError,AssertionError,TypeError,FileNotFoundError):negative.append({'case':name,'rejected':True});return
 raise AssertionError('EXPECTED_REFUSAL:'+name)
def check():return m.load_bundle(app,bundle,manifest_sha,expected_target=app,expected_port=23456)
base_pins={n:pin(app/n)for n in [*sources,'private/server-configuration.json','payload-manifest.json','release-manifest.json']}
with patch('subprocess.Popen',side_effect=AssertionError('NO_PROCESS_IN_CODE_FIXTURE')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK_IN_CODE_FIXTURE')):
 checked,oldsha,changes=check();assert oldsha==fakeoldsha and len(changes)==len(plan['files'])==7
 pool=m.candidate_runtime_pool_preflight(app,bundle,checked);assert pool['originalMapperPreflight']['passed']
 backup=O/'normal-before';m.backup_code(app,backup,changes);m.replace_code(app,bundle,changes)
 assert sha(app/'release-manifest.json')==plan['newReleaseSHA256']
 assert all(sha(app/n)==p['SHA256']for n,p in plan['files'].items())
 m.restore_code(app,backup,changes);assert all(pin(app/n)==p for n,p in base_pins.items())
 assert all(not(app/n).exists()for n,c in changes.items()if c['before']is None)
 backup=O/'fourth-before';m.backup_code(app,backup,changes);seen=[]
 def fourth(n):
  seen.append(n)
  if len(seen)==4:raise OSError('OWN_FOURTH_STATIC_WRITE_FAILURE')
 try:m.replace_code(app,bundle,changes,after_each=fourth)
 except OSError as e:assert str(e)=='OWN_FOURTH_STATIC_WRITE_FAILURE'
 else:raise AssertionError('FOURTH_WRITE_FAULT_NOT_HIT')
 m.restore_code(app,backup,changes);assert all(pin(app/n)==p for n,p in base_pins.items())
 assert all(not(app/n).exists()for n,c in changes.items()if c['before']is None)
 rejected('wrong-manifest-hash',lambda:m.load_bundle(app,bundle,'0'*64,expected_target=app,expected_port=23456))
 rejected('wrong-target',lambda:m.load_bundle(app,bundle,manifest_sha,expected_target=O/'OtherApplication',expected_port=23456))
 css=next(n for n in plan['files']if n.endswith('.css'));path=bundle/'payload'/css;good=path.read_bytes();m.atomic(path,b'corrupt-css')
 rejected('changed-css-transport-bytes',check);m.atomic(path,good)
 path=app/'payload/business/application.jar';good=path.read_bytes();m.atomic(path,b'corrupt-retained-jar')
 rejected('retained-original-business-jar-drift',check);m.atomic(path,good)
 oldmeta=(app/'release-manifest.json').read_bytes();m.atomic(app/'release-manifest.json',oldmeta+b' ')
 rejected('unknown-base-release',check);m.atomic(app/'release-manifest.json',oldmeta)
 # Contract-only negative cases still call the exact new production function.
 for name,key,value in [('removal','removedFrontendFiles',{'frontend/security_pc/index.html':{}}),('legacy-path','legacyEntrySHA256',{'unwanted':[]}),('extra-write','files',{**plan['files'],'private/extra.json':{'bytes':0,'SHA256':'0'*64}})]:
  foreign=copy.deepcopy(plan);foreign[key]=value
  rejected(name,lambda f=foreign:m.r46_home_bundle_contract(app,bundle,f,old,nextrelease,nextpayload))
 for key in ['allOriginalGlyphsRetained','originalICCAndPixelsRetained','completeSecurityFrontendAfter','changedFiles']:
  changed=copy.deepcopy(nextrelease);changed[m.R46_HOME_FIELD][key]='foreign'
  rejected('changed-home-feature-'+key,lambda r=changed:m.r46_home_bundle_contract(app,bundle,plan,old,r,nextpayload))
 changed=copy.deepcopy(nextpayload);changed['files']['private/server-configuration.json']={'bytes':1,'sha256':'0'*64}
 rejected('private-configuration-payload-drift',lambda:m.r46_home_bundle_contract(app,bundle,plan,old,nextrelease,changed))
 changed=copy.deepcopy(nextrelease);changed['controllerFiles']['tools/serve_original_server_release.py']='0'*64
 rejected('retained-controller-descriptor-drift',lambda:m.r46_home_bundle_contract(app,bundle,plan,old,changed,nextpayload))
 assert all(pin(app/n)==p for n,p in base_pins.items())
assert all(pin(src)==required[n]for n,src in sources.items()),'ORIGINAL_SOURCE_INODES_CHANGED'
proof={'schema':'xnby.home-sparse.file-acceptance.v1','passed':True,'installedProgramOrControllerFiles':len(sources),'logicalSharedProgramBytesNotNewPhysicalCopies':logical,
 'changes':7,'removedFiles':0,'realNewBundleLoaderUsed':True,'normalReplacementAndRestorePassed':True,'fourthWriteFailureAndRestorePassed':True,
 'allBaseProgramAndPrivateConfigurationHashesRestored':True,'originalSharedSourceBytesPreserved':True,'negativeCases':negative,
 'poolAndMapperPreflightBeforeDowntimePassed':True,'fixturePrivateConfigurationManifestOnlyAdaptation':True,'productionFunctionBodiesNotPatched':True,
 'allFaultTamperingUsedAtomicDetachNotHardlinkInPlaceWrites':True,'processNetworkDatabaseOrPublicUsed':False,'fixtureRoot':str(O),'fixtureCleanupStillPending':True,'fullCloneReady':False}
put(D/'verified-files-r915.json',enc(proof));print(json.dumps({'passed':True,'fullProgramFiles':len(sources),'negativeCases':len(negative),'normalAndFourthWriteRecovery':True,'servicesStarted':False}))
