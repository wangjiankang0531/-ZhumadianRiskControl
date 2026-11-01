from pathlib import Path
import copy,ctypes,hashlib,importlib.util,json
R=Path('D:/Project/Zhumadian');A=R/'_f/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r129';F=R/'work/user_feedback_20261031/emergency-workflow-source-r9'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode();digest=lambda b:hashlib.sha256(b).hexdigest()
assert A.resolve()==A.absolute()and not(A.parent/'user-manual-protected.json').exists()and J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
proof=J(C/'r5/result.json');terminal=J(C/'r5/controller-terminal.json');baseline=J(C/'r5/material-browser/stale-save-baseline.json')
assert proof['allPassed']and proof['allSixComponentsNormallyExitedZero']and terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']
assert baseline['originalActualCodeZeroFalse']and baseline['falseSaveNavigatedAsSuccess']
k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.restype=ctypes.c_void_p;k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong];k.CloseHandle.argtypes=[ctypes.c_void_p]
handle=k.OpenProcess(0x1000,False,terminal['pid'])
if handle:k.CloseHandle(handle);raise AssertionError('PRIOR_PID_EXISTS_NO_INSTALL')
assert ctypes.get_last_error()in[87,1168],'PRIOR_PID_EXIT_NOT_CONFIRMED'
assert J(A/'UserData/OriginalServer/current-run.json')['controllerPID']==terminal['pid']
prepared=J(R/'work/event_delivery_consistency_20261030/full-controller-r128/candidate-install-r1/controller-fixture-ready.json');assert sha(A/'release-manifest.json')==prepared['releaseSHA256']
b=J(F/'build-result.json');v=J(F/'independent-build-verification.json');assert b['buildPassed']and b['fileCount']==338 and v['allBuildBytesAndSourcePinsVerified']and v['undeclaredSourceDifferences']==0
out=C/'candidate-install-r1';assert not out.exists();out.mkdir();bundle=out/'bundle'
spec=importlib.util.spec_from_file_location('owned_update',A/'tools/original_public_test_update.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
payload=J(A/'payload-manifest.json');release=J(A/'release-manifest.json');new=copy.deepcopy(payload);prefix='frontend/emergency_pc/';new['files']={n:p for n,p in new['files'].items()if not n.startswith(prefix)};bodies={}
for rel,pin in b['files'].items():
 name=prefix+rel;raw=(F/'dist'/rel).read_bytes();assert digest(raw)==pin['sha256']and len(raw)==pin['bytes'];new['files'][name]=pin
 if payload['files'].get(name)!=pin:bodies[name]=raw
new.setdefault('frontendUpdate',{})['preservedOperationGuardsWF9']={'threeResourceForms':True,'fourteenOldOperationGuardsRestored':True,'workflowAndImportPreserved':True,'publicInstalled':False}
bodies['payload-manifest.json']=enc(new);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json']);release['preservedEmergencyOperationGuardsCandidate']='WF9-exact-original-retained-guard-composition';bodies['release-manifest.json']=enc(release)
removed={n:pin for n,pin in payload['files'].items()if n.startswith(prefix)and n not in new['files']};changes={n:{'before':sha(A/n)if(A/n).exists()else None,'after':digest(raw)}for n,raw in bodies.items()};changes.update({n:{'before':pin['sha256'],'after':None}for n,pin in removed.items()})
for n,row in changes.items():
 assert n.startswith(prefix)or n in ['release-manifest.json','payload-manifest.json']
 if row['before']is not None:assert row['before']==payload['files'].get(n,{}).get('sha256',sha(A/n))
for n,raw in bodies.items():p=bundle/'payload'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
m.backup_code(A,out/'backup',changes);m.replace_code(A,bundle,changes)
assert all((not(A/n).exists())if row['after']is None else sha(A/n)==row['after']for n,row in changes.items())
assert all(sha(A/n)==pin for n,pin in release['controllerFiles'].items())
prepared=copy.deepcopy(prepared);prepared.update(releaseSHA256=sha(A/'release-manifest.json'),wholeControllerActuallyStarted=False)
for name,obj in [('controller-fixture-ready.json',prepared),('changes.json',changes),('result.json',{'installedOnlyStoppedOwnedF':True,'priorPIDActualMissingVerified':True,'writes':len(bodies),'removals':len(removed),'backendDatabaseConfigControllerAndPublicUntouched':True,'runtimeStillPending':True})]:(out/name).write_bytes(enc(obj))
print(json.dumps({'onlyOwnedStoppedFFontendInstalled':True,'writes':len(bodies),'removals':len(removed),'dataSchemaOrPublicChanged':False}))
