from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';M=R/'work/addsign-history-r180/production-module-r199-r2';OLD=W/'r35-personal-workflow-candidate-r1/bundle';OUT=W/'r36-native-history-candidate-r2';TX=R/'work/r36tx-r2';G=R/'_g/Application';D=R/'Document/Deployment/public_test_native_history_r36_20261103'
J=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();sha=lambda p:digest(p.read_bytes());enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
assert not OUT.exists()and not TX.exists();source=T/'original_public_test_update_r36_20261103_r2.py';spec=importlib.util.spec_from_file_location('exact_r36_history',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=J(OLD/'payload/release-manifest.json');oldq=J(OLD/'payload/payload-manifest.json');oldraw=(OLD/'payload/release-manifest.json').read_bytes();oldqraw=(OLD/'payload/payload-manifest.json').read_bytes();assert digest(oldraw)=='ccede060e9c329d44e65aef3200d86f8666c73d071d743cc1535031ab15d0ca4'
q=copy.deepcopy(oldq);q['files'].update(m.R36_HISTORY_CONTRACT['files']);release=copy.deepcopy(old);release[m.R36_HISTORY_FIELD]=copy.deepcopy(m.R36_HISTORY_CONTRACT);release.update(publicTestRevision='20261103-R36-native-before-addsign-original-date-history',publicAccepted=False)
paths={'payload/platform/run-template/own-before-addsign-history.jar':M/'own-before-addsign-history.jar','payload/platform/run-template/persistent-launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class':M/'launcher-classes/xnby/platform/OriginalHistoryPersistentPlatformLaunch.class','tools/serve_original_server_release.py':M/'serve_original_server_release.py',m.R36_HISTORY_HELPER:M/'original_native_history_release_support.py','tools/original_public_test_update.py':source};bodies={n:p.read_bytes()for n,p in paths.items()}
for n in paths:
 if n.startswith('tools/'):release['controllerFiles'][n]=digest(bodies[n])
bodies['payload-manifest.json']=enc(q);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);bodies['release-manifest.json']=enc(release)
plan=copy.deepcopy(J(OLD/'update-manifest.json'));plan.update(updateId='20261103-R36-native-history-from-exact-R35',acceptedOldReleases={digest(oldraw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=release['payloadManifestSHA256'],newReleaseSHA256=digest(bodies['release-manifest.json']),oldPayloadFiles={},legacyEntrySHA256={},removedFrontendFiles={},files={n:{'bytes':len(b),'SHA256':digest(b)}for n,b in bodies.items()})
assert len(bodies)==7 and len(release['controllerFiles'])==21 and not any(n.startswith(('frontend/','private/','seed/','UserData/'))for n in bodies)
basecontrols=W/'r35-personal-workflow-candidate-r1/contract-Application';baseline={'payload-manifest.json':oldqraw,'release-manifest.json':oldraw,'tools/serve_original_server_release.py':(basecontrols/'tools/serve_original_server_release.py').read_bytes(),'tools/original_public_test_update.py':(T/'original_public_test_update_r35_20261103.py').read_bytes()}
for n,b in baseline.items():
 if n.startswith('tools/'):assert digest(b)==old['controllerFiles'][n]
changes={n:{'before':digest(baseline[n])if n in baseline else None,'after':digest(b)}for n,b in bodies.items()};peak=sum(map(len,baseline.values()))*20+sum(map(len,bodies.values()))*4;free=shutil.disk_usage(R).free;assert peak<1024**3 and free>peak+1024**3
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
OUT.mkdir();TX.mkdir();put(OUT/'storage-plan.json',enc({'estimatedAdditionalPeakBytesUpperBound':peak,'freeBytesBefore':free,'GISDatabaseOrDependenciesCopied':False}));bundle=OUT/'bundle'
for n,b in bodies.items():put(bundle/'payload'/n,b)
put(bundle/'update-manifest.json',enc(plan));put(OUT/'changes.json',enc(changes));app=OUT/'contract-Application';put(app/'payload-manifest.json',oldqraw);put(app/'release-manifest.json',oldraw)
required={**m.risk_backend_rows(old,oldq),**m.R23_ASYNC_ROWS,m.R24_TASK_CLASS:m.R24_TASK_PIN,**m.R25_MATERIAL_ROWS,**m.R26_TEAM_SOURCE,**m.R26_TEAM_ROWS}
for n,pin in required.items():raw=(G/n).read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['sha256'];put(app/n,raw)
for n,pin in old['controllerFiles'].items():raw=baseline[n]if n in baseline else(basecontrols/n).read_bytes();assert digest(raw)==pin;put(app/n,raw)
contracts=['r32_avatar_bundle_contract','risk_bundle_contract','runtime_pool_bundle_contract','async_bundle_contract','material_bundle_contract','team_bundle_contract','workflow_bundle_contract'];assert all(getattr(m,n)(app,bundle,plan,old,release,q)for n in contracts)
cases=[]
def negative(label,mutate):
 p,o,r,n=map(copy.deepcopy,[plan,old,release,q]);mutate(p,o,r,n)
 try:accepted=m.history_bundle_contract(app,bundle,p,o,r,n)
 except ValueError as e:cases.append({'case':label,'passed':True,'refusal':str(e)});return
 assert not accepted,'BAD_HISTORY_COMPOSITION_ACCEPTED:'+label
negative('missing-history-descriptor',lambda p,o,r,n:r.pop(m.R36_HISTORY_FIELD))
for key,val in [('revision','other'),('originalJavaDateFieldsCopied',False),('sameOriginalDynamicTransactionAndConnection',False),('originalNativeServiceCallGate',False),('newDatasourceDDLOrStatusCode',True),('originalAsyncAndAuthArchivesRetained',False)]:negative('history-'+key,lambda p,o,r,n,k=key,v=val:r[m.R36_HISTORY_FIELD].__setitem__(k,v))
negative('missing-original-personal-route-contract',lambda p,o,r,n:o.pop(m.R35_PERSONAL_FIELD))
for key in [m.R31_NATIVE_CLASS,m.R24_TASK_CLASS,'private/server-configuration.json','payload/business/application.jar','payload/platform/run-template/own-platform-async-request.jar',next(x for x in oldq['files']if x.startswith('frontend/emergency_pc/'))]:negative('retained-'+Path(key).name,lambda p,o,r,n,k=key:n['files'][k].__setitem__('sha256','0'*64))
for key in m.R36_HISTORY_CONTRACT['files']:negative('wrong-new-history-pin-'+Path(key).name,lambda p,o,r,n,k=key:n['files'][k].__setitem__('sha256','0'*64))
for key in [m.R23_CONTROLLER,m.R36_HISTORY_HELPER,'tools/original_public_test_update.py',m.R23_JOB]:negative('candidate-controller-'+Path(key).name,lambda p,o,r,n,k=key:r['controllerFiles'].__setitem__(k,'0'*64))
negative('wrong-old-updater',lambda p,o,r,n:o['controllerFiles'].__setitem__('tools/original_public_test_update.py','0'*64))
negative('wrong-old-controller',lambda p,o,r,n:o['controllerFiles'].__setitem__(m.R23_CONTROLLER,'0'*64))
negative('existing-old-history-helper',lambda p,o,r,n:o['controllerFiles'].__setitem__(m.R36_HISTORY_HELPER,m.R36_HISTORY_HELPER_SHA))
negative('extra-accepted-release',lambda p,o,r,n:p['acceptedOldReleases'].__setitem__('0'*64,{}))
negative('legacy-entry',lambda p,o,r,n:p['legacyEntrySHA256'].__setitem__('old.cmd',['0'*64]))
negative('obsolete-front-removal',lambda p,o,r,n:p['removedFrontendFiles'].__setitem__('frontend/emergency_pc/old.js',{}))
negative('unexpected-frontend-transport',lambda p,o,r,n:p['files'].__setitem__('frontend/emergency_pc/new.js',{'bytes':1,'SHA256':'0'*64}))
negative('missing-required-new-helper',lambda p,o,r,n:p['files'].pop(m.R36_HISTORY_HELPER))
negative('wrong-new-helper-transport',lambda p,o,r,n:p['files'][m.R36_HISTORY_HELPER].__setitem__('SHA256','0'*64))
negative('old-payload-transport-present',lambda p,o,r,n:p['oldPayloadFiles'].__setitem__(m.R24_TASK_CLASS,m.R24_TASK_PIN))
negative('drop-retained-pending-visibility',lambda p,o,r,n:r.pop(m.R34_PENDING_FIELD))
negative('replace-original-async-descriptor',lambda p,o,r,n:r.__setitem__(m.R23_ASYNC_FIELD,{}))
negative('premature-full-acceptance',lambda p,o,r,n:r.__setitem__('publicAccepted',True))
put(OUT/'contract-negative-cases.json',enc(cases));triggers=[('normal',None),('first-path',1),('fourth-path',4),('history-archive-write','payload/platform/run-template/own-before-addsign-history.jar'),('new-helper-write',m.R36_HISTORY_HELPER),('updater-write','tools/original_public_test_update.py'),('payload-manifest-write','payload-manifest.json'),('release-pointer-write','release-manifest.json')];recoveries=[]
for label,trigger in triggers:
 case=TX/label;app=case/'Application'
 for n,b in baseline.items():put(app/n,b)
 m.backup_code(app,case/'backup',changes);count=[0];caught=False
 def after(name):
  count[0]+=1
  if name==trigger or count[0]==trigger:raise RuntimeError('OWN_R36_FAULT_'+label)
 try:m.replace_code(app,bundle,changes,after_each=after)
 except RuntimeError as e:assert trigger is not None and str(e)=='OWN_R36_FAULT_'+label;caught=True
 assert caught==(trigger is not None)
 if trigger is None:assert all((app/n).read_bytes()==b for n,b in bodies.items())
 m.restore_code(app,case/'backup',changes);assert all((app/n).read_bytes()==b for n,b in baseline.items())and all(not(app/n).exists()for n in changes if n not in baseline)
 row={'scenario':label,'pathsBeforeRecovery':count[0],'allOriginalBytesRestored':True,'allNewPathsRemoved':True,'paths':len(changes)};put(case/'result.json',enc(row));recoveries.append(row)
case=TX/'foreign-drift';app=case/'Application'
for n,b in baseline.items():put(app/n,b)
m.backup_code(app,case/'backup',changes);put(app/'tools/serve_original_server_release.py',b'own unrelated edit\n');snapshot={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
try:m.restore_code(app,case/'backup',changes)
except ValueError as e:assert str(e).startswith('ROLLBACK_FILE_DRIFT:')
else:raise AssertionError('FOREIGN_EDIT_OVERWRITTEN')
assert snapshot=={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
proof={'schema':'xnby.r209.exact-native-history-sparse-update.v1','allCompositionContractsPassed':True,'contracts':contracts,'negativeCases':len(cases),'allNegativeCasesRefused':True,'oldPublicReleaseSHA256':digest(oldraw),'newReleaseSHA256':plan['newReleaseSHA256'],'newUpdaterSHA256':sha(source),'updateManifestSHA256':sha(bundle/'update-manifest.json'),'writes':7,'oldAssetRemovals':0,'totalInstallPaths':7,'writeBytes':sum(map(len,bodies.values())),'recoveryScenarios':recoveries,'foreignDriftRefusedBeforeAnyRestore':True,'allPriorFrontendAuthAsyncPrivateDataAndNonHistoryPayloadBytesRetained':True,'other18ControlsRetainedOneNewHelperAdded':True,'fullProgramPreflightPassed':False,'publicUploadedOrInstalled':False,'fullCloneReady':False};put(OUT/'result.json',enc(proof));print(json.dumps({k:v for k,v in proof.items()if k!='recoveryScenarios'}))
