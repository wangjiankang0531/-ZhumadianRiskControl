from pathlib import Path
import copy,hashlib,importlib.util,json
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/event_result_runtime_r1000_20261105';W=R/'work/r48-metadata-contract-r1002'
J=lambda p:json.loads(Path(p).read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not W.exists();W.mkdir()
wrapper=load('r48_contract_r1001',D/'source/original_public_test_update.py');m=wrapper.runtime();cases=[]
release=J(D/'candidate/release-manifest.json');payload=J(D/'candidate/payload-manifest.json')
realcheck=m.check_file
for label,origin in [('r45',R/'work/original-backend-bootstrap-r847/r36/bundle/payload'),('r47',R/'work/unified-home-supervision-r928/bundle/payload')]:
 app=W/label/'Application';bundle=W/label/'bundle';app.mkdir(parents=True);(bundle/'payload').mkdir(parents=True)
 for n in ['release-manifest.json','payload-manifest.json']:(app/n).write_bytes((origin/n).read_bytes())
 old=J(app/'release-manifest.json');oldfiles=J(app/'payload-manifest.json')['files'];plan=J(D/('update-from-'+label+'.json'))
 calls=[]
 def semantic_file_check(root,name,expected_sha,expected_bytes=None):
  root=Path(root)
  if name in ['payload-manifest.json','release-manifest.json']:return realcheck(root,name,expected_sha,expected_bytes)
  source=oldfiles.get(name)if root==app else payload['files'].get(name)
  if source is None:
   controls=old['controllerFiles']if root==app else release['controllerFiles']
   source={'sha256':controls.get(name),'bytes':expected_bytes}
  assert source is not None and expected_sha==source['sha256']and(expected_bytes is None or expected_bytes==source['bytes']),'UNIT_IO_MODEL_PIN_MISMATCH'
  calls.append(name);return root/name
 m.check_file=semantic_file_check
 def run(case,changed_plan=None,changed_payload=None,changed_release=None,positive=False):
  p=copy.deepcopy(plan if changed_plan is None else changed_plan);p2=copy.deepcopy(payload if changed_payload is None else changed_payload);r2=copy.deepcopy(release if changed_release is None else changed_release)
  (bundle/'payload/payload-manifest.json').write_bytes(enc(p2));(bundle/'payload/release-manifest.json').write_bytes(enc(r2))
  # The standalone contract receives the original loader's verified hashes.
  p['newPayloadManifestSHA256']=sha(bundle/'payload/payload-manifest.json');p['newReleaseSHA256']=sha(bundle/'payload/release-manifest.json')
  r2['payloadManifestSHA256']=p['newPayloadManifestSHA256'];(bundle/'payload/release-manifest.json').write_bytes(enc(r2));p['newReleaseSHA256']=sha(bundle/'payload/release-manifest.json')
  for n in ['payload-manifest.json','release-manifest.json']:p['files'][n]={'bytes':(bundle/'payload'/n).stat().st_size,'SHA256':sha(bundle/'payload'/n)}
  calls.clear()
  try:m.r48_bundle_contract(app,bundle,p,old,r2,p2)
  except ValueError as error:
   assert not positive,case+':'+str(error);cases.append({'base':label,'case':case,'rejected':True,'reason':str(error)})
  else:
   assert positive,'INVALID_SCOPE_ACCEPTED:'+case
   scanned=[n for n in oldfiles if not n.startswith(('private/','UserData/','seed/','Assets/'))]
   assert set(scanned).issubset(calls)
   cases.append({'base':label,'case':case,'passed':True,'immutableProgramPinChecksModeled':len(scanned),'fileIOForProgramsExplicitlyStubbed':True})
 run('closed-positive-target',positive=True)
 p=copy.deepcopy(plan);p['unreviewed']=True;run('unknown-plan-key',changed_plan=p)
 for field,value in [('targetApplication','C:/elsewhere'),('gatewayPort',80),('databaseUploadsCredentialsGISOrDependenciesIncluded',True),('iisProxySHA256','0'*64),('callbackOverlaySHA256','0'*64)]:
  p=copy.deepcopy(plan);p[field]=value;run('immutable-'+field,changed_plan=p)
 p=copy.deepcopy(plan);p['acceptedOldReleases'][next(iter(p['acceptedOldReleases']))]['controllerFiles'].pop(next(iter(old['controllerFiles'])));run('incomplete-old-controls',changed_plan=p)
 p=copy.deepcopy(plan);p['updateId']='unknown';run('wrong-update-id',changed_plan=p)
 p=copy.deepcopy(plan);p['files']['UserData/foreign.json']={'bytes':1,'SHA256':'0'*64};run('extra-data-write',changed_plan=p)
 p=copy.deepcopy(plan);p['removedFrontendFiles']['frontend/security_pc/foreign.js']={'bytes':1,'SHA256':'0'*64};run('out-of-scope-removal',changed_plan=p)
 p=copy.deepcopy(plan);key=next(iter(p['oldPayloadFiles']));del p['oldPayloadFiles'][key];run('missing-preimage',changed_plan=p)
 p2=copy.deepcopy(payload);p2['files']['private/server-configuration.json']['sha256']='0'*64;run('private-pin-change',changed_payload=p2)
 p2=copy.deepcopy(payload);p2['files']['payload/business/application.jar']['sha256']='0'*64;run('original-jar-change',changed_payload=p2)
 p2=copy.deepcopy(payload);key=next(n for n in p2['files']if n.startswith('frontend/emergency_pc/'));del p2['files'][key];run('incomplete-complete-frontend',changed_payload=p2)
 r2=copy.deepcopy(release);r2['runtimeConnectionPoolPolicy']={'changed':True};run('unrelated-release-feature',changed_release=r2)
 r2=copy.deepcopy(release);r2[m.R48_FIELD]['falseOrRejectedSaveKeepsEditorInput']=False;run('event-feature-change',changed_release=r2)
 m.check_file=realcheck
for name,r in [('R47',J(R/'work/unified-home-supervision-r928/bundle/payload/release-manifest.json')),('R48',release)]:
 assert wrapper.declared(r);bad=copy.deepcopy(r);bad['controllerFiles'][wrapper.CORE]='0'*64
 try:wrapper.declared(bad)
 except ValueError:cases.append({'base':name,'case':'wrong-declared-core-pin','rejected':True})
 else:raise AssertionError('DECLARED_CORE_DRIFT_ACCEPTED')
out={'passed':True,'checks':len(cases),'cases':cases,'actualMetadataFilesReadAndHashed':True,'immutableProgramFileIOIsExplicitUnitModel':True,
 'originalGenericLoaderFullFileContractOrServiceLifecycleExercised':False,'publicOrUserDataTouched':False,'priorR1001UnitStubOmittedRetainedControlsBeforeAnyLifecycle':True,'sourceSHA256':{'wrapper':sha(D/'source/original_public_test_update.py'),'core':sha(D/'source/original_public_test_base_r46.py')},'fullCloneReady':False}
(D/'verified-metadata-contract-r1002.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'checks':len(cases),'fullFileOrLifecycleClaimed':False}))
