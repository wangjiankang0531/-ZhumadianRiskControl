from pathlib import Path
import ast,hashlib,json,subprocess,importlib.util,time
V=Path(__file__).resolve().parent;OLD=V/'ledger_root_r948';H=V/'ledger_download_r950';R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prior=J(R/'work/ledgerfull-r948/verified-ledger-ui-r948.json');assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and all(c==0 for c in t['exitCodes'].values())for t in prior['terminals'])
P=R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941';context=J(P/'ledger-context.private.json')
assert context['phase']=='generated-verified' and not(P/'resume-r950').exists()
first=J(R/'work/ledger-browser-r948/first-start/result.json');assert first['generationRequests']==1 and len(first['cases'])==5 and first['stage']=='original-pdf-download-button'
assert J(R/'work/ledger-browser-r948/first-start/browser-terminal.json')['normalBrowserClosed']
assert not H.exists() and not(R/'work/ledgerfull-r950').exists();H.mkdir();(H/'classes').mkdir()
runner=(OLD/'run_ledger_lifecycle_r948.py').read_text('utf8').replace('ledgerfull-r948','ledgerfull-r950').replace('resume-r948','resume-r950').replace('ledger-source-pins-r948.json','ledger-source-pins-r950.json').replace('verified-ledger-ui-r948.json','verified-ledger-ui-r950.json').replace('ledger-ui-full-result-r948.json','ledger-ui-full-result-r950.json')
(H/'run_ledger_lifecycle_r950.py').write_text(runner,encoding='utf8')
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('ledger-source-pins-r948.json','ledger-source-pins-r950.json');(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
probe=(OLD/'home_transfer_probe_r906.py').read_text('utf8').replace('ledger-source-pins-r948.json','ledger-source-pins-r950.json').replace('ledger-browser-r948','ledger-browser-r950').replace('resume-r948','resume-r950')
probe=once(probe,"mode='repair-root'if label=='first-start'else'readback'","mode='readback'")
probe=once(probe,"'metadata-'+mode+'-r948-'+label","'metadata-'+mode+'-r950-'+label")
probe=once(probe,"metadata['persistentWritesIssued']==str(label=='first-start').lower()","metadata['persistentWritesIssued']=='false'")
probe=once(probe,"'mode':'create'if label=='first-start'else'readback','nonce':nonce","'mode':'readback','phase':label,'nonce':nonce")
probe=once(probe,"expected=1 if label=='first-start'else 0","expected=0")
(H/'home_transfer_probe_r906.py').write_text(probe,encoding='utf8')
java=(OLD/'OwnLedgerMetadataR940.java').read_text('utf8')
java=once(java,'need(a.length==6&&Set.of("repair-root","readback").contains(a[4])&&Set.of("first-start","normal-restart").contains(a[5])&&a[4].equals(a[5].equals("first-start")?"repair-root":"readback"),"EXACT_ONE_OWN_ROOT_REPAIR_OR_READBACK_ARGUMENTS");boolean repair=a[4].equals("repair-root");','need(a.length==6&&a[4].equals("readback")&&Set.of("first-start","normal-restart").contains(a[5]),"EXACT_EXISTING_LEDGER_ROOT_READBACK_ONLY");boolean repair=false;')
java=once(java,'"-r948-"','"-r950-"')
(H/'OwnLedgerMetadataR940.java').write_text(java,encoding='utf8')
js=(OLD/'verify_ledger_ui_r940.mjs').read_text('utf8').replace('ledger-browser-r948','ledger-browser-r950')
js=once(js,"const label=w.mode==='create'?'first-start':'normal-restart',O=","if(w.mode!=='readback'||!['first-start','normal-restart'].includes(w.phase))throw Error('EXISTING_GENERATED_LEDGER_READBACK_ONLY');\nconst label=w.phase,O=")
js=once(js,"stage='original-pdf-download-button';await evaluate('(()=>{const b=Array.from(document.querySelectorAll(\".el-drawer button\")).find(e=>e.textContent.trim()===\"下载\");if(!b)throw Error(\"ORIGINAL_PDF_DOWNLOAD_BUTTON\");b.click()})()');",'''stage='original-pdf-download-button';
 const hit=await evaluate('(()=>{const buttons=Array.from(document.querySelectorAll(".el-drawer button")).filter(e=>e.getClientRects().length&&e.textContent.trim()==="下载");if(buttons.length!==1||buttons[0].disabled)throw Error("ONE_VISIBLE_ORIGINAL_PDF_DOWNLOAD_BUTTON");const r=buttons[0].getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2,width:r.width,height:r.height}})()');
 if(!(hit.x>0&&hit.x<1600&&hit.y>0&&hit.y<1100))throw Error('VISIBLE_ORIGINAL_DOWNLOAD_HIT_TARGET');
 await save('download-click-target.json',{visibleOriginalButton:true,insideViewport:true,actualInputDispatch:true});
 await send('Input.dispatchMouseEvent',{type:'mousePressed',x:hit.x,y:hit.y,button:'left',clickCount:1},session);
 await send('Input.dispatchMouseEvent',{type:'mouseReleased',x:hit.x,y:hit.y,button:'left',clickCount:1},session);''')
js=once(js,"v.method==='Browser.downloadWillBegin'","['Browser.downloadWillBegin','Page.downloadWillBegin'].includes(v.method)")
js=once(js,"v.method==='Browser.downloadProgress'","['Browser.downloadProgress','Page.downloadProgress'].includes(v.method)")
js=once(js,"}catch(d){await save('diagnostic-observation-error.json',{type:d.message})}","}catch(d){await save('diagnostic-observation-error.json',{type:d.message});try{const tree=await send('Page.getFrameTree',{},session);await save('failure-frame-tree.private.json',tree)}catch{}}")
(H/'verify_ledger_ui_r940.mjs').write_text(js,encoding='utf8')
(H/'owned_ready_observation_r924.py').write_bytes((OLD/'owned_ready_observation_r924.py').read_bytes())
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_ledger_ui_r940.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
jobs=load('ledger_download_compile_jobs_r950',G/'tools/original_server_windows_job.py');budget=load('ledger_download_compile_budget_r950',A/'tools/bounded_build_job_r671.py')
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>1024**3
with(H/'compile.private.log').open('xb')as out:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(H/'OwnLedgerMetadataR940.java')],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);limit=budget.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':limit.metrics()};job.close()
assert p.returncode==0
(H/'metadata-compile-proof.json').write_bytes(enc({'passed':True,'sourceSHA256':sha(H/'OwnLedgerMetadataR940.java'),'classSHA256':sha(H/'classes/OwnLedgerMetadataR940.class'),'terminal':terminal}))
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
(H/'ledger-source-pins-r950.json').write_bytes(enc({'candidatePlanSHA256':J(OLD/'ledger-source-pins-r948.json')['candidatePlanSHA256'],'files':pins}))
out={'prepared':True,'sameExistingOneGeneratedRecordAndFileReused':True,'noBusinessOrMetadataWritesPrepared':True,'twoNormalLifecyclesReadbackOnly':True,'downloadUsesActualInputDispatchOnVisibleOriginalButton':True,'priorDOMClickTimeoutPreserved':True,'productAuthPreviewAndDownloadCodeUnchanged':True,'servicesStarted':False}
(H/'prepared-r950.json').write_bytes(enc(out));print(json.dumps(out))
