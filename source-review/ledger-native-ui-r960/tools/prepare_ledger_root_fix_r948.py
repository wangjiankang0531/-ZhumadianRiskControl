from pathlib import Path
import ast,hashlib,json,subprocess,importlib.util,time
V=Path(__file__).resolve().parent;OLD=V/'ledger_resume_r946';H=V/'ledger_root_r948';R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prior=J(R/'work/ledgerfull-r946/verified-ledger-ui-r946.json');assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero'] and all(c==0 for c in t['exitCodes'].values())for t in prior['terminals'])
P=R/'work/original-manager-full-lifecycle-r609/ledger-ui-r941'
assert not(P/'ledger-context.private.json').exists() and not(P/'resume-r948').exists()
diag=J(R/'work/ledger-browser-r946/first-start/normal-login-route-diagnostic.private.json')
assert len([n for n in diag['menus']if n['path']=='/hiddenInvestigate'])==2 and not diag['dom']['table']
assert J(R/'work/ledger-browser-r946/first-start/result.json')['generationRequests']==0
assert not H.exists() and not(R/'work/ledgerfull-r948').exists();H.mkdir();(H/'classes').mkdir()
# Execute the actual compiled route conversion on the two observed synthetic roots.
compiled=G/'frontend/security_pc/assets/js/index-kAcgthiJ.js';s=compiled.read_text('utf8')
er=s[s.index('function er('):s.index('function Bc(')]
ec=s[s.index('function ec('):s.index('function xm(')]
routes=s[s.index('function yet('):s.index('const op=function(',s.index('function yet('))]
case='''const path="/hiddenInvestigate/perilLedger";
const input=[{path:"/hiddenInvestigate",children:[{path:"/hiddenInvestigate/riskAnalysisUnit",component:"risk"}]},{path:"/hiddenInvestigate",children:[{path,component:"ledger"}]}];
const paths=a=>{const out=[];er(a,r=>out.push(r.path));return out};
const before=paths(Pj(input,x=>x));input[1].path="/own-ledger-r941";const after=paths(Pj(input,x=>x));
if(before.includes(path)||!after.includes(path))throw Error("ACTUAL_ROUTE_DEDUPLICATION_NOT_REPRODUCED");
console.log(JSON.stringify({passed:true,actualCompiledRouteFunctions:true,duplicateRootDropsWholeBranch:true,uniqueOwnRootRetainsOriginalLedgerPath:true,before,after}));'''
(H/'actual-route-deduplication-r948.mjs').write_text(er+ec+routes+case,encoding='utf8')
actual=subprocess.run(['node',str(H/'actual-route-deduplication-r948.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert actual.returncode==0,actual.stderr.decode('utf8','replace')
(H/'route-deduplication-proof-r948.json').write_bytes(enc({**json.loads(actual.stdout),'compiledSourceSHA256':sha(compiled)}))
runner=(OLD/'run_ledger_lifecycle_r946.py').read_text('utf8').replace('ledgerfull-r946','ledgerfull-r948').replace('resume-r946','resume-r948').replace('ledger-source-pins-r946.json','ledger-source-pins-r948.json').replace('verified-ledger-ui-r946.json','verified-ledger-ui-r948.json').replace('ledger-ui-full-result-r946.json','ledger-ui-full-result-r948.json')
(H/'run_ledger_lifecycle_r948.py').write_text(runner,encoding='utf8')
health=(OLD/'home_transfer_health_r906.py').read_text('utf8').replace('ledger-source-pins-r946.json','ledger-source-pins-r948.json');(H/'home_transfer_health_r906.py').write_text(health,encoding='utf8')
probe=(OLD/'home_transfer_probe_r906.py').read_text('utf8').replace('ledger-source-pins-r946.json','ledger-source-pins-r948.json').replace('ledger-browser-r946','ledger-browser-r948').replace('resume-r946','resume-r948')
probe=once(probe,"mode='readback'","mode='repair-root'if label=='first-start'else'readback'")
probe=once(probe,"'metadata-'+mode+'-r946-'+label","'metadata-'+mode+'-r948-'+label")
probe=once(probe,"metadata['persistentWritesIssued']=='false'","metadata['persistentWritesIssued']==str(label=='first-start').lower()")
(H/'home_transfer_probe_r906.py').write_text(probe,encoding='utf8')
java=(OLD/'OwnLedgerMetadataR940.java').read_text('utf8')
java=once(java,'need(a.length==6&&a[4].equals("readback")&&Set.of("first-start","normal-restart").contains(a[5]),"EXACT_EXISTING_LEDGER_METADATA_READONLY_ARGUMENTS");','need(a.length==6&&Set.of("repair-root","readback").contains(a[4])&&Set.of("first-start","normal-restart").contains(a[5])&&a[4].equals(a[5].equals("first-start")?"repair-root":"readback"),"EXACT_ONE_OWN_ROOT_REPAIR_OR_READBACK_ARGUMENTS");boolean repair=a[4].equals("repair-root");')
java=once(java,'"-r946-"','"-r948-"')
java=once(java,'"f_path","/hiddenInvestigate","f_url_address"','"f_path",repair?"/hiddenInvestigate":"/own-ledger-r941","f_url_address"')
java=once(java,'c.setReadOnly(true);','c.setReadOnly(!repair);')
java=once(java,'   try{\n    if(prepare)', '''   Path repairJournal=ROOT.resolve("ledger-root-placement-r948.private.properties");Properties repairState=new Properties();
   if(repair){need(!Files.exists(repairJournal),"NO_REPLAY_OF_ROOT_METADATA_REPAIR");for(var e:before.entrySet())need(e.getValue().equals(state.getProperty("otherRowsSHA256."+e.getKey())),"ORIGINAL_OTHER_METADATA_BEFORE_REPAIR");repairState.setProperty("phase","single-owned-root-path-update-intent");repairState.setProperty("rowId",id(100100));repairState.setProperty("beforePath","/hiddenInvestigate");repairState.setProperty("afterPath","/own-ledger-r941");save(repairJournal,repairState);}
   else{try(InputStream in=Files.newInputStream(repairJournal)){repairState.load(in);}need("committed-readback-verified".equals(repairState.getProperty("phase")),"EXACT_PRIOR_ROOT_REPAIR_COMMIT_REQUIRED");}
   try{
    if(repair){try(PreparedStatement patch=c.prepareStatement("UPDATE jnpf.base_module SET f_path=? WHERE f_id=? AND f_path=?")){patch.setString(1,"/own-ledger-r941");patch.setString(2,id(100100));patch.setString(3,"/hiddenInvestigate");need(patch.executeUpdate()==1,"ONLY_THE_ONE_OWN_ROOT_PATH_CHANGED");}wanted.get("base_module").get(id(100100)).put("f_path","/own-ledger-r941");}
    if(prepare)''')
java=once(java,'    c.commit();','    c.commit();if(repair){repairState.setProperty("phase","committed-readback-verified");repairState.setProperty("onlyOneOwnMetadataPathChanged","true");save(repairJournal,repairState);}')
java=once(java,'Boolean.toString(prepare)','Boolean.toString(repair)')
(H/'OwnLedgerMetadataR940.java').write_text(java,encoding='utf8')
js=(OLD/'verify_ledger_ui_r940.mjs').read_text('utf8').replace('ledger-browser-r946','ledger-browser-r948')
(H/'verify_ledger_ui_r940.mjs').write_text(js,encoding='utf8')
(H/'owned_ready_observation_r924.py').write_bytes((OLD/'owned_ready_observation_r924.py').read_bytes())
for p in H.glob('*.py'):ast.parse(p.read_text('utf8'))
assert subprocess.run(['node','--check',str(H/'verify_ledger_ui_r940.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
jobs=load('ledger_root_compile_jobs_r948',G/'tools/original_server_windows_job.py');budget=load('ledger_root_compile_budget_r948',A/'tools/bounded_build_job_r671.py')
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>1024**3
with(H/'compile.private.log').open('xb')as out:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(H/'OwnLedgerMetadataR940.java')],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);limit=budget.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':limit.metrics()};job.close()
assert p.returncode==0
(H/'metadata-compile-proof.json').write_bytes(enc({'passed':True,'sourceSHA256':sha(H/'OwnLedgerMetadataR940.java'),'classSHA256':sha(H/'classes/OwnLedgerMetadataR940.class'),'terminal':terminal}))
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
(H/'ledger-source-pins-r948.json').write_bytes(enc({'candidatePlanSHA256':J(OLD/'ledger-source-pins-r946.json')['candidatePlanSHA256'],'files':pins}))
out={'prepared':True,'actualCompiledRouteDeduplicationReproduced':True,'oneExactNewSyntheticRootPathCorrectionPrepared':True,'noAccountRoleSchemaOrOriginalMetadataChangePrepared':True,'normalRestartReadbackOnly':True,'priorFailuresRetained':True,'productR47PackageUnchanged':True,'servicesStarted':False}
(H/'prepared-r948.json').write_bytes(enc(out));print(json.dumps(out))
