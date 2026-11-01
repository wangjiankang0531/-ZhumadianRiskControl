from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';S=W/'r26-team-native-candidate-r1';OUT=W/'r27-team-contract-r2';assert not OUT.exists();OUT.mkdir()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,indent=2)+'\n').encode()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
source=T/'original_public_test_update_r27_20261101.py';spec=importlib.util.spec_from_file_location('own_team_contract',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bundle=OUT/'bundle';shutil.copytree(S/'bundle',bundle);app=OUT/'Application';shutil.copytree(S/'contract-Application',app);old=J(W/'r25-material-unified-candidate-r1/bundle/payload/release-manifest.json');oldq=J(app/'payload-manifest.json');r=J(bundle/'payload/release-manifest.json');q=J(bundle/'payload/payload-manifest.json');p=J(bundle/'update-manifest.json');target=next(iter(m.R26_TEAM_ROWS));cases=[]
def check(name,fn,deny=False):
    caught=False
    try:fn()
    except(ValueError,FileNotFoundError,KeyError):caught=True
    assert caught==deny,name;cases.append({'case':name,'expectedRefusal':deny,'passed':True})
def contract(plan=p,previous=old,release=r,payload=q):return m.material_bundle_contract(app,bundle,plan,previous,release,payload)
check('complete-exact-R25-one-original-XML-extension',contract)
for value in [None,{},'foreign',dict(m.R26_TEAM_CONTRACT,extra=True)]:
    x=copy.deepcopy(r);x[m.R26_TEAM_FIELD]=value;check('wrong-descriptor-'+str(len(cases)),lambda x=x:contract(release=x),True)
x=copy.deepcopy(r);x.pop(m.R26_TEAM_FIELD);check('missing-descriptor-with-new-XML',lambda:contract(release=x),True)
x=copy.deepcopy(q);x['files'].pop(target);check('missing-declared-XML',lambda:contract(payload=x),True)
for key,value in [('bytes',2569),('sha256','0'*64),('extra',True)]:
    x=copy.deepcopy(q);x['files'][target][key]=value;check('wrong-declared-'+key,lambda x=x:contract(payload=x),True)
x=copy.deepcopy(p);x['files'].pop(target);check('missing-fresh-XML-transport',lambda:contract(plan=x),True)
for key,value in [('bytes',2569),('SHA256','0'*64),('extra',True)]:
    x=copy.deepcopy(p);x['files'][target][key]=value;check('wrong-XML-transport-'+key,lambda x=x:contract(plan=x),True)
for field in [m.R25_MATERIAL_FIELD,m.R24_WORKFLOW_FIELD,m.R23_ASYNC_FIELD]:
    x=copy.deepcopy(r);x.pop(field);check('missing-retained-contract-'+field,lambda x=x:contract(release=x),True)
x=copy.deepcopy(old);x.pop(m.R25_MATERIAL_FIELD);check('fresh-Team-cannot-bypass-exact-installed-material-base',lambda:contract(previous=x),True)
for name in m.R26_TEAM_SOURCE:
    x=copy.deepcopy(q);x['files'][name]['sha256']='0'*64;check('retained-source-pin-drift-'+name,lambda x=x:contract(payload=x),True)
    f=app/name;raw=f.read_bytes();put(f,raw+b'own-drift');check('actual-retained-source-drift-'+name,contract,True);put(f,raw)
f=bundle/'payload'/target;raw=f.read_bytes();put(f,raw+b'own-drift');check('actual-XML-transport-drift',contract,True);put(f,raw)
extra='payload/business/run-template/classes/mapper/OtherMapper.xml';x=copy.deepcopy(q);x['files'][extra]={'bytes':1,'sha256':'0'*64};check('undeclared-extra-XML',lambda:contract(payload=x),True)
for name in ['private/extra.json','runtime/extra.exe',next(iter(m.R25_MATERIAL_ROWS)),next(iter(m.R26_TEAM_SOURCE)),next(n for n in oldq['files']if n.startswith('frontend/security_pc/'))]:
    x=copy.deepcopy(p);x['files'][name]={'bytes':1,'SHA256':'0'*64};check('outside-transport-'+name,lambda x=x:contract(plan=x),True)
for prefix in ['frontend/security_pc/','payload/platform/']:
    name=next(n for n in oldq['files']if n.startswith(prefix));x=copy.deepcopy(q);x['files'][name]['sha256']='0'*64;check('nonemergency-payload-drift-'+prefix,lambda x=x:contract(payload=x),True)
x=copy.deepcopy(p);x['removedFrontendFiles'].pop(next(iter(x['removedFrontendFiles'])));check('missing-old-emergency-removal',lambda:contract(plan=x),True)
x=copy.deepcopy(p);x['removedFrontendFiles'][target]={'bytes':2568,'SHA256':m.R26_TEAM_ROWS[target]['sha256']};check('backend-resource-removal-forbidden',lambda:contract(plan=x),True)
def save(rel,payload):
    raw=enc(payload);result=copy.deepcopy(rel);result['payloadManifestSHA256']=hashlib.sha256(raw).hexdigest();put(app/'payload-manifest.json',raw);put(app/'release-manifest.json',enc(result));return result
put(app/target,(bundle/'payload'/target).read_bytes());retained=save(r,q)
check('retained-exact-Team-and-material-with-no-transport',lambda:contract(plan={'files':{},'removedFrontendFiles':{}},previous=retained))
x=copy.deepcopy(retained);x[m.R26_TEAM_FIELD]['revision']='foreign';check('foreign-retained-Team-descriptor',lambda:contract(plan={'files':{},'removedFrontendFiles':{}},previous=x),True)
x=copy.deepcopy(r);x.pop(m.R26_TEAM_FIELD);y=copy.deepcopy(q);y['files'].pop(target);check('retained-Team-extension-cannot-be-dropped',lambda:m.team_bundle_contract(app,bundle,{'files':{}},retained,x,y),True)
run=app/'UserData/OriginalServer/runs/j1';business=run/'b';owner_raw=b'schema=zhumadian.original.server.owner.v1\nownerId=own-r26-contract\n';ownerFile=business/'server-owner.properties';put(ownerFile,owner_raw)
for n in [*m.R25_MATERIAL_ROWS,m.R24_TASK_CLASS,*m.R26_TEAM_ROWS,*[n for n in m.R26_TEAM_SOURCE if n.startswith('payload/business/run-template/')]]:put(business/n.removeprefix('payload/business/run-template/'),(app/n).read_bytes())
row={'run':str(run),'ownerId':'own-r26-contract'};check('exact-current-owned-runtime-original-XML-service-and-retained-material',lambda:m.team_ready(app,row))
for name,value in [('foreign-owner',dict(row,ownerId='other')),('foreign-location',dict(row,run=str(OUT/'other/j1'))),('j0',dict(row,run=str(run.parent/'j0')))]:check(name,lambda value=value:m.team_ready(app,value),True)
put(ownerFile,owner_raw+b'extra=true\n');check('extra-owner-field',lambda:m.team_ready(app,row),True);put(ownerFile,owner_raw)
for n in [*m.R26_TEAM_ROWS,*[n for n in m.R26_TEAM_SOURCE if n.startswith('payload/business/run-template/')]]:
    for f in [app/n,business/n.removeprefix('payload/business/run-template/')]:
        raw=f.read_bytes();put(f,raw+b'own-drift');check('source-or-runtime-drift-'+str(len(cases)),lambda:m.team_ready(app,row),True);put(f,raw)
save(old,oldq);check('R25-retained-without-Team-needs-no-Team-runtime',lambda:m.team_ready(app,{}))
defs=lambda raw:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};before=defs((T/'original_public_test_update_r25_20261101.py').read_text(encoding='utf-8'));after=defs(source.read_text(encoding='utf-8'));assert {n for n in before if before[n]!=after[n]}=={'async_bundle_contract','async_ready','health','load_bundle','material_bundle_contract','material_declared','workflow_bundle_contract','workflow_declared','workflow_ready'} and set(after)-set(before)=={'controller_pin_for','parameter_pin_for','runtime_pool_bundle_contract','runtime_pool_declared','runtime_pool_ready','team_bundle_contract','team_declared','team_ready','workflow_contract_for'}
result={'schema':'xnby.r26.team-contract.v1','allPassed':True,'checks':len(cases),'cases':cases,'sourceSHA256':sha(source),'normalStopBackupReplaceRestoreASTUnchanged':True,'actualServicesOrSQLOrUserRootsOperated':False,'fullInstalledPreflightNotClaimed':True};put(OUT/'result.json',enc(result));print(json.dumps({n:v for n,v in result.items()if n!='cases'}))
