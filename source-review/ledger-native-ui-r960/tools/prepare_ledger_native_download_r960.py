from pathlib import Path
import ast,hashlib,json,subprocess,importlib.util,time
V=Path(__file__).resolve().parent;OLD=V/'ledger_stable_r952';H=V/'ledger_native_r960';R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prior=J(R/'work/ledgerfull-r952/verified-ledger-ui-r952.json');assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and all(c==0 for c in t['exitCodes'].values())for t in prior['terminals'])
light=J(R/'work/dl958/result.json');terminal=J(V/'stable-download-terminal-r958.json');assert light['passed'] and light['normalBrowserClosed'] and light['actualFetchInterceptionEnabled'] and terminal['exitCode']==0 and terminal['actualJobDescendantsZero']
P=R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941';assert J(P/'ledger-context.private.json')['phase']=='generated-verified' and not(P/'resume-r960').exists()
assert J(R/'work/ledger-browser-r952/first-start/result.json')['generationRequests']==0
assert not H.exists() and not(R/'work/ledgerfull-r960').exists();H.mkdir();(H/'classes').mkdir()
runner=(OLD/'run_ledger_lifecycle_r952.py').read_text('utf8').replace('ledgerfull-r952','ledgerfull-r960').replace('resume-r952','resume-r960').replace('ledger-source-pins-r952.json','ledger-source-pins-r960.json').replace('verified-ledger-ui-r952.json','verified-ledger-ui-r960.json').replace('ledger-ui-full-result-r952.json','ledger-ui-full-result-r960.json');(H/'run_ledger_lifecycle_r960.py').write_text(runner,encoding='utf8')
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('ledger-source-pins-r952.json','ledger-source-pins-r960.json');(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
probe=(OLD/'home_transfer_probe_r906.py').read_text('utf8').replace('ledger-source-pins-r952.json','ledger-source-pins-r960.json').replace('ledger-browser-r952','ledger-browser-r960').replace('resume-r952','resume-r960').replace("'metadata-'+mode+'-r952-'+label","'metadata-'+mode+'-r960-'+label");(H/'home_transfer_probe_r906.py').write_text(probe,encoding='utf8')
java=(OLD/'OwnLedgerMetadataR940.java').read_text('utf8');java=once(java,'"-r952-"','"-r960-"');(H/'OwnLedgerMetadataR940.java').write_text(java,encoding='utf8')
js=(OLD/'verify_ledger_ui_r940.mjs').read_text('utf8').replace('ledger-browser-r952','ledger-browser-r960')
js="import{win32}from'node:path';\nimport{clickStableOriginalDownload}from'./stable_original_download_click_r954.mjs';\n"+js
a=js.index(' let hit;');b=js.index(" await until(()=>[...downloads.values()]",a)
js=js[:a]+" await clickStableOriginalDownload({evaluate,send,session,save,until});\n"+js[b:]
js=once(js,"downloadPath:O+'/downloads',eventsEnabled:true","downloadPath:win32.normalize(O+'/downloads'),eventsEnabled:true")
(H/'verify_ledger_ui_r940.mjs').write_text(js,encoding='utf8')
(H/'stable_original_download_click_r954.mjs').write_bytes((V/'stable_original_download_click_r954.mjs').read_bytes())
(H/'owned_ready_observation_r924.py').write_bytes((OLD/'owned_ready_observation_r924.py').read_bytes())
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
for p in H.glob('*.mjs'):assert subprocess.run(['node','--check',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
jobs=load('ledger_native_compile_jobs_r960',G/'tools/original_server_windows_job.py');budget=load('ledger_native_compile_budget_r960',A/'tools/bounded_build_job_r671.py')
with(H/'compile.private.log').open('xb')as out:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(H/'OwnLedgerMetadataR940.java')],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);limit=budget.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':limit.metrics()};job.close()
assert p.returncode==0
(H/'metadata-compile-proof.json').write_bytes(enc({'passed':True,'sourceSHA256':sha(H/'OwnLedgerMetadataR940.java'),'classSHA256':sha(H/'classes/OwnLedgerMetadataR940.class'),'terminal':terminal}))
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
(H/'ledger-source-pins-r960.json').write_bytes(enc({'candidatePlanSHA256':J(OLD/'ledger-source-pins-r952.json')['candidatePlanSHA256'],'files':pins}))
out={'prepared':True,'sameExistingRecordAndPDFReadOnly':True,'twoNormalLifecyclesAndRefreshPrepared':True,'stableActualOriginalButtonClickPrepared':True,'nativeWindowsDownloadPathMechanismActuallyPassed':True,'actualFetchInterceptionRetained':True,'productAuthDownloadAndPreviewCodeUnchanged':True,'servicesStarted':False};(H/'prepared-r960.json').write_bytes(enc(out));print(json.dumps(out))
