from pathlib import Path
import importlib.util,subprocess,sys,json,time
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
attempt='r71';assert len(sys.argv)==1;assert not(C/attempt).exists()
spec=importlib.util.spec_from_file_location('owned_return_job',R/'_g/Application/tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
with(C/(attempt+'-outer.private.log')).open('xb')as log:
 p=subprocess.Popen([sys.executable,str(V/'verify_full_controller_transfer_r171_20261102.py'),'--attempt',attempt,'--variant','combined','--event-dictionaries'],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=j.OwnedWindowsJob(p);p.wait()
while job.active_processes():print('OWN_RETURN_DESCENDANTS_STILL_LIVE_NO_FORCE',flush=True);time.sleep(.2)
job.close();(C/(attempt+'-outer-terminal.json')).write_text(json.dumps({'exitCode':p.returncode,'actualDescendantsZeroBeforeClose':True,'forceTerminationUsed':False},indent=2)+'\n',encoding='utf-8')
restored=subprocess.run([sys.executable,str(V/'restore_owned_return_serial_r163_20261102.py'),'--attempt',attempt],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
if restored.returncode:print('OWN_RETURN_CONFIG_RESTORE_REFUSED_INSPECT_EXACT_PROOF');raise RuntimeError('OWN_RETURN_RESTORE_NOT_PASSED')
receipt=json.loads(restored.stdout);assert receipt['passed']and receipt['exactOriginalBytesRestored']
print(json.dumps({'ownedReturnControllerExitCode':p.returncode,'allActualDescendantsZero':True,'syntheticConfigurationRestoredExactOriginalBytes':True,'publicFormalOrDesktopChanged':False}))
assert p.returncode==0,'OWN_RETURN_TEST_FAILED_EVIDENCE_KEPT'
