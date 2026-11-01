"""Install code only into the stopped, never-user-delivered _f synthetic fixture."""
from pathlib import Path
import copy, hashlib, importlib.util, json
R=Path('D:/Project/Zhumadian');A=R/'_f/Application';T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r128'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=lambda b:hashlib.sha256(b).hexdigest();enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
assert A.resolve()==(R/'_f/Application').absolute()and not(A.parent/'user-manual-protected.json').exists()
assert read(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
last=read(C/'r5/result.json');terminal=read(C/'r5/controller-terminal.json')
assert last['allPassed']and last['allSixComponentsNormallyExitedZero']and terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']
baseline=read(C/'r5/material-browser/baseline-defect.json');assert baseline['previousBatchPersisted']==3000
current=read(A/'UserData/OriginalServer/current-run.json');assert current['controllerPID']==terminal['pid']
original=read(R/'work/event_delivery_consistency_20261030/full-controller-r127/controller-fixture-ready.json')
assert sha(A/'release-manifest.json')==original['releaseSHA256']
assert sha(R/'Document/Deployment/public_test_unified_r24_20261101/delivery-manifest.json')=='0a6d7682ba9d0b39611ad91ed1dea01c9eafd5c44d246d8873048a00260567e6'
F=R/'work/user_feedback_20261031/emergency-workflow-source-r7';b=read(F/'build-result.json');v=read(F/'independent-build-verification.json')
assert b['buildPassed']and b['fileCount']==338 and v['allBuildBytesAndSourcePinsVerified']and v['undeclaredSourceDifferences']==0
K=C/'material-excel-candidate-r1';c=read(K/'candidate.json');assert c['publicControllerABIUnchanged']and len(c['classFiles'])==3
out=C/'candidate-install-r1';assert not out.exists();out.mkdir();bundle=out/'bundle'
spec=importlib.util.spec_from_file_location('owned_fixture_code_update',A/'tools/original_public_test_update.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
payload=read(A/'payload-manifest.json');release=read(A/'release-manifest.json');new=copy.deepcopy(payload);bodies={};prefix='frontend/emergency_pc/'
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
new['files']={n:pin for n,pin in new['files'].items()if not n.startswith(prefix)}
for rel,pin in b['files'].items():
 name=prefix+rel;raw=(F/'dist'/rel).read_bytes();assert digest(raw)==pin['sha256']and len(raw)==pin['bytes'];new['files'][name]=pin
 if payload['files'].get(name)!=pin:bodies[name]=raw
for rel,pin in c['classFiles'].items():
 name='payload/business/run-template/classes/'+rel;assert name not in payload['files']and not(A/name).exists()
 raw=(K/'classes'/rel).read_bytes();assert digest(raw)==pin['sha256']and len(raw)==pin['bytes'];new['files'][name]=pin;bodies[name]=raw
new.setdefault('frontendUpdate',{})['materialImportWF7']={'onlyMaterialDialogCallerAndNewDialogChanged':True,'publicInstalled':False}
bodies['payload-manifest.json']=enc(new);release['payloadManifestSHA256']=digest(bodies['payload-manifest.json'])
release['materialExcelImportCandidate']='original-file-transaction-and-dialog-request-epoch-v1'
bodies['release-manifest.json']=enc(release)
removed={n:pin for n,pin in payload['files'].items()if n.startswith(prefix)and n not in new['files']}
changes={n:{'before':sha(A/n)if(A/n).exists()else None,'after':digest(raw)}for n,raw in bodies.items()}
changes.update({n:{'before':pin['sha256'],'after':None}for n,pin in removed.items()})
for n,row in changes.items():
 assert n.startswith((prefix,'payload/business/run-template/classes/'))or n in ['release-manifest.json','payload-manifest.json']
 assert not n.startswith(('private/','UserData/','seed/'))
 if row['before']is not None:
  expected=payload['files'].get(n,{}).get('sha256')or sha(A/n);assert row['before']==expected
for n,raw in bodies.items():put(bundle/'payload'/n,raw)
m.backup_code(A,out/'backup',changes);m.replace_code(A,bundle,changes)
assert all((not(A/n).exists())if row['after']is None else sha(A/n)==row['after']for n,row in changes.items())
assert all(sha(A/n)==pin for n,pin in release['controllerFiles'].items())
prepared=copy.deepcopy(original);prepared.update(releaseSHA256=sha(A/'release-manifest.json'),allProgramBytesRemainCandidate=True,wholeControllerActuallyStarted=False)
put(out/'controller-fixture-ready.json',enc(prepared));put(out/'changes.json',enc(changes))
put(out/'result.json',enc({'schema':'xnby.r128.owned-material-install.v1','installedIntoOwnedStoppedF':True,'writes':len(bodies),'removals':len(removed),
 'candidateClassFiles':c['classFiles'],'controllerFilesUnchanged':True,'schemaOrDataOrPrivateConfigChanged':False,
 'allOldCodeBackedUpByExactSHA':True,'fixedR24AndPublicAndFormalAndUserPreviewsUntouched':True,'actualCandidateRuntimePassed':False}))
print(json.dumps({'ownedStoppedCandidateInstalled':True,'writes':len(bodies),'removals':len(removed),'dataChanged':False,'publicChanged':False}))
