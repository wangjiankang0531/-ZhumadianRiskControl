"""Verify runtime selection and real DTO shape differences using fixed existing private artifacts."""
import argparse,hashlib,json,os,pathlib,subprocess,sys
import reference_business_runtime as runtime
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--selection',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();W=a.workspace.resolve(strict=True);A=W.parents[1];out=a.output.resolve();assert A.name=='Application' and out.is_relative_to(W) and not out.exists();out.mkdir()
sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest();checks=0
flat,spec=runtime.select(W,a.selection,sha(a.selection));assert spec['mode']=='reference-source-rebuilt' and spec['dependencyCount']==220;checks+=1
legacy,old=runtime.select(W);assert legacy==W/'original-shared-runtime-r1_20261024/flat' and old['mode']=='deployed-archive' and old['dependencyCount']==219;checks+=1
def rejected(call,code):
 global checks
 try:call()
 except (ValueError,FileNotFoundError) as error:
  if code is not None:assert code in str(error),(code,str(error))
  checks+=1
 else:raise AssertionError('INVALID_RUNTIME_SELECTION_ACCEPTED')
for file,pin in [(a.selection,None),(None,'0'*64)]:rejected(lambda:runtime.select(W,file,pin),'RUNTIME_RECEIPT_AND_PIN_PAIR_REQUIRED')
for pin in ['0'*64,'X'*64,'bad']:rejected(lambda:runtime.select(W,a.selection,pin),'EXPLICIT_OWN_SOURCE_RUNTIME_SELECTION_PIN_REQUIRED')
original=json.loads(a.selection.read_bytes())
for i,(key,value) in enumerate([('kind','other'),('dependencyCount',219),('sourceRebuiltArchiveSHA256','0'*64),('originalSourceOrDependenciesModified',True),('sourceInputsSHA256','0'*64)]):
 folder=out/('bad-'+str(i));folder.mkdir();file=folder/'selection.json';file.write_text(json.dumps(dict(original,**{key:value})),encoding='utf-8');rejected(lambda:runtime.select(W,file,sha(file)),None)
rejected(lambda:runtime.prepare(W,a.selection.parent),'FRESH_OWN_RUNTIME_OUTPUT_REQUIRED')
# The production controller must reject the selector before it creates any candidate or acquires locks.
controller=pathlib.Path(__file__).parent/'serve_original_integrated_candidate.py';prior=W/'own-j10/receipt.json';name='own-j991';assert not (W/name).exists();dummy=out/'owned-config-fixture.yml';dummy.write_text('own-fixture: true\n',encoding='ascii')
base=[sys.executable,'-B',str(controller),'--workspace',str(W),'--name',name,'--previous-receipt',str(prior),'--minutes','1']
def run(command,name,success=True):
 r=subprocess.run(list(map(str,command)),capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW);(out/(name+'.private.log')).write_bytes(r.stdout+r.stderr);assert (r.returncode==0)==success,name;return r.stdout+r.stderr
raw=run([*base,'--reference-business-runtime',a.selection,'--reference-business-runtime-sha256',sha(a.selection)],'missing-semantics',False);assert b'REFERENCE_SOURCE_RUNTIME_REQUIRES_ORIGINAL_BUSINESS_SEMANTICS' in raw and not (W/name).exists();checks+=1
raw=run([*base,'--original-business-config',dummy,'--original-business-config-sha256',sha(dummy),'--reference-business-runtime',a.selection,'--reference-business-runtime-sha256','0'*64],'bad-runtime-pin',False);assert b'EXPLICIT_OWN_SOURCE_RUNTIME_SELECTION_PIN_REQUIRED' in raw and not (W/name).exists();checks+=1
run([sys.executable,'-B',controller,'--help'],'controller-help');checks+=1
meta=json.loads((W/'own-pboot-r32/preparation.json').read_bytes());jdk=pathlib.Path(meta['javaHome']);classes=out/'classes';classes.mkdir();java=pathlib.Path(__file__).parent/'java/OriginalReferenceDTOContractProbe.java'
run([jdk/'bin/javac.exe','-proc:none','-encoding','UTF-8','-cp',flat/'application.jar','-d',classes,java],'compile-dto-probe')
rebuild=json.loads((W/'original-business-rebuild-d-original-flags/receipt.json').read_bytes());dto=out/'dto-contracts.private.json'
run([jdk/'bin/java.exe','-Xmx128m','-cp',str(classes)+os.pathsep+str(flat/'application.jar'),'xnby.replica.OriginalReferenceDTOContractProbe',rebuild['originalRuntime'],rebuild['candidate'],legacy/'application.jar',dto],'dto-contracts')
contracts=json.loads(dto.read_bytes());assert contracts['checks']==5 and contracts['syntheticDTOOnly'] and not contracts['applicationStarted'] and not contracts['databaseConnected'];checks+=5
result={'checks':checks,'referenceRuntimeDependencyCount':220,'defaultDeployedRuntimePreserved':True,'actualDTOContractChecks':5,'referenceAndRebuiltDTOShapesMatch':True,'deployedDTOShapesDiffer':True,'invalidControllerFlagsRejectedBeforeCandidateCreation':True,'sourceInputsVerified':863,'originalApplicationOrServiceStarted':False,'databaseConnected':False,'compiledDTOProbeSHA256':sha(classes/'xnby/replica/OriginalReferenceDTOContractProbe.class'),'runtimeSelectionSHA256':sha(a.selection),'sourceFiles':{f:sha(pathlib.Path(__file__).parent/f) for f in ['reference_business_runtime.py','serve_original_integrated_candidate.py','test_reference_business_runtime.py','java/OriginalReferenceDTOContractProbe.java']},'fullCloneReady':False}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
