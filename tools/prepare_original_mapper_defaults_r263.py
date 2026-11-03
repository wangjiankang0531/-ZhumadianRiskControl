from pathlib import Path
import ast,hashlib,json,importlib.util,copy,uuid
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';T=R/'Application/tools';D=R/'Document/Deployment/original_mapper_default_candidate_r263_20261103'
assert not D.exists();D.mkdir()
oldpath=A/'tools/original_server_release_parameters.py';old=oldpath.read_text(encoding='utf-8');sha=lambda b:hashlib.sha256(b).hexdigest()
anchor='def materialize(spec,*,side,';assert old.count(anchor)==1
helper='''def original_business_mapper_defaults(values):
    """Resolve original XML resources when no explicit MybatisPlus location is configured."""
    explicit = any(re.fullmatch(r'mybatisplusmapperlocations(?:\\[[0-9]+\\])?', re.sub(r'[-_.]', '', key).lower()) for key in values)
    if not explicit:
        values['mybatis-plus.mapper-locations'] = 'classpath*:/xml/**/*.xml'

'''
new=old.replace(anchor,helper+anchor)
anchor="    values={k:render(v) for k,v in spec['configuration'][side].items()}";assert new.count(anchor)==1
new=new.replace(anchor,anchor+"\n    if side=='business':original_business_mapper_defaults(values)")
ast.parse(new);oldast=ast.parse(old);newast=ast.parse(new);oldfunc={n.name:ast.dump(n,include_attributes=False)for n in oldast.body if isinstance(n,ast.FunctionDef)};newfunc={n.name:ast.dump(n,include_attributes=False)for n in newast.body if isinstance(n,ast.FunctionDef)}
assert set(newfunc)-set(oldfunc)=={'original_business_mapper_defaults'}and[n for n in oldfunc if oldfunc[n]!=newfunc[n]]==['materialize']
path=T/'original_server_release_parameters_r263_mapper_default.py';assert not path.exists();path.write_text(new,encoding='utf-8',newline='\n')
def module(name,p):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
before=module('mapper_default_before',oldpath);after=module('mapper_default_candidate',path)
cfg=json.loads((A/'private/server-configuration.json').read_bytes())
for k in list(cfg['configuration']['business']):
 if 'mapper'in k.lower()and'location'in k.lower():del cfg['configuration']['business'][k]
args=dict(application=A,platform_run=A/'UserData/TianjinOriginalPlatform/runs/j1',business_run=A/'UserData/OriginalServer/runs/j1/b',platform_data_owner='10000000-0000-0000-0000-000000000001',run_owner='10000000-0000-0000-0000-000000000002',database_uuid='10000000-0000-0000-0000-000000000003',database_port=41001,redis_port=41002,object_port=41003,database_password=cfg['seedRootPassword'],redis_password=cfg['seedRootPassword'],object_access='own-synthetic-access',object_secret=cfg['seedRootPassword'])
cases=[]
for side in ['platform','business']:
 extra={}if side=='platform'else{'platform_port':41004};original=copy.deepcopy(cfg)
 a=before.materialize(cfg,side=side,**args,**extra);b=after.materialize(cfg,side=side,**args,**extra)
 assert cfg==original
 if side=='platform':assert a==b
 else:
  delta={k for k in set(a['configuration'])|set(b['configuration'])if a['configuration'].get(k)!=b['configuration'].get(k)};assert delta=={'mybatis-plus.mapper-locations'}and b['configuration']['mybatis-plus.mapper-locations']=='classpath*:/xml/**/*.xml'
  assert a['arguments']==b['arguments']and all(a[k]==b[k]for k in a if k not in ['configuration','properties'])
 cases.append({'case':side+'-actual-frozen-input-render-diff','passed':True})
for key,value in [('mybatis-plus.mapper-locations','classpath*:/custom/**/*.xml'),('mybatis-plus.mapperLocations','classpath*:/explicit/**/*.xml'),('mybatis-plus.mapper-locations[0]','classpath*:/one/**/*.xml'),('mybatis_plus.mapper_locations','classpath*:/two/**/*.xml'),('mybatis-plus.mapper-locations',''),('mybatis-plus.mapper-locations','classpath*:/xml/**/*.xml,classpath*:/other/**/*.xml')]:
 spec=copy.deepcopy(cfg);spec['configuration']['business'][key]=value;a=before.materialize(spec,side='business',platform_port=41004,**args);b=after.materialize(spec,side='business',platform_port=41004,**args);assert a==b;cases.append({'case':'explicit-'+key+('-empty-preserved'if not value else ''),'passed':True})
report={'sourceBeforeSHA256':sha(old.encode()),'sourceCandidateSHA256':sha(path.read_bytes()),'onlyExistingFunctionChanged':'materialize','newPureHelper':'original_business_mapper_defaults','allOtherFunctionsASTIdentical':True,'actualFrozenConfigurationRendererCases':cases,'privateValuesOrCredentialsExported':False,'originalSQLJarOrControllersInstalled':False,'runtimeCandidateUsesTemporaryConfigurationNotThisProductHelper':True,'publicDeployed':False}
(D/'source-and-renderer-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'preparedProductSource':True,'actualFrozenRendererCases':len(cases),'allOtherFunctionsUnchanged':True,'installedOrPublicDeployed':False}))
