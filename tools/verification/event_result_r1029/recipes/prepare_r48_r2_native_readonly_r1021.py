"""Prepare exact R2 lifecycle/read-only resume in the existing owned fixture."""
from pathlib import Path
import ast,copy,hashlib,json,socket,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application'
OLD=R/'Document/Deployment/event_result_owned_full_r1003_20261105'
R2=V/'r48-retained-preflight-r2-r1013'
BASE=R/'Document/Deployment/event_result_owned_r2_r1020_20261105'
D=R/'Document/Deployment/event_r2_native_r1021_20261105';H=V/'event_crud_r1021'
J=lambda p:json.loads(Path(p).read_bytes())
enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pin=lambda p:{'bytes':Path(p).stat().st_size,'sha256':sha(p)}if Path(p).is_file()else None
assert not BASE.exists() and not D.exists() and not H.exists() and not (R/'work/ev1021').exists()
assert J(R/'work/ev1010/verified-event-crud-r1010.json')['passed']
plan=J(OLD/'full-source-and-restore-plan.private.json')
assert pin(G/'private/server-configuration.json')==plan['configBefore']
assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']
BASE.mkdir();(BASE/'candidate').mkdir()
payload=J(R2/'candidate/payload-manifest.json');release=J(R2/'candidate/release-manifest.json')
payload['files']['private/server-configuration.json']=plan['configBefore']
for rel in ['tools/original_public_test_update.py','tools/original_public_test_base_r46.py']:
 source=R2/'source'/Path(rel).name
 assert payload['files'][rel]==pin(source)
 plan['sources'][rel]={'source':str(source),**pin(source)}
 if rel in plan['mutations']:plan['mutations'][rel].update(after=pin(source),source=str(source))
for rel in ['payload-manifest.json','release-manifest.json']:
 if rel=='release-manifest.json':release['payloadManifestSHA256']=sha(BASE/'candidate/payload-manifest.json')
 target=BASE/'candidate'/rel;target.write_bytes(enc(payload if rel=='payload-manifest.json'else release))
 plan['mutations'][rel].update(after=pin(target),source=str(target))
plan.update(candidateReleaseSHA256=sha(BASE/'candidate/release-manifest.json'),candidatePayloadManifestSHA256=sha(BASE/'candidate/payload-manifest.json'),
            preparedR48PublicPayloadManifestSHA256=sha(R2/'candidate/payload-manifest.json'),exactR2UpdaterBytes=True)
(BASE/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
# Only prepare six synthetic loopback receiver settings. No live configuration write.
with socket.socket() as s:s.bind(('127.0.0.1',0));receiver=s.getsockname()[1]
assert receiver not in {8767,18891,18892}
cfg=J(G/'private/server-configuration.json');cfg2=copy.deepcopy(cfg)
keys=['riskReport','safetyEmergency','workReport','otherWorkReport','otherRiskReport','otherThird']
for key in keys:
 assert key+'Url'in cfg2['configuration']['business']
 assert not any(key+'Url'in arg for arg in cfg2.get('businessArguments',[]))
 cfg2['configuration']['business'][key+'Url']='http://127.0.0.1:'+str(receiver)+'/own-event-crud-r1021/'+key
D.mkdir();(D/'candidate').mkdir();H.mkdir()
(D/'candidate/configuration.private.json').write_bytes(enc(cfg2));cfg=None;cfg2=None
payload['files']['private/server-configuration.json']=pin(D/'candidate/configuration.private.json')
(D/'candidate/payload-manifest.json').write_bytes(enc(payload));release['payloadManifestSHA256']=sha(D/'candidate/payload-manifest.json')
(D/'candidate/release-manifest.json').write_bytes(enc(release))
plan.update(candidateReleaseSHA256=sha(D/'candidate/release-manifest.json'),candidatePayloadManifestSHA256=release['payloadManifestSHA256'],
            configAfter=pin(D/'candidate/configuration.private.json'),receiverPort=receiver,
            onlySixOwnedDockReceiverURLsAndPrivateManifestPinsAdapted=True,
            codeCandidateReleaseSHA256=sha(BASE/'candidate/release-manifest.json'))
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
for old in (V/'event_crud_r1010').iterdir():
 if old.suffix not in {'.py','.mjs'}:continue
 text=old.read_text('utf8').replace('r1010','r1021').replace('R1010','R1021').replace('ev1010','ev1021').replace('ecfg1010','ecfg1021')
 text=text.replace('event_crud_native_r1021_20261105','event_r2_native_r1021_20261105')
 new=H/old.name.replace('r1010','r1021')
 if old.name=='run_event_crud_r1010.py':
  text=text.replace('a09a708399e5e2ea0e059cdb1636429874a33c970e61f149906a78d8ca7b94cc',sha(D/'full-source-and-restore-plan.private.json'))
  marker="try:\n phase='backup-original-code'"
  assert text.count(marker)==1
  function='''preflightResults=[]
def actual_candidate_preflights():
 # Exercise the exact production R2 preflight without mocking file/helper/pool
 # functions. Both variants use the same actual installed owned configuration.
 root=Z/'candidate-preflight';(root/'payload').mkdir(parents=True)
 raw=(G/'release-manifest.json').read_bytes();code.atomic(root/'payload/release-manifest.json',raw)
 descriptor=helper.DESCRIPTOR;module=descriptor['file']
 for transported in [False,True]:
  files={}
  if transported:
   destination=root/'payload'/module;destination.parent.mkdir(parents=True,exist_ok=True)
   os.link(G/module,destination);assert os.path.samefile(G/module,destination)
   files[module]={'bytes':descriptor['bytes'],'SHA256':descriptor['sha256']}
  result=runtime.candidate_runtime_pool_preflight(G,root,{'files':files,'newReleaseSHA256':sha(G/'release-manifest.json')})
  assert result and result['supervisionModuleAndInitializerPreflightPassed'] is True
  assert result['configurationSHA256']==expectedConfig['sha256']
  preflightResults.append({'transportedModule':transported,'actualPoolMapperInitializerAndFileChecks':True})
 save('actual-r2-preflight-results.json',preflightResults)

'''
  text=text.replace(marker,function+marker)
  needle="expectedConfig=plan['configAfter'];configuration_invariant()\n for label"
  assert text.count(needle)==1
  text=text.replace(needle,"expectedConfig=plan['configAfter'];configuration_invariant();phase='exact-r2-candidate-preflight';actual_candidate_preflights()\n for label")
  text=text.replace("'passed':failure is None and len(checks)==1", "'passed':failure is None and len(preflightResults)==2 and len(checks)==1")
  text=text.replace("'failure':failure,'actualOneReadOnlyResumeLifecycle'", "'failure':failure,'actualR2CandidatePreflights':preflightResults,'actualOneReadOnlyResumeLifecycle'")
  # Retire inherited labels which implied new CRUD in this read-only run.
  text=text.replace('actualOriginalEventCRUDAndNormalRestart','actualReadOnlyExistingDeletedEventResume')
  text=text.replace('normalOriginalEventCRUDAndRestartAccepted','normalReadOnlyExistingDeletedEventAccepted')
 new.write_text(text,encoding='utf8')
 for_type=ast.parse(text)if new.suffix=='.py'else None
 if new.suffix=='.mjs':
  p=subprocess.run(['node','--check',str(new)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
  assert p.returncode==0,p.stderr.decode('utf8',errors='replace')[:300]
files=J(V/'ledger_native_r960/ledger-source-pins-r960.json')['files']
for p in H.iterdir():
 if p.suffix in {'.py','.mjs'}:files[str(p)]=sha(p)
for rel in ['original_public_test_update.py','original_public_test_base_r46.py']:
 p=R2/'source'/rel;files[str(p)]=sha(p)
pins={'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':files,'exactPreparedR2SourceBytes':True,'actualRuntimeAccepted':False}
(H/'event-source-pins-r1021.json').write_bytes(enc(pins))
summary={'preparedOnly':True,'sources':len(plan['sources']),'nativeSixComponentsNotStarted':True,
 'sameDeletedR1004EventReadOnlyOnly':True,'actualR2PreflightsWillCheckInstalledAndTransportedJar':True,
 'originalDataConfigCodeAndPointersNotChangedByPreparation':True,'sourcePins':len(files),
 'runner':str(H/'run_event_crud_r1021.py'),'runnerSHA256':sha(H/'run_event_crud_r1021.py')}
(D/'prepared-r1021.json').write_bytes(enc(summary));print(json.dumps(summary))
