from pathlib import Path
import ast,hashlib,json,subprocess,sys

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
J=lambda p:json.loads(p.read_bytes())
assert J(D/'r36/full-program-preflight.json')['allPassed']
assert J(D/'full-preflight-driver-failure-r339.json')['variant']=='R37'
assert not(R/'work/r39-full-preflight-r37-r339').exists()
assert not(R/'work/r39-full-preflight-r37-r341').exists()
old=V/'verify_plan_unified_full_r37_r339.py';text=old.read_text(encoding='utf-8')
anchor="candidates=[OLD/'payload'/n,W/'r35-personal-workflow-candidate-r1/contract-Application'/n,G/n,R/'Application'/n]"
assert text.count(anchor)==1
text=text.replace(anchor,"candidates=[OLD/'payload'/n,W/'r36-native-history-candidate-r2/bundle/payload'/n,W/'r35-personal-workflow-candidate-r1/contract-Application'/n,G/n,R/'Application'/n]",1)
anchor="for p in [OLD/'payload'/n,W/'r35-personal-workflow-candidate-r1/contract-Application'/n,G/n,R/'Application'/n]:"
assert text.count(anchor)==1
text=text.replace(anchor,"for p in [OLD/'payload'/n,W/'r36-native-history-candidate-r2/bundle/payload'/n,W/'r35-personal-workflow-candidate-r1/contract-Application'/n,G/n,R/'Application'/n]:",1)
text=text.replace('r39-full-preflight-r37-r339','r39-full-preflight-r37-r341')
ast.parse(text);source=V/'verify_plan_unified_full_r37_r341.py';assert not source.exists();source.write_text(text,encoding='utf-8')
proof={'prepared':True,'source':source.name,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'initialR37DriverMissingSharedR36HistorySourceBeforeViewAllocation':True,
 'newDriverKeepsEveryFileSizeAndSHARequired':True,'fixedCandidateSourceOrPayloadChanged':False,
 'R36AlreadyPassedNotRerun':True,'servicesStarted':False}
(D/'r37/full-preflight-dependency-correction-r341.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print('OWN_R37_FULL_PROGRAM_RETRY_WITH_EXACT_SHARED_HISTORY_SOURCE',flush=True)
log=D/'r37/full-preflight-driver-r341.log';assert not log.exists()
with log.open('xb')as out:done=subprocess.run([sys.executable,str(source)],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
if done.returncode:raise RuntimeError('OWN_R37_FULL_PROGRAM_RETRY_FAILED_INSPECT_LOG')
r37=J(D/'r37/full-program-preflight.json');assert r37['allPassed']and r37['candidatePlanClassContractAndTransportPassed']
out={'passed':True,'variants':[{k:v for k,v in J(D/label/'full-program-preflight.json').items()if k in ['baselineVariant','fullProgramFilesVerified','oldDeclaredControls','newDeclaredControls','candidateInstallPaths','obsoleteEmergencyFrontendRemovals','allChangePaths','sourceProgramsUnchanged','allPassed']}for label in ['r36','r37']],
 'initialR37DependencyDriverFailureRetained':True,'servicesStarted':False,'candidateSourceSHA256':r37['newUpdaterSHA256'],
 'actualServerIISOrPublicDeploymentPassed':False}
(D/'full-program-verification-r341.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out),flush=True)
