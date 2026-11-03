from pathlib import Path
import argparse,hashlib,json,subprocess,sys

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_unified_candidate_r39_20261103'
J=lambda p:json.loads(p.read_bytes())
p=argparse.ArgumentParser();p.add_argument('--variant',choices=['R36','R37'],required=True);args=p.parse_args()
assert J(D/args.variant.lower()/'full-program-preflight.json')['allPassed']
scope=J(D/'transaction-sources-r342.json');row=next(v for v in scope['sources']if v['variant']==args.variant)
source=V/row['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256']
assert not(D/args.variant.lower()/'composition-and-recovery.json').exists()
print('OWN_R39_COMPOSITION_AND_FILE_RECOVERY_START_'+args.variant,flush=True)
log=D/args.variant.lower()/'transaction-driver-r342.log';assert not log.exists()
with log.open('xb')as output:done=subprocess.run([sys.executable,str(source)],stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
if done.returncode:
    (D/args.variant.lower()/'transaction-driver-failure-r342.json').write_text(json.dumps({'variant':args.variant,'exitCode':done.returncode,'servicesStarted':False},indent=2)+'\n',encoding='utf-8')
    raise RuntimeError('OWN_R39_TRANSACTION_VALIDATION_FAILED:'+args.variant)
proof=J(D/args.variant.lower()/'composition-and-recovery.json')
assert proof['passed']and proof['allNegativeCasesRefused']and proof['planReadinessByteBoundaryScenarios']==8
assert len(proof['normalAndFaultFileRecoveryCases'])==16 and proof['changePaths']==364
report={'passed':True,'variant':args.variant,'compositionNegativeCases':proof['negativeCompositionCases'],
 'actualFileScenarios':len(proof['normalAndFaultFileRecoveryCases']),'planReadinessFileBoundaries':8,
 'writes':proof['writes'],'removals':proof['removals'],'changePaths':proof['changePaths'],
 'estimatedPeakBytes':proof['peakAllocationBudgetBytes'],'servicesSQLPublicOrFormalStartedOrModified':False}
(D/args.variant.lower()/'verified-transactions-r342.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report),flush=True)
