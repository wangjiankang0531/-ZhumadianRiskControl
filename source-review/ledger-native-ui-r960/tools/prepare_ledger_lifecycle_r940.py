"""Prepare two actual R47 lifecycles for original ledger supervision/preview/download UI."""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application'
OLD=V/'supervision_exact_r931';H=V/'ledger_full_r941';D=R/'Document/Deployment/ledger_original_ui_r940_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert not H.exists()and not D.exists()and not(R/'work/ledgerfull-r941').exists()
prior=J(R/'work/sv931/verified-exact-supervision-r931.json');assert prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in prior['terminals'])
H.mkdir();(H/'classes').mkdir();D.mkdir()
runner=(OLD/'run_home_transfer_full_r906.py').read_text('utf8').replace("P=O/'exact-supervision-r931';Z=R/'work/sv931'","P=O/'ledger-ui-r941';Z=R/'work/ledgerfull-r941'")
runner=runner.replace('exact-supervision-source-pins-r931.json','ledger-source-pins-r941.json').replace('verified-exact-supervision-r931.json','verified-ledger-ui-r941.json').replace('exact-supervision-full-result-r931.json','ledger-ui-full-result-r941.json')
runner=once(runner,"fixture_nonce=next(line.split('=',1)[1]for line in (W/'flight.private.properties').read_text('ascii').splitlines()if line.startswith('nonce='))","fixture_nonce=hashlib.sha256(str(P).encode('utf8')).hexdigest()[:32]")
runner=once(runner,"P.mkdir();(P/'own-normal-manager-test.marker').write_bytes(b'own-original-manager-full-lifecycle-r609\\n')","P.mkdir();(P/'own-ledger-ui.marker').write_bytes(b'own-ledger-ui-r941\\n')")
runner=once(runner,"for label in ['normal-restart']:","for label in ['first-start','normal-restart']:")
runner=runner.replace('len(checks)==1','len(checks)==2').replace('len(probeChecks)==1','len(probeChecks)==2').replace('actualOneSixComponentLifecycle','actualTwoSixComponentLifecycles').replace('actualReadOnlyCompletedTaskReopen','actualOriginalLedgerUIAndNormalRestart').replace('normalLoginReadOnlyRoutesAndExistingDetailAccepted','normalOriginalLedgerPreviewDownloadAndRestartAccepted')
marker="assert J(R/'work/sv927/verified-current-supervision-r927.json')['passed']";assert runner.count(marker)==1;runner=runner.replace(marker,"assert J(R/'work/sv931/verified-exact-supervision-r931.json')['passed']")
runner=runner.replace('No business submit, approval, SQL mutation or callback rebinding is performed.','Only this new owned ledger fixture is created and supervised through the normal API/UI; metadata is prepared in the exact G namespace. No public business write, account/role change, schema change, task approval or callback rebinding is performed.')
assert "P=O/'ledger-ui-r941';Z=R/'work/ledgerfull-r941'"in runner
(H/'run_ledger_lifecycle_r941.py').write_text(runner,encoding='utf8');ast.parse(runner)
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('exact-supervision-source-pins-r931.json','ledger-source-pins-r941.json');(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
for src,name in [(V/'ledger_probe_r940.py','home_transfer_probe_r906.py'),(V/'verify_ledger_ui_r940.mjs','verify_ledger_ui_r940.mjs'),(V/'OwnLedgerMetadataR940.java','OwnLedgerMetadataR940.java'),(V/'owned_ready_observation_r924.py','owned_ready_observation_r924.py')]: (H/name).write_bytes(src.read_bytes())
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_ledger_ui_r940.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
assert sha(G/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
jobs=load('ledger_compile_jobs_r940',G/'tools/original_server_windows_job.py');budget=load('ledger_compile_budget_r940',A/'tools/bounded_build_job_r671.py')
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>1024**3
with(H/'metadata-compile.private.log').open('xb')as f:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(H/'OwnLedgerMetadataR940.java')],stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':cap.metrics()};job.close()
assert p.returncode==0,'LEDGER_METADATA_FIXTURE_COMPILE_REQUIRED'
(H/'metadata-compile-proof.json').write_bytes(enc({'passed':True,'sourceSHA256':sha(H/'OwnLedgerMetadataR940.java'),'classSHA256':sha(H/'classes/OwnLedgerMetadataR940.class'),'terminal':terminal}))
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
plan=R/'Document/Deployment/unified_home_supervision_exact_r930_20261104/full-source-and-restore-plan.private.json'
(H/'ledger-source-pins-r941.json').write_bytes(enc({'candidatePlanSHA256':sha(plan),'files':pins}))
proof={'prepared':True,'metadataJavaCompiledAndActualJobNormallyExited':True,'productR47CandidateUnchanged':True,'twoNormalLifecycleStagesPrepared':True,
 'actualOriginalLedgerSupervisionPreviewDownloadUIStillToRun':True,'onlyOwnMetadataTablesAndOneOwnNormalAPIRowMayBePrepared':True,'noAccountsRolesSchemaOrPublicWritesPrepared':True,'servicesOrDatabaseStarted':False,'fullCloneReady':False}
(D/'prepared-r940.json').write_bytes(enc(proof));print(json.dumps(proof))
