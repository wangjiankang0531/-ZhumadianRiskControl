from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_exercise_department_filter_verified_r320_20261103'
scope=json.loads((D/'prepared-result-r317.json').read_bytes());assert scope['attempt']=='r139'and scope['expectedBrowserCases']==16
assert not(C/'r139').exists()
for name,pin in scope['sourcePins'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
print('OWN_EXERCISE_DEPARTMENT_R139_REAL_FILTER_AND_RESET_STARTING',flush=True)
code=subprocess.call([sys.executable,str(T/'run_native_exercise_filter_r320.py')],creationflags=subprocess.CREATE_NO_WINDOW)
if code and not(C/'r139').exists():
    log=C/'r139-outer.private.log'
    if log.exists()and'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'in log.read_text(encoding='utf-8'):
        done=subprocess.run([sys.executable,str(V/'restore_exercise_department_prestart_r321.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        assert done.returncode==0 and json.loads(done.stdout)['passed'],'OWN_R139_PRESTART_RESTORE_REFUSED'
        print('OWN_R139_MEMORY_REFUSAL_RESTORED_WITHOUT_FAKE_NORMAL_RECEIPTS',flush=True)
print(json.dumps({'attempt':'r139','runnerExitCode':code,'publicFormalOrDesktopChanged':False}),flush=True)
assert code==0,'OWN_EXERCISE_DEPARTMENT_R139_NOT_PASSED_EVIDENCE_KEPT'
