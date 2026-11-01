from pathlib import Path
import hashlib,json,re,zipfile
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101'
assert not(A.parent/'user-manual-protected.json').exists()and json.loads((A.parent/'own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly']
config=json.loads((A/'private/server-configuration.json').read_bytes());rows={};names={}
for side in ['platform','business']:
    rows[side]={k:v for k,v in config['configuration'][side].items()if re.search('hikari|druid|pool|initial.size|max.active|min.idle|maximum.pool|minimum.idle',k,re.I)and re.fullmatch(r'[0-9.]+|true|false',str(v),re.I)}
    names[side]=sorted({k.split('.')[4]for k in config['configuration'][side]if k.startswith('spring.datasource.dynamic.datasource.')})
libs={}
for side in ['business','platform']:
    found=[]
    for p in (A/'payload'/side).rglob('*.jar'):
        if re.search('hikari|druid|datasource|jdbc',p.name,re.I):found.append(p.relative_to(A).as_posix())
    libs[side]=found
result={'onlyNumericPoolSettingsFromOwnSyntheticConfiguration':rows,'logicalDynamicDatasourceNames':names,'pinnedProgramPoolLibraries':libs,'actualCredentialsURLsAccountRowsOrSessionsIncluded':False}
D.mkdir(exist_ok=True);(D/'pool-budget-inputs.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
