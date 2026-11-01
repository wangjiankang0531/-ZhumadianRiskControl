from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools';V=Path(__file__).parent;D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101';out=T/'connection-budget-r136';assert not out.exists();out.mkdir()
release=json.loads((A/'release-manifest.json').read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest();policy=(V/'original_connection_pool_policy_r136_20261101.py').read_text(encoding='utf-8');ast.parse(policy)
(T/'original_connection_pool_policy_r136_20261101.py').write_text(policy,encoding='utf-8',newline='\n')
changes={}
for name in ['original_server_release_parameters.py','serve_original_server_release.py']:
    raw=(A/'tools'/name).read_bytes();assert sha(raw)==release['controllerFiles']['tools/'+name];s=raw.decode('utf-8')
    if name.startswith('original_server'):
        a='def materialize(';assert s.count(a)==1;s=s.replace(a,policy+'\n\n'+a)
        a="    values={k:render(v) for k,v in spec['configuration'][side].items()}";assert s.count(a)==1;s=s.replace(a,a+"\n    values.update(runtime_pool_properties(spec,side))")
    else:
        a='from original_server_release_parameters import materialize, runtime_temporary_path';assert s.count(a)==1;s=s.replace(a,a+', connection_pool_budget')
        a='    config=configure_platform(release,config,callback_enabled=callback is not None)';assert s.count(a)==1;s=s.replace(a,a+'\n    connection_budget=connection_pool_budget(config)')
        a="'--max-connections=24'";assert s.count(a)==1;s=s.replace(a,"'--max-connections='+str(connection_budget['mysqlMaxConnections'])")
        a="    run=runs/('j'+str(number));run.mkdir();business=run/'b';business.mkdir();owner=str(uuid.uuid4())";assert s.count(a)==1;s=s.replace(a,a+"\n    (run/'connection-budget.json').write_text(json.dumps(connection_budget,indent=2)+'\\n',encoding='utf-8')")
    ast.parse(s);after=s.encode();(out/name).write_bytes(after);changes['tools/'+name]={'beforeSHA256':sha(raw),'afterSHA256':sha(after)}
(D/'runtime-candidate-source-pins.json').write_text(json.dumps({'twoControllerSources':changes,'policySHA256':sha(policy.encode()),'privateConfigurationOrBusinessJarsOrDatabaseChanged':False,'runtimeInstalled':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidateControllerFiles':2,'onlyNumericPoolPropertiesAndBudgetAdded':True,'runtimeInstalled':False}))
