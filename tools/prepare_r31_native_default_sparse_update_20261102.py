"""Compose verified native task feedback, edit and event picker changes from exact R28; no services or real data."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil,sys,zipfile
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';OLD=W/'r28-duty-layout-candidate-r1/bundle';OUT=W/'r31-task-unified-candidate-r2';TX=R/'work/r31gx-r2';G=R/'_g/Application';F=W/'emergency-workflow-source-r17';C=R/'work/event_delivery_consistency_20261030/full-controller-r136';N=R/'work/event_delivery_consistency_20261030/full-controller-r148';assert not OUT.exists()and not TX.exists()and not(G.parent/'user-manual-protected.json').exists()
J=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();sha=lambda p:digest(p.read_bytes());enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
updater=T/'original_public_test_update_r31_20261102.py';spec=importlib.util.spec_from_file_location('own_r27_delta',updater);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
oldraw=(OLD/'payload/release-manifest.json').read_bytes();oldqraw=(OLD/'payload/payload-manifest.json').read_bytes();old=J(OLD/'payload/release-manifest.json');oldq=J(OLD/'payload/payload-manifest.json')
assert digest(oldraw)=='a024b426c2399431746f7b9a8c4da698d84d31a869f34f9c5315d85c617697e9'and digest(oldqraw)==old['payloadManifestSHA256']and old[m.R26_TEAM_FIELD]==m.R26_TEAM_CONTRACT and old[m.R27_POOL_FIELD]==m.R27_POOL_POLICY
assert J(N/'r3/result.json')['allPassed']and J(N/'r3/result.json')['updaterSHA256']==old['controllerFiles']['tools/original_public_test_update.py']and J(N/'r3/task-picker-browser/result.json')['exceptions']==[] and J(F/'independent-build-verification.json')['allBuildBytesAndSourcePinsVerified'];b=J(F/'build-result.json');assert b['fileCount']==339 and b['sourceClosureSHA256']==sha(F/'source-closure.json')
assert J(N/'r3/task-picker-browser/result.json')['passed']and len(J(N/'r3/task-picker-browser/result.json')['cases'])==16
prefix='frontend/emergency_pc/';front={prefix+n:copy.deepcopy(pin)for n,pin in b['files'].items()};q=copy.deepcopy(oldq);q['files']={n:pin for n,pin in q['files'].items()if not n.startswith(prefix)};q['files'].update(front)
retained=lambda files:{n:pin for n,pin in files.items()if not n.startswith(prefix)};assert retained(oldq['files'])==retained(q['files'])
bodies={}
for name,pin in front.items():
    raw=(F/'dist'/name.removeprefix(prefix)).read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
    if oldq['files'].get(name)!=pin:bodies[name]=raw
native_path=m.R31_NATIVE_CLASS;native_raw=(W/'native-business-session-r3/classes/xnby/replica/OriginalNativeSessionInterceptor.class').read_bytes();assert digest(native_raw)==m.R31_NATIVE_PIN['sha256'];q['files'][native_path]=copy.deepcopy(m.R31_NATIVE_PIN);bodies[native_path]=native_raw
r=copy.deepcopy(old);r[m.R27_POOL_FIELD]=copy.deepcopy(m.R27_POOL_POLICY);r[m.R24_WORKFLOW_FIELD]=copy.deepcopy(m.R27_POOL_WORKFLOW_CONTRACT);r[m.R31_NATIVE_FIELD]=copy.deepcopy(m.R31_NATIVE_CONTRACT);r.update(publicTestRevision='20261102-R31-native-default-session-and-task-guards',publicAccepted=False)
for name,pin in m.R27_POOL_PINS.items():
    raw=(T/'connection-budget-r139'/Path(name).name).read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['sha256'];bodies[name]=raw;r['controllerFiles'][name]=pin['sha256']
control='tools/original_public_test_update.py';bodies[control]=updater.read_bytes();r['controllerFiles'][control]=sha(updater);assert {n:h for n,h in r['controllerFiles'].items()if n not in {control,*m.R27_POOL_PINS}}=={n:h for n,h in old['controllerFiles'].items()if n not in {control,*m.R27_POOL_PINS}}
bodies['payload-manifest.json']=enc(q);r['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);bodies['release-manifest.json']=enc(r)
removed={n:{'bytes':pin['bytes'],'SHA256':pin['sha256']}for n,pin in oldq['files'].items()if n.startswith(prefix)and n not in q['files']}
plan=copy.deepcopy(J(OLD/'update-manifest.json'));plan.update(updateId='20261102-R31-native-default-session-task-guards-from-exact-R28',acceptedOldReleases={digest(oldraw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=r['payloadManifestSHA256'],newReleaseSHA256=digest(bodies['release-manifest.json']),oldPayloadFiles={n:oldq['files'][n]for n in bodies if n in oldq['files']},legacyEntrySHA256={},removedFrontendFiles=removed,files={n:{'bytes':len(raw),'SHA256':digest(raw)}for n,raw in bodies.items()})
assert 5<len(bodies)<400 and 0<len(removed)<340 and sum(map(len,bodies.values()))<32*1024**2
assert shutil.disk_usage(R).free>2*1024**3;OUT.mkdir();bundle=OUT/'bundle'
for n,raw in bodies.items():put(bundle/'payload'/n,raw)
put(bundle/'update-manifest.json',enc(plan))
baseline={}
for n in set(bodies)|set(removed):
    if n=='release-manifest.json':raw=oldraw
    elif n=='payload-manifest.json':raw=oldqraw
    elif n==control:raw=(G/n).read_bytes()
    elif n in m.R27_POOL_PINS:raw=(G/n).read_bytes()
    elif n.startswith(prefix)and n in oldq['files']:raw=(W/'emergency-workflow-source-r14/dist'/n.removeprefix(prefix)).read_bytes()
    elif n in oldq['files']:raw=(G/n).read_bytes()
    else:continue
    pin=old['controllerFiles'].get(n)or oldq['files'].get(n,{}).get('sha256')
    if pin:assert digest(raw)==pin,n
    baseline[n]=raw
changes={n:{'before':digest(baseline[n])if n in baseline else None,'after':digest(raw)}for n,raw in bodies.items()};changes.update({n:{'before':pin['SHA256'],'after':None}for n,pin in removed.items()});put(OUT/'changes.json',enc(changes))
app=OUT/'contract-Application';put(app/'payload-manifest.json',oldqraw)
for n,pin in {**m.R22_BACKEND_ROWS,**m.R23_ASYNC_ROWS,m.R24_TASK_CLASS:m.R24_TASK_PIN,**m.R25_MATERIAL_ROWS,**m.R26_TEAM_SOURCE,**m.R26_TEAM_ROWS}.items():raw=(G/n).read_bytes();assert digest(raw)==pin['sha256']and len(raw)==pin['bytes'];put(app/n,raw)
for n,pin in old['controllerFiles'].items():
    source=G/n
    raw=source.read_bytes();assert digest(raw)==pin;put(app/n,raw)
assert m.risk_bundle_contract(app,bundle,plan,old,r,q)and m.async_bundle_contract(app,bundle,plan,old,r,q)and m.material_bundle_contract(app,bundle,plan,old,r,q)and m.team_bundle_contract(app,bundle,plan,old,r,q)and m.runtime_pool_bundle_contract(app,bundle,plan,old,r,q)and m.workflow_bundle_contract(app,bundle,plan,old,r,q)
results=[];TX.mkdir()
for label,trigger in [('normal',None),('first-write',1),('fourth-write',4),('controller-write',m.R23_CONTROLLER),('parameter-write',m.R24_PARAMETER),('updater-write',control),('payload-manifest-write','payload-manifest.json'),('release-pointer-write','release-manifest.json')]:
    case=TX/label;app=case/'Application'
    for n,raw in baseline.items():put(app/n,raw)
    m.backup_code(app,case/'backup',changes);count=[0];caught=False
    def after(n):
        count[0]+=1
        if n==trigger or count[0]==trigger:raise RuntimeError('OWN_R31_FAULT_'+label)
    try:m.replace_code(app,bundle,changes,after_each=after)
    except RuntimeError as e:assert trigger is not None and str(e)=='OWN_R31_FAULT_'+label;caught=True
    assert caught==(trigger is not None)
    if trigger is None:assert all((app/n).read_bytes()==raw for n,raw in bodies.items())and all(not(app/n).exists()for n in removed)
    m.restore_code(app,case/'backup',changes);assert all((app/n).read_bytes()==raw for n,raw in baseline.items())and all(not(app/n).exists()for n in changes if n not in baseline)
    result={'scenario':label,'writesBeforeRecovery':count[0],'allOriginalBytesRestored':True,'allNewPathsRemoved':True,'paths':len(changes)};put(case/'result.json',enc(result));results.append(result)
case=TX/'foreign-drift';app=case/'Application'
for n,raw in baseline.items():put(app/n,raw)
m.backup_code(app,case/'backup',changes);target=next(n for n in baseline if n.startswith(prefix));put(app/target,b'own unrelated edit\n');snapshot={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
try:m.restore_code(app,case/'backup',changes)
except ValueError as e:assert str(e).startswith('ROLLBACK_FILE_DRIFT:')
else:raise AssertionError('FOREIGN_DRIFT_NOT_REFUSED')
assert snapshot=={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
result={'schema':'xnby.r31.task-feedback-sparse-update.v1','allCompositionContractsPassed':True,'basePublicReleaseSHA256':digest(oldraw),'programWrites':len(bodies),'oldEmergencyRemovals':len(removed),'totalInstallPaths':len(changes),'programWriteBytes':sum(map(len,bodies.values())),'newUpdaterSHA256':sha(updater),'newReleaseSHA256':plan['newReleaseSHA256'],'updateManifestSHA256':sha(bundle/'update-manifest.json'),'recoveryScenarios':results,'foreignDriftRefusedBeforeAnyRestore':True,'all20ControllerBytesOriginalJarsTaskMaterialTeamAuthenticationDatabaseAndIISRetained':old['controllerFiles']==r['controllerFiles'],'fullProgramPreflightPassed':False,'newUpdaterActualLifecyclePassed':False,'businessSourcesChangedFromWF14':3,'nativeTaskCreateEditDisposalChecks':16,'nativeSessionDefaultHTTPChecks':27,'nativeSessionDefaultActualSixComponentIntegrationPassed':False,'transportSealed':False,'publicOrProtectedUserApplicationsOperated':False}
put(OUT/'result.json',enc(result));print(json.dumps({n:v for n,v in result.items()if n!='recoveryScenarios'}))
