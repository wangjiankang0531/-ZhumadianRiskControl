from pathlib import Path
import ast,hashlib,json,subprocess,importlib.util,time
V=Path(__file__).resolve().parent;OLD=V/'ledger_full_r941';H=V/'ledger_resume_r946';R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prior=J(R/'work/ledgerfull-r941/verified-ledger-ui-r941.json');assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and all(c==0 for c in t['exitCodes'].values())for t in prior['terminals'])
P=R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941'
assert (P/'own-ledger-ui.marker').read_bytes()==b'own-ledger-ui-r941\n' and not(P/'ledger-context.private.json').exists() and not(P/'resume-r946').exists()
assert 'phase=committed-readback-verified' in (P/'ledger-metadata-journal.private.properties').read_text('ascii').splitlines()
browser=J(R/'work/ledger-browser-r941/first-start/result.json');assert not browser['passed'] and browser['generationRequests']==0 and browser['cases']==[]
assert J(R/'work/ledger-browser-r941/first-start/browser-terminal.json')['normalBrowserClosed']
assert not H.exists() and not(R/'work/ledgerfull-r946').exists();H.mkdir();(H/'classes').mkdir()
runner=(OLD/'run_ledger_lifecycle_r941.py').read_text('utf8')
runner=once(runner,"Z=R/'work/ledgerfull-r941'","Z=R/'work/ledgerfull-r946'")
runner=once(runner,"assert W.is_dir()and not P.exists()and not Z.exists(),'NEW_COMPONENT_BOOTSTRAP_ATTEMPT_REQUIRED'","assert W.is_dir()and P.is_dir()and (P/'own-ledger-ui.marker').read_bytes()==b'own-ledger-ui-r941\\n'and not(P/'resume-r946').exists()and not Z.exists(),'EXACT_EXISTING_METADATA_NEW_RESUME_REQUIRED'")
runner=once(runner,"P.mkdir();(P/'own-ledger-ui.marker').write_bytes(b'own-ledger-ui-r941\\n')","(P/'resume-r946').mkdir()")
runner=runner.replace('ledger-source-pins-r941.json','ledger-source-pins-r946.json').replace("save('verified-ledger-ui-r941.json'","save('verified-ledger-ui-r946.json'").replace("(V/'ledger-ui-full-result-r941.json')","(V/'ledger-ui-full-result-r946.json')")
(H/'run_ledger_lifecycle_r946.py').write_text(runner,encoding='utf8')
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('ledger-source-pins-r941.json','ledger-source-pins-r946.json');(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
probe=(OLD/'home_transfer_probe_r906.py').read_text('utf8').replace('ledger-source-pins-r941.json','ledger-source-pins-r946.json').replace("OUT=R/'work/ledger-browser-r941'","OUT=R/'work/ledger-browser-r946'")
probe=once(probe,"stage=P/label;stage.mkdir();terminals=[]","stage=P/'resume-r946'/label;stage.mkdir();terminals=[]")
probe=once(probe,"mode='prepare'if label=='first-start'else'readback'","mode='readback'")
probe=once(probe,"str(P),mode]","str(P),mode,label]")
probe=once(probe,"metadata=props(P/('metadata-'+mode+'.private.properties'))","metadata=props(P/('metadata-'+mode+'-r946-'+label+'.private.properties'))")
probe=once(probe,"metadata['persistentWritesIssued']==str(mode=='prepare').lower()","metadata['persistentWritesIssued']=='false'")
(H/'home_transfer_probe_r906.py').write_text(probe,encoding='utf8')
java=(OLD/'OwnLedgerMetadataR940.java').read_text('utf8')
java=once(java,'need(a.length==5&&Set.of("prepare","readback").contains(a[4]),"EXACT_LEDGER_METADATA_ARGUMENTS");','need(a.length==6&&a[4].equals("readback")&&Set.of("first-start","normal-restart").contains(a[5]),"EXACT_EXISTING_LEDGER_METADATA_READONLY_ARGUMENTS");')
java=once(java,'ROOT.resolve("metadata-"+a[4]+".private.properties")','ROOT.resolve("metadata-"+a[4]+"-r946-"+a[5]+".private.properties")')
(H/'OwnLedgerMetadataR940.java').write_text(java,encoding='utf8')
js=(OLD/'verify_ledger_ui_r940.mjs').read_text('utf8').replace("O='D:/Project/Zhumadian/work/ledger-browser-r941/'+label","O='D:/Project/Zhumadian/work/ledger-browser-r946/'+label")
js=once(js,"await until(()=>token&&current);ua=await evaluate('navigator.userAgent');await until(()=>Array.isArray(ledgerRows));await until(()=>evaluate('!!document.querySelector(\".el-table__body-wrapper\")'));",'''await until(()=>token&&current);ua=await evaluate('navigator.userAgent');
 const menuFlat=[];function walkMenu(nodes){for(const n of nodes||[]){menuFlat.push({path:n.path,urlAddress:n.urlAddress,id:n.id,hasChildren:n.hasChildren});walkMenu(n.children)}}walkMenu(current.menuList);
 await save('normal-login-route-diagnostic.private.json',{menus:menuFlat,permissions:(current.permissionList||[]).map(n=>({modelId:n.modelId,button:(n.button||[]).map(b=>({path:b.path,urlAddress:b.urlAddress}))})),dom:await evaluate('({path:location.pathname,title:document.title,table:!!document.querySelector(".el-table__body-wrapper"),home:!!document.querySelector(".home-wrapper"),body:document.body.textContent.slice(0,500)})')});
 stage='fresh-original-ledger-navigation';await send('Page.navigate',{url:w.base+'/zhumadian/hiddenInvestigate/perilLedger'},session);
 await until(()=>Array.isArray(ledgerRows));await until(()=>evaluate('!!document.querySelector(".el-table__body-wrapper")'));''')
js=once(js,"}catch{}}\nfinally", "}catch(d){await save('diagnostic-observation-error.json',{type:d.message})}}\nfinally")
(H/'verify_ledger_ui_r940.mjs').write_text(js,encoding='utf8')
(H/'owned_ready_observation_r924.py').write_bytes((OLD/'owned_ready_observation_r924.py').read_bytes())
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_ledger_ui_r940.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
jobs=load('ledger_resume_compile_jobs_r946',G/'tools/original_server_windows_job.py');budget=load('ledger_resume_compile_budget_r946',A/'tools/bounded_build_job_r671.py')
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>1024**3
with(H/'compile.private.log').open('xb')as out:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(H/'OwnLedgerMetadataR940.java')],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);limit=budget.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':limit.metrics()};job.close()
assert p.returncode==0
(H/'metadata-compile-proof.json').write_bytes(enc({'passed':True,'sourceSHA256':sha(H/'OwnLedgerMetadataR940.java'),'classSHA256':sha(H/'classes/OwnLedgerMetadataR940.class'),'terminal':terminal}))
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
(H/'ledger-source-pins-r946.json').write_bytes(enc({'candidatePlanSHA256':J(OLD/'ledger-source-pins-r941.json')['candidatePlanSHA256'],'files':pins}))
out={'prepared':True,'priorFailedFirstRouteRetained':True,'priorNormalShutdownAndCodePointerRestoreVerified':True,'same17MetadataRowsReadbackOnly':True,'noNewMenuOrAccountGrants':True,'oneBusinessRowStillUnissued':True,'originalProductUnchanged':True,'normalLoginThenFreshOriginalRouteAndDiagnosticsAdded':True,'servicesStarted':False}
(H/'prepared-r946.json').write_bytes(enc(out));print(json.dumps(out))
