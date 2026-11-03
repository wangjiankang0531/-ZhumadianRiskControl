from pathlib import Path
import ast,json,hashlib,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';D=R/'Document/Deployment/original_mapper_product_task_r270_20261103';assert not D.exists();D.mkdir();pins={}
def save(name,s):
 p=T/name;assert not p.exists()
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8',newline='\n');pins[name]=hashlib.sha256(p.read_bytes()).hexdigest()
patch=(T/'mapper_product_patch_r266.py').read_text(encoding='utf-8').replace('mapper_runtime_r265.py','mapper_runtime_r268.py').replace('own-r266-product-restore','own-r270-product-restore')
save('mapper_product_patch_r270.py',patch)
for stem in ['prepare_production_history_runtime','restore_production_history_runtime','prepare_personal_workflow_frontend','restore_personal_workflow_frontend']:
 save(stem+'_r270.py',(T/(stem+'_r252.py')).read_text(encoding='utf-8').replace('r122','r132').replace('r252','r270'))
save('configure_owned_parallel_gateway_r270.py',(T/'configure_owned_parallel_gateway_r250.py').read_text(encoding='utf-8').replace('r121','r132'))
save('OwnPersonalWorkflowMenuVisibilityR270.java',(T/'OwnPersonalWorkflowMenuVisibilityR252.java').read_text(encoding='utf-8').replace('R252','R270').replace('r122','r132'))
save('verify_native_task_attachment_r270_20261103.mjs',(T/'verify_native_task_attachment_r252_20261103.mjs').read_text(encoding='utf-8'))
host=(T/'verify_full_controller_task_attachment_r252_20261103.py').read_text(encoding='utf-8').replace('r121','r132').replace('r122','r132').replace('r252','r270').replace('R252','R270')
anchor="history_scope=read(prepared_base/'history-runtime-scope.json');assert history_scope['onlyOwnedSyntheticG']";assert host.count(anchor)==1
host=host.replace(anchor,anchor+"\nobserver_scope=read(prepared_base/'mapper-observer-scope.json');product_scope=read(prepared_base/'mapper-product-scope.json');assert observer_scope['onlyOwnedStoppedSyntheticFixture']and product_scope['exactProductParameterSourceExecuted']\nfor n,pin in product_scope['newFiles'].items():\n    if n not in ['payload-manifest.json','release-manifest.json']:assert sha(app/n)==pin['sha256']\ncfg=read(app/'private/server-configuration.json');assert not any('mapper'in k.lower()and'location'in k.lower()for k in cfg['configuration']['business']);cfg=None")
anchor="if n not in ['payload-manifest.json','release-manifest.json']:assert sha(app/n)==pin['sha256']";assert host.count(anchor)==2
start=host.index("for n,pin in history_scope['newFiles'].items():");end=host.index('frontend_scope=',start)
block=host[start:end].replace("sha(app/n)==pin['sha256']","sha(app/n)==observer_scope['newFiles'].get(n,product_scope['newFiles'].get(n,pin))['sha256']")
host=host[:start]+block+host[end:]
anchor="        checks['productionNativeServiceGateInstalled']=True";assert host.count(anchor)==1
observation="""
        phase='observe-actual-product-default-mapper-registration'
        report_path=Path(row['run'])/'b/own-mapper-observation.json';until=time.monotonic()+20
        while not report_path.exists():
            assert time.monotonic()<until and process.poll()is None,'OWN_MAPPER_OBSERVATION_NOT_READY';time.sleep(.1)
        mapper_report=read(report_path);assert mapper_report['actualApplicationReadySpringFactoryObservation']and mapper_report['originalXMLResources']==96 and mapper_report['expectedOriginalXMLStatements']==226 and mapper_report['allFactoriesHaveEveryOriginalXMLStatement']and not mapper_report['SQLExecutedOrConfigurationRegistrationMutatedByObserver']
        dump(root/'actual-mapper-registration.json',mapper_report);checks['actualAllOriginalXMLStatementsRegistered']=True
"""
host=host.replace(anchor,anchor+observation)
host=host.replace("'schema':'xnby.r270.task-attachment-candidate-regression.v1'","'schema':'xnby.r270.product-mapper-and-task-regression.v1','actualProductParameterAndFinalRuntimeAdapterUsed':True,'actualAll226OriginalXMLStatementsRegistered':True,'publicTransportContractProven':False")
save('verify_full_controller_mapper_task_r270.py',host)
runner=(T/'run_task_attachment_r252_20261103.py').read_text(encoding='utf-8').replace('r122','r132').replace('r252','r270').replace('verify_full_controller_task_attachment_r270_20261103','verify_full_controller_mapper_task_r270')
anchor='restored=subprocess.run';assert runner.count(anchor)==1
restore="mapper=subprocess.run([sys.executable,str(V/'mapper_observation_support_r266.py'),'restore','--attempt',attempt],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert mapper.returncode==0 and json.loads(mapper.stdout)['passed'],'OWN_OBSERVER_RESTORE_REFUSED'\nproduct=subprocess.run([sys.executable,str(V/'mapper_product_patch_r270.py'),'restore','--attempt',attempt],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert product.returncode==0 and json.loads(product.stdout)['passed'],'OWN_PRODUCT_PARAMETER_RESTORE_REFUSED'\n"
runner=runner.replace(anchor,restore+anchor);save('run_mapper_product_task_r270.py',runner)
node=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(T/'verify_native_task_attachment_r270_20261103.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert node.returncode==0
(D/'preparation.json').write_text(json.dumps({'sources':pins,'attempt':'r132','actualProductParameterSource':'original_server_release_parameters_r263_mapper_default.py','actualRuntimeAdapter':'original_public_test_update_mapper_runtime_r268.py','originalNinePhaseTaskAndParallelWorkflowKept':True,'noExplicitMapperSettingInjected':True,'publicTransportContractProven':False},indent=2)+'\n',encoding='utf-8');print(json.dumps({'sources':len(pins),'attempt':'r132','finalRuntimeDeclarationsAndNineNativePhasesPrepared':True}))
