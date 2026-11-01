from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';G=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r139';D=R/'Document/Deployment/emergency_pool_layout_r139_20261101'
ap=argparse.ArgumentParser();ap.add_argument('--attempt',default='r1');args=ap.parse_args();assert args.attempt in ['r1','r2','r3'];root=C/('pool-contract-'+args.attempt);assert not root.exists();root.mkdir()
source=T/'original_public_test_update_r28_20261101.py';spec=importlib.util.spec_from_file_location('new_pool_contract',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
J=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda o:(json.dumps(o,indent=2)+'\n').encode()
def put(p,raw):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
F=R/'work/r28gv-r1/Application';old_raw=(F/'release-manifest.json').read_bytes();old=json.loads(old_raw);qraw=(F/'payload-manifest.json').read_bytes();q=json.loads(qraw);assert sha(qraw)==old['payloadManifestSHA256']
app=root/'Application';bundle=root/'bundle';put(app/'release-manifest.json',old_raw);put(app/'payload-manifest.json',qraw)
for n,pin in old['controllerFiles'].items():
    f=F/n;raw=f.read_bytes();assert sha(raw)==pin,n;put(app/n,raw)
for n,pin in {**m.R22_BACKEND_ROWS,**m.R23_ASYNC_ROWS,m.R24_TASK_CLASS:m.R24_TASK_PIN,**m.R25_MATERIAL_ROWS,**m.R26_TEAM_ROWS,**m.R26_TEAM_SOURCE}.items():
    raw=(F/n).read_bytes();assert sha(raw)==pin['sha256'];put(app/n,raw)
programs={n:p for n,p in q['files'].items()if not n.startswith('seed/mysql/')}
logical=sum(p['bytes']for p in programs.values());physical_estimate=len(programs)*4096+32*1024**2;free=shutil.disk_usage(R).free
assert free>max(512*1024**2,physical_estimate*2)and not(G.parent/'user-manual-protected.json').exists()and J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']
put(root/'storage-plan.json',enc({'programLogicalBytes':logical,'programFiles':len(programs),'freeBefore':free,'estimatedAdditionalPhysicalPeak':physical_estimate,'sameVolumeReadOnlyProgramHardlinksExceptExplicitMutableFixtureCopies':True,'assetsReferenceUserDataAndSeedDatabasesExcluded':True}))
for n,pin in programs.items():
    assert not n.startswith(('Assets/','Reference/','UserData/','seed/'))and Path(n).suffix.lower()not in ['.tif','.tiff','.las','.laz','.osgb','.shp','.dlg']
    target=app/n
    if target.exists():continue
    src=m.regular(F,n);assert src.stat().st_size==pin['bytes'];target.parent.mkdir(parents=True,exist_ok=True);os.link(src,target)
new=copy.deepcopy(old);new[m.R27_POOL_FIELD]=copy.deepcopy(m.R27_POOL_POLICY);new[m.R24_WORKFLOW_FIELD]=copy.deepcopy(m.R27_POOL_WORKFLOW_CONTRACT)
files={n:(T/'connection-budget-r139'/Path(n).name).read_bytes()for n in m.R27_POOL_PINS};files['tools/original_public_test_update.py']=source.read_bytes()
for n,raw in files.items():new['controllerFiles'][n]=sha(raw)
files['release-manifest.json']=enc(new);files['payload-manifest.json']=qraw
plan={'schema':'zhumadian.public-test-update.v1','targetApplication':'C:/inetpub/wwwroot/Zhumadian/Application','gatewayPort':18892,'databaseUploadsCredentialsGISOrDependenciesIncluded':False,'releaseId':old['releaseId'],'acceptedOldReleases':{sha(old_raw):{'payloadManifestSHA256':old['payloadManifestSHA256'],'controllerFiles':old['controllerFiles']}},'basePayloadManifestSHA256':old['payloadManifestSHA256'],'newPayloadManifestSHA256':old['payloadManifestSHA256'],'newReleaseSHA256':sha(files['release-manifest.json']),'oldPayloadFiles':{},'legacyEntrySHA256':{},'removedFrontendFiles':{},'files':{n:{'bytes':len(raw),'SHA256':sha(raw)}for n,raw in files.items()}}
for n,raw in files.items():put(bundle/'payload'/n,raw)
cases=[]
def check(name,fn,deny=False):
    refused=False
    try:fn()
    except(ValueError,FileNotFoundError):refused=True
    assert refused==deny,name
    cases.append({'case':name,'expectedRefusal':deny,'passed':True})
def load(p=None,r=None,payload=None):
    pr=copy.deepcopy(plan if p is None else p);nr=copy.deepcopy(new if r is None else r);pq=qraw if payload is None else enc(payload);put(bundle/'payload/payload-manifest.json',pq);nr['payloadManifestSHA256']=sha(pq);pr['newPayloadManifestSHA256']=sha(pq);pr['files']['payload-manifest.json']={'bytes':len(pq),'SHA256':sha(pq)};rr=enc(nr);put(bundle/'payload/release-manifest.json',rr);pr['newReleaseSHA256']=sha(rr);pr['files']['release-manifest.json']={'bytes':len(rr),'SHA256':sha(rr)};raw=enc(pr);put(bundle/'update-manifest.json',raw);return m.load_bundle(app,bundle,sha(raw))
check('complete-exact-old-to-new-control-policy-load',load)
for field,value in [('revision','foreign'),('reservedConnections',0),('mysqlMaximum',100000)]:
    r=copy.deepcopy(new);r[m.R27_POOL_FIELD][field]=value;check('wrong-policy-'+field,lambda r=r:load(r=r),True)
r=copy.deepcopy(new);r.pop(m.R27_POOL_FIELD);check('new-controls-without-policy-refused',lambda:load(r=r),True)
r=copy.deepcopy(new);r[m.R24_WORKFLOW_FIELD]=copy.deepcopy(m.R24_WORKFLOW_CONTRACT);check('new-parameter-with-old-workflow-descriptor-refused',lambda:load(r=r),True)
for n in m.R27_POOL_PINS:
    p=copy.deepcopy(plan);p['files'].pop(n);check('missing-new-source-transport-'+Path(n).name,lambda p=p:load(p=p),True)
    r=copy.deepcopy(new);r['controllerFiles'][n]='0'*64;check('wrong-declared-source-'+Path(n).name,lambda r=r:load(r=r),True)
    f=bundle/'payload'/n;raw=f.read_bytes();put(f,raw+b'foreign');check('new-source-byte-drift-'+Path(n).name,load,True);put(f,raw)
r=copy.deepcopy(new);r['controllerFiles'][m.R23_JOB]='0'*64;check('other-controller-declaration-drift-refused',lambda:load(r=r),True)
pq=copy.deepcopy(q);pq['files'][m.R24_TASK_CLASS]['sha256']='0'*64;check('retained-backend-payload-drift-refused',lambda:load(payload=pq),True)
f=app/m.R24_PARAMETER;raw=f.read_bytes();put(f,raw+b'foreign');check('installed-source-drift-refused-before-update',load,True);put(f,raw)
check('old-version-without-pool-policy-needs-no-new-report',lambda:m.runtime_pool_ready(app,{}))
put(app/'release-manifest.json',enc(new))
for n,raw in files.items():
    if n.startswith('tools/'):put(app/n,raw)
run=app/'UserData/OriginalServer/runs/j1';business=run/'b';put(business/'server-owner.properties',b'schema=zhumadian.original.server.owner.v1\nownerId=own-pool-contract\n');put(business/m.R24_TASK_CLASS.removeprefix('payload/business/run-template/'),(G/m.R24_TASK_CLASS).read_bytes())
row={'run':str(run),'ownerId':'own-pool-contract'};report=run/'connection-budget.json'
budget={'policy':copy.deepcopy(m.R27_POOL_POLICY),'datasources':[{'side':side,'name':name,'hikariMaximum':4,'hikariMinimumIdle':0,'hikariConnectionTimeoutMillis':5000,'druidMaximum':4,'maximumBudget':4}for side,name in [('platform','master'),('business','master'),('business','tow')]],'maximumPoolConnections':12,'reservedConnections':12,'mysqlMaxConnections':24}
put(report,enc(budget));check('owned-runtime-exact-policy-and-budget',lambda:m.runtime_pool_ready(app,row))
for field,value in [('maximumPoolConnections',13),('mysqlMaxConnections',25),('reservedConnections',0),('unknown',1)]:
    b=copy.deepcopy(budget);b[field]=value;put(report,enc(b));check('bad-runtime-total-'+field,lambda:m.runtime_pool_ready(app,row),True)
for field,value in [('hikariMaximum',0),('hikariMinimumIdle',5),('hikariConnectionTimeoutMillis',1),('name','../../private'),('maximumBudget',5),('side','foreign'),('hikariMaximum',True)]:
    b=copy.deepcopy(budget);b['datasources'][0][field]=value;put(report,enc(b));check('bad-runtime-row-'+field+str(len(cases)),lambda:m.runtime_pool_ready(app,row),True)
b=copy.deepcopy(budget);b['datasources'].append(copy.deepcopy(b['datasources'][0]));put(report,enc(b));check('duplicate-runtime-datasource-refused',lambda:m.runtime_pool_ready(app,row),True)
put(report,enc(budget));check('foreign-runtime-owner-refused',lambda:m.runtime_pool_ready(app,dict(row,ownerId='foreign')),True)
put(report,b' '*16385);check('oversized-runtime-report-refused',lambda:m.runtime_pool_ready(app,row),True);put(report,enc(budget));report.unlink();check('missing-runtime-report-refused',lambda:m.runtime_pool_ready(app,row),True)
result={'schema':'xnby.r28.pool-policy-contract.v1','allPassed':True,'checks':len(cases),'cases':cases,'sourceSHA256':sha(source.read_bytes()),'actualServicesOrSQLOrProtectedUserRootsOperated':False,'normalStopRecoveryFunctionsKept':True};put(root/'result.json',enc(result));put(D/'r28-pool-contract-verification.json',enc(result));print(json.dumps({k:v for k,v in result.items()if k!='cases'}))
