from pathlib import Path
import copy,hashlib,json,shutil,subprocess
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;A=R/'_g/Application'
old=R/'work/plan-six-relations-typed-r390';O=R/'work/plan-six-relations-ui-r394'
D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
terminal=J(old/'terminal.json');assert terminal['allOwnedControllerHandlesTerminal']and terminal['originalGCodeAndPointersRestored']and len(terminal['controllers'])==3
for c in terminal['controllers']:assert c['controllerExitCode']==0 and c['actualJobDescendantsZero']and c['receipt']['normalOwnedShutdown']
assert sha(A/'release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
assert not O.exists()and shutil.disk_usage(R).free>2*1024**3+128*1024**2
scope=copy.deepcopy(J(old/'scope.json'));plan=J(old/'bundle/update-manifest.json')
for n,pin in scope['originalBefore'].items():
 p=A/n;assert (None if not p.exists()else{'bytes':p.stat().st_size,'sha256':sha(p)})==pin
O.mkdir()
for n,pin in scope['originalBefore'].items():
 if pin is not None:
  src=old/'original-before'/n;assert src.stat().st_size==pin['bytes']and sha(src)==pin['sha256']
  dest=O/'original-before'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
for n,pin in plan['files'].items():
 src=old/'bundle/payload'/n;assert src.stat().st_size==pin['bytes']and sha(src)==pin['SHA256']
 dest=O/'bundle/payload'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
shutil.copyfile(old/'bundle/update-manifest.json',O/'bundle/update-manifest.json')
desired=copy.deepcopy(scope['desiredBaseline'])
for n,pin in plan['files'].items():desired[n]={'bytes':pin['bytes'],'sha256':pin['SHA256'],'source':str(O/'bundle/payload'/n)}
for n in plan['removedFrontendFiles']:desired[n]=None
for n,pin in desired.items():
 if pin is not None:
  src=Path(pin['source']);assert src.stat().st_size==pin['bytes']and sha(src)==pin['sha256']
  dest=O/'candidate-code'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);pin['source']=str(dest)
scope['desiredCandidate']=desired;(O/'scope.json').write_bytes(enc(scope))
# Keep diagnostics in the same lexical scope as the failure handler.
bf=V/'verify_native_plan_six_relations_dialog_r394.mjs';browser=bf.read_text(encoding='utf-8');oldpin=sha(bf)
start=browser.index(' const resourceDeletionSteps=[];');end=browser.index(' async function removeResourceA',start)
declarations=browser[start:end];browser=browser[:start]+browser[end:]
anchor='async function until(fn,ms=40000)';assert browser.count(anchor)==1;browser=browser.replace(anchor,declarations+'\n'+anchor,1)
bf.write_text(browser,encoding='utf-8');newpin=sha(bf)
driver=V/'plan_relation_ui_r394.py';s=driver.read_text(encoding='utf-8');assert s.count(oldpin)==1;s=s.replace(oldpin,newpin,1)
anchor="    phase='install-owned-exact-candidate-code-for-UI-iteration'\n    for n,value in scope['desiredCandidate'].items():"
replace="    phase='install-owned-exact-candidate-code-for-UI-iteration'\n    for n,value in scope['desiredCandidate'].items():\n        if value is not None:assert pin(Path(value['source']))=={k:value[k]for k in ['bytes','sha256']}\n    installed=True\n    for n,value in scope['desiredCandidate'].items():"
assert s.count(anchor)==1;s=s.replace(anchor,replace,1);driver.write_text(s,encoding='utf-8')
p=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(bf)],capture_output=True);assert p.returncode==0
(D/'lifecycle-r394').mkdir()
proof={'preparedOnly':True,'browserSHA256':newpin,'driverSHA256':sha(driver),'allOriginalBeforePinsMatched':True,
 'allCandidateCodeIndependentCopies':True,'databaseCopiedOrReplaced':False,'originalGCodeStillUntouched':True,
 'previousActualApplyRollbackCompleteBut29NotAccepted':True,'native29Pending':True}
(D/'ui-fixture-prepared-r394.json').write_bytes(enc(proof));print(json.dumps(proof))
