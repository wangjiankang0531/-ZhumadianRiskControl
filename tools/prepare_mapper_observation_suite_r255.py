from pathlib import Path
import ast,hashlib,json,subprocess,os
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools';V=Path(__file__).parent
D=R/'Document/Deployment/original_mapper_registration_r255_20261103';assert not D.exists();D.mkdir()
pins={}
def save(name,s):
 p=T/name;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8',newline='\n');pins[name]=hashlib.sha256(p.read_bytes()).hexdigest()
def swap(s,a,b):assert s.count(a)==1,(a[:80],s.count(a));return s.replace(a,b)
save('java/mapper_observation_r255/OwnMapperRegistrationObservationR255.java',(V/'OwnMapperRegistrationObservationR255.java').read_text(encoding='utf-8'))
classes=D/'classes';classes.mkdir();cp=';'.join(map(str,[A/'payload/business/run-template/classes',A/'payload/business/application.jar',*sorted((A/'payload/business/lib').glob('*.jar'))]))
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
p=subprocess.run([str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(classes),str(T/'java/mapper_observation_r255/OwnMapperRegistrationObservationR255.java')],capture_output=True,env=env,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
(D/'compile.private.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0,'OBSERVER_COMPILE_FAILED'
compiled=list(classes.rglob('*.class'));assert len(compiled)==1
support='''from pathlib import Path
import argparse,hashlib,json,subprocess,os
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_mapper_registration_r255_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\\n').encode()
p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','restore']);p.add_argument('--attempt',required=True,choices=['r123','r124']);o=p.parse_args();P=C/('prepared-'+o.attempt)
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
cmd="(Get-CimInstance Win32_Process -Filter \\\"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\\\" | Where-Object {($_.CommandLine -replace '\\\\\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
r=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30);assert r.returncode==0 and r.stdout.decode('utf-8-sig').strip()=='0'
classrel='payload/business/run-template/classes/xnby/own/OwnMapperRegistrationObservationR255.class'
if o.action=='prepare':
 assert not(C/o.attempt).exists()and not(P/'mapper-observer-scope.json').exists()and not(A/classrel).exists()
 before={n:(A/n).read_bytes()for n in ['private/server-configuration.json','payload-manifest.json','release-manifest.json']}
 cfg=J(A/'private/server-configuration.json');business=cfg['configuration']['business'];key='context.initializer.classes';initializer='xnby.own.OwnMapperRegistrationObservationR255';old=business.get(key,'');assert initializer not in old
 business[key]=','.join([x for x in old.split(',')if x]+[initializer])
 mapper_keys=[x for x in business if 'mapper' in x.lower()and'location' in x.lower()];assert not mapper_keys,'EXPLICIT_MAPPER_CONFIGURATION_MUST_NOT_BE_OVERWRITTEN'
 if o.attempt=='r124':business['mybatis-plus.mapper-locations']='classpath*:/xml/**/*.xml'
 after={'private/server-configuration.json':enc(cfg),classrel:(D/'classes/xnby/own/OwnMapperRegistrationObservationR255.class').read_bytes()};q=J(A/'payload-manifest.json');release=J(A/'release-manifest.json')
 for n,b in after.items():q['files'][n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 after['payload-manifest.json']=enc(q);release['payloadManifestSHA256']=hashlib.sha256(after['payload-manifest.json']).hexdigest();after['release-manifest.json']=enc(release)
 scope={'onlyOwnedStoppedSyntheticFixture':True,'observerOnlyOrCandidateSetting':o.attempt,'oldFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in before.items()},'newFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in after.items()},'newPaths':[classrel],'originalJarSQLAndDatasourceAndSchemaChanged':False}
 for n,b in before.items():p=P/'mapper-observer-before'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 (P/'mapper-observer-scope.json').write_bytes(enc(scope))
 for n,b in after.items():
  p=A/n;assert p.resolve()==p and not p.is_symlink();p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert not p.lstat().st_file_attributes&0x400;p.unlink()
  p.write_bytes(b)
 baseline=J(P/'controller-fixture-ready.json');baseline['releaseSHA256']=sha(A/'release-manifest.json');(P/'controller-fixture-ready.json').write_bytes(enc(baseline));print(json.dumps({'prepared':True,'mode':o.attempt,'onlyOwnSyntheticConfigurationAndObserverClass':True,'allOriginalControllerJarAndSQLBytesKept':True}))
else:
 t=J(C/o.attempt/'controller-terminal.json');outer=J(C/(o.attempt+'-outer-terminal.json'));receipt=J(C/o.attempt/'scoped-controller-receipt.json');assert t['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 scope=J(P/'mapper-observer-scope.json')
 for n,pin in scope['newFiles'].items():assert sha(A/n)==pin['sha256'],'FOREIGN_DRIFT_REFUSE_RESTORE'
 for n,pin in scope['oldFiles'].items():assert sha(P/'mapper-observer-before'/n)==pin['sha256']
 for n in scope['newPaths']:(A/n).unlink()
 for n in scope['oldFiles']:
  p=A/n;tmp=p.with_name(p.name+'.own-r255-restore.tmp');assert not tmp.exists();tmp.write_bytes((P/'mapper-observer-before'/n).read_bytes());os.replace(tmp,p)
 assert all(sha(A/n)==pin['sha256']for n,pin in scope['oldFiles'].items())and all(not(A/n).exists()for n in scope['newPaths'])
 proof={'passed':True,'originalConfigAndManifestsRestored':True,'onlyOwnObserverClassRemoved':True,'normalAllComponentsAndActualDescendantsZero':True,'businessDataOrSchemaChangedByRestore':False};(P/'mapper-observer-restored.json').write_bytes(enc(proof));print(json.dumps(proof))
'''
save('mapper_observation_support_r255.py',support)
for mode,attempt in [('baseline','r123'),('candidate','r124')]:
 for stem in ['prepare_production_history_runtime','restore_production_history_runtime']:
  save(stem+'_r255_'+mode+'.py',(T/(stem+'_r252.py')).read_text(encoding='utf-8').replace('r122',attempt).replace('r252','r255_'+mode))
 if mode=='candidate':
  for stem in ['prepare_personal_workflow_frontend','restore_personal_workflow_frontend']:
   save(stem+'_r255_candidate.py',(T/(stem+'_r252.py')).read_text(encoding='utf-8').replace('r122',attempt).replace('r252','r255_candidate'))
 host=(T/'verify_full_controller_plan_exercise_r245_20261103.py').read_text(encoding='utf-8')
 host=swap(host,"plan_mapper_scope=read(prepared_base/'plan-mapper-scope.json');assert plan_mapper_scope['onlyOwnedStoppedSyntheticFixture']", "observer_scope=read(prepared_base/'mapper-observer-scope.json');assert observer_scope['onlyOwnedStoppedSyntheticFixture']")
 host=swap(host,"plan_mapper_scope['newFiles'].get(n,pin['sha256'])", "observer_scope['newFiles'].get(n,pin)['sha256']")
 host=swap(host,"        checks['exactDeclaredOriginalPlanXMLRuntimePinsPassed']=m.plan_mapper_ready(app,row)is not None\n        assert checks['exactDeclaredOriginalPlanXMLRuntimePinsPassed']\n",'')
 observation="""        phase='observe-actual-original-mapper-registration'
        report_path=Path(row['run'])/'b/own-mapper-observation.json';until=time.monotonic()+20
        while not report_path.exists():
            assert time.monotonic()<until and process.poll()is None,'OWN_MAPPER_OBSERVATION_NOT_READY';time.sleep(.1)
        mapper_report=read(report_path);assert mapper_report['actualApplicationReadySpringFactoryObservation']and mapper_report['originalXMLResources']==96 and not mapper_report['SQLExecutedOrConfigurationRegistrationMutatedByObserver']
        dump(root/'actual-mapper-registration.json',mapper_report)
"""
 host=swap(host,"        phase='seed-only-own-resource-menus'",observation+"        phase='seed-only-own-resource-menus'")
 if mode=='baseline':
  start=host.index("frontend_scope=read(prepared_base/'frontend-scope.json')");end=host.index('for name,key in ',start);host=host[:start]+host[end:]
  start=host.index("        phase='native-normal-plan-exercise-browser'");end=host.index("        phase='verify-original-398-models'",start)
  host=host[:start]+"        browser_passed=True;browser_result={'cases':[]};fake_password=None;checks['mapperObservationOnlyNoBrowserAcceptanceClaimed']=True\n"+host[end:]
  host=host.replace("checks['actualNormalPlanExerciseBrowserResultPassed']=True","checks['normalBrowserAcceptanceClaimed']=False")
 else:
  host=host.replace("['r119','r120']","['r124']").replace("options.attempt=='r119'","options.attempt=='r123'")
  host=swap(host,"        dump(root/'actual-mapper-registration.json',mapper_report)","        dump(root/'actual-mapper-registration.json',mapper_report)\n        assert mapper_report['allFactoriesHaveEveryOriginalXMLStatement'],'ORIGINAL_XML_RUNTIME_STATEMENTS_MISSING'")
 begin=host.index("proof={'schema':'xnby.r245.native-plan-exercise-regression.v1'");end=host.index("\ndump(root/'result.json',proof)",begin)
 host=host[:begin]+"proof={'schema':'xnby.r255.actual-mapper-observation.v1','allPassed':True,'mode':'"+mode+"','nativeBrowserCases':len(browser_result['cases']),'actualMapperRegistration':mapper_report,'sixComponentsNormalZeroActualDescendantsZero':True,'original398ModelsUnchanged':True,'connectionCapacityWithoutRefusals':True,'publicFormalOrDesktopChanged':False,'originalNangangWholeAcceptanceClaimed':False,'fullCloneReady':False}\n"+host[end:]
 save('verify_full_controller_mapper_r255_'+mode+'.py',host)
 runner=(T/'run_task_attachment_r252_20261103.py').read_text(encoding='utf-8').replace('r122',attempt).replace('verify_full_controller_task_attachment_r252_20261103','verify_full_controller_mapper_r255_'+mode).replace('restore_production_history_runtime_r252','restore_production_history_runtime_r255_'+mode)
 start=runner.index('frontend=subprocess.run');end=runner.index('restored=subprocess.run',start)
 frontend=''
 if mode=='candidate':frontend=runner[start:end].replace('restore_personal_workflow_frontend_r252','restore_personal_workflow_frontend_r255_candidate')
 observer="mapper=subprocess.run([sys.executable,str(V/'mapper_observation_support_r255.py'),'restore','--attempt',attempt],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert mapper.returncode==0 and json.loads(mapper.stdout)['passed'],'OWN_OBSERVER_RESTORE_REFUSED'\n"
 runner=runner[:start]+frontend+observer+runner[end:]
 save('run_mapper_observation_r255_'+mode+'.py',runner)
(D/'preparation.json').write_text(json.dumps({'sources':pins,'baselineAttempt':'r123','candidateAttempt':'r124','compiledObserverClassSHA256':hashlib.sha256(compiled[0].read_bytes()).hexdigest(),'originalJarSQLOrRuntimeControlBytesChanged':False,'candidateOnlyTemporaryMapperLocationSetting':True,'newProductDeployment':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preparedSources':len(pins),'observerCompiled':True,'actualContainersNotYetRun':True,'baseline':'r123','candidate':'r124'}))
