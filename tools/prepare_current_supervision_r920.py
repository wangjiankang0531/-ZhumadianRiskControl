"""Compose the already tested PDF module over complete current R45 plus home assets.

Only prepares local sources and a new guarded owned-fixture run, no processes/data.
"""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).resolve().parent
P=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104';D=R/'Document/Deployment/supervision_current_full_r920_20261104'
S=R/'Document/Deployment/supervision_factory_candidate_r694_20261104';H=V/'supervision_full_r921';OLD=V/'home_full_r912'
J=lambda p:json.loads(p.read_bytes());enc=lambda x:(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):return {'bytes':p.stat().st_size,'sha256':sha(p)}if p.is_file()else None
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
assert not D.exists()and not H.exists()
prior=J(R/'work/hf912/verified-home-transfer-r912.json');assert prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in prior['terminals'])
assert sha(P/'full-source-and-restore-plan.private.json')=='6802586b505476efd80c750f9271d6eb6f59ed667aba5f76d973b58a1082c82b'
plan=copy.deepcopy(J(P/'full-source-and-restore-plan.private.json'));payload=J(P/'candidate/payload-manifest.json');release=J(P/'candidate/release-manifest.json')
assert sha(G/'release-manifest.json')==plan['baseOwnedReleaseSHA256']and pin(G/'private/server-configuration.json')==plan['configBefore']and pin(G/'UserData/OriginalServer/installation.json')==plan['installationBefore']
old=J(S/'full-source-and-restore-plan.private.json');before_release=copy.deepcopy(release);before_files=copy.deepcopy(payload['files'])
names=['payload/business/run-template/own-supervision-pdf.jar','tools/original_supervision_release_support.py','tools/serve_original_server_release.py']
for name in names:
 source=Path(old['sources'][name]['source']);expected={k:old['sources'][name][k]for k in ['bytes','sha256']};assert pin(source)==expected
 plan['sources'][name]=copy.deepcopy(old['sources'][name]);payload['files'][name]=expected
 if name.startswith('tools/'):release['controllerFiles'][name]=expected['sha256']
old_launcher=Path(J(P/'full-source-and-restore-plan.private.json')['sources'][names[-1]]['source']).read_text('utf8');new_launcher=Path(plan['sources'][names[-1]]['source']).read_text('utf8')
funcs=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
f0,f1=funcs(old_launcher),funcs(new_launcher);assert f0.keys()==f1.keys()and [n for n in f0 if f0[n]!=f1[n]]==['main']
helper_source=Path(plan['sources'][names[1]]['source']);spec=importlib.util.spec_from_file_location('supervision_current_descriptor_r920',helper_source);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
release[helper.FIELD]=copy.deepcopy(helper.CONTRACT);release['publicTestRevision']='owned-current-r45-home-and-supervision-r920-not-public'
assert set(release)-set(before_release)=={helper.FIELD}and release['homeTransferAssets']==before_release['homeTransferAssets']
assert {n for n in set(before_files)|set(payload['files'])if before_files.get(n)!=payload['files'].get(n)}==set(names)
assert pin(Path(plan['sources']['payload/business/application.jar']['source']))==before_files['payload/business/application.jar']
D.mkdir();(D/'candidate').mkdir();H.mkdir()
raw_payload=enc(payload);release['payloadManifestSHA256']=hashlib.sha256(raw_payload).hexdigest();raw_release=enc(release)
for name,raw in [('payload-manifest.json',raw_payload),('release-manifest.json',raw_release)]: (D/'candidate'/name).write_bytes(raw)
rows={}
for name,p in plan['sources'].items():
 after={k:p[k]for k in ['bytes','sha256']};assert pin(Path(p['source']))==after,'CURRENT_SOURCE_DRIFT:'+name
 before=pin(G/name)
 if before!=after:rows[name]={'source':p['source'],'before':before,'after':after}
for name in ['payload-manifest.json','release-manifest.json']:rows[name]={'source':str(D/'candidate'/name),'before':pin(G/name),'after':pin(D/'candidate'/name)}
plan.update(schema='xnby.current-supervision.owned-full-candidate.plan.v1',candidateReleaseSHA256=hashlib.sha256(raw_release).hexdigest(),candidatePayloadManifestSHA256=hashlib.sha256(raw_payload).hexdigest(),mutations=rows,
 onlyFourFrontendFilesDifferFromR45=True,originalR45ControllerAndAllOtherProgramBytesRetained=False,onlyThreeSupervisionProgramChangesOverHomeR905=True,
 privateConfigurationNotChanged=True,supervisionContract=release[helper.FIELD],sourceHomePlanSHA256=sha(P/'full-source-and-restore-plan.private.json'))
(D/'full-source-and-restore-plan.private.json').write_bytes(enc(plan))
runner=(OLD/'run_home_transfer_full_r906.py').read_text('utf8')
runner=runner.replace('home_transfer_full_candidate_r905_20261104','supervision_current_full_r920_20261104').replace('home-transfer-r912','current-supervision-r921').replace("R/'work/hf912'","R/'work/sv921'")
runner=runner.replace('6802586b505476efd80c750f9271d6eb6f59ed667aba5f76d973b58a1082c82b',sha(D/'full-source-and-restore-plan.private.json')).replace('xnby.home-transfer.owned-full-candidate.plan.v1','xnby.current-supervision.owned-full-candidate.plan.v1')
runner=once(runner,"prior=J(R/'work/hf910/verified-home-transfer-r910.json')\nassert not prior['passed']","prior=J(R/'work/hf912/verified-home-transfer-r912.json')\nassert prior['passed']")
runner=runner.replace('home-transfer-source-pins-r912.json','current-supervision-source-pins-r921.json').replace('verified-home-transfer-r912.json', 'verified-current-supervision-r921.json').replace('home-transfer-full-result-r912.json','current-supervision-full-result-r921.json')
# Restore the prior-proof reference after renaming only this attempt's output.
runner=runner.replace("prior=J(R/'work/hf912/verified-current-supervision-r921.json')","prior=J(R/'work/hf912/verified-home-transfer-r912.json')")
assert funcs(runner)==funcs((OLD/'run_home_transfer_full_r906.py').read_text('utf8')),'REUSE_EXACT_LIFECYCLE_FUNCTIONS'
(H/'run_home_transfer_full_r906.py').write_text(runner,encoding='utf8')
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('home_transfer_full_candidate_r905_20261104','supervision_current_full_r920_20261104').replace('home-transfer-source-pins-r912.json','current-supervision-source-pins-r921.json').replace('xnby.home-transfer.owned-full-candidate.plan.v1','xnby.current-supervision.owned-full-candidate.plan.v1')
health=once(health,"    assert 'businessSupervisionPdf'not in release","    assert release['businessSupervisionPdf']==plan['supervisionContract']")
health=once(health,'    return plan,m,None',"    controller=plan['sources']['tools/serve_original_server_release.py']\n    m.R36_HISTORY_CONTROLLER_PIN={k:controller[k]for k in ['bytes','sha256']}\n    helperPath=Path(plan['sources']['tools/original_supervision_release_support.py']['source'])\n    assert sha(helperPath)==release['controllerFiles']['tools/original_supervision_release_support.py']\n    hs=importlib.util.spec_from_file_location('current_supervision_helper_r921',helperPath);helper=importlib.util.module_from_spec(hs);hs.loader.exec_module(helper);helper.descriptor(release)\n    return plan,m,helper")
health=once(health,'    plan,runtime,_=profile()','    plan,runtime,helper=profile()')
health=once(health,"    return {'originalReleaseHealthRetained':True,'newBackendOrSupervisionModulePresent':False,", "    ready=helper.require_ready(G,runtime.read(G/'release-manifest.json'),Path(row['run'])/'b');assert ready and ready['installed']\n    return {'originalReleaseHealthRetained':True,'newBackendOrSupervisionModulePresent':True,'supervisionReadinessRequired':True,")
(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
probe=(OLD/'home_transfer_probe_r906.py').read_text('utf8').replace('home-transfer-r912','current-supervision-r921').replace('home-browser-r912','current-supervision-browser-r921')
probe=once(probe,"'mode':'completed-readonly','opinion':flight['approval']", "'mode':'completed-readonly','opinion':flight['approval']")
node=(OLD/'verify_home_transfer_browser_r906.mjs').read_text('utf8').replace('home-browser-r912','current-supervision-browser-r921')
needle=" stage='original-security-header-logout';";assert node.count(needle)==1
addition=r'''
 stage='normal-user-existing-supervision-readback';
 const context=JSON.parse(await fs.readFile('D:/Project/Zhumadian/work/factory-integrated-full-lifecycle-r697/supervision-http-context.private.json','utf8'));
 if(context.phase!=='complete'||context.actor!==w.expectedUserId||!/^[a-f0-9]{32}$/.test(context.fixtureNonce))throw Error('EXACT_EXISTING_SUPERVISION_CONTEXT');
 const ua=await evaluate('navigator.userAgent');
 async function ownedRead(path,pdf=false){
  const response=await fetch(w.base+'/zhumadian/api/serv'+path,{headers:{Authorization:token,'User-Agent':ua},signal:AbortSignal.timeout(20000)});
  if(response.status!==200)throw Error('EXISTING_SUPERVISION_HTTP_REQUIRED');
  const reader=response.body.getReader(),chunks=[];let length=0;
  for(;;){const v=await reader.read();if(v.done)break;length+=v.value.length;if(length>4*1024*1024){await reader.cancel();throw Error('SUPERVISION_READBACK_BOUND');}chunks.push(Buffer.from(v.value));}
  const bytes=Buffer.concat(chunks);if(pdf)return bytes;
  const data=JSON.parse(bytes.toString('utf8'));if(data.code!==0)throw Error('EXISTING_SUPERVISION_BUSINESS_SUCCESS');return data.data;
 }
 for(const slot of ['a','b']){
  const prior=context.records[slot],id='own-sh-'+context.fixtureNonce.slice(0,20)+'-'+slot;
  if(prior.id!==id||!/^\/sys-file\/[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]\/[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\.pdf$/.test(prior.url))throw Error('EXACT_EXISTING_SUPERVISION_RECORD');
  const row=await ownedRead('/checkHiddenDanger/getDetails/'+id),log=await ownedRead('/checkHiddenDangerLog/getByCheckHiddenDangerId?checkHiddenDangerId='+id);
  if(row.id!==id||row.logStatus!==true||log.id!==prior.logId||log.url!==prior.url||log.createDate!==prior.createDate||log.createId!==w.expectedUserId)throw Error('EXISTING_SUPERVISION_STATE_CHANGED');
  const pdf=await ownedRead(prior.url,true);if(pdf.length!==prior.pdf.bytes||digest(pdf)!==prior.pdf.sha256||pdf.subarray(0,5).toString('ascii')!=='%PDF-')throw Error('EXISTING_SUPERVISION_PDF_CHANGED');
 }
 cases.push({case:'current-r45-home-supervision-module-normal-user-reopens-two-original-records-and-exact-pdfs',passed:true,newBusinessWrites:false,actualLedgerUIButtonAccepted:false});
'''
node=node.replace(needle,addition+needle)
for name,text in [('home_transfer_probe_r906.py',probe),('verify_home_transfer_browser_r906.mjs',node)]: (H/name).write_text(text,encoding='utf8')
gateway=(OLD/'home_transfer_gateway_r906.py').read_text('utf8').replace("R/'work/hf912'","R/'work/sv921'").replace('D:/Project/Zhumadian/work/hf912','D:/Project/Zhumadian/work/sv921');(H/'home_transfer_gateway_r906.py').write_text(gateway,encoding='utf8')
(H/'classes').mkdir()
for name in ['classes/OwnHomeNavigationReadbackR912.class','fixture-compile-proof.json']:(H/name).write_bytes((OLD/name).read_bytes())
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
deps=['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in deps})
(H/'current-supervision-source-pins-r921.json').write_bytes(enc({'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':pins}))
report={'prepared':True,'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'candidateReleaseSHA256':plan['candidateReleaseSHA256'],
 'completeProgramSources':len(plan['sources']),'mutationPaths':len(rows),'existingLifecycleFunctionBodiesRetained':True,
 'programChangesOverHomeR905':names,'homeAssetsAndCurrentOriginalBackendRetained':True,'normalRoleReadbackOfExistingPDFsPrepared':True,
 'newUIOrPublicOrFullLifecycleAccepted':False,'databaseWritesOrServicesOrDesktopUsed':False,'fullCloneReady':False}
(D/'prepared-r920.json').write_bytes(enc(report));print(json.dumps(report))
