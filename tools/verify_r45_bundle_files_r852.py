"""Real frozen-core file preflight/replacement/restore on code-only fixtures.

No database, services, network, runtime executable or desktop action is allowed.
Program bytes are immutable hardlinks; readonly files are copied independently.
"""
from pathlib import Path
from unittest.mock import patch
import copy,hashlib,importlib.util,json,os,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
O=R/'work/r45-code-file-fixtures-r852';D=R/'Document/Deployment/original_backend_bootstrap_r45_20261104'
J=lambda p:json.loads(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
cache={}
def sha(p):
 p=Path(p);s=p.stat();key=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
 if key not in cache:
  with p.open('rb')as f:cache[key]=hashlib.file_digest(f,'sha256').hexdigest()
 return cache[key]
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.exists()else None
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
builder=load('mapper_chart_builder_r572',V/'r45_file_fixture_builder_r851.py')
resolution=J(R/'work/r39-full-preflight-r37-r341/resolution.json');previous={**resolution['programs'],**resolution['controls']}
assert not O.exists()
def find(name,h,size,oldroot):
 candidates=[oldroot/'payload'/name]
 if name in previous:candidates.append(Path(previous[name]['source']))
 candidates.extend([G/name,A/name])
 for p in candidates:
  if p.is_file()and(size is None or p.stat().st_size==size)and sha(p)==h:return p
 raise AssertionError('MISSING_FROZEN_CODE_SOURCE:'+name)
sources={};metadata={};logical=readonly=0
for label in ['r36','r37']:
 oldroot=R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle'if label=='r36'else R/'work/r39-plan-runtime-unified-r1/original-r37-contract'
 release=J(oldroot/'payload/release-manifest.json');payload=J(oldroot/'payload/payload-manifest.json');rows={n:p for n,p in payload['files'].items()if not n.startswith(('private/','UserData/','Assets/','seed/'))}
 required={n:(p['sha256'],p['bytes'])for n,p in rows.items()}
 for n,h in release['controllerFiles'].items():required.setdefault(n,(h,None))
 own={}
 for i,(n,(h,size))in enumerate(required.items(),1):
  p=find(n,h,size,oldroot);own[n]=p;logical+=p.stat().st_size
  if p.stat().st_file_attributes&1:readonly+=p.stat().st_size
  if i%4000==0:print(json.dumps({'phase':'resolve-frozen-source','base':label,'files':i}),flush=True)
 baseplan=J(R/('work/r42-mapper-equivalence-r457/'+label+'/bundle/update-manifest.json'))
 for n,accepted in baseplan['legacyEntrySHA256'].items():
  assert len(accepted)==1
  mapped='deploy/iis_original/App_Code/XnbyReferenceProxy.cs'if n=='iis/App_Code/XnbyReferenceProxy.cs'else n
  assert mapped in own and sha(own[mapped])==accepted[0]
  own[n]=own[mapped];logical+=own[mapped].stat().st_size
  if own[mapped].stat().st_file_attributes&1:readonly+=own[mapped].stat().st_size
 sources[label]=own;metadata[label]=(release,payload)
assert readonly<256*1024**2,'READONLY_INDEPENDENT_COPY_BUDGET_EXCEEDED'
assert shutil.disk_usage(R).free>2*1024**3+readonly+256*1024**2
O.mkdir();(D/'code-fixture-storage-plan-r852.json').write_bytes(enc({'logicalSharedProgramBytes':logical,'readonlyIndependentCopyBytes':readonly,'estimatedNewMetadataAndCodeCopiesBytes':readonly+256*1024**2,'databasesGISOrSeedsCopied':False}))
def immutable_link(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if src.stat().st_file_attributes&1:dst.write_bytes(src.read_bytes())
 else:os.link(src,dst)
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
core=builder.runtime;variants={};negative=[]
def rejected(name,fn):
 try:fn()
 except (ValueError,FileNotFoundError,AssertionError,TypeError):negative.append({'case':name,'rejected':True});return
 raise AssertionError('EXPECTED_BUNDLE_REFUSAL:'+name)

for label in ['r36','r37']:
 print(json.dumps({'phase':'prepare-code-only-fixture','base':label}),flush=True)
 root=O/label;app=root/'Application';app.mkdir(parents=True)
 release,payload=map(copy.deepcopy,metadata[label]);config=G/'private/server-configuration.json'
 for i,(n,p)in enumerate(sources[label].items(),1):
  immutable_link(p,app/n)
  if i%4000==0:print(json.dumps({'phase':'link-program-code','base':label,'files':i}),flush=True)
 put(app/'private/server-configuration.json',config.read_bytes());payload['files']['private/server-configuration.json']=pin(app/'private/server-configuration.json')
 oldpayloadRaw=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(oldpayloadRaw).hexdigest();oldreleaseRaw=enc(release);oldsha=hashlib.sha256(oldreleaseRaw).hexdigest()
 put(app/'payload-manifest.json',oldpayloadRaw);put(app/'release-manifest.json',oldreleaseRaw)
 overlay=G/'payload/callback-overlay/20261026-password-identity'
 for p in overlay.rglob('*'):
  if p.is_file():immutable_link(p,app/p.relative_to(G))
 original=R/('work/r42-mapper-equivalence-r457/'+label+'/bundle');base=root/'adapted-base';baseplan=J(original/'update-manifest.json')
 baseRelease=J(original/'payload/release-manifest.json');basePayload=J(original/'payload/payload-manifest.json');basePayload['files']['private/server-configuration.json']=payload['files']['private/server-configuration.json']
 basePayloadRaw=enc(basePayload);baseRelease['payloadManifestSHA256']=hashlib.sha256(basePayloadRaw).hexdigest();baseReleaseRaw=enc(baseRelease)
 accepted=copy.deepcopy(next(iter(baseplan['acceptedOldReleases'].values())));accepted['payloadManifestSHA256']=release['payloadManifestSHA256']
 baseplan.update(targetApplication=app.as_posix(),gatewayPort=23456,acceptedOldReleases={oldsha:accepted},basePayloadManifestSHA256=release['payloadManifestSHA256'],newPayloadManifestSHA256=baseRelease['payloadManifestSHA256'],newReleaseSHA256=hashlib.sha256(baseReleaseRaw).hexdigest())
 raw={'release-manifest.json':baseReleaseRaw,'payload-manifest.json':basePayloadRaw}
 for n,b in raw.items():baseplan['files'][n]={'bytes':len(b),'SHA256':hashlib.sha256(b).hexdigest()}
 for n in baseplan['files']:
  if n in raw:put(base/'payload'/n,raw[n])
  else:immutable_link(original/'payload'/n,base/'payload'/n)
 put(base/'update-manifest.json',enc(baseplan));bundle=root/'bundle';built=builder.compose(base,payload,bundle,label)
 base_file_pins={n:pin(app/n)for n in [*sources[label],'release-manifest.json','payload-manifest.json','private/server-configuration.json']}
 with patch('subprocess.Popen',side_effect=AssertionError('NO_PROCESS_START_IN_FILE_FIXTURE')),patch('socket.socket',side_effect=AssertionError('NO_NETWORK_IN_FILE_FIXTURE')):
  plan,checkedOld,changes=core.load_bundle(app,bundle,built['manifestSHA256'],expected_target=app,expected_port=23456)
  assert checkedOld==oldsha and len(changes)==len(plan['files'])+len(plan['removedFrontendFiles'])
  preflight=core.candidate_runtime_pool_preflight(app,bundle,plan);assert preflight['originalMapperPreflight']['passed']
  attempt=root/'normal-backup';core.backup_code(app,attempt,changes);core.replace_code(app,bundle,changes)
  assert sha(app/'release-manifest.json')==plan['newReleaseSHA256'];assert all(sha(app/n)==p['sha256']for n,p in core.R44_STYLE_ROWS.items())
  core.restore_code(app,attempt,changes);assert all(pin(app/n)==p for n,p in base_file_pins.items())
  assert all(not(app/n).exists()for n,p in changes.items()if p['before']is None)
  attempt=root/'fourth-backup';core.backup_code(app,attempt,changes);written=[]
  def fourth(name):
   written.append(name)
   if len(written)==4:raise OSError('SYNTHETIC_FOURTH_REPLACE_FAILURE')
  try:core.replace_code(app,bundle,changes,after_each=fourth)
  except OSError as e:assert str(e)=='SYNTHETIC_FOURTH_REPLACE_FAILURE'
  else:raise AssertionError('FOURTH_REPLACE_FAULT_NOT_INJECTED')
  core.restore_code(app,attempt,changes);assert all(pin(app/n)==p for n,p in base_file_pins.items())
  # Detach hardlinks atomically for corruption tests; never modify source inodes.
  module=bundle/'payload/frontend/security_pc/assets/css/xnby-workplace-period-736f7b07dd2c.css';good=module.read_bytes();core.atomic(module,b'corrupted stylesheet')
  rejected(label+'-stylesheet-bytes-drift',lambda:core.load_bundle(app,bundle,built['manifestSHA256'],expected_target=app,expected_port=23456));core.atomic(module,good)
  other=copy.deepcopy(plan);other['files']['private/not-permitted.json']={'bytes':0,'SHA256':hashlib.sha256(b'').hexdigest()};core.atomic(bundle/'update-manifest.json',enc(other));badpin=sha(bundle/'update-manifest.json')
  rejected(label+'-extra-private-path-even-with-valid-manifest-hash',lambda:core.load_bundle(app,bundle,badpin,expected_target=app,expected_port=23456));core.atomic(bundle/'update-manifest.json',enc(plan))
  rejected(label+'-wrong-target',lambda:core.load_bundle(app,bundle,built['manifestSHA256'],expected_target=root/'DifferentApplication',expected_port=23456))
  rejected(label+'-wrong-manifest-pin',lambda:core.load_bundle(app,bundle,'0'*64,expected_target=app,expected_port=23456))
  for key in ['completeGlobalComponentsRetained','onlyCodeLoadPromiseShared','originalSDKAndBackendRetained','newSupervisionModuleRequired','staticBase','originalApplicationBase','compiledSourceDeltaFromR44']:
   foreign=copy.deepcopy(plan);badRelease=J(bundle/'payload/release-manifest.json');badPayload=J(bundle/'payload/payload-manifest.json')
   badRelease[core.R45_BOOTSTRAP_FIELD][key]='foreign'
   rejected(label+'-changed-bootstrap-descriptor-'+key,lambda:core.r38_unified_bundle_contract(app,bundle,foreign,release,badRelease,badPayload))

  # The baseline remains intact after all refused operations and core recovery.
  assert all(pin(app/n)==p for n,p in base_file_pins.items())
 variants[label]={'passed':True,'installedProgramOrControlFiles':len(sources[label]),'combinedWrites':len(plan['files']),'oldFrontendRemovals':len(plan['removedFrontendFiles']),
  'normalAndFourthFaultActualCoreFileRecoveryPassed':True,'fullBaseCodeHashesAndPrivateConfigurationPreserved':True,'candidatePoolAndMapperBeforeStopPreflightPassed':True,
  'originalCoreApplyStopAndRestoreFunctionASTUnmodified':True,'actualRuntimeOrPublicAcceptance':False}
 (D/'file-tests-progress-r852.json').write_bytes(enc({'variants':variants,'negativeCases':negative}));print(json.dumps({'base':label,'passed':True,'changes':len(changes),'servicesStarted':False}),flush=True)
proof={'passed':True,'variants':variants,'negativeCases':negative,'physicalOriginalSourceFilesNeverOverwritten':True,'readonlySourceAttributesPreservedByIndependentCopies':True,
 'allFixtureTamperingUsedAtomicReplacementNotHardlinkInPlaceWrites':True,'onlyOneBundleContractFunctionChangedFromR42':True,'servicesNetworkDatabasesGISOrPublicTouched':False,'fullCloneReady':False}
(D/'verified-full-bundle-files-r852.json').write_bytes(enc(proof));print(json.dumps({'passed':True,'bases':2,'negativeCases':len(negative),'actualLifecycleAccepted':False}))
