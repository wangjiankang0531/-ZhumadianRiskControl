"""Prepare exact synthetic navigation metadata and a fresh full-app retry.

The failed R906 output and journals remain immutable. Same four frontend bytes.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application'
OLD=V/'home_full_r905';H=V/'home_full_r909';D=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not H.exists() and not(R/'work/hf910').exists()
prior=J(R/'work/hf906/verified-home-transfer-r906.json')
assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and set(t['exitCodes'].values())=={0}for t in prior['terminals'])
def change(s,a,b):assert s.count(a)>=1,(a,s.count(a));return s.replace(a,b)
H.mkdir();(H/'classes').mkdir()
for name in ['home_transfer_health_r906.py','home_transfer_gateway_r906.py','home_transfer_probe_r906.py','run_home_transfer_full_r906.py','verify_home_transfer_browser_r906.mjs']:
 s=(OLD/name).read_text('utf8');s=s.replace('home-transfer-source-pins-r906.json','home-transfer-source-pins-r910.json')
 s=s.replace("P=O/'home-transfer-r906';Z=R/'work/hf906'","P=O/'home-transfer-r910';Z=R/'work/hf910'")
 s=s.replace('original-manager-full-lifecycle-r609/home-transfer-r906','original-manager-full-lifecycle-r609/home-transfer-r910')
 s=s.replace('D:/Project/Zhumadian/work/home-browser-r906','D:/Project/Zhumadian/work/home-browser-r910').replace("OUT=R/'work/home-browser-r906'","OUT=R/'work/home-browser-r910'")
 s=s.replace("O=Path('D:/Project/Zhumadian/work/hf906')","O=Path('D:/Project/Zhumadian/work/hf910')")
 s=s.replace('verified-home-transfer-r906.json','verified-home-transfer-r910.json').replace('home-transfer-full-result-r906.json','home-transfer-full-result-r910.json')
 if name=='run_home_transfer_full_r906.py':
  s=change(s,"prior=J(R/'work/fb889/verified-feedback-chain-r889.json')","prior=J(R/'work/hf906/verified-home-transfer-r906.json')")
  s=change(s,"assert prior['passed']and prior['codeRestored']and prior['taskConfigurationRestoredBeforeCode']and prior['originalCurrentPointerRestored']","assert not prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']")
 if name=='home_transfer_probe_r906.py':
  marker='    env={k:v for k,v in os.environ.items()if k.upper()not in'
  assert s.count(marker)==1
  # Place the separate synthetic-metadata process after env construction.
  after="    with(stage/'browser.private.log').open('xb')as out:"
  addition='''    fixtureSource=Path(__file__).resolve().parent/'classes/OwnHomeNavigationFixtureR909.class'
    compileProof=J(Path(__file__).resolve().parent/'fixture-compile-proof.json')
    assert compileProof['passed']and hashlib.sha256(fixtureSource.read_bytes()).hexdigest()==compileProof['classSHA256']
    connector=G/'payload/business/lib/mysql-connector-j-8.0.33.jar'
    expectedConnector=J(G/'payload-manifest.json')['files'][connector.relative_to(G).as_posix()]
    assert connector.stat().st_size==expectedConnector['bytes']and hashlib.sha256(connector.read_bytes()).hexdigest()==expectedConnector['sha256']
    journal=P/'home-navigation-journal.private.properties';metadata=P/'home-navigation-result.private.properties'
    assert not journal.exists()and not metadata.exists()
    command=[str(G/'runtime/jdk17/bin/java.exe'),'-Xmx128m','-cp',str(fixtureSource.parent)+os.pathsep+str(connector),'OwnHomeNavigationFixtureR909',str(row['databasePort']),row['databaseUUID'],str(G/'UserData/OriginalServer/database/data'),str(journal),str(metadata)]
    with(stage/'home-metadata.private.log').open('xb')as out:
        fixtureProc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=out,stderr=subprocess.STDOUT,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
        fixtureChild={'process':fixtureProc,'job':None};CHILDREN.append(fixtureChild)
        fixtureChild['job']=jobs.OwnedWindowsJob(fixtureProc);fixtureBudget=budget.BoundedBuildJob(fixtureChild['job'],512*1024**2)
        fixtureProc.communicate(input=(wire['password']+'\\n').encode('ascii'))
        while fixtureChild['job'].active_processes():time.sleep(.1)
        fixtureTerminal={'exitCode':fixtureProc.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':fixtureBudget.metrics()};fixtureChild['job'].close()
    (stage/'home-metadata-terminal.json').write_text(json.dumps(fixtureTerminal,indent=2)+'\\n',encoding='utf8')
    assert fixtureProc.returncode==0,'EXACT_OWN_HOME_METADATA_PREPARATION_FAILED'
    checked=props(metadata);assert checked['phase']=='readback-verified'and checked['allOtherMetadataDigestsMatched']=='true'and checked['accountsRolesBusinessTablesAndSchemaWritten']=='false'
'''
  s=s.replace(after,addition+after)
 if name.endswith('.mjs'):
  s=change(s,'||!state.overlay||state.cards!==3)','||!state.overlay||state.cards!==3)') if False else s
  marker="  if(state.title!=='驻马店重大风险防控'"
  assert marker in s
  # Assert the actual original API now supplies all eight scoped navigation entries.
  target=" stage='original-security-home-render';await homeCheck();"
  s=change(s,target,target+"\n if(!await evaluate('document.querySelectorAll(\".menu-item\").length===8'))throw Error('EIGHT_ORIGINAL_HOME_NAVIGATION_ENTRIES_REQUIRED');")
 (H/name).write_text(s,encoding='utf8')
source=V/'OwnHomeNavigationFixtureR909.java'
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
jobSource=G/'tools/original_server_windows_job.py';assert sha(jobSource)=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
jobs=load('home_compile_jobs_r909',jobSource);policy=load('home_compile_budget_r909',A/'tools/bounded_build_job_r671.py')
snap=policy.memory_snapshot();assert snap['availablePhysicalBytes']>1024**3 and snap['availableCommitBytes']>1024**3
with(H/'fixture-compile.private.log').open('xb')as log:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(source)],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);cap=policy.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':cap.metrics()};job.close()
assert p.returncode==0,'OWN_HOME_FIXTURE_COMPILE_FAILED'
compiled=H/'classes/OwnHomeNavigationFixtureR909.class'
(H/'fixture-compile-proof.json').write_text(json.dumps({'passed':True,'sourceSHA256':sha(source),'classSHA256':sha(compiled),'terminal':terminal},indent=2)+'\n',encoding='utf8')
files=[*H.glob('*.py'),H/'verify_home_transfer_browser_r906.mjs',source,compiled,H/'fixture-compile-proof.json']
for p in H.glob('*.py'):ast.parse(p.read_bytes(),filename=p.name)
assert subprocess.run(['node','--check',str(H/'verify_home_transfer_browser_r906.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
pins={'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':{str(p):sha(p)for p in files},'normalOriginalSDKStillPending':True,'onlyOwnSyntheticNavigationMetadataMayBeInserted':True}
(H/'home-transfer-source-pins-r910.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':True,'fixtureCompiled':True,'possibleSyntheticMetadataRows':33,'databaseConnectedYet':False,'classJobExitCode':terminal['exitCode']}))
