"""Test R23 contracts on owned metadata/code fixtures, without starting any service."""
from pathlib import Path
import argparse, ast, copy, hashlib, importlib.util, json, re, sys
from unittest.mock import patch

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r1');args=parser.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',args.revision)
W=R/'work/user_feedback_20261031'/('r27-inherited-updater-contract-'+args.revision)
assert not W.exists();W.mkdir()
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda v:(json.dumps(v,indent=2)+'\n').encode()
source=T/'original_public_test_update_r27_20261101.py'
spec=importlib.util.spec_from_file_location('own_r23_contract',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

# Execute all inherited risk/factory/session cases against this exact updater.
driver=(T/'verify_r22_update_guard_20261101.py').read_text(encoding='utf-8')
driver=driver.replace("r22-updater-contract-r1", "r27-inherited-risk-contract-"+args.revision)
driver=driver.replace("original_public_test_update_r22_20261101.py",source.name)
driver=driver.replace("{'risk_declared','risk_bundle_contract','native_session_ready'}",
                      "{'async_bundle_contract','async_declared','async_ready','async_state','controller_pin_for','material_bundle_contract','material_declared','material_ready','native_session_ready','parameter_pin_for','risk_bundle_contract','risk_declared','runtime_pool_bundle_contract','runtime_pool_declared','runtime_pool_ready','team_bundle_contract','team_declared','team_ready','workflow_bundle_contract','workflow_contract_for','workflow_declared','workflow_ready'}")
(W/'executed-inherited-risk-checks.py').write_text(driver,encoding='utf-8')
exec(compile(driver,'inherited-risk-checks','exec'),{'__name__':'inherited_risk_checks'})
inherited=read(W.parent/('r27-inherited-risk-contract-'+args.revision)/'result.json')
assert inherited['checks']==50 and inherited['sourceSHA256']==sha(source) and inherited['allPassed']

app=W/'Application';bundle=W/'bundle';app.mkdir();bundle.mkdir()
old=read(S/'r21-base-release-manifest.json')
payload=copy.deepcopy(read(S/'r21-base-payload-manifest.json'))
release=copy.deepcopy(old)
release[m.R23_ASYNC_FIELD]=copy.deepcopy(m.R23_ASYNC_CONTRACT)
controls={m.R23_CONTROLLER:m.R23_CONTROLLER_SHA,m.R23_ASYNC_HELPER:m.R23_HELPER_SHA,m.R23_JOB:m.R23_JOB_SHA,
          'tools/original_public_test_update.py':sha(source)}
release['controllerFiles'].update(controls)
payload['files'].update(copy.deepcopy(m.R23_ASYNC_ROWS))
plan={'files':{}}
def put(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for name in [*m.R23_ASYNC_ROWS,*controls]:
    raw=(source if name=='tools/original_public_test_update.py' else ((S/'payload'/name)if name in m.R23_ASYNC_ROWS else(S/'graceful-public-control'/name))).read_bytes()
    put(bundle/'payload'/name,raw)
    plan['files'][name]={'bytes':len(raw),'SHA256':hashlib.sha256(raw).hexdigest()}
checks=[]
def check(label,fn,denied=False):
    caught=False
    try:fn()
    except(ValueError,FileNotFoundError):caught=True
    assert caught==denied,label
    checks.append({'case':label,'expectedRefusal':denied,'passed':True})
def contract(p=None,r=None,q=None,o=None):
    return m.async_bundle_contract(app,bundle,plan if p is None else p,old if o is None else o,
                                   release if r is None else r,payload if q is None else q)
check('complete-exact-extension-controller-upgrade',contract)
for replacement in [None,{},'foreign',dict(m.R23_ASYNC_CONTRACT,extra=True)]:
    r=copy.deepcopy(release);r[m.R23_ASYNC_FIELD]=replacement
    check('invalid-descriptor-'+str(len(checks)),lambda r=r:contract(r=r),True)
r=copy.deepcopy(release);r.pop(m.R23_ASYNC_FIELD)
check('missing-descriptor-with-code',lambda:contract(r=r),True)
for name in [*m.R23_ASYNC_ROWS,*controls]:
    p=copy.deepcopy(plan);p['files'].pop(name)
    check('missing-fresh-transport-'+name,lambda p=p:contract(p=p),True)
    p=copy.deepcopy(plan);p['files'][name]['SHA256']='0'*64
    check('wrong-transport-hash-'+name,lambda p=p:contract(p=p),True)
    file=bundle/'payload'/name;raw=file.read_bytes();file.write_bytes(raw+b'X')
    check('wrong-actual-code-'+name,contract,True);file.write_bytes(raw)
for name in m.R23_ASYNC_ROWS:
    q=copy.deepcopy(payload);q['files'][name]['bytes']+=1
    check('wrong-declared-size-'+name,lambda q=q:contract(q=q),True)
    q=copy.deepcopy(payload);q['files'].pop(name)
    check('missing-declared-code-'+name,lambda q=q:contract(q=q),True)
for name in controls:
    r=copy.deepcopy(release);r['controllerFiles'][name]='0'*64
    check('wrong-new-controller-'+name,lambda r=r:contract(r=r),True)
r=copy.deepcopy(release);r['controllerFiles']['tools/foreign.py']='0'*64
check('extra-controller-refused',lambda:contract(r=r),True)
r=copy.deepcopy(release);unchanged=next(n for n in old['controllerFiles']if n not in controls)
r['controllerFiles'][unchanged]='0'*64
check('retained-original-controller-drift',lambda:contract(r=r),True)
o=copy.deepcopy(old);o['controllerFiles'][m.R23_CONTROLLER]='0'*64
check('unknown-original-controller',lambda:contract(o=o),True)
o=copy.deepcopy(old);o['controllerFiles'][m.R23_JOB]='0'*64
check('unknown-original-job',lambda:contract(o=o),True)
for name in [*m.R23_ASYNC_ROWS,*controls]:put(app/name,(bundle/'payload'/name).read_bytes())
check('retained-exact-extension',lambda:contract(p={'files':{}},o=release))
o=copy.deepcopy(release);o[m.R23_ASYNC_FIELD]['revision']='other'
check('retained-foreign-extension',lambda:contract(p={'files':{}},o=o),True)

def save_release(r=release,q=payload):
    raw=enc(q);r=copy.deepcopy(r);r['payloadManifestSHA256']=hashlib.sha256(raw).hexdigest()
    put(app/'payload-manifest.json',raw);put(app/'release-manifest.json',enc(r))
save_release()
platform=app/'UserData/TianjinOriginalPlatform/runs/j1';platform.mkdir(parents=True)
for name in m.R23_ASYNC_ROWS:
    put(platform/name.split('/run-template/',1)[1],(S/'payload'/name).read_bytes())
adapter=Path('D:/Zqa20261025/Application/payload/callback-overlay/20261026-password-identity/own-platform-observation.jar')
assert sha(adapter)==m.R23_AUTH_ADAPTER_SHA
put(platform/'own-platform-observation.jar',adapter.read_bytes())
owner='own-r23-readiness-test';owner_file=platform/'server-owner.properties'
owner_text='schema=zhumadian.original.server.owner.v1\nownerId='+owner+'\n'
owner_file.write_bytes(owner_text.replace('\n','\r\n').encode('ascii'))
report=platform/'async-request-snapshot-state.properties'
actual=(R/'work/event_delivery_consistency_20261030/full-business-main-r114/closed-short-runtime-evidence/platform/async-request-snapshot-state.properties').read_bytes()
assert m.async_state(actual)['finishedJobs']=='115'
report.write_bytes(actual);row={'platformRun':str(platform),'ownerId':owner}
check('actual-r114-state-and-pinned-runtime-code-crlf-owner',lambda:m.async_ready(app,row))
owner_file.write_bytes(owner_text.encode('ascii'))
check('lf-owner-same-content',lambda:m.async_ready(app,row))
valid=actual.decode('ascii').splitlines()
for key in m.async_state(actual):
    changed='\n'.join(line if not line.startswith(key+'=')else key+'=wrong'for line in valid)+'\n'
    check('wrong-state-value-'+key,lambda changed=changed:m.async_state(changed.encode()),True)
for label,raw in [('duplicate-key',actual+ b'activeJobs=0\n'),('unknown-field',actual+b'extra=false\n'),
                  ('oversize',b'a'*4097),('non-ascii',actual+b'\xff'),('empty',b''),
                  ('negative-count',actual.replace(b'activeJobs=0',b'activeJobs=-1')),
                  ('overflow-count',actual.replace(b'activeJobs=0',b'activeJobs=9223372036854775808')),
                  ('leading-zero',actual.replace(b'activeJobs=0',b'activeJobs=00'))]:
    check('state-refuses-'+label,lambda raw=raw:m.async_state(raw),True)
live=actual.replace(b'capturedJobs=115',b'capturedJobs=116').replace(b'activeJobs=0',b'activeJobs=1')
check('live-independent-counters-do-not-require-equality',lambda:m.async_state(live))
check('foreign-current-owner',lambda:m.async_ready(app,dict(row,ownerId='other')),True)
check('foreign-runtime-root',lambda:m.async_ready(app,dict(row,platformRun=str(W/'other/j1'))),True)
check('j0-runtime-refused',lambda:m.async_ready(app,dict(row,platformRun=str(platform.parent/'j0'))),True)
owner_file.write_bytes(owner_text.encode()+b'ownerId=other\n')
check('duplicate-owner-key',lambda:m.async_ready(app,row),True);owner_file.write_bytes(owner_text.encode())
for name in [*m.R23_ASYNC_ROWS,*controls]:
    if name=='tools/original_public_test_update.py':continue
    file=app/name;raw=file.read_bytes();file.write_bytes(raw+b'X')
    check('installed-code-drift-'+name,lambda:m.async_ready(app,row),True);file.write_bytes(raw)
for name in [*[n.split('/run-template/',1)[1]for n in m.R23_ASYNC_ROWS],'own-platform-observation.jar']:
    file=platform/name;raw=file.read_bytes();file.write_bytes(raw+b'X')
    check('runtime-code-drift-'+name,lambda:m.async_ready(app,row),True);file.write_bytes(raw)
bad=read(app/'release-manifest.json');bad['payloadManifestSHA256']='0'*64
put(app/'release-manifest.json',enc(bad));check('runtime-payload-manifest-drift',lambda:m.async_ready(app,row),True);save_release()
report.write_bytes(b'partial')
with patch.object(m.time,'sleep',lambda seconds:None):
    check('persistently-partial-state-refused',lambda:m.async_ready(app,row),True)
    report.unlink();check('missing-state-refused',lambda:m.async_ready(app,row),True)
    report.write_bytes(b'partial');calls=[]
    def finish_write(seconds):
        calls.append(seconds)
        if len(calls)==2:report.write_bytes(actual)
    with patch.object(m.time,'sleep',finish_write):
        check('transient-incomplete-state-retried-until-valid',lambda:m.async_ready(app,row))
        assert calls==[0.05,0.05]
legacy_payload=read(S/'r21-base-payload-manifest.json')
save_release(old,legacy_payload)
check('old-r21-has-no-async-runtime-requirement',lambda:m.async_ready(app,{}))
oldtree=ast.parse((T/'original_public_test_update_r22_20261101.py').read_text(encoding='utf-8'))
newtree=ast.parse(source.read_text(encoding='utf-8'))
defs=lambda tree:{n.name:ast.dump(n,include_attributes=False)for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before,after=defs(oldtree),defs(newtree)
assert {n for n in before if before[n]!=after[n]}=={'load_bundle','health'}
assert set(after)-set(before)=={'async_bundle_contract','async_declared','async_ready','async_state','controller_pin_for','material_bundle_contract','material_declared','material_ready','parameter_pin_for','runtime_pool_bundle_contract','runtime_pool_declared','runtime_pool_ready','team_bundle_contract','team_declared','team_ready','workflow_bundle_contract','workflow_contract_for','workflow_declared','workflow_ready'}
result={'schema':'xnby.r23.updater-contract-checks.v1','inheritedRiskChecks':50,'asyncChecks':len(checks),
        'checks':50+len(checks),'cases':checks,'allPassed':True,'actualR114MarkerUsed':True,
        'sourceSHA256':sha(source),'oldStopOwnershipAndRecoveryFunctionsUnchanged':True,
        'transientPartialWriteReadRetryVerified':True,'wholeInstalledLoadBundleNotExercised':True,
        'servicesStarted':False,'privateConfigurationOrBusinessTablesRead':False,'publicOrFormalChanged':False}
(W/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items()if k!='cases'}))
