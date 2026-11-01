"""Install only already verified code artifacts in the new stopped _e synthetic fixture."""
from pathlib import Path,PurePosixPath
import hashlib,json,os,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_e/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r123';T=R/'Application/tools';F=R/'work/user_feedback_20261031/emergency-workflow-source-r3'
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert read(C/'synthetic-database-prepared.json')['mysqlExitCode']==0 and read(C/'synthetic-database-prepared.json')['onlyOwnedSyntheticR114DatasetCopied']
assert read(F/'independent-build-verification.json')['undeclaredSourceDifferences']==0
payload=read(A/'payload-manifest.json');release=read(A/'release-manifest.json');prefix='frontend/emergency_pc/';old={n.removeprefix(prefix):v for n,v in payload['files'].items()if n.startswith(prefix)};new=read(F/'build-result.json')['files'];assert len(old)==204 and len(new)==338
root=(A/'frontend/emergency_pc').resolve(strict=True)
for n,row in old.items():assert sha(A/(prefix+n))==row['sha256']
for n,row in new.items():
 p=PurePosixPath(n);assert not p.is_absolute()and'..'not in p.parts and':'not in n and'\\'not in n
 assert sha(F/'dist'/n)==row['sha256']
for n in set(old)-set(new):
 p=A/(prefix+n);assert p.resolve(strict=True).is_relative_to(root)and not p.lstat().st_file_attributes&0x400;p.unlink();del payload['files'][prefix+n]
for n,row in new.items():
 p=A/(prefix+n);p.parent.mkdir(parents=True,exist_ok=True);assert p.resolve().is_relative_to(root)
 if not p.exists()or sha(p)!=row['sha256']:
  if p.exists():p.unlink()
  p.write_bytes((F/'dist'/n).read_bytes())
 payload['files'][prefix+n]=row
relative='payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class';source=R/'work/event_delivery_consistency_20261030/full-controller-r121/flow-guard-candidate-r6/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class';assert sha(source)=='9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375';p=A/relative;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(source.read_bytes());payload['files'][relative]={'bytes':p.stat().st_size,'sha256':sha(p)}
relative='tools/original_server_release_parameters.py';source=T/'server-runtime-temp-r2/original_server_release_parameters.py';assert sha(source)=='caf82f852f3ab80d66378869b09497f21f2965975364394579351a4bfda14bc9';p=A/relative;assert sha(p)==release['controllerFiles'][relative]=='8e8a7ee659ae765a0bc8248b3da107e14a9bdc293840aeb745553f6a8f7ac1f9';p.unlink();p.write_bytes(source.read_bytes());release['controllerFiles'][relative]=sha(p)
payload['ownedApprovalBaseline']={'onlyNewEChanged':True,'fullSourceRevision':'r3','noUserPreviewDataRead':True};dump(A/'payload-manifest.json',payload);release['payloadManifestSHA256']=sha(A/'payload-manifest.json');dump(A/'release-manifest.json',release);prepared=read(C/'controller-fixture-ready.json');prepared.update(releaseSHA256=sha(A/'release-manifest.json'),verifiedTaskGuardAnd19OriginalControlsWithTempCandidate=True);dump(C/'controller-fixture-ready.json',prepared)
reader=read(C/'schema-reader.json');meta=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json');paths=[reader['classpath']]
for path in meta['classpath'].split(';'):
 n=Path(path).name;paths.append(str(A/'payload/business'/(n if n in ['application.jar','process-boundary.jar']else'lib/'+n)))
callback={'java':reader['java'],'classpath':';'.join(paths)};dump(C/'callback-reader.json',callback);env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']};result=subprocess.run([str(Path(reader['java']).with_name('javac.exe')),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',callback['classpath'],'-d',str(C/'classes'),str(T/'java/approval_ui_fixture_r1/OwnWorkflowCallbackEndpointFixture.java')],env=env,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW);assert result.returncode==0,'OWN_CALLBACK_FIXTURE_COMPILE_FAILED'
dump(C/'approval-baseline-ready.json',{'verifiedFrontendFiles':338,'sourceRevision':'r3','taskGuardSHA256':sha(A/'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class'),'originalControlsUnchanged':19,'noUserManualDataReadOrChanged':True,'onlySyntheticR114DataSource':True})
print('OWN_E_VERIFIED_R3_BASELINE_READY_NO_USER_PREVIEW_DATA_READ')
