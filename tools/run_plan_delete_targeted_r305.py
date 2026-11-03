from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/native_plan_delete_roundtrip_r304_20261103'
scope=json.loads((D/'prepared-result-r304.json').read_bytes());assert not(C/'r135').exists()
for name,pin in scope['sourcePins'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
print('OWN_NATIVE_DELETE_R135_FIXED_DEPENDENCIES_AND_MEMORY_GUARD_STARTING',flush=True)
code=subprocess.call([sys.executable,str(T/'run_native_plan_delete_r304.py')],creationflags=subprocess.CREATE_NO_WINDOW)
if code and not(C/'r135').exists():
    log=C/'r135-outer.private.log'
    if log.exists()and'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'in log.read_text(encoding='utf-8'):
        done=subprocess.run([sys.executable,str(V/'restore_plan_delete_prestart_r305.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        assert done.returncode==0 and json.loads(done.stdout)['passed'],'OWN_R135_PRESTART_RESTORE_REFUSED'
        print('OWN_R135_MEMORY_REFUSAL_RESTORED_WITHOUT_FAKE_NORMAL_RECEIPTS',flush=True)
print(json.dumps({'attempt':'r135','runnerExitCode':code,'publicFormalOrDesktopChanged':False}),flush=True)
assert code==0,'OWN_NATIVE_DELETE_R135_NOT_PASSED_EVIDENCE_KEPT'
