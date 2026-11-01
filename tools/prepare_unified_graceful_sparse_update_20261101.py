"""Compose the tested R23 delta and test code recovery; do not seal a public transport."""
from pathlib import Path
import argparse, ast, copy, hashlib, importlib.util, json, re, shutil, sys, zipfile

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031'
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r1');args=parser.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',args.revision)
S=W/'r23-unified-candidate-r1';OUT=S/('sparse-graceful-update-preparation-'+args.revision);assert not OUT.exists()
TX=R/'work'/('r23gx-'+args.revision);assert not TX.exists()
read=lambda p:json.loads(p.read_bytes());digest=lambda b:hashlib.sha256(b).hexdigest()
sha=lambda p:digest(p.read_bytes());enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def put(path,raw):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
free=shutil.disk_usage(W).free;assert free>2*1024**3
UPDATER=T/'original_public_test_update_r23_graceful_20261101.py'
checks=read(W/'r23-graceful-updater-contract-r1/result.json')
assert checks['checks']==123 and checks['allPassed']and checks['sourceSHA256']==sha(UPDATER)
runtime=read(R/'work/event_delivery_consistency_20261030/full-business-main-r114/independent-unified-observed.json')
assert runtime['disposalAndReopenBrowserChecks']==20 and runtime['startupContractCasesPassed']==37
archive=R/'Document/Deployment/public_test_workflow_r21_20261031/delivery/Zhumadian_Workflow_20261031_R21.zip'
assert sha(archive)=='b9b866bfb828d90abb78b450c34ff1b0befdb1413e5e4e527beccbc18eb06b2c'
with zipfile.ZipFile(archive)as z:
    old_release=z.read('payload/release-manifest.json');old_payload=z.read('payload/payload-manifest.json')
    old_updater=z.read('payload/tools/original_public_test_update.py');plan=json.loads(z.read('update-manifest.json'))
old,payload=json.loads(old_release),json.loads(old_payload)
OLD='9f5c34ab7fe0fe698acb0c75e7d40f2bf9256dd42924828c7b8d31072a216b47'
assert digest(old_release)==OLD and digest(old_payload)==old['payloadManifestSHA256']
assert old==read(S/'r21-base-release-manifest.json')and payload==read(S/'r21-base-payload-manifest.json')
stage=read(S/'candidate-stage.json');rows=stage['allMaterializedPayloadFiles'];assert len(rows)==1047
new=copy.deepcopy(payload);prefixes=('frontend/security_pc/','frontend/emergency_pc/')
new['files']={n:v for n,v in new['files'].items()if not n.startswith(prefixes)}
new['files'].update(copy.deepcopy(rows))
bodies={}
for name,pin in rows.items():
    file=S/'payload'/name;raw=file.read_bytes();assert len(raw)==pin['bytes']and digest(raw)==pin['sha256']
    if payload['files'].get(name)!=pin:bodies[name]=raw
assert len(bodies)==593 and sum(map(len,bodies.values()))==11164268
assert {n:v for n,v in payload['files'].items()if not n.startswith(prefixes)and n not in rows}=={
    n:v for n,v in new['files'].items()if not n.startswith(prefixes)and n not in rows}
new.setdefault('frontendUpdate',{})['unifiedRiskAndEmergencyR23']={
    'revision':'20261101-r23-preparation','actualDisposalAndReopenBrowserChecks':20,
    'actualDistinctNativeCallbacksPassed':2,'startupAdapterCasesPassed':37,
    'updaterContractChecksPassed':123,'publicControllerWholeLifecycleActuallyExecuted':False,
    'sourceIssueCellsMarkedCompleteByThisCandidate':[]}
release=copy.deepcopy(old)
spec=importlib.util.spec_from_file_location('r23_transaction_updater',UPDATER)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
release.update(read(S/'async-extension-release-fragment.json'))
release.update(publicTestRevision='20261101-R23-unified-risk-and-emergency-preparation',
               riskUnitNativeSessionCandidate=m.R22_RISK_SESSION_REVISION,publicAccepted=False)
changed_controls=['tools/serve_original_server_release.py','tools/original_platform_async_release_support.py',
                  'tools/original_public_test_update.py','tools/original_server_windows_job.py']
for name in changed_controls:
    raw=(S/'graceful-public-control'/name).read_bytes();bodies[name]=raw
    release['controllerFiles'][name]=digest(raw)
assert {n:p for n,p in release['controllerFiles'].items()if n not in changed_controls}=={
    n:p for n,p in old['controllerFiles'].items()if n not in changed_controls}
bodies['payload-manifest.json']=enc(new);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json'])
bodies['release-manifest.json']=enc(release)
removed={n:{'bytes':v['bytes'],'SHA256':v['sha256']}for n,v in payload['files'].items()
         if n.startswith(prefixes)and n not in new['files']}
assert len(removed)==584 and not set(bodies).intersection(removed)
plan.update(updateId='20261101-R23-unified-risk-emergency-from-R21-preparation',
    acceptedOldReleases={OLD:{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},
    basePayloadManifestSHA256=old['payloadManifestSHA256'],newPayloadManifestSHA256=release['payloadManifestSHA256'],
    newReleaseSHA256=digest(bodies['release-manifest.json']),
    oldPayloadFiles={n:payload['files'][n]for n in bodies if n in payload['files']},
    legacyEntrySHA256={},removedFrontendFiles=removed,
    files={n:{'bytes':len(raw),'SHA256':digest(raw)}for n,raw in bodies.items()})
assert len(bodies)<=1000 and sum(map(len,bodies.values()))<=32*1024**2
baseline={}
oldfront=W/'workplace-security-build-r21-workflow/build/dist'
oldemergency=W/'published-emergency-frontend-r1/frontend'
base_program=R/'Document/Deployment/server_directory_migration_20261030_r17d/delivery/payload'
for name in set(bodies)|set(removed):
    raw=None
    if name=='release-manifest.json':raw=old_release
    elif name=='payload-manifest.json':raw=old_payload
    elif name=='tools/original_public_test_update.py':raw=old_updater
    elif name in old['controllerFiles']:
        row=read(R/'work/r23pv-r1/dependency-resolution.json')['controllers'][name];raw=Path(row['source']).read_bytes()
    elif name in payload['files']:
        if name.startswith(prefixes[0]):file=oldfront/name.removeprefix(prefixes[0])
        elif name.startswith(prefixes[1]):file=oldemergency/name.removeprefix(prefixes[1])
        else:file=W/'public-r21-template-recovery-r1'/name
        raw=file.read_bytes()
    if raw is not None:
        pin=old['controllerFiles'].get(name)or payload['files'].get(name,{}).get('sha256')
        if pin:assert digest(raw)==pin,name
        baseline[name]=raw
changes={n:{'before':digest(baseline[n])if n in baseline else None,'after':digest(raw)}for n,raw in bodies.items()}
changes.update({n:{'before':v['SHA256'],'after':None}for n,v in removed.items()})
OUT.mkdir();bundle=OUT/'bundle'
for name,raw in bodies.items():put(bundle/'payload'/name,raw)
put(bundle/'update-manifest.json',enc(plan))
# Exercise the real new contracts over exactly the composed bundle, without running load_bundle
# against an incomplete installed-program fixture or pretending to verify real services.
contract_app=OUT/'contract-Application';factory='payload/business/run-template/classes/META-INF/spring.factories'
put(contract_app/factory,baseline[factory])
assert m.risk_bundle_contract(contract_app,bundle,plan,old,release,new)
assert m.async_bundle_contract(contract_app,bundle,plan,old,release,new)
print(json.dumps({'phase':'graceful-bundle-composed-contracts-passed','programWrites':len(bodies)}),flush=True)
TX.mkdir();results=[]
jar=next(n for n in m.R23_ASYNC_ROWS if n.endswith('.jar'))
launcher=next(n for n in m.R23_ASYNC_ROWS if n.endswith('.class'))
faults=[('normal',None),('fourth-write',4),('async-jar-write',jar),('async-launcher-write',launcher),
        ('controller-write',changed_controls[0]),('helper-write',changed_controls[1]),
        ('updater-write',changed_controls[2]),('job-write',changed_controls[3]),('payload-manifest-write','payload-manifest.json'),
        ('release-pointer-write','release-manifest.json')]
for label,trigger in faults:
    case=TX/label;app=case/'Application'
    for name,raw in baseline.items():put(app/name,raw)
    m.backup_code(app,case/'backup',changes);counter=[0];caught=False
    def after(name):
        counter[0]+=1
        if name==trigger or counter[0]==trigger:raise RuntimeError('OWN_R23_FAULT_'+label)
    try:m.replace_code(app,bundle,changes,after_each=after)
    except RuntimeError as error:
        assert trigger is not None and str(error)=='OWN_R23_FAULT_'+label;caught=True
    assert caught==(trigger is not None)
    if trigger is None:
        assert all((app/n).read_bytes()==raw for n,raw in bodies.items())
        assert all(not(app/n).exists()for n in removed)
    if label=='updater-write':assert sha(app/changed_controls[2])==sha(UPDATER)and sha(app/'release-manifest.json')==OLD
    m.restore_code(app,case/'backup',changes)
    assert all((app/n).read_bytes()==raw for n,raw in baseline.items())
    assert all(not(app/n).exists()for n in changes if n not in baseline)
    result={'scenario':label,'writesBeforeRecovery':counter[0],'faultInjected':trigger is not None,
            'allOriginalBytesRestored':True,'allNewPathsRemoved':True,'paths':len(changes)}
    put(case/'result.json',enc(result));results.append(result)
# Refuse unrelated drift before restoring any path.
case=TX/'foreign-file-drift';app=case/'Application'
for name,raw in baseline.items():put(app/name,raw)
m.backup_code(app,case/'backup',changes)
target=next(n for n in sorted(baseline)if n.startswith('frontend/'))
put(app/target,b'own deliberately unrelated edit\n')
snapshot={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
try:m.restore_code(app,case/'backup',changes)
except ValueError as error:assert str(error).startswith('ROLLBACK_FILE_DRIFT:')
else:raise AssertionError('FOREIGN_DRIFT_RESTORED')
assert snapshot=={p.relative_to(app).as_posix():sha(p)for p in app.rglob('*')if p.is_file()}
put(case/'result.json',enc({'scenario':'foreign-file-drift','refusedBeforeAnyRestore':True,'allFilesUnchanged':True}))
target_root=Path(plan['targetApplication'])
max_temp=max(len(str(target_root/Path(n).parent/('.zmd-'+'f'*32+'.tmp')))for n in bodies)
assert max_temp<260
result={'schema':'xnby.r23.sparse-update-preparation.v1','programWrites':len(bodies),
        'programWriteBytes':sum(map(len,bodies.values())),'oldFrontendRemovals':len(removed),
        'totalInstallPaths':len(changes),'newUpdaterSHA256':sha(UPDATER),
        'newReleaseSHA256':plan['newReleaseSHA256'],'updateManifestSHA256':sha(bundle/'update-manifest.json'),
        'updaterContractChecks':123,'compositionContractsPassed':True,'recoveryScenarios':results,
        'foreignDriftRefusedBeforeAnyRestore':True,'realCodeReplacementAndRestoreExecuted':True,
        'other16OriginalControllersAndIISRetained':True,'publicTransportSealed':False,
        'fullInstalledLoadBundleAndPublicControllerLifecyclePassed':False,
        'publicOrFormalInstalled':False,'servicesStartedOrStopped':False,'freeBytesBefore':free,
        'transactionEvidenceRoot':str(TX),'longestPublicTemporaryFilePathCharacters':max_temp,
        'expectedTemporaryPeakBelowBytes':512*1024**2}
put(OUT/'result.json',enc(result));put(OUT/'changes.json',enc(changes))
print(json.dumps({k:v for k,v in result.items()if k!='recoveryScenarios'}))
