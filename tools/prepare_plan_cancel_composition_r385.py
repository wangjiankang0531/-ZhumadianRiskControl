from pathlib import Path
import ast,copy,hashlib,importlib.util,json,os,subprocess,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
W=R/'work/user_feedback_20261031';F=W/'plan-resource-cancel-r378/retry-r2'
OLD=R/'work/r39-plan-runtime-unified-r1';O=R/'work/r40-plan-resource-cancel-r385'
D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
assert not O.exists()and not D.exists()
assert J(F/'full-build-result.json')['passed']and J(F/'source-restored.json')['allSevenOverrideLayersRestored']
assert J(F/'build-terminal.json')['nodeExitCode']==0
assert J(R/'Document/Deployment/native_plan_six_relations_r372_20261103/verified-component-and-build-r381.json')['passedComponentAndFullBuildStage']
source=T/'original_public_test_update_r39_plan_runtime_r337.py'
assert sha(source)=='e935f51aa3c7a5aae3346c632b90423ce99f6a0887b1d44781ea0ed8e8c16d8f'
spec=importlib.util.spec_from_file_location('previous',source);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
build=J(F/'full-build-result.json');rows={'frontend/emergency_pc/'+n:p for n,p in build['compiledFiles'].items()}
assert len(rows)==341
for n,p in build['compiledFiles'].items():assert (F/'dist'/n).stat().st_size==p['bytes']and sha(F/'dist'/n)==p['sha256']
previous=J(W/'plan-exercise-retained-r224/full-build-result.json')
changed=set(previous['changedSourcePaths'])|set(build['changedSourcePaths'])
contract=copy.deepcopy(base.R38_FRONTEND_CONTRACT)
contract.update(revision='retained-plan-exercise-task-resource-cancel-v2',changedCompiledSourcePaths=len(changed),
 actualCompiledSourceInventorySHA256=sha(F/'actual-compiled-source-files.json'),
 resourceDeleteCancellation={'actions':['cancel','close'],'unknownRejectionsPropagated':True,
  'relativeToR224OnlyThreeComponentsChanged':True,'components':{n:sha(F/'compiled-inputs'/n)for n in build['changedSourcePaths']}})
contract['frontends']['emergency_pc']=base.r32_frontend_manifest(rows,'emergency_pc')
text=source.read_text(encoding='utf-8');parsed=ast.parse(text)
assign={n.targets[0].id:n for n in parsed.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)}
for name,value in [('R38_FRONTEND_ROWS',rows),('R38_FRONTEND_CONTRACT',contract),('R38_REVISION','20261103-R40-plan-resource-cancel-mappers-performance')]:
 old=ast.get_source_segment(text,assign[name]);assert text.count(old)==1;text=text.replace(old,name+'='+repr(value),1)
before={n.name:ast.dump(n,include_attributes=False)for n in parsed.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
after={n.name:ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert before==after,'NO_LIFECYCLE_OR_TRANSACTION_FUNCTION_CHANGED'
S=T/'original_public_test_update_r40_resource_cancel_r385.py';assert not S.exists();S.write_text(text,encoding='utf-8')
spec=importlib.util.spec_from_file_location('candidate',S);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
D.mkdir();O.mkdir();variants={}
for label in ['r36','r37']:
 previous_bundle=OLD/label/'bundle';plan=copy.deepcopy(J(previous_bundle/'update-manifest.json'))
 q=J(previous_bundle/'payload/payload-manifest.json');release=J(previous_bundle/'payload/release-manifest.json')
 oldfront={n:p for n,p in plan['oldPayloadFiles'].items()if n.startswith('frontend/emergency_pc/')}
 # oldPayloadFiles omits unchanged old frontend; derive full exact baseline declaration instead.
 oldbase= W/'r36-native-history-candidate-r2/bundle' if label=='r36' else OLD/'original-r37-contract'
 oldrelease=J(oldbase/'payload/release-manifest.json');oldq=J(oldbase/'payload/payload-manifest.json')
 oldfront={n:p for n,p in oldq['files'].items()if n.startswith('frontend/emergency_pc/')}
 q['files']={n:p for n,p in q['files'].items()if not n.startswith('frontend/emergency_pc/')};q['files'].update(rows)
 updater='tools/original_public_test_update.py';upin={'bytes':S.stat().st_size,'sha256':sha(S)}
 if updater in q['files']:q['files'][updater]=upin
 qraw=enc(q);release['payloadManifestSHA256']=hashlib.sha256(qraw).hexdigest()
 release['controllerFiles'][updater]=upin['sha256'];release[m.R38_FRONTEND_FIELD]=contract;release['publicTestRevision']=m.R38_REVISION
 rraw=enc(release)
 files={n:p for n,p in plan['files'].items()if not n.startswith('frontend/emergency_pc/')}
 files.update({n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in rows.items()if oldfront.get(n)!=p})
 raw_overrides={updater:S.read_bytes(),'release-manifest.json':rraw,'payload-manifest.json':qraw}
 for n,raw in raw_overrides.items():files[n]={'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest()}
 plan.update(updateId='20261103-r40-resource-cancel-from-'+label,files=files,
  newReleaseSHA256=hashlib.sha256(rraw).hexdigest(),newPayloadManifestSHA256=hashlib.sha256(qraw).hexdigest(),
  oldPayloadFiles={n:oldq['files'][n]for n in files if n in oldq['files']},
  removedFrontendFiles={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in oldfront.items()if n not in rows})
 bundle=O/label/'bundle'
 for n,pin in files.items():
  out=bundle/'payload'/n;out.parent.mkdir(parents=True,exist_ok=True)
  if n in raw_overrides:out.write_bytes(raw_overrides[n])
  else:
   src=F/'dist'/n.split('/',2)[2] if n.startswith('frontend/emergency_pc/')else previous_bundle/'payload'/n
   assert src.stat().st_size==pin['bytes']and sha(src)==pin['SHA256'];os.link(src,out)
 (bundle/'update-manifest.json').write_bytes(enc(plan))
 assert len(plan['acceptedOldReleases'])==1 and m.native_plan_runtime_declared(release,q)
 variants[label]={'bundle':bundle.as_posix(),'manifestSHA256':sha(bundle/'update-manifest.json'),
  'newReleaseSHA256':plan['newReleaseSHA256'],'newPayloadManifestSHA256':plan['newPayloadManifestSHA256'],
  'writes':len(files),'removals':len(plan['removedFrontendFiles'])}
assert variants['r36']['newReleaseSHA256']==variants['r37']['newReleaseSHA256']
# Reuse the existing owned six-component lifecycle driver with explicit new payload/source pins.
old_browser=(T/'verify_native_plan_six_relations_r374.mjs').read_text(encoding='utf-8')
anchor="await until(async()=>await selectedResourceCount()===2);\n  await remove();"
assert old_browser.count(anchor)==1
browser=old_browser.replace(anchor,"await until(async()=>await selectedResourceCount()===2);await until(()=>evaluate('!Array.from(document.querySelectorAll(\".el-message-box\")).some(e=>e.getClientRects().length)'));\n  await remove();",1)
bf=V/'verify_native_plan_six_relations_cancel_r386.mjs';assert not bf.exists();bf.write_text(browser,encoding='utf-8')
p=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(bf)],capture_output=True);assert p.returncode==0
sources=[]
for role in ['inspect','prepare','run']:
 s=(T/('plan_six_relations_'+role+'_r373.py')).read_text(encoding='utf-8')
 s=s.replace('native_plan_six_relations_r372_20261103/lifecycle','native_plan_resource_cancel_r385_20261103/lifecycle')
 s=s.replace('plan-six-relations-r373','plan-six-relations-cancel-r386')
 s=s.replace('original_public_test_update_r39_plan_runtime_r337.py',S.name)
 if role=='prepare':s=s.replace("public=R/'work/r39-plan-runtime-unified-r1/r37/bundle'","public=R/'work/r40-plan-resource-cancel-r385/r37/bundle'")
 if role=='run':
  s=s.replace("full-controller-r163/r147'","full-controller-r163/r149'")
  s=s.replace('verify_native_plan_six_relations_r374.mjs',bf.name).replace('c3939edd9e7bc8cc708796e8752100b09a6a87fc347b1da8958582834e5bb34f',sha(bf))
  s=s.replace('len(changes)==364','len(changes)=='+str(variants['r37']['writes']+variants['r37']['removals']))
  s=s.replace('exactFinalR39CandidateRuntime','exactR40ResourceCancelCandidateRuntime')
  s=s.replace('OWN_FINAL_R39_NATIVE_29','OWN_FINAL_R40_NATIVE_29').replace('actual-candidate-normal-role-plan-ui-21-cases','actual-candidate-normal-role-six-relations-29-cases')
 ast.parse(s);out=V/('plan_cancel_'+role+'_r386.py');assert not out.exists();out.write_text(s,encoding='utf-8')
 sources.append({'role':role,'path':out.name,'sha256':sha(out)})
report={'prepared':True,'updaterSHA256':sha(S),'updaterBytes':S.stat().st_size,'allExistingFunctionAndClassASTUnchanged':True,
 'changedOnlyThreeFrontendContractAssignments':True,'compiledFileCount':len(rows),'changedOriginalInputPaths':len(changed),
 'variants':variants,'nativeBrowserSHA256':sha(bf),'nativeDrivers':sources,'expectedNativeCases':29,
 'browserCancelWaitsUntilDialogActuallyCloses':True,'actualNativeAccepted':False,'publicDeployed':False}
(D/'composition-r385.json').write_bytes(enc(report));print(json.dumps(report))
