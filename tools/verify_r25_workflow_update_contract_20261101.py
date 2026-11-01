"""Check the exact R24 workflow addition on owned code/metadata only; no services or databases."""
from pathlib import Path
import argparse, ast, copy, hashlib, importlib.util, json, re, sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
p=argparse.ArgumentParser();p.add_argument('--revision',default='r1');args=p.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',args.revision)
W=R/'work/user_feedback_20261031'/('r25-workflow-contract-'+args.revision);assert not W.exists();W.mkdir()
read=lambda f:json.loads(f.read_bytes());sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,indent=2)+'\n').encode()
source=T/'original_public_test_update_r25_20261101.py'
spec=importlib.util.spec_from_file_location('own_r24_contract',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
app=W/'Application';bundle=W/'bundle';app.mkdir();bundle.mkdir()
old=read(S/'r21-base-release-manifest.json');q=read(S/'r21-base-payload-manifest.json');r=copy.deepcopy(old)
r[m.R23_ASYNC_FIELD]=copy.deepcopy(m.R23_ASYNC_CONTRACT);r[m.R24_WORKFLOW_FIELD]=copy.deepcopy(m.R24_WORKFLOW_CONTRACT)
controls={m.R23_CONTROLLER:m.R23_CONTROLLER_SHA,m.R23_ASYNC_HELPER:m.R23_HELPER_SHA,m.R23_JOB:m.R23_JOB_SHA,
          'tools/original_public_test_update.py':sha(source),m.R24_PARAMETER:m.R24_PARAMETER_PIN['sha256']}
r['controllerFiles'].update(controls);q['files'].update(m.R23_ASYNC_ROWS);q['files'][m.R24_TASK_CLASS]=copy.deepcopy(m.R24_TASK_PIN)
plan={'files':{}}
def put(f,raw):f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
for n in [*m.R23_ASYNC_ROWS,*controls,m.R24_TASK_CLASS]:
    if n==m.R24_TASK_CLASS:f=R/'work/event_delivery_consistency_20261030/full-controller-r121/flow-guard-candidate-r6/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class'
    elif n==m.R24_PARAMETER:f=T/'server-runtime-temp-r2/original_server_release_parameters.py'
    elif n=='tools/original_public_test_update.py':f=source
    elif n in m.R23_ASYNC_ROWS:f=S/'payload'/n
    else:f=S/'graceful-public-control'/n
    raw=f.read_bytes();put(bundle/'payload'/n,raw);plan['files'][n]={'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest()}
checks=[]
def check(label,fn,deny=False):
    caught=False
    try:fn()
    except(ValueError,FileNotFoundError):caught=True
    assert caught==deny,label
    checks.append({'case':label,'expectedRefusal':deny,'passed':True})
def contract(p=None,o=None,rel=None,pay=None):
    return m.async_bundle_contract(app,bundle,plan if p is None else p,old if o is None else o,r if rel is None else rel,q if pay is None else pay)
check('complete-r21-to-r24-five-control-and-task-class-extension',contract)
for descriptor in [None,{},'foreign',dict(m.R24_WORKFLOW_CONTRACT,extra=True)]:
    value=copy.deepcopy(r);value[m.R24_WORKFLOW_FIELD]=descriptor
    check('foreign-descriptor-'+str(len(checks)),lambda value=value:contract(rel=value),True)
value=copy.deepcopy(r);value.pop(m.R24_WORKFLOW_FIELD)
check('missing-descriptor-with-new-code-refused',lambda:contract(rel=value),True)
value=copy.deepcopy(r);value.pop(m.R23_ASYNC_FIELD)
check('workflow-without-original-async-extension-refused',lambda:contract(rel=value),True)
for n in [m.R24_TASK_CLASS,m.R24_PARAMETER]:
    p=copy.deepcopy(plan);p['files'].pop(n)
    check('missing-fresh-transport-'+n,lambda p=p:contract(p=p),True)
    for k,v in [('SHA256','0'*64),('bytes',plan['files'][n]['bytes']+1),('extra',True)]:
        p=copy.deepcopy(plan);p['files'][n][k]=v
        check('wrong-transport-'+k+'-'+n,lambda p=p:contract(p=p),True)
    f=bundle/'payload'/n;raw=f.read_bytes();f.write_bytes(raw+b'X')
    check('actual-code-drift-'+n,contract,True);f.write_bytes(raw)
for k in ['sha256','bytes']:
    value=copy.deepcopy(q);value['files'][m.R24_TASK_CLASS][k]='0'*64 if k=='sha256'else 8544
    check('wrong-class-declaration-'+k,lambda value=value:contract(pay=value),True)
value=copy.deepcopy(r);value['controllerFiles'][m.R24_PARAMETER]='0'*64
check('wrong-adapter-declaration',lambda:contract(rel=value),True)
o=copy.deepcopy(old);o['controllerFiles'][m.R24_PARAMETER]='0'*64
check('unknown-original-adapter-refused',lambda:contract(o=o),True)
value=copy.deepcopy(r);retained=next(n for n in old['controllerFiles']if n not in controls)
value['controllerFiles'][retained]='0'*64
check('unannounced-retained-control-drift-refused',lambda:contract(rel=value),True)
for n in plan['files']:put(app/n,(bundle/'payload'/n).read_bytes())
check('retained-complete-extension-with-no-transport',lambda:contract(p={'files':{}},o=r))
o=copy.deepcopy(r);o[m.R24_WORKFLOW_FIELD]['revision']='foreign'
check('foreign-retained-extension-refused',lambda:contract(p={'files':{}},o=o),True)
run=app/'UserData/OriginalServer/runs/j1';business=run/'b';owner='own-r24-workflow-fixture'
relative=m.R24_TASK_CLASS.removeprefix('payload/business/run-template/')
put(business/relative,(bundle/'payload'/m.R24_TASK_CLASS).read_bytes())
owner_file=business/'server-owner.properties';owner_raw=('schema=zhumadian.original.server.owner.v1\nownerId='+owner+'\n').encode()
put(owner_file,owner_raw)
def save(rel=r,pay=q):
    raw=enc(pay);value=copy.deepcopy(rel);value['payloadManifestSHA256']=hashlib.sha256(raw).hexdigest()
    put(app/'payload-manifest.json',raw);put(app/'release-manifest.json',enc(value))
save();row={'run':str(run),'ownerId':owner}
check('owned-runtime-task-class-source-and-parameter-pins',lambda:m.workflow_ready(app,row))
check('foreign-runtime-owner-refused',lambda:m.workflow_ready(app,dict(row,ownerId='other')),True)
check('foreign-runtime-location-refused',lambda:m.workflow_ready(app,dict(row,run=str(W/'foreign/j1'))),True)
check('j0-runtime-refused',lambda:m.workflow_ready(app,dict(row,run=str(run.parent/'j0'))),True)
owner_file.write_bytes(owner_raw+b'extra=true\n')
check('unexpected-owner-field-refused',lambda:m.workflow_ready(app,row),True);owner_file.write_bytes(owner_raw)
for f in [business/relative,app/m.R24_TASK_CLASS,app/m.R24_PARAMETER]:
    raw=f.read_bytes();f.write_bytes(raw+b'X')
    check('runtime-or-installed-byte-drift-'+str(len(checks)),lambda:m.workflow_ready(app,row),True);f.write_bytes(raw)
raw=(app/'payload-manifest.json').read_bytes();(app/'payload-manifest.json').write_bytes(raw+b' ')
check('payload-manifest-pin-drift-refused',lambda:m.workflow_ready(app,row),True);(app/'payload-manifest.json').write_bytes(raw)
save(old,read(S/'r21-base-payload-manifest.json'))
check('original-r21-needs-no-new-workflow-runtime',lambda:m.workflow_ready(app,{}))
defs=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a=defs((T/'original_public_test_update_r23_graceful_20261101.py').read_text(encoding='utf-8'));b=defs(source.read_text(encoding='utf-8'))
assert {k for k in a if a[k]!=b[k]}=={'load_bundle','async_bundle_contract','health'}
assert set(b)-set(a)=={'workflow_declared','workflow_bundle_contract','workflow_ready','material_declared','material_bundle_contract','material_ready'}
result={'schema':'xnby.r24.workflow-updater-contract.v1','checks':len(checks),'allPassed':True,'cases':checks,
        'sourceSHA256':sha(source),'stopBackupReplaceRestoreUnchanged':True,'servicesOrDatabasesStarted':False,
        'protectedUserPreviewReadOrChanged':False,'publicOrFormalChanged':False}
put(W/'result.json',enc(result));print(json.dumps({k:v for k,v in result.items()if k!='cases'}))
