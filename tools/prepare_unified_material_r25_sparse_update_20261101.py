"""Build an R24-based sparse program delta and exercise real replacement/recovery, offline only."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031'
BASE=W/'r24-unified-candidate-r1';OLD_BUNDLE=BASE/'sparse-graceful-update-preparation-r1/bundle'
OUT=W/'r25-material-unified-candidate-r1';TX=R/'work/r25gx-r1';assert not OUT.exists()and not TX.exists()
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest();sha=lambda p:digest(p.read_bytes())
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
updater=T/'original_public_test_update_r25_20261101.py'
spec=importlib.util.spec_from_file_location('own_r25_material',updater);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old_release_raw=(OLD_BUNDLE/'payload/release-manifest.json').read_bytes();old_payload_raw=(OLD_BUNDLE/'payload/payload-manifest.json').read_bytes()
assert digest(old_release_raw)=='a2a2ebb961a8cfd906b4e5fd8e46588140233b83c238f4b0c06ce831f4fccb43'
old=read(OLD_BUNDLE/'payload/release-manifest.json');old_payload=read(OLD_BUNDLE/'payload/payload-manifest.json')
assert digest(old_payload_raw)==old['payloadManifestSHA256']and m.R25_MATERIAL_FIELD not in old
workflow=W/'emergency-workflow-source-r11';build=read(workflow/'build-result.json');closure=read(workflow/'source-closure.json')
assert build['buildPassed']and len(build['files'])==338 and build['sourceClosureSHA256']==sha(workflow/'source-closure.json')
assert read(workflow/'independent-build-verification.json')['allBuildBytesAndSourcePinsVerified']
prefix='frontend/emergency_pc/';front={prefix+n:copy.deepcopy(pin)for n,pin in build['files'].items()}
new=copy.deepcopy(old_payload);new['files']={n:p for n,p in new['files'].items()if not n.startswith(prefix)}
new['files'].update(front);new['files'].update(copy.deepcopy(m.R25_MATERIAL_ROWS))
retained=lambda q:{n:p for n,p in q['files'].items()if not n.startswith(prefix)and n not in m.R25_MATERIAL_ROWS}
assert retained(old_payload)==retained(new)
bodies={};classes=R/'work/event_delivery_consistency_20261030/full-controller-r128/material-excel-candidate-r1/classes'
for name,pin in {**front,**m.R25_MATERIAL_ROWS}.items():
    source=workflow/'dist'/name.removeprefix(prefix)if name.startswith(prefix)else classes/name.removeprefix('payload/business/run-template/classes/')
    raw=source.read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['sha256'],name
    if old_payload['files'].get(name)!=pin:bodies[name]=raw
release=copy.deepcopy(old);release[m.R25_MATERIAL_FIELD]=copy.deepcopy(m.R25_MATERIAL_CONTRACT)
release.update(publicTestRevision='20261101-R25-material-and-retained-emergency-guards-preparation',publicAccepted=False)
control='tools/original_public_test_update.py';bodies[control]=updater.read_bytes();release['controllerFiles'][control]=digest(bodies[control])
assert {n:p for n,p in release['controllerFiles'].items()if n!=control}=={n:p for n,p in old['controllerFiles'].items()if n!=control}
bodies['payload-manifest.json']=enc(new);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);bodies['release-manifest.json']=enc(release)
removed={n:{'bytes':p['bytes'],'SHA256':p['sha256']}for n,p in old_payload['files'].items()if n.startswith(prefix)and n not in new['files']}
plan=copy.deepcopy(read(OLD_BUNDLE/'update-manifest.json'))
plan.update(updateId='20261101-R25-material-emergency-from-exact-R24-preparation',
    acceptedOldReleases={digest(old_release_raw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
    basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=release['payloadManifestSHA256'],
    newReleaseSHA256=digest(bodies['release-manifest.json']),oldPayloadFiles={n:old_payload['files'][n]for n in bodies if n in old_payload['files']},
    legacyEntrySHA256={},removedFrontendFiles=removed,files={n:{'bytes':len(b),'SHA256':digest(b)}for n,b in bodies.items()})
assert len(bodies)<=1000 and sum(map(len,bodies.values()))<32*1024**2 and not set(bodies).intersection(removed)
free=shutil.disk_usage(W).free;assert free>2*1024**3
baseline={}
for name in set(bodies)|set(removed):
    if name=='release-manifest.json':raw=old_release_raw
    elif name=='payload-manifest.json':raw=old_payload_raw
    elif name==control:raw=(BASE/'graceful-public-control'/name).read_bytes()
    elif name in old_payload['files']:raw=(BASE/'payload'/name).read_bytes()
    else:continue
    expected=old['controllerFiles'].get(name)or old_payload['files'].get(name,{}).get('sha256')
    if expected:assert digest(raw)==expected,name
    baseline[name]=raw
changes={n:{'before':digest(baseline[n])if n in baseline else None,'after':digest(b)}for n,b in bodies.items()}
changes.update({n:{'before':p['SHA256'],'after':None}for n,p in removed.items()})
OUT.mkdir();bundle=OUT/'bundle'
for n,b in bodies.items():put(bundle/'payload'/n,b)
put(bundle/'update-manifest.json',enc(plan));put(OUT/'changes.json',enc(changes))
contract_app=OUT/'contract-Application';put(contract_app/'payload-manifest.json',old_payload_raw)
for n,p in {**m.R22_BACKEND_ROWS,**m.R23_ASYNC_ROWS,m.R24_TASK_CLASS:m.R24_TASK_PIN}.items():
    raw=(BASE/'payload'/n).read_bytes();assert digest(raw)==p['sha256'];put(contract_app/n,raw)
for n,h in old['controllerFiles'].items():
    if n==control:continue
    path=BASE/'graceful-public-control'/n
    if not path.exists():path=Path(read(R/'work/r23pv-r1/dependency-resolution.json')['controllers'][n]['source'])
    assert not any(Path('D:/Project/Zhumadian')/p in path.parents for p in ['_c','_d','_e','_f'])
    raw=path.read_bytes();assert digest(raw)==h,n;put(contract_app/n,raw)
assert m.risk_bundle_contract(contract_app,bundle,plan,old,release,new)
assert m.async_bundle_contract(contract_app,bundle,plan,old,release,new)
assert m.material_bundle_contract(contract_app,bundle,plan,old,release,new)
results=[];TX.mkdir()
faults=[('normal',None),('fourth-write',4),*[(f'material-class-{i}-write',n)for i,n in enumerate(m.R25_MATERIAL_ROWS,1)],
        ('updater-write',control),('payload-manifest-write','payload-manifest.json'),('release-pointer-write','release-manifest.json')]
for label,trigger in faults:
    case=TX/label;app=case/'Application'
    for n,b in baseline.items():put(app/n,b)
    m.backup_code(app,case/'backup',changes);count=[0];caught=False
    def after(n):
        count[0]+=1
        if n==trigger or count[0]==trigger:raise RuntimeError('OWN_R25_FAULT_'+label)
    try:m.replace_code(app,bundle,changes,after_each=after)
    except RuntimeError as e:assert trigger is not None and str(e)=='OWN_R25_FAULT_'+label;caught=True
    assert caught==(trigger is not None)
    if trigger is None:
        assert all((app/n).read_bytes()==b for n,b in bodies.items())and all(not(app/n).exists()for n in removed)
    m.restore_code(app,case/'backup',changes)
    assert all((app/n).read_bytes()==b for n,b in baseline.items())and all(not(app/n).exists()for n in changes if n not in baseline)
    result={'scenario':label,'writesBeforeRecovery':count[0],'faultInjected':trigger is not None,'allOriginalBytesRestored':True,'allNewPathsRemoved':True,'paths':len(changes)}
    put(case/'result.json',enc(result));results.append(result)
case=TX/'foreign-file-drift';app=case/'Application'
for n,b in baseline.items():put(app/n,b)
m.backup_code(app,case/'backup',changes);target=next(n for n in baseline if n.startswith(prefix));put(app/target,b'own unrelated edit\n')
snapshot={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
try:m.restore_code(app,case/'backup',changes)
except ValueError as e:assert str(e).startswith('ROLLBACK_FILE_DRIFT:')
else:raise AssertionError('FOREIGN_DRIFT_RESTORED')
assert snapshot=={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
put(case/'result.json',enc({'scenario':'foreign-file-drift','refusedBeforeAnyRestore':True,'allFilesUnchanged':True}))
max_temp=max(len(str(Path(plan['targetApplication'])/Path(n).parent/('.zmd-'+'f'*32+'.tmp')))for n in bodies);assert max_temp<260
result={'schema':'xnby.r25.sparse-update-preparation.v1','basePublicReleaseSHA256':digest(old_release_raw),'programWrites':len(bodies),
    'programWriteBytes':sum(map(len,bodies.values())),'oldEmergencyFrontendRemovals':len(removed),'totalInstallPaths':len(changes),
    'newUpdaterSHA256':sha(updater),'newReleaseSHA256':plan['newReleaseSHA256'],'updateManifestSHA256':sha(bundle/'update-manifest.json'),
    'compositionContractsPassed':True,'recoveryScenarios':results,'foreignDriftRefusedBeforeAnyRestore':True,'realCodeReplacementAndRestoreExecuted':True,
    'other19OriginalControllersAndIISRetained':True,'allNonEmergencyFrontendAndOriginalJarsRetained':True,'publicTransportSealed':False,
    'fullInstalledLoadBundleAndPublicControllerLifecyclePassed':False,'publicOrFormalInstalled':False,'servicesStartedOrStopped':False,
    'protectedUserPreviewReadOrChanged':False,'freeBytesBefore':free,'transactionEvidenceRoot':str(TX),'longestPublicTemporaryFilePathCharacters':max_temp}
put(OUT/'result.json',enc(result));print(json.dumps({k:v for k,v in result.items()if k!='recoveryScenarios'}))
