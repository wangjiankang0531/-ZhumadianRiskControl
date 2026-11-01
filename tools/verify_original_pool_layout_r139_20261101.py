from pathlib import Path
import copy,contextlib,hashlib,importlib.util,io,json,secrets,types
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;D=R/'Document/Deployment/emergency_pool_layout_r139_20261101';C=R/'work/event_delivery_consistency_20261030/full-controller-r139/pool-policy-checks';assert not C.exists();C.mkdir()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=load('layout_policy',V/'original_connection_pool_policy_r139_20261101.py');old=load('old_policy',R/'Application/tools/original_connection_pool_policy_r136_20261101.py')
sha=lambda raw:hashlib.sha256(raw).hexdigest();cases=[]
def config(implicit=False):
 result={'configuration':{}}
 for side,names in [('platform',[] if implicit else ['master']),('business',['master','tow'])]:
  v={'spring.datasource.dynamic.datasource.'+n+'.url':'jdbc:mysql://127.0.0.1:9/own_layout'for n in names}
  v.update({'spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0','spring.datasource.dynamic.druid.max-wait':'5000'})
  result['configuration'][side]=v
 if implicit:result['configuration']['platform'].update({'spring.datasource.host':'127.0.0.1','spring.datasource.db-name':'own_layout','spring.datasource.dynamic.primary':'jnpf'})
 return result
def verify(label,c,count,total,implicit=False):
 before=copy.deepcopy(c);p=m.connection_pool_budget(c);assert c==before
 assert len(p['datasources'])==count and p['maximumPoolConnections']==total and p['mysqlMaxConnections']==max(24,total+12)
 props=m.runtime_pool_properties(c,'platform')
 assert ('spring.datasource.dynamic.hikari.max-pool-size'in props)==implicit
 assert not any(k.endswith('.url')for k in props)
 cases.append(label);return p
explicit=config();verify('three-explicit-pools-retain-prior-budget',explicit,3,12)
implicit=config(True)
try:old.connection_pool_budget(implicit)
except ValueError as e:assert str(e)=='BOUNDED_DYNAMIC_POOL_LAYOUT_REQUIRED'
else:raise AssertionError('OLD_FAILURE_NOT_REPRODUCED')
verify('original-host-dbname-primary-accepted-without-inventing-url',implicit,3,12,True)
extra=copy.deepcopy(implicit);extra['configuration']['platform']['spring.datasource.dynamic.datasource.reporting.url']='jdbc:mysql://127.0.0.1:9/own_layout';verify('generated-primary-plus-extra-declared-pool-both-counted',extra,4,16,True)
group=copy.deepcopy(implicit)
for n in ['jnpf_1','jnpf_2']:group['configuration']['platform']['spring.datasource.dynamic.datasource.'+n+'.url']='jdbc:mysql://127.0.0.1:9/own_layout'
verify('original-primary-group-does-not-add-phantom-default',group,4,16)
alias=copy.deepcopy(implicit);alias['configuration']['platform'].update({'spring.datasource.dynamic.datasource.named.url':'jdbc:mysql://127.0.0.1:9/own_layout','spring.datasource.dynamic.datasource.named.pool-name':'jnpf'});verify('original-pool-name-alias-covers-primary',alias,3,12)
native=copy.deepcopy(implicit);native['configuration']['platform'].update({'spring.datasource.dynamic.hikari.maximum-pool-size':'7','spring.datasource.dynamic.hikari.minimum-idle':'2'});verify('explicit-global-hikari-preserved-for-generated-pool',native,3,15,True)
override=copy.deepcopy(extra);override['configuration']['platform']['spring.datasource.dynamic.datasource.reporting.hikari.max-pool-size']='6';verify('declared-override-is-independent-of-generated-global-mapping',override,4,18,True)
defaults=config(True)
for side in defaults['configuration']:defaults['configuration'][side]={k:v for k,v in defaults['configuration'][side].items()if '.druid.'not in k}
verify('native-default-capacity-not-silently-downsized',defaults,3,30,True)
for label,change in [
 ('missing-host-definition',lambda c:c['configuration']['platform'].pop('spring.datasource.host')),
 ('invalid-generated-primary',lambda c:c['configuration']['platform'].update({'spring.datasource.dynamic.primary':'../../outside'})),
 ('hikari-idle-exceeds-max',lambda c:c['configuration']['platform'].update({'spring.datasource.dynamic.hikari.min-idle':'5'})),
 ('druid-idle-exceeds-max',lambda c:c['configuration']['platform'].update({'spring.datasource.dynamic.druid.min-idle':'5'})),
 ('conflicting-max-aliases',lambda c:c['configuration']['platform'].update({'spring.datasource.dynamic.hikari.max-pool-size':'4','spring.datasource.dynamic.hikari.maximum-pool-size':'5'})),
 ('invalid-numeric',lambda c:c['configuration']['platform'].update({'spring.datasource.dynamic.druid.max-active':'4;no'})),
 ('total-outside-server-budget',lambda c:[v.update({'spring.datasource.dynamic.druid.max-active':'128'})for v in c['configuration'].values()]),
 ('declared-pool-missing-url',lambda c:(c['configuration']['business'].pop('spring.datasource.dynamic.datasource.master.url'),c['configuration']['business'].update({'spring.datasource.dynamic.datasource.master.driver-class-name':'com.mysql.cj.jdbc.Driver'})))]:
 c=copy.deepcopy(implicit);change(c)
 try:m.connection_pool_budget(c)
 except ValueError:cases.append(label+'-refused')
 else:raise AssertionError(label)
sentinel=secrets.token_hex(32);c=copy.deepcopy(implicit);c['configuration']['platform']['spring.datasource.password']=sentinel
assert sentinel not in json.dumps(m.connection_pool_budget(c)) and sentinel not in json.dumps(m.runtime_pool_properties(c,'platform'));cases.append('private-values-not-returned')
app=C/'Application';bundle=C/'bundle';(app/'private').mkdir(parents=True);(bundle/'payload/tools').mkdir(parents=True)
source=(D/'candidate-sources-r3/original_server_release_parameters.py').read_bytes();(bundle/'payload/tools/original_server_release_parameters.py').write_bytes(source)
u=load('candidate_updater',D/'candidate-sources-r3/original_public_test_update.py')
assert u.R27_POOL_PINS[u.R24_PARAMETER]=={'bytes':len(source),'sha256':sha(source)};cases.append('generated-pool-parameter-sha-and-length-match-executed-bytes')
assert u.R27_POOL_WORKFLOW_CONTRACT['parameterAdapter']==dict(path=u.R24_PARAMETER,bytes=len(source),sha256=sha(source));cases.append('retained-workflow-parameter-sha-and-length-match-executed-bytes')
release={u.R27_POOL_FIELD:copy.deepcopy(m.CONNECTION_POOL_POLICY),'controllerFiles':{'tools/original_server_release_parameters.py':sha(source)}}
raw=json.dumps(release).encode();rp=bundle/'payload/release-manifest.json';rp.write_bytes(raw)
plan={'newReleaseSHA256':sha(raw),'releaseId':'OWN_LAYOUT_RELEASE','updateId':'OWN_LAYOUT_TEST','callbackOverlay':'OWN_NONE','callbackOverlaySHA256':'0'*64}
cfg=app/'private/server-configuration.json'
def save_cfg(c):cfg.write_text(json.dumps(dict(c,schema='zhumadian.original.server.configuration.v1')),encoding='utf-8')
save_cfg(implicit);p=u.candidate_runtime_pool_preflight(app,bundle,plan);assert p['budget']['mysqlMaxConnections']==24 and p['configurationSHA256']==sha(cfg.read_bytes());cases.append('exact-candidate-source-checks-original-shape-without-starting-services')
for label,mutate in [('release-source-drift',lambda:rp.write_bytes(raw+b' ')),('parameter-source-drift',lambda:(bundle/'payload/tools/original_server_release_parameters.py').write_bytes(source+b'\n#changed'))]:
 mutate()
 try:u.candidate_runtime_pool_preflight(app,bundle,plan)
 except ValueError:cases.append(label+'-refused')
 else:raise AssertionError(label)
 rp.write_bytes(raw);(bundle/'payload/tools/original_server_release_parameters.py').write_bytes(source)
calls=[]
def forbidden(*a,**k):calls.append('unexpected-lifecycle');raise AssertionError('SERVICE_OR_CODE_ACTION_BEFORE_PREFLIGHT')
u.load_bundle=lambda *a:(plan,'0'*64,{})
for name in ['owned_ready','normal_stop','backup_code','replace_code','launch','ingress_preflight']:setattr(u,name,forbidden)
bad=copy.deepcopy(implicit);bad['configuration']['platform'].pop('spring.datasource.host');save_cfg(bad)
before=sorted(q.relative_to(app).as_posix()for q in app.rglob('*'))
with contextlib.redirect_stdout(io.StringIO()):
 try:u.apply_update(app,bundle,'unused')
 except ValueError as e:assert str(e)=='ORIGINAL_PLATFORM_PRIMARY_LAYOUT_REQUIRED'
 else:raise AssertionError('INVALID_CANDIDATE_WAS_NOT_REFUSED')
assert not calls and before==sorted(q.relative_to(app).as_posix()for q in app.rglob('*'));cases.append('actual-apply-path-refuses-layout-before-owned-ready-backup-stop-or-mutation')
# A configuration changed during backup must not cross the normal-stop boundary.
save_cfg(implicit)
for rel,value in [('UserData/OriginalServer/installation.json',{'releaseId':plan['releaseId'],'databaseUUID':'OWN_SYNTHETIC_DATABASE'}),('UserData/OriginalDeployment/active-deployment.private.json',{'releaseId':plan['releaseId']})]:
 q=app/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(value),encoding='utf-8')
u.owned_ready=lambda *a:{'databaseUUID':'OWN_SYNTHETIC_DATABASE'};u.ingress_preflight=lambda *a:(None,None);u.preserve_previous_update=lambda *a:False
original_disk_usage=u.shutil.disk_usage;u.shutil.disk_usage=lambda *a:types.SimpleNamespace(free=13*1024**3)
def backup_and_drift(a,attempt,changes):attempt.mkdir(parents=True);cfg.write_bytes(cfg.read_bytes()+b' ')
u.backup_code=backup_and_drift
try:
 with contextlib.redirect_stdout(io.StringIO()):
  try:u.apply_update(app,bundle,'unused')
  except ValueError as e:assert str(e)=='CONFIGURATION_CHANGED_BEFORE_NORMAL_STOP'
  else:raise AssertionError('CONFIGURATION_DRIFT_WAS_NOT_REFUSED')
finally:u.shutil.disk_usage=original_disk_usage
assert not calls;cases.append('configuration-drift-during-backup-refused-before-stop')
save_cfg(implicit)
fixtures=C/'binding-cases';fixtures.mkdir()
for name,c in [('generated',implicit),('extra',extra),('group',group),('alias',alias),('native-override',native),('declared-override',override)]:
 props={**c['configuration']['platform'],**m.runtime_pool_properties(c,'platform')};(fixtures/(name+'.properties')).write_text(''.join(k+'='+v+'\n'for k,v in props.items()),encoding='ascii')
proof={'schema':'xnby.r139.pool-layout-pure-and-preflight.v1','allPassed':True,'checks':len(cases),'cases':cases,'oldR27ShapeFailureReproduced':True,'actualUpdaterControlFlowTested':True,'noActualServicesSQLDesktopOrProtectedRootsOperated':True,'sourceSHA256':sha((V/'original_connection_pool_policy_r139_20261101.py').read_bytes()),'actualOriginalJNPFBindingPending':True}
(C/'result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
