from pathlib import Path
import ast,hashlib,json,subprocess,importlib.util,time
V=Path(__file__).resolve().parent;OLD=V/'ledger_download_r950';H=V/'ledger_stable_r952';R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prior=J(R/'work/ledgerfull-r950/verified-ledger-ui-r950.json');assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and all(c==0 for c in t['exitCodes'].values())for t in prior['terminals'])
P=R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941';assert J(P/'ledger-context.private.json')['phase']=='generated-verified' and not(P/'resume-r952').exists()
first=J(R/'work/ledger-browser-r950/first-start/result.json');assert first['generationRequests']==0 and len(first['cases'])==3 and first['type']=='VISIBLE_ORIGINAL_DOWNLOAD_HIT_TARGET'
assert not H.exists() and not(R/'work/ledgerfull-r952').exists();H.mkdir();(H/'classes').mkdir()
runner=(OLD/'run_ledger_lifecycle_r950.py').read_text('utf8').replace('ledgerfull-r950','ledgerfull-r952').replace('resume-r950','resume-r952').replace('ledger-source-pins-r950.json','ledger-source-pins-r952.json').replace('verified-ledger-ui-r950.json','verified-ledger-ui-r952.json').replace('ledger-ui-full-result-r950.json','ledger-ui-full-result-r952.json');(H/'run_ledger_lifecycle_r952.py').write_text(runner,encoding='utf8')
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('ledger-source-pins-r950.json','ledger-source-pins-r952.json');(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
probe=(OLD/'home_transfer_probe_r906.py').read_text('utf8').replace('ledger-source-pins-r950.json','ledger-source-pins-r952.json').replace('ledger-browser-r950','ledger-browser-r952').replace('resume-r950','resume-r952').replace("'metadata-'+mode+'-r950-'+label","'metadata-'+mode+'-r952-'+label");(H/'home_transfer_probe_r906.py').write_text(probe,encoding='utf8')
java=(OLD/'OwnLedgerMetadataR940.java').read_text('utf8');java=once(java,'"-r950-"','"-r952-"');(H/'OwnLedgerMetadataR940.java').write_text(java,encoding='utf8')
js=(OLD/'verify_ledger_ui_r940.mjs').read_text('utf8').replace('ledger-browser-r950','ledger-browser-r952')
start=js.index(" const hit=await evaluate(");end=js.index(" await save('download-click-target.json'",start)
js=js[:start]+''' let hit;
 await until(async()=>{const row=await evaluate('(()=>{const buttons=Array.from(document.querySelectorAll(".el-drawer button")).filter(e=>e.getClientRects().length&&e.textContent.trim()==="下载");if(buttons.length!==1||buttons[0].disabled)return null;const b=buttons[0],r=b.getBoundingClientRect(),x=r.x+r.width/2,y=r.y+r.height/2,top=document.elementFromPoint(x,y);return{x,y,width:r.width,height:r.height,viewWidth:innerWidth,viewHeight:innerHeight,inside:r.width>0&&r.height>0&&r.x>=0&&r.y>=0&&r.right<=innerWidth&&r.bottom<=innerHeight,topmost:!!top&&(b===top||b.contains(top))}})()');
 if(row)await save('download-target-observation.private.json',row);
 if(!row?.inside||!row.topmost)return false;hit=row;return true;});
''' +js[end:]
js=once(js,"e.textContent.slice(0,80))})()'","e.textContent.slice(0,80))})'")
js=once(js,"}catch(d){await save('diagnostic-observation-error.json'",'''}catch(d){await save('diagnostic-observation-error.json' ''').replace("'diagnostic-observation-error.json' ,","'diagnostic-observation-error.json',")
needle="finally{token='';current=null;w.password='';await close();"
replacement="finally{if(!proof?.passed){try{const shot=await send('Page.captureScreenshot',{format:'png'},session);await fs.writeFile(O+'/failure.png',Buffer.from(shot.data,'base64'))}catch{}}token='';current=null;w.password='';await close();"
js=once(js,needle,replacement)
(H/'verify_ledger_ui_r940.mjs').write_text(js,encoding='utf8');(H/'owned_ready_observation_r924.py').write_bytes((OLD/'owned_ready_observation_r924.py').read_bytes())
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_ledger_ui_r940.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
jobs=load('ledger_stable_compile_jobs_r952',G/'tools/original_server_windows_job.py');budget=load('ledger_stable_compile_budget_r952',A/'tools/bounded_build_job_r671.py')
with(H/'compile.private.log').open('xb')as out:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(H/'OwnLedgerMetadataR940.java')],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);limit=budget.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':limit.metrics()};job.close()
assert p.returncode==0
(H/'metadata-compile-proof.json').write_bytes(enc({'passed':True,'sourceSHA256':sha(H/'OwnLedgerMetadataR940.java'),'classSHA256':sha(H/'classes/OwnLedgerMetadataR940.class'),'terminal':terminal}))
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
(H/'ledger-source-pins-r952.json').write_bytes(enc({'candidatePlanSHA256':J(OLD/'ledger-source-pins-r950.json')['candidatePlanSHA256'],'files':pins}))
out={'prepared':True,'sameExistingGeneratedRecordReadOnly':True,'waitForVisibleTopmostButtonWithinActualViewport':True,'actualBrowserMouseInputAfterHitTestOnly':True,'invalidDiagnosticObjectInvocationCorrected':True,'originalProductAndAuthUnchanged':True,'servicesStarted':False};(H/'prepared-r952.json').write_bytes(enc(out));print(json.dumps(out))
