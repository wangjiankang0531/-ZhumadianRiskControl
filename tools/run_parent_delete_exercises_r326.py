from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
D=R/'Document/Deployment/native_parent_delete_with_exercises_r325_20261103'
scope=json.loads((D/'prepared-result-r325.json').read_bytes())
assert scope['attempt']=='r141'and scope['expectedBrowserCases']==18 and not(C/'r141').exists()
for name,pin in scope['sourcePins'].items():assert hashlib.sha256((T/name).read_bytes()).hexdigest()==pin
print('OWN_PARENT_DELETE_R141_REAL_CHILD_RETENTION_AND_OBJECT_STARTING',flush=True)
code=subprocess.call([sys.executable,str(T/'run_native_parent_delete_r325.py')],creationflags=subprocess.CREATE_NO_WINDOW)
if code and not(C/'r141').exists():
    log=C/'r141-outer.private.log'
    if log.exists()and'OWN_FIXTURE_REQUIRES_FOUR_GIB_AVAILABLE_MEMORY'in log.read_text(encoding='utf-8'):
        restored=subprocess.run([sys.executable,str(V/'restore_parent_delete_prestart_r326.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        assert restored.returncode==0 and json.loads(restored.stdout)['passed'],'OWN_R141_PRESTART_RESTORE_REFUSED'
        print('OWN_R141_MEMORY_REFUSAL_RESTORED_WITHOUT_FAKE_NORMAL_RECEIPTS',flush=True)
print(json.dumps({'attempt':'r141','runnerExitCode':code,'publicFormalOrDesktopChanged':False}),flush=True)
assert code==0,'OWN_PARENT_DELETE_R141_NOT_PASSED_EVIDENCE_KEPT'
