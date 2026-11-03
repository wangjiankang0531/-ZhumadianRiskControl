from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/native_plan_delete_roundtrip_r301_20261103'
scope=json.loads((D/'prepared-result-r301.json').read_bytes());assert not(C/'r134').exists()
for name,pin in scope['sourcePins'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
print('OWN_NATIVE_DELETE_R134_NEW_ATTEMPT_STARTING_WITH_MEMORY_GUARD',flush=True)
code=subprocess.call([sys.executable,str(T/'run_native_plan_delete_r301.py')],creationflags=subprocess.CREATE_NO_WINDOW)
if code and not(C/'r134').exists():
    log=C/'r134-outer.private.log'
    if log.exists()and'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'in log.read_text(encoding='utf-8'):
        restored=subprocess.run([sys.executable,str(V/'restore_plan_delete_prestart_r302.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        assert restored.returncode==0 and json.loads(restored.stdout)['passed'],'OWN_RETRY_PRESTART_RESTORE_REFUSED'
        print('OWN_RETRY_MEMORY_REFUSAL_RESTORED_WITHOUT_FABRICATING_NORMAL_RECEIPTS',flush=True)
print(json.dumps({'attempt':'r134','runnerExitCode':code,'publicFormalOrDesktopChanged':False}),flush=True)
assert code==0,'OWN_NATIVE_DELETE_RETRY_NOT_PASSED_EVIDENCE_KEPT'
