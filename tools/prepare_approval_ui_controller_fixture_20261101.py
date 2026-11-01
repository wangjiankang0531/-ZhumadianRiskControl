"""Prepare only an owned synthetic full-controller fixture; never read installed secrets/DBs."""
from pathlib import Path
import hashlib,importlib.util,json,os,re,secrets,shutil,socket,subprocess,sys,time,uuid

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';sys.path.insert(0,str(T))
from original_full_platform_probe_config_20261031 import build as platform_configuration
from original_compiled_portal_inputs_20261031 import frontend_wire_key
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def dump(p,value):p.write_text(json.dumps(value,indent=2),encoding='utf-8')
app=R/'_e/Application';root=R/'work/event_delivery_consistency_20261030/full-controller-r123'
root.mkdir(exist_ok=True)
assert all(p.is_dir() and p.name in ['tmp','classes']and not any(p.iterdir())for p in root.iterdir()if p.name!='code-prepared.json')
(root/'tmp').mkdir(exist_ok=True);(root/'classes').mkdir(exist_ok=True)
assert read(R/'_e/own-fixture.json')['ownedSyntheticFixtureOnly']
assert not(app/'UserData/OriginalServer').exists()
release=read(app/'release-manifest.json');payload=read(app/'payload-manifest.json')
assert sha(app/'tools/serve_original_server_release.py')=='8b6006fac79e096939bfb7b2cffc333c1bcd39dc01f9d43070c68dee4f402660'
assert sha(app/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
source=R/'work/event_delivery_consistency_20261030/full-business-main-r114'
assert read(source/'storage-plan.json')['originalDataCopied']is False
assert read(source/'native-engine-system-prepared.json')['originalAccountOrBusinessRowsCopied']is False
assert read(source/'independent-unified-observed.json')['disposalAndReopenBrowserChecks']==20
assert read(source/'mysql-stopped.json')['exitCode']==0
command="[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; Get-CimInstance Win32_Process -Filter \"Name='mysqld.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
result=subprocess.run(['powershell.exe','-NoProfile','-Command',command],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
assert result.returncode==0
live=json.loads(result.stdout.decode('utf-8-sig'))if result.stdout.strip()else[]
live=[]if live is None else(live if isinstance(live,list)else[live])
assert not any(str(source/'data').lower()in(row.get('CommandLine')or'').lower()for row in live)
data_source=source/'data';before={p.relative_to(data_source).as_posix():sha(p)for p in data_source.rglob('*')if p.is_file()}
assert before and shutil.disk_usage(root).free>2*1024**3
for p in [data_source,*data_source.rglob('*')]:assert not p.is_symlink()and not p.lstat().st_file_attributes&0x400
data=app/'UserData/OriginalServer/database/data';shutil.copytree(data_source,data)
assert before=={p.relative_to(data).as_posix():sha(p)for p in data.rglob('*')if p.is_file()}
bootstrap=(source/'own-bootstrap.sql').read_text(encoding='ascii')
match=re.search(r"ALTER USER 'root'@'localhost' IDENTIFIED BY '([0-9a-f]{32})';",bootstrap);assert match
password=match[1];bootstrap=None;db_uuid=str(uuid.uuid4());owner=str(uuid.uuid4())
(data/'auto.cnf').write_text('[auto]\nserver-uuid='+db_uuid+'\n',encoding='ascii')
server=app/'UserData/OriginalServer';(server/'store-data').mkdir()
dump(server/'installation.json',{'schema':'zhumadian.original.server.data.v1','ownerId':owner,'releaseId':release['releaseId'],'databaseUUID':db_uuid})
dump(server/'store-credentials.private.json',{'accessKey':'own-'+secrets.token_hex(8),'secretKey':secrets.token_hex(24)})
tables=read(source/'schema-models.json')['tables'];assert len(tables)==398
(root/'original-table-names.txt').write_text(''.join(t['schema']+'.'+t['table']+'\n'for t in sorted(tables,key=lambda t:(t['schema'],t['table']))),encoding='ascii')
java=app/'runtime/jdk17/bin/java.exe';javac=java.with_name('javac.exe')
java_source=T/'java/unified_controller_lifecycle_fixture_r1/OwnControllerSchemaSnapshot.java'
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']}
env.update(TEMP=str(root/'tmp'),TMP=str(root/'tmp'))
compiled=subprocess.run([str(javac),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(root/'classes'),str(java_source),str(T/'java/approval_ui_fixture_r1/OwnWorkflowPortalMenusFixture.java'),str(T/'java/approval_ui_fixture_r1/OwnWorkflowFormStorageFixture.java')],env=env,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
assert compiled.returncode==0
drivers=list((app/'payload/business/lib').glob('mysql-connector-*.jar'));assert len(drivers)==1
cp=str(root/'classes')+';'+str(drivers[0]);dump(root/'schema-reader.json',{'classpath':cp,'java':str(java),'sourceSHA256':sha(java_source)})
with socket.socket()as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
grant=root/'owned-normal-stop-grant.private.sql';grant.write_text("GRANT SHUTDOWN ON *.* TO 'root'@'127.0.0.1';\n",encoding='ascii')
cnf=root/'owned-clone-client.private.cnf';cnf.write_text('[client]\nhost=127.0.0.1\nport='+str(port)+'\nuser=root\npassword="'+password+'"\n',encoding='ascii')
mysqld=app/'runtime/mysql/bin/mysqld.exe';mysqladmin=mysqld.with_name('mysqladmin.exe')
cmd=[str(mysqld),'--no-defaults','--no-monitor','--basedir='+str(mysqld.parent.parent),'--datadir='+str(data),'--lower-case-table-names=1','--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M','--innodb-data-file-path=ibdata1:12M:autoextend:max:256M','--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M','--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL','--event-scheduler=OFF','--bind-address=127.0.0.1','--port='+str(port),'--pid-file='+str(root/'own-mysqld.pid'),'--console','--max-connections=24','--skip-slave-start','--init-file='+str(grant)]
spec=importlib.util.spec_from_file_location('nonterminating_job',app/'tools/original_server_windows_job.py');j=importlib.util.module_from_spec(spec);spec.loader.exec_module(j)
process=None;job=None
with (root/'prepare-mysql.private.log').open('wb')as log:
    try:
        process=subprocess.Popen(cmd,cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        job=j.OwnedWindowsJob(process);end=time.monotonic()+60
        while b'ready for connections'not in(root/'prepare-mysql.private.log').read_bytes():
            assert process.poll()is None and time.monotonic()<end,'OWN_CLONE_DATABASE_NOT_READY';time.sleep(.1)
        seeded=subprocess.run([str(java),'-Xmx128m','-cp',cp,'OwnWorkflowPortalMenusFixture',str(port),db_uuid,str(data)],env=env,input=password.encode(),capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        assert seeded.returncode==0,'OWN_WORKFLOW_MENUS_SEED_FAILED'
        scratch_form=subprocess.run([str(java),'-Xmx128m','-cp',cp,'OwnWorkflowFormStorageFixture',str(port),db_uuid,str(data)],env=env,input=password.encode(),capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
        assert scratch_form.returncode==0,'OWN_APPROVAL_FORM_STORAGE_PREPARE_FAILED'
        dump(root/'own-form-storage-prepared.json',json.loads(scratch_form.stdout.decode('utf-8')))
        result=subprocess.run([str(java),'-Xmx128m','-cp',cp,'OwnControllerSchemaSnapshot',str(port),db_uuid,str(data),str(root/'original-table-names.txt'),str(root/'schema-before.json')],env=env,input=password.encode(),capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
        assert result.returncode==0,'OWN_CLONE_SCHEMA_BASELINE_FAILED'
    finally:
        if process:
            while process.poll()is None:
                subprocess.run([str(mysqladmin),'--defaults-extra-file='+str(cnf),'shutdown'],env=env,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(.2)
            if job:
                while job.active_processes():time.sleep(.1)
                job.close()
assert process.returncode==0
dump(root/'synthetic-database-prepared.json',{'mysqlExitCode':0,'onlyOwnedSyntheticR114DatasetCopied':True,
    'originalPrivateConfigurationOrDatabaseRead':False,'normalStopGrantAddedOnlyToSyntheticClone':True,
    'sourceDatasetByteHashesUnchanged':before=={p.relative_to(data_source).as_posix():sha(p)for p in data_source.rglob('*')if p.is_file()},
    'sourceDatasetBytes':sum(p.stat().st_size for p in data_source.rglob('*')if p.is_file()),'schemaBefore':read(root/'schema-before.json')})
# Create synthetic settings using the previously tested source-default whitelist.
scratch=root/'configuration-scratch/Application/UserData/TianjinOriginalPlatform/runs/j1';scratch.mkdir(parents=True)
props=platform_configuration(scratch,app/'payload/platform/original-platform.jar',18991,18992,18993,password,'own-fixture',owner)
props['security.SecurityKey']=frontend_wire_key()
props['context.initializer.classes']=','.join(n for n in props['context.initializer.classes'].split(',')if n!='xnby.platform.OriginalTaskTokenBridgeSpringRegistration')
scratch_data=scratch.parents[1]
platform_props={k:v.replace(scratch.as_posix(),'${PLATFORM_RUN}').replace(scratch_data.as_posix(),'${PLATFORM_DATA}')for k,v in props.items()}
base='http://127.0.0.1:18990'
b={'spring.application.name':'cqweh-endanger','server.address':'127.0.0.1','server.port':'0','server.servlet.context-path':'/',
   'spring.main.banner-mode':'off','spring.main.allow-circular-references':'true','spring.cloud.bootstrap.enabled':'false',
   'spring.cloud.discovery.enabled':'false','spring.cloud.nacos.discovery.enabled':'false','spring.cloud.nacos.config.enabled':'false',
   'spring.jmx.enabled':'false','management.endpoints.enabled-by-default':'false','spring.datasource.dynamic.primary':'master',
   'spring.datasource.dynamic.strict':'true','spring.datasource.dynamic.druid.initial-size':'0','spring.datasource.dynamic.druid.min-idle':'0',
   'spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.max-wait':'5000',
   'spring.data.redis.host':'127.0.0.1','spring.data.redis.port':'18992','spring.data.redis.password':password,'spring.data.redis.database':'0',
   'minio.url':'127.0.0.1','minio.port':'18993','minio.secure':'false','minio.accessKey':'own-fixture','minio.secretKey':password,
   'minio.bucket':'own-full-main','minio.bucketName':'own-full-main','flow.url':base,'flow.code':'OWN_FORM_CODE',
   'flow.event-task-handle':'OWN_FORM_CODE','safety.jnpfUrl':base,'riskReportDb':'OWN_REPORT_DB','safetyEmergencyDb':'OWN_REPORT_DB',
   'context.initializer.classes':'xnby.replica.ServerLifecycleObservation','logging.level.root':'INFO','logging.file.name':'${BUSINESS_RUN}/logs/business.log'}
for key in ['swagger.token','meteorological.token','riskReportToken','safetyEmergencyToken','workReportToken','otherWorkReportToken','otherRiskReportToken','otherThirdToken']:b[key]='OWN_'+uuid.uuid4().hex
for key in ['meteorological.url','riskReportUrl','safetyEmergencyUrl','workReportUrl','otherWorkReportUrl','otherRiskReportUrl','otherThirdUrl']:b[key]=base+'/own-unavailable'
for name,db in [('master','tj_endanger'),('tow','jnpf')]:
    prefix='spring.datasource.dynamic.datasource.'+name+'.'
    b.update({prefix+'url':'jdbc:mysql://127.0.0.1:18991/'+db+'?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=15000',prefix+'username':'root',prefix+'password':password,prefix+'driver-class-name':'com.mysql.cj.jdbc.Driver'})
meta=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
classpath=[]
for source_path in meta['classpath'].split(';'):
    name=Path(source_path).name;relative='payload/business/'+name if name in ['application.jar','process-boundary.jar']else'payload/business/lib/'+name
    target=app/relative;assert target.is_file()and sha(target)==payload['files'][relative]['sha256']
    classpath.append('${APP}/'+relative)
business_cp=';'.join(['${BUSINESS_RUN}/classes','${APP}/payload/business/legacy-classes','${APP}/payload/business/scheduling-isolation.jar',*classpath])
platform_cp=';'.join(['${PLATFORM_RUN}/wrapper-classes','${PLATFORM_RUN}/persistent-launcher-classes','${APP}/payload/platform/process-boundary.jar','${APP}/payload/platform/boot-loader.jar'])
platform_args=['-Xmx768m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Down.platform.root=${PLATFORM_RUN}','-Down.platform.source.path=${APP}/payload/platform/original-platform.jar','-Down.platform.manage.id-generator-shutdown=true','-Duser.home=${PLATFORM_RUN}/home','-Djava.awt.headless=true','-DLOG_PATH=${PLATFORM_RUN}/logs','-Dspring.cloud.bootstrap.enabled=false','-Dspring.cloud.discovery.enabled=false','-Dspring.cloud.nacos.discovery.enabled=false','-Dspring.cloud.nacos.config.enabled=false','-cp',platform_cp,'xnby.platform.OriginalPersistentPlatformLaunch','${APP}/payload/platform/original-platform.jar','${PLATFORM_RUN}']
business_args=['-Xmx512m','-XX:ActiveProcessorCount=2','--add-opens','java.base/java.lang=ALL-UNNAMED','--add-opens','java.base/java.io=ALL-UNNAMED','--add-opens','java.rmi/sun.rmi.transport=ALL-UNNAMED','-Dfile.encoding=UTF-8','-Down.direct.main=true','-Down.internal.platform.base='+base,'-Djava.awt.headless=true','-Duser.home=${BUSINESS_RUN}/home','-cp',business_cp,'xnby.replica.OriginalBusinessLaunch','${BUSINESS_RUN}']
config={'schema':'zhumadian.original.server.configuration.v1','seedRootPassword':password,
        'configuration':{'platform':platform_props,'business':b},'platformArguments':platform_args,'businessArguments':business_args}
private=app/'private/server-configuration.json';private.parent.mkdir(exist_ok=True);private.write_text(json.dumps(config,ensure_ascii=True,indent=2),encoding='ascii')
payload['files']['private/server-configuration.json']={'bytes':private.stat().st_size,'sha256':sha(private)}
(app/'payload-manifest.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
release['payloadManifestSHA256']=sha(app/'payload-manifest.json')
(app/'release-manifest.json').write_text(json.dumps(release,indent=2)+'\n',encoding='utf-8')
dump(root/'controller-fixture-ready.json',{'application':str(app),'releaseSHA256':sha(app/'release-manifest.json'),
    'controllerSHA256':sha(app/'tools/serve_original_server_release.py'),'jobSHA256':sha(app/'tools/original_server_windows_job.py'),
    'updaterSHA256':sha(app/'tools/original_public_test_update.py'),'allProgramBytesRemainCandidate':True,
    'syntheticConfigurationAndIdentityOnly':True,'databasePreparedAndNormallyStopped':True,'realPrivateOrSeedRead':False,
    'wholeControllerActuallyStarted':False})
password=None;config=None
print('OWNED_SYNTHETIC_DATABASE_CONFIG_AND_EXACT_CONTROLLER_FIXTURE_READY_NO_REAL_PRIVATE_OR_SEED_READ')
