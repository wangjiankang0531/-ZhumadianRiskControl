"""R2 physical-file verifier source. Requires normal approval before execution.
Do not run superseded R1008. No service startup or public deployment.
"""
from pathlib import Path,PurePosixPath
import copy,hashlib,importlib.util,json,os,shutil,subprocess,time
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');D=V/'r48-retained-preflight-r2-r1013';W=R/'work/f482';REPORT=R/'Document/Deployment/event_result_runtime_r1015_20261105/verified-real-files-r1015.json'
J=lambda p:json.loads(Path(p).read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not W.exists() and not REPORT.exists()
assert REPORT.parent.is_dir(), 'PREPARE_EXACT_REVIEWED_REPORT_DIRECTORY_FIRST'
assert J(V/'verified-retained-preflight-unit-r1014.json')['passed']
assert sha(D/'source/original_public_test_update.py') == '43d3096f73f766e6500da330868d63ba13a869b9e075cfa0092e27ee511ecfa7'
assert J(R/'work/ev1010/verified-event-crud-r1010.json')['passed']
resolution=J(V/'r48-file-source-resolution-r1007.private.json');assert not resolution['unresolved']
# Override only the two changed-control sources; immutable retained programs use the prior resolution.
for relative in ['tools/original_public_test_update.py','tools/original_public_test_base_r46.py']:
 source=D/'source'/Path(relative).name
 resolution['newSources'][relative]={'source':str(source),'bytes':source.stat().st_size,'sha256':sha(source)}
query="$ErrorActionPreference='Stop'; (Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='nginx.exe' OR Name='redis-server.exe' OR Name='chrome.exe'\" | Where-Object { ($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application') } | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
assert shutil.disk_usage(R).free>2*1024**3+128*1024**2
maxpaths=max(len(str(W/label/n))for label,b in resolution['bases'].items()for n in b['programs']);assert maxpaths<248
W.mkdir();(W/'own-r48-file-fixture.json').write_bytes(enc({'ownedProgramsOnly':True,'noServicesOrAccountBusinessSeedGISData':True,'hardlinkLogicalBytesNotPhysicalStorage':True}))
cases=[];stats=[];source_mutation_checks=[]
def owned(p):
 p=Path(p).absolute();assert p.is_relative_to(W)and p!=W
 for x in [p,*p.parents]:
  if x.exists():assert not x.is_symlink()and not x.lstat().st_file_attributes&0x400
 return p
def link_program(source,dest,pin):
 source=Path(source);dest=owned(dest);assert source.is_file()and source.stat().st_size==pin['bytes']and source.drive.casefold()==dest.drive.casefold(),'SAME_VOLUME_PINNED_PROGRAM_REQUIRED'
 dest.parent.mkdir(parents=True,exist_ok=True);os.link(source,dest);assert os.path.samefile(source,dest)
def atom(p,raw):
 p=owned(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=owned(p.with_name('.'+p.name+'.filetest'))
 with tmp.open('xb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def rejected(name,fn):
 try:fn()
 except ValueError as e:cases.append({'case':name,'rejected':True,'reason':str(e)})
 else:raise AssertionError('INVALID_REAL_FILE_ACCEPTED:'+name)
for label,b in resolution['bases'].items():
 print(json.dumps({'phase':'materialize-readonly-program-links','base':label,'programs':len(b['programs'])}),flush=True)
 app=owned(W/label);bundle=owned(W/('b'+label[1:]));app.mkdir();(bundle/'payload').mkdir(parents=True)
 for index,(name,pin)in enumerate(b['programs'].items(),1):
  rel=PurePosixPath(name);assert not rel.is_absolute()and '..'not in rel.parts and ':'not in name and not name.startswith(('private/','UserData/','seed/','Assets/'))
  link_program(pin['source'],app/name,pin)
  if index%4000==0:print(json.dumps({'phase':'program-links','base':label,'linked':index}),flush=True)
 old_release=J(Path(b['metadataRoot'])/'release-manifest.json');old_payload=J(Path(b['metadataRoot'])/'payload-manifest.json')
 # Do not import or fabricate real private configuration bytes. Test bindings
 # adapt only this private row/hash and the owned target path, not program pins.
 dummy=enc({'schema':'xnby.synthetic.private.file-fixture.v1','containsCredentials':False})
 old_payload['files']['private/server-configuration.json']={'bytes':len(dummy),'sha256':hashlib.sha256(dummy).hexdigest()}
 atom(app/'private/server-configuration.json',dummy);atom(app/'payload-manifest.json',enc(old_payload));old_release['payloadManifestSHA256']=sha(app/'payload-manifest.json');atom(app/'release-manifest.json',enc(old_release))
 wrapper=load('r48_actual_file_'+label,D/'source/original_public_test_update.py');m=wrapper.runtime()
 original_common=copy.deepcopy(m.R48_PLAN_COMMON);original_bases=copy.deepcopy(m.R48_BASES)
 formal_plan=J(D/('update-from-'+label+'.json'));formal_base=next(iter(formal_plan['acceptedOldReleases']))
 binding=copy.deepcopy(original_bases[formal_base]);binding['accepted']['payloadManifestSHA256']=old_release['payloadManifestSHA256']
 m.R48_BASES={sha(app/'release-manifest.json'):binding};m.R48_PLAN_COMMON={**original_common,'targetApplication':app.as_posix()}
 target_payload=copy.deepcopy(old_payload);target_payload['files']=m.r48_expected_files(old_payload['files'])
 atom(bundle/'payload/payload-manifest.json',enc(target_payload));target_release=m.r48_expected_release(old_release,sha(bundle/'payload/payload-manifest.json'));atom(bundle/'payload/release-manifest.json',enc(target_release))
 assert wrapper.declared(target_release)
 changed={n:p for n,p in target_payload['files'].items()if old_payload['files'].get(n)!=p}
 files={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in changed.items()}
 for name,pin in changed.items():
  assert not name.startswith(('private/','UserData/','seed/','Assets/'))
  source=resolution['newSources'][name];assert source['sha256']==pin['sha256']and source['bytes']==pin['bytes']
  link_program(source['source'],bundle/'payload'/name,pin)
 for name in ['payload-manifest.json','release-manifest.json']:
  p=bundle/'payload'/name;files[name]={'bytes':p.stat().st_size,'SHA256':sha(p)}
 removed={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in old_payload['files'].items()if n.startswith('frontend/emergency_pc/')and n not in target_payload['files']}
 plan={**m.R48_PLAN_COMMON,'acceptedOldReleases':{sha(app/'release-manifest.json'):binding['accepted']},'basePayloadManifestSHA256':old_release['payloadManifestSHA256'],'files':files,'newPayloadManifestSHA256':sha(bundle/'payload/payload-manifest.json'),'newReleaseSHA256':sha(bundle/'payload/release-manifest.json'),
  'oldPayloadFiles':{n:old_payload['files'][n]for n in files if n in old_payload['files']},'removedFrontendFiles':removed,'updateId':'20261105-r48-event-results-from-'+label}
 atom(bundle/'update-manifest.json',enc(plan))
 def validate():return m.load_bundle(app,bundle,sha(bundle/'update-manifest.json'),expected_target=app.as_posix(),expected_port=18892)
 print(json.dumps({'phase':'real-full-loader','base':label}),flush=True)
 started=time.monotonic();checked,old_pin,changes=validate();assert checked==plan and old_pin==sha(app/'release-manifest.json')and set(changes)==set(files)|set(removed)
 cases.append({'case':label+'-real-generic-and-R48-loader','passed':True,'programsMaterializedAndHashRead':len(b['programs']),'fileCheckerReadAndSHAFunctionsMocked':False,'ownedTargetAndSyntheticPrivateMetadataBindingsAdapted':True,'seconds':round(time.monotonic()-started,3)})
 # Break only the fixture hardlink with atomic replacement; never truncate a
 # shared original file. Each injected byte set is restored before continuing.
 old_name=next(n for n,p in old_payload['files'].items()if n.startswith('frontend/security_pc/')and n.endswith('.css')and n not in files and p['bytes']<65536 and not (app/n).stat().st_file_attributes&1)
 p=app/old_name;before=p.read_bytes();source=Path(b['programs'][old_name]['source']);source_before=sha(source);atom(p,before+b'\n')
 try:rejected(label+'-unknown-retained-program-drift',validate)
 finally:atom(p,before)
 assert sha(source)==source_before;source_mutation_checks.append(True)
 stage_name=next(n for n in changed if n.startswith('frontend/emergency_pc/')and n.endswith('.js')and changed[n]['bytes']<65536)
 p=bundle/'payload'/stage_name;before=p.read_bytes();source=Path(resolution['newSources'][stage_name]['source']);source_before=sha(source);atom(p,before+b'\n')
 try:rejected(label+'-staged-program-drift',validate)
 finally:atom(p,before)
 assert sha(source)==source_before;source_mutation_checks.append(True)
 atom(bundle/'update-manifest.json',enc({**plan,'unknownScope':True}))
 try:rejected(label+'-unknown-manifest-key-with-valid-new-hash',validate)
 finally:atom(bundle/'update-manifest.json',enc(plan))
 collision=next(n for n in changed if n.startswith('frontend/emergency_pc/')and n not in old_payload['files']);p=owned(app/collision);assert not p.exists();atom(p,b'own-unexpected-path')
 try:rejected(label+'-unexpected-existing-new-path',validate)
 finally:p.unlink()
 wrong=copy.deepcopy(plan);wrong['targetApplication']='C:/unapproved';atom(bundle/'update-manifest.json',enc(wrong))
 try:rejected(label+'-wrong-target-before-files',validate)
 finally:atom(bundle/'update-manifest.json',enc(plan))
 checked,_,_=validate();assert checked==plan
 cases.append({'case':label+'-restored-fixture-normal-recheck','passed':True})
 m.R48_PLAN_COMMON=original_common;m.R48_BASES=original_bases
 stats.append({'base':label,'programLinks':len(b['programs']),'stageWrites':len(files),'removedFrontendPaths':len(removed),'sharedProgramLogicalBytesNotPhysicalAllocation':sum(p['bytes']for p in b['programs'].values())})
out={'passed':True,'checks':len(cases),'cases':cases,'bases':stats,'actualGenericAndNewContractFunctionsExecuted':True,'actualFileSHAAndReadFunctionsUnmodified':True,
 'productionSourceBytesAndOther81CoreFunctionsRetained':True,'onlyOwnedTargetAndPrivateFixtureMetadataBindingsAdaptedInMemory':True,'realPrivateConfigurationAccountBusinessSeedGISOrUserDataNotCopied':True,'injectedFixtureFileWritesUsedAtomicLinkBreakAndOriginalSourceSHAHeld':all(source_mutation_checks),
 'sparseApplyLifecycleOrActualIISTLSExecuted':False,'publicOrServicesTouched':False,'maximumFixturePathCharacters':maxpaths,'fullCloneReady':False}
REPORT.write_bytes(enc(out));print(json.dumps({'passed':True,'checks':len(cases),'actualProgramFilesPerBase':{b['base']:b['programLinks']for b in stats},'realFileChecksMocked':False,'publicOrServiceLifecycleClaimed':False}))
