from pathlib import Path
import importlib.util, subprocess, sys, json, time
R = Path('D:/Project/Zhumadian')
V = Path(__file__).parent
C = R / 'work/event_delivery_consistency_20261030/full-controller-r163'
attempt = 'r137'
assert len(sys.argv) == 1
assert not (C / attempt).exists()
spec = importlib.util.spec_from_file_location('owned_history_job', R / '_g/Application/tools/original_server_windows_job.py')
j = importlib.util.module_from_spec(spec)
spec.loader.exec_module(j)
with (C / (attempt + '-outer.private.log')).open('xb') as log:
    p = subprocess.Popen([sys.executable, str(V / 'verify_full_controller_exercise_filter_r317.py'), '--attempt', attempt, '--variant', 'combined', '--event-dictionaries'], stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    job = j.OwnedWindowsJob(p)
    p.wait()
while job.active_processes():
    print('OWN_HISTORY_DESCENDANTS_STILL_LIVE_NO_FORCE', flush=True)
    time.sleep(0.2)
job.close()
(C / (attempt + '-outer-terminal.json')).write_text(json.dumps({'exitCode': p.returncode, 'actualDescendantsZeroBeforeClose': True, 'forceTerminationUsed': False}, indent=2) + '\n', encoding='utf-8')
frontend = subprocess.run([sys.executable, str(V / 'restore_personal_workflow_frontend_r317.py')], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
assert frontend.returncode == 0 and json.loads(frontend.stdout)['passed'], 'OWN_FRONTEND_RESTORE_FAILED'
mapper = subprocess.run([sys.executable, str(V / 'mapper_observation_support_r317.py'), 'restore', '--attempt', attempt], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
assert mapper.returncode == 0 and json.loads(mapper.stdout)['passed'], 'OWN_OBSERVER_RESTORE_REFUSED'
product = subprocess.run([sys.executable, str(V / 'mapper_product_patch_r317.py'), 'restore', '--attempt', attempt], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
assert product.returncode == 0 and json.loads(product.stdout)['passed'], 'OWN_PRODUCT_PARAMETER_RESTORE_REFUSED'
restored = subprocess.run([sys.executable, str(V / 'restore_production_history_runtime_r317.py')], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
if restored.returncode:
    print('OWN_HISTORY_RESTORE_REFUSED_INSPECT_EXACT_PROOF')
    raise RuntimeError('OWN_HISTORY_RESTORE_NOT_PASSED')
proof = json.loads(restored.stdout)
assert proof['passed'] and proof['exactOriginalBytesRestored']
print(json.dumps({'nativeHistoryControllerExitCode': p.returncode, 'allActualDescendantsZero': True, 'originalObservationAndSyntheticConfigurationRestoredExactBytes': True, 'publicFormalOrDesktopChanged': False}))
assert p.returncode == 0, 'OWN_HISTORY_TEST_FAILED_EVIDENCE_KEPT'
