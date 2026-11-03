from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';D=R/'Document/Deployment/original_mapper_product_suite_r266_20261103';assert not D.exists();D.mkdir();pins={}
def save(name,s):
 p=T/name;assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8',newline='\n');pins[name]=hashlib.sha256(p.read_bytes()).hexdigest()
patch='''from pathlib import Path
import argparse,hashlib,json,subprocess,os,importlib.util
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\\n').encode()
p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','restore']);p.add_argument('--attempt',required=True,choices=['r131','r132']);o=p.parse_args();P=C/('prepared-'+o.attempt)
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
query="(Get-CimInstance Win32_Process -Filter \\\"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='minio.exe' OR Name='chrome.exe' OR Name='nginx.exe' OR Name='redis-server.exe'\\\" | Where-Object {($_.CommandLine -replace '\\\\\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
s=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30);assert s.returncode==0 and s.stdout.decode('utf-8-sig').strip()=='0'
if o.action=='prepare':
 assert not(C/o.attempt).exists()and not(P/'mapper-product-scope.json').exists()
 before={n:(A/n).read_bytes()for n in ['tools/original_server_release_parameters.py','tools/original_public_test_update.py','payload-manifest.json','release-manifest.json']}
 assert hashlib.sha256(before['tools/original_server_release_parameters.py']).hexdigest()=='8ca02e5e99c0b0c1aae282889ceca6c9f31c9ee0f2cd4750e506a25c6267c106'
 source=T/'original_public_test_update_mapper_runtime_r265.py';spec=importlib.util.spec_from_file_location('mapper_product',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 parameter=T/'original_server_release_parameters_r263_mapper_default.py';assert sha(parameter)==m.R38_PARAMETER_PIN['sha256']
 after={'tools/original_server_release_parameters.py':parameter.read_bytes(),'tools/original_public_test_update.py':source.read_bytes()};q=J(A/'payload-manifest.json');release=J(A/'release-manifest.json')
 for n,b in after.items():
  release['controllerFiles'][n]=hashlib.sha256(b).hexdigest()
  if n in q['files']:q['files'][n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 release[m.R38_MAPPER_FIELD]=m.R38_MAPPER_CONTRACT;release[m.R24_WORKFLOW_FIELD]=m.workflow_contract_for(release);assert m.workflow_declared(release,q)and m.runtime_pool_declared(release)
 after['payload-manifest.json']=enc(q);release['payloadManifestSHA256']=hashlib.sha256(after['payload-manifest.json']).hexdigest();after['release-manifest.json']=enc(release)
 scope={'onlyOwnedStoppedSyntheticFixture':True,'exactProductParameterSourceExecuted':True,'oldFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in before.items()},'newFiles':{n:{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}for n,b in after.items()},'runtimeAdapterOnlyChangesDeclarations':True,'publicTransportContractAvailable':False,'privateConfigurationChangedByProductPatch':False}
 for n,b in before.items():p=P/'mapper-product-before'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 (P/'mapper-product-scope.json').write_bytes(enc(scope))
 for n,b in after.items():p=A/n;assert p.resolve()==p and not p.lstat().st_file_attributes&0x400;p.unlink();p.write_bytes(b)
 ready=J(P/'controller-fixture-ready.json');ready.update(releaseSHA256=sha(A/'release-manifest.json'),updaterSHA256=sha(A/'tools/original_public_test_update.py'));(P/'controller-fixture-ready.json').write_bytes(enc(ready));print(json.dumps({'prepared':True,'exactR263ParameterAndRuntimeDeclarationsInstalled':True,'allOriginalSQLAndJarAndAuthKept':True}))
else:
 t=J(C/o.attempt/'controller-terminal.json');outer=J(C/(o.attempt+'-outer-terminal.json'));receipt=J(C/o.attempt/'scoped-controller-receipt.json');assert t['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 scope=J(P/'mapper-product-scope.json')
 for n,pin in scope['newFiles'].items():assert sha(A/n)==pin['sha256'],'FOREIGN_DRIFT_REFUSE_PRODUCT_RESTORE'
 for n,pin in scope['oldFiles'].items():assert sha(P/'mapper-product-before'/n)==pin['sha256']
 for n in scope['oldFiles']:
  p=A/n;tmp=p.with_name(p.name+'.own-r266-product-restore.tmp');assert not tmp.exists();tmp.write_bytes((P/'mapper-product-before'/n).read_bytes());os.replace(tmp,p)
 assert all(sha(A/n)==pin['sha256']for n,pin in scope['oldFiles'].items())
 proof={'passed':True,'exactProductParameterUpdaterAndManifestBytesRestored':True,'actualDescendantsZeroBeforeRestore':True,'configurationDatabaseOrSQLRewritten':False};(P/'mapper-product-restored.json').write_bytes(enc(proof));print(json.dumps(proof))
'''
save('mapper_product_patch_r266.py',patch)
support=(T/'mapper_observation_support_r260.py').read_text(encoding='utf-8').replace('r129','r131').replace('r130','r132')
line=" if o.attempt=='r132':business['mybatis-plus.mapper-locations']='classpath*:/xml/**/*.xml'\n";assert support.count(line)==1;support=support.replace(line,'')
save('mapper_observation_support_r266.py',support)
for stem in ['prepare_production_history_runtime','restore_production_history_runtime','prepare_personal_workflow_frontend','restore_personal_workflow_frontend']:
 save(stem+'_r266.py',(T/(stem+'_r260_candidate.py')).read_text(encoding='utf-8').replace('r130','r131').replace('r260_candidate','r266'))
host=(T/'verify_full_controller_mapper_r260_candidate.py').read_text(encoding='utf-8').replace('r130','r131')
a="observer_scope=read(prepared_base/'mapper-observer-scope.json');assert observer_scope['onlyOwnedStoppedSyntheticFixture']";assert host.count(a)==1
host=host.replace(a,a+"\nproduct_scope=read(prepared_base/'mapper-product-scope.json');assert product_scope['exactProductParameterSourceExecuted']\nfor n,pin in product_scope['newFiles'].items():\n    if n not in ['payload-manifest.json','release-manifest.json']:assert sha(app/n)==pin['sha256']\ncfg=read(app/'private/server-configuration.json');assert not any('mapper'in k.lower()and'location'in k.lower()for k in cfg['configuration']['business']);cfg=None")
a="observer_scope['newFiles'].get(n,pin)['sha256']";assert host.count(a)==1;host=host.replace(a,"observer_scope['newFiles'].get(n,product_scope['newFiles'].get(n,pin))['sha256']")
host=host.replace("'schema':'xnby.r260.actual-mapper-observation.v1'","'schema':'xnby.r266.actual-product-mapper-runtime.v1','actualR263ParameterFileUsedWithoutExplicitMapperSetting':True,'publicTransportContractProven':False")
save('verify_full_controller_mapper_product_r266.py',host)
runner=(T/'run_mapper_observation_r260_candidate.py').read_text(encoding='utf-8').replace('r130','r131').replace('verify_full_controller_mapper_r260_candidate','verify_full_controller_mapper_product_r266').replace('restore_personal_workflow_frontend_r260_candidate','restore_personal_workflow_frontend_r266').replace('restore_production_history_runtime_r260_candidate','restore_production_history_runtime_r266').replace("V/'mapper_observation_support_r260.py'","V/'mapper_observation_support_r266.py'")
anchor='restored=subprocess.run';assert runner.count(anchor)==1;runner=runner.replace(anchor,"product=subprocess.run([sys.executable,str(V/'mapper_product_patch_r266.py'),'restore','--attempt',attempt],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert product.returncode==0 and json.loads(product.stdout)['passed'],'OWN_PRODUCT_PARAMETER_RESTORE_REFUSED'\n"+anchor)
save('run_mapper_product_r266.py',runner)
(D/'preparation.json').write_text(json.dumps({'sources':pins,'attempt':'r131','actualProductParameterFile':True,'explicitMapperConfigurationAbsentRequired':True,'originalSQLJarOrAuthChanged':False,'publicTransportContractProven':False},indent=2)+'\n',encoding='utf-8');print(json.dumps({'sources':len(pins),'attempt':'r131','exactProductDefaultWillRun':True,'explicitMapperValueNotInjectedByTest':True}))
