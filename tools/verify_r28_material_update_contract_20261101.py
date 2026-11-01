"""Exercise material extension refusal/ownership rules over owned program fixtures; no service or DB."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';S=W/'r25-material-unified-candidate-r1'
OUT=W/'r28-material-contract-r3';assert not OUT.exists();OUT.mkdir()
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def normalize_candidate_preflight_ast(text):
    tree=ast.parse(text)
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='apply_update')
    assignment=ast.parse("candidate_pool = candidate_runtime_pool_preflight(app, bundle, plan)").body[0]
    guard=ast.parse("if candidate_pool is not None:\n    require(sha(regular(app, 'private/server-configuration.json')) == candidate_pool['configurationSHA256'],\n            'CONFIGURATION_CHANGED_BEFORE_NORMAL_STOP')").body[0]
    fingerprint=lambda n:ast.dump(n,include_attributes=False)
    matches=[n for n in fn.body if fingerprint(n)==fingerprint(assignment)];assert len(matches)==1
    fn.body.remove(matches[0])
    matches=[(n,b)for n in fn.body if isinstance(n,ast.Try)for b in n.body if fingerprint(b)==fingerprint(guard)];assert len(matches)==1
    matches[0][0].body.remove(matches[0][1])
    return tree

source=T/'original_public_test_update_r28_20261101.py';spec=importlib.util.spec_from_file_location('own_r25_contract',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
bundle=S/'bundle';old_bundle=W/'r24-unified-candidate-r1/sparse-graceful-update-preparation-r1/bundle'
old=read(old_bundle/'payload/release-manifest.json');oldq=read(old_bundle/'payload/payload-manifest.json')
r=read(bundle/'payload/release-manifest.json');q=read(bundle/'payload/payload-manifest.json');p=read(bundle/'update-manifest.json')
app=OUT/'Application';shutil.copytree(S/'contract-Application',app);checks=[]
def check(label,fn,deny=False):
    caught=False
    try:fn()
    except(ValueError,FileNotFoundError):caught=True
    assert caught==deny,label
    checks.append({'case':label,'expectedRefusal':deny,'passed':True})
def contract(plan=p,previous=old,release=r,payload=q):return m.material_bundle_contract(app,bundle,plan,previous,release,payload)
check('complete-exact-R24-three-class-extension',contract)
for descriptor in [None,{},'foreign',dict(m.R25_MATERIAL_CONTRACT,extra=True)]:
    x=copy.deepcopy(r);x[m.R25_MATERIAL_FIELD]=descriptor
    check('wrong-descriptor-'+str(len(checks)),lambda x=x:contract(release=x),True)
x=copy.deepcopy(r);x.pop(m.R25_MATERIAL_FIELD);check('missing-descriptor-with-new-classes',lambda:contract(release=x),True)
for field in [m.R24_WORKFLOW_FIELD,m.R23_ASYNC_FIELD]:
    x=copy.deepcopy(r);x.pop(field);check('required-retained-extension-'+field,lambda x=x:contract(release=x),True)
for name in m.R25_MATERIAL_ROWS:
    x=copy.deepcopy(p);x['files'].pop(name);check('missing-fresh-transport-'+name,lambda x=x:contract(plan=x),True)
    for key,value in [('SHA256','0'*64),('bytes',p['files'][name]['bytes']+1),('extra',True)]:
        x=copy.deepcopy(p);x['files'][name][key]=value;check('wrong-transport-'+key+'-'+name,lambda x=x:contract(plan=x),True)
    for key,value in [('sha256','0'*64),('bytes',q['files'][name]['bytes']+1)]:
        x=copy.deepcopy(q);x['files'][name][key]=value;check('wrong-declared-'+key+'-'+name,lambda x=x:contract(payload=x),True)
    x=copy.deepcopy(q);x['files'].pop(name);check('missing-declared-'+name,lambda x=x:contract(payload=x),True)
    f=bundle/'payload'/name;raw=f.read_bytes()
    # Copy this one class into a new private transport fixture, never mutate the immutable bundle.
    testbundle=OUT/('drift-'+str(len(checks)));shutil.copytree(bundle,testbundle);put(testbundle/'payload'/name,raw+b'own-drift')
    check('actual-transport-drift-'+name,lambda b=testbundle:m.material_bundle_contract(app,b,p,old,r,q),True)
extra='payload/business/run-template/classes/xnby/replica/OriginalMaterialExcelImport$2.class'
x=copy.deepcopy(q);x['files'][extra]={'bytes':1,'sha256':'0'*64};check('undeclared-extra-helper',lambda:contract(payload=x),True)
for prefix in ['frontend/security_pc/','payload/platform/','payload/business/run-template/']:
    n=next(n for n in oldq['files']if n.startswith(prefix)and n not in m.R25_MATERIAL_ROWS)
    x=copy.deepcopy(q);x['files'][n]['sha256']='0'*64;check('nonemergency-payload-drift-'+prefix,lambda x=x:contract(payload=x),True)
for n in ['private/extra.json','runtime/extra.exe','tools/serve_original_server_release.py',next(n for n in q['files']if n.startswith('frontend/security_pc/'))]:
    x=copy.deepcopy(p);x['files'][n]={'bytes':1,'SHA256':'0'*64};check('outside-transport-scope-'+n,lambda x=x:contract(plan=x),True)
for n in [next(iter(q['files'])),next(n for n in q['files']if n.startswith('frontend/emergency_pc/'))]:
    x=copy.deepcopy(p);x['removedFrontendFiles'][n]={'bytes':1,'SHA256':'0'*64};check('unexpected-removal-'+n,lambda x=x:contract(plan=x),True)
x=copy.deepcopy(p);x['removedFrontendFiles'].pop(next(iter(x['removedFrontendFiles'])));check('missing-obsolete-removal',lambda:contract(plan=x),True)
for n,pin in m.R25_MATERIAL_ROWS.items():put(app/n,(bundle/'payload'/n).read_bytes())
def save(rel,pay):
    raw=enc(pay);x=copy.deepcopy(rel);x['payloadManifestSHA256']=hashlib.sha256(raw).hexdigest();put(app/'payload-manifest.json',raw);put(app/'release-manifest.json',enc(x));return x
retained=save(r,q);check('retained-exact-three-classes-without-transport',lambda:contract(plan={'files':{},'removedFrontendFiles':{}},previous=retained))
x=copy.deepcopy(retained);x[m.R25_MATERIAL_FIELD]['revision']='foreign';check('foreign-retained-descriptor',lambda:contract(plan={'files':{},'removedFrontendFiles':{}},previous=x),True)
run=app/'UserData/OriginalServer/runs/j1';business=run/'b';owner='own-r26-material-contract';owner_file=business/'server-owner.properties'
owner_raw=('schema=zhumadian.original.server.owner.v1\nownerId='+owner+'\n').encode();put(owner_file,owner_raw)
for n in [*m.R25_MATERIAL_ROWS,m.R24_TASK_CLASS]:put(business/n.removeprefix('payload/business/run-template/'),(app/n).read_bytes())
row={'run':str(run),'ownerId':owner};check('exact-owned-three-runtime-and-source-classes',lambda:m.material_ready(app,row))
check('foreign-runtime-owner',lambda:m.material_ready(app,dict(row,ownerId='other')),True)
check('foreign-runtime-location',lambda:m.material_ready(app,dict(row,run=str(OUT/'foreign/j1'))),True)
check('j0-runtime',lambda:m.material_ready(app,dict(row,run=str(run.parent/'j0'))),True)
put(owner_file,owner_raw+b'extra=true\n');check('extra-owner-field',lambda:m.material_ready(app,row),True);put(owner_file,owner_raw)
for n in m.R25_MATERIAL_ROWS:
    for f in [app/n,business/n.removeprefix('payload/business/run-template/')]:
        raw=f.read_bytes();put(f,raw+b'own-drift');check('source-or-runtime-class-drift-'+str(len(checks)),lambda:m.material_ready(app,row),True);put(f,raw)
save(old,oldq);check('original-R24-requires-no-material-runtime',lambda:m.material_ready(app,{}))
defs=lambda x:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(x).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=defs((T/'original_public_test_update_r24_20261101.py').read_text(encoding='utf-8'));b={n.name:ast.dump(n,include_attributes=False)for n in normalize_candidate_preflight_ast(source.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert{k for k in a if a[k]!=b[k]}=={'async_bundle_contract','async_ready','health','load_bundle','workflow_bundle_contract','workflow_declared','workflow_ready'} and set(b)-set(a)=={'candidate_runtime_pool_preflight','controller_pin_for','material_bundle_contract','material_declared','material_ready','parameter_pin_for','runtime_pool_bundle_contract','runtime_pool_declared','runtime_pool_ready','team_bundle_contract','team_declared','team_ready','workflow_contract_for'}
result={'schema':'xnby.r25.material-updater-contract.v1','checks':len(checks),'allPassed':True,'cases':checks,'sourceSHA256':sha(source),
    'stopBackupReplaceRestoreASTUnchanged':True,'servicesOrDatabasesStarted':False,'protectedUserPreviewReadOrChanged':False,
    'publicOrFormalChanged':False,'wholeInstalledProgramPreflightNotExercisedByThisTest':True}
put(OUT/'result.json',enc(result));print(json.dumps({k:v for k,v in result.items()if k!='cases'}))
