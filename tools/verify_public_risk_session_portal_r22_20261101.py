"""Pinned published R21 business launch + R22 risk classes on fresh synthetic 398-table storage.
This verifies business compatibility; it does not claim full native-platform login or merged browser acceptance.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,socket,subprocess,sys,time,uuid,threading,urllib.request,importlib.util
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
sys.dont_write_bytecode=True
T=Path('D:/Project/Zhumadian/Application/tools');sys.path.insert(0,str(T))
import verify_emergency_business_http_20261030 as c
from original_r4_identity_stopped_observation_v2_20261031 import observe
from original_task_identity_authority import listener_owner
from original_object_store_runtime import stop_owned_provider
from original_whole_business_isolated_redis_20261031 import AuditRedis
from original_full_platform_probe_config_20261031 import build as platform_configuration
from original_compiled_portal_inputs_20261031 import frontend_wire_key
import zipfile,re
class UnavailablePeer(BaseHTTPRequestHandler):
 def do_GET(self):
  body=b'{"code":503,"msg":"OWN_PLATFORM_NOT_STARTED"}';self.send_response(503);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 do_POST=do_GET
 def log_message(self,*a):pass

def main():
 p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--prepared-short',action='store_true');args=p.parse_args()
 assert __import__('re').fullmatch(r'r[1-9][0-9]*',args.revision)
 root=c.W/('full-business-main-'+args.revision);short=c.R/'_b';assert not root.exists() and args.prepared_short
 prepared=c.read(short/'own-fixture.json');assert prepared['evidenceRoot']==str(root)and prepared['preparedRuntime']and Path(sys.executable).resolve()==short/'Application/runtime/python/python.exe'
 assert shutil.disk_usage(c.W).free>3*1024**3
 before,held=observe(),c.protected();root.mkdir();owner=prepared['owner'];app=short/'Application';business=app/'UserData/OriginalServer/runs/j1/b';platform=app/'UserData/TianjinOriginalPlatform/runs/j1'
 for folder in [root/'classes',root/'tmp',business,platform]:folder.mkdir(parents=True,exist_ok=True)
 for n in ['tmp','home','logs']:(business/n).mkdir()
 c.dump(root/'short-runtime.json',{'owner':owner,'business':str(business),'root':str(short)})
 active=c.R/'work/user_feedback_20261031/r22-risk-candidate-r3';candidate=c.read(active/'candidate-stage.json');old=c.read(active/'r21-base-payload-manifest.json')['files'];template='payload/business/run-template/'
 for n,pin in old.items():
  if n.startswith(template):
   origin=c.Q/n
   if not origin.exists()or c.sha(origin)!=pin['sha256']:origin=c.R/'work/user_feedback_20261031/public-r21-template-recovery-r1'/n
   assert c.sha(origin)==pin['sha256'];target=business/n[len(template):];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin,target)
 for n,pin in old.items():
  prefix='payload/platform/run-template/'
  if n.startswith(prefix):
   origin=c.Q/n;assert c.sha(origin)==pin['sha256'];target=platform/n[len(prefix):];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin,target)
 overlay=c.Q/'payload/callback-overlay/20261026-password-identity';assert c.sha(overlay/'manifest.json')=='91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb'
 overlayManifest=c.read(overlay/'manifest.json')
 for n in ['OriginalBusinessLaunch','OriginalBusinessListenBoundary']:
  relative='business-classes/xnby/replica/'+n+'.class';assert c.sha(overlay/relative)==overlayManifest['files'][relative]['SHA256'];shutil.copyfile(overlay/relative,business/'classes/xnby/replica'/(n+'.class'))
 for relative in ['persistent-launcher-classes/xnby/platform/OriginalPersistentPlatformLaunch.class','persistent-launcher-classes/xnby/platform/OriginalPlatformCallbackScope.class']:
  assert c.sha(overlay/relative)==overlayManifest['files'][relative]['SHA256'];target=platform/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(overlay/relative,target)
 auth=overlay/'own-platform-observation.jar';assert c.sha(auth)=='eae7642792992da2ed4d2f6ff94f55001bda649888c754ffb0aeba4a39ae19d5';shutil.copyfile(auth,platform/'own-platform-observation.jar')
 for item in candidate['backendOperations']:
  source=active/'payload'/item['relative'];assert c.sha(source)==item['newSHA256'];target=business/'classes'/item['relative'].split('/classes/',1)[1];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
 parameterSource=active/'public-control/tools/original_server_release_parameters.py';assert c.sha(parameterSource)=='8e8a7ee659ae765a0bc8248b3da107e14a9bdc293840aeb745553f6a8f7ac1f9'
 module=importlib.util.spec_from_file_location('exact_published_parameters',parameterSource);parameters=importlib.util.module_from_spec(module);module.loader.exec_module(parameters)
 for target in [business,platform]:(target/'server-owner.properties').write_bytes(parameters.properties_ascii({'schema':'zhumadian.original.server.owner.v1','ownerId':owner}))
 models=c.read(c.R/'Application/work/tianjin_native_20261023/own-mysql-r26/restored-verification-export/catalog.json');tables=[]
 for row in models['tablesAndViews']:
  if row['TABLE_SCHEMA']in ['jnpf','tj_endanger']:tables.append({'schema':row['TABLE_SCHEMA'],'table':row['TABLE_NAME'],'ddl':__import__('re').sub(r'\bAUTO_INCREMENT=\d+\s*','',row['create']['Create Table'])})
 assert len(tables)==398;c.dump(root/'schema-models.json',{'tables':tables,'originalRowsOrAccountsIncluded':False});c.dump(root/'storage-plan.json',{'freeBefore':shutil.disk_usage(c.W).free,'estimatedTemporaryPeakBytes':1610612736,'originalDataCopied':False})
 meta=c.read(c.R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json');java=Path(meta['java']);assert c.sha(java)==meta['javaSHA256']
 for name,pin in meta['inputPins'].items():assert c.sha(name)==pin['SHA256']
 cp=';'.join([str(business/'classes'),str(root/'classes'),str(c.Q/'payload/business/scheduling-isolation.jar'),meta['classpath']])
 sources=[T/'java/OriginalWholeBusinessSchemaFixture.java',T/'java/OriginalSocketProcessBoundary.java',*sorted((T/'java/public_risk_session_chain_fixture_r1').glob('*.java'))]
 sources+=[*sorted((T/'java/public_risk_portal_fixture_r1').glob('*.java'))]
 production=c.R/'work/user_feedback_20261031/security-build-risk-r22-from-r21-r2';environment=(production/'source/.env').read_text(encoding='utf-8');match=re.search(r'^VITE_ORG_ID=([A-Za-z0-9-]{1,64})$',environment,re.M);assert match;organization=match[1];assert any(organization in p.read_text(encoding='utf-8')for p in(production/'build/dist/assets/js').glob('*.js'));orgFlag='-Down.fixture.production.organization.id='+organization
 c.dump(root/'production-build-contract.json',{'actualUnchangedProductionFrontendUsed':True,'productionOrganizationIDFoundInCompiledArtifact':True,'syntheticDirectoryUsesCompatibleRootOnly':True,'frontendNotRebuiltForQA':True})
 controls=root/'executed-control-sources';controls.mkdir()
 for src in [*sources,Path(__file__),parameterSource]:shutil.copyfile(src,controls/src.name)
 extraSources=[T/n for n in ['original_public_risk_login_http_r22_20261101.py', 'original_public_risk_portal_chain_r22_20261101.py', 'original_public_risk_newest_http_r22_20261101.py', 'original_public_risk_portal_host_r22_20261101.py', 'original_risk_unit_portal_session_handoff_20261031.py', 'verify_compiled_public_risk_portal_r22_20261101.mjs', 'original_full_platform_probe_config_20261031.py']]+[T/'java/original_platform_runtime8/OriginalFlowableSystemMetadataFixture.java',T/'java/original_platform_runtime8/OriginalFlowableSystemMetadataLaunch.java']
 for src in extraSources:shutil.copyfile(src,controls/src.name)
 c.dump(root/'source-pins.json',{str(s):c.sha(s)for s in [*sources,*extraSources,Path(__file__),parameterSource]});c.dump(root/'production-class-pins.json',{str(p.relative_to(business)):c.sha(p)for p in business.rglob('*.class')})
 c.run(root,'compile',[java.with_name('javac.exe'),'-J-Xmx256m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',root/'classes',*sources],45)
 fixture=T/'test-data/risk-import-atomic-r83';(business/'own-import-fixtures').mkdir()
 for n,pin in c.read(fixture/'fixture-manifest.json')['files'].items():assert c.sha(fixture/n)==pin['sha256'];shutil.copyfile(fixture/n,business/'own-import-fixtures'/n)
 exe=c.Q/'runtime/mysql/bin/mysqld.exe';assert c.sha(exe)=='47ffd2c32f36e5cb79f78bed0ff5272d7559c383f88c43c753470d5a5dfbe8a0'
 env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME']};env.update(TEMP=str(root/'tmp'),TMP=str(root/'tmp'))
 base=[str(exe),'--no-defaults','--no-monitor','--basedir='+str(exe.parent.parent),'--datadir='+str(root/'data'),'--lower-case-table-names=1','--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M','--innodb-data-file-path=ibdata1:12M:autoextend:max:256M','--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M','--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL','--console','--max-connections=24','--skip-slave-start']
 with open(root/'initialize.log','wb')as log:
  init=subprocess.Popen(base+['--initialize-insecure'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);init.wait(timeout=100);assert init.returncode==0;c.dump(root/'initialize-process.json',{'pid':init.pid,'exitCode':init.returncode})
 own_uuid=next(x.split('=',1)[1].strip()for x in(root/'data/auto.cnf').read_text().splitlines()if x.startswith('server-uuid='));secret=uuid.uuid4().hex.encode();password=secret.decode();nonce=uuid.uuid4().hex;port=c.port();businessPort=c.port();objectPort=c.port();consolePort=c.port()
 bootstrap=root/'own-bootstrap.sql';bootstrap.write_text("ALTER USER 'root'@'localhost' IDENTIFIED BY '"+password+"';\nCREATE DATABASE jnpf CHARACTER SET utf8mb4;\nCREATE DATABASE tj_endanger CHARACTER SET utf8mb4;\nCREATE USER 'xnby_whole_main'@'127.0.0.1' IDENTIFIED BY '"+password+"';\nGRANT ALL PRIVILEGES ON jnpf.* TO 'xnby_whole_main'@'127.0.0.1';\nGRANT ALL PRIVILEGES ON tj_endanger.* TO 'xnby_whole_main'@'127.0.0.1';\nGRANT SHUTDOWN ON *.* TO 'xnby_whole_main'@'127.0.0.1';\n",encoding='ascii')
 with bootstrap.open('a',encoding='ascii')as sql:sql.write("CREATE USER 'root'@'127.0.0.1' IDENTIFIED BY '"+password+"';\nGRANT ALL PRIVILEGES ON jnpf.* TO 'root'@'127.0.0.1';\nGRANT ALL PRIVILEGES ON tj_endanger.* TO 'root'@'127.0.0.1';\n")
 seedSchema='xnby_native_schema_'+owner.replace('-','')
 with bootstrap.open('a',encoding='ascii')as sql:sql.write('CREATE DATABASE `'+seedSchema+'` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;\nGRANT ALL PRIVILEGES ON `'+seedSchema+"`.* TO 'xnby_whole_main'@'127.0.0.1';\n")
 cache=mysql=store=process=peer=identity=None;logs=[];failure=None
 def schema(label,mode):c.run(root,label,[java,'-Xmx256m','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-cp',cp,'xnby.replica.OriginalWholeBusinessSchemaFixture',root,port,own_uuid,mode],90,secret)
 snapshotNonce=uuid.uuid4().hex
 def login_snapshot(phase):
  assert phase in ('negative','positive','final');url='http://127.0.0.1:'+str(businessPort)+'/serv/__own_readonly__/login-snapshot?phase='+phase;request=urllib.request.Request(url,headers={'X-OWN-READONLY':snapshotNonce,'Accept':'application/json'});opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  with opener.open(request,timeout=12)as response:raw=response.read(65537);assert response.status==200 and len(raw)<=65536
  result=json.loads(raw);assert result['readOnlyExistingPoolConnection']and result['maxConnections']==24 and not result['databasePrivilegesChanged'];c.dump(root/('normal-login-snapshot-'+phase+'.json'),result['users']);c.dump(root/('own-readonly-pool-observation-'+phase+'.json'),{k:v for k,v in result.items()if k!='users'})
 try:
  cache=AuditRedis(root,secret,nonce);cache.start();mysqlLog=open(root/'mysql.log','wb');logs.append(mysqlLog);mysql=subprocess.Popen(base+['--bind-address=127.0.0.1','--port='+str(port),'--pid-file='+str(root/'own-mysqld.pid'),'--init-file='+str(bootstrap)],cwd=root,env=env,stdout=mysqlLog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  c.dump(root/'mysql-started.json',{'pid':mysql.pid});deadline=time.monotonic()+45
  while'ready for connections'not in(root/'mysql.log').read_text(encoding='utf-8',errors='replace'):assert mysql.poll()is None and time.monotonic()<deadline;time.sleep(.1)
  assert listener_owner(port)==[('127.0.0.1',mysql.pid)];schema('restore','restore')
  native=c.Q/'payload/platform/original-platform.jar';assert c.sha(native)=='294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8'
  seedLibraries=root/'native-seed-libraries';seedLibraries.mkdir();seedClasses=root/'native-seed-classes';seedClasses.mkdir();seedCP=[]
  with zipfile.ZipFile(native)as archive:
   for entry in archive.namelist():
    name=Path(entry).name
    if entry.startswith('BOOT-INF/lib/')and name.endswith('.jar')and name.startswith(('flowable-','jackson-','mybatis-','spring-','slf4j-api-','javax.servlet-api-')):
     dest=seedLibraries/name;dest.write_bytes(archive.read(entry));seedCP.append(dest)
  boot=c.Q/'payload/platform/boot-loader.jar';boundary=c.Q/'payload/platform/process-boundary.jar';compileCP=';'.join(map(str,[boot,boundary,platform/'wrapper-classes',*seedCP]));seedSources=[T/'java/original_platform_runtime8'/name for name in ['OriginalFlowableSystemMetadataFixture.java','OriginalFlowableSystemMetadataLaunch.java']]
  c.run(root,'compile-native-seed',[java.with_name('javac.exe'),'-J-Xmx256m','-source','8','-target','8','-encoding','UTF-8','-proc:none','-cp',compileCP,'-d',seedClasses,*seedSources],45);seedJar=root/'native-seed-helper.jar'
  with zipfile.ZipFile(seedJar,'w',zipfile.ZIP_DEFLATED)as archive:
   for entry in seedClasses.rglob('*.class'):archive.write(entry,entry.relative_to(seedClasses).as_posix())
  launcherClasses=root/'native-seed-launcher-classes';launcherTarget=launcherClasses/'xnby/platform/OriginalFlowableSystemMetadataLaunch.class';launcherTarget.parent.mkdir(parents=True);shutil.copyfile(seedClasses/'xnby/platform/OriginalFlowableSystemMetadataLaunch.class',launcherTarget);runCP=';'.join(map(str,[launcherClasses,platform/'wrapper-classes',boundary,boot]));java8=app/'runtime/jdk8/bin/java.exe';assert c.sha(java8)==c.sha(c.Q/'runtime/jdk8/bin/java.exe')
  c.run(root,'native-engine-prepare',[java8,'-Xmx384m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-Down.platform.root='+str(root),'-Down.platform.source.path='+str(native),'-Djava.io.tmpdir='+str(root/'tmp'),'-Duser.home='+str(root/'tmp'),'-cp',runCP,'xnby.platform.OriginalFlowableSystemMetadataLaunch',native,seedJar,root,port,own_uuid,seedSchema],90,secret)
  c.run(root,'normal-login-seed',[java,'-Xmx192m','-Dfile.encoding=UTF-8',orgFlag,'-cp',cp,'xnby.replica.OriginalCompiledPortalLoginDataFixture',root,port,own_uuid,'seed'],35,secret)
  c.run(root,'risk-unit-seed',[java,'-Xmx128m','-Dfile.encoding=UTF-8',orgFlag,'-cp',cp,'xnby.replica.OriginalRiskUnitDataFixture',root,port,own_uuid],35,secret)
  c.run(root,'risk-portal-directory-seed',[java,'-Xmx128m','-Dfile.encoding=UTF-8',orgFlag,'-cp',cp,'xnby.replica.OriginalRiskUnitPortalDataFixture',root,port,own_uuid],35,secret)
  peer=ThreadingHTTPServer(('127.0.0.1',0),UnavailablePeer);thread=threading.Thread(target=peer.serve_forever,daemon=True);thread.start();peerPort=peer.server_port;peerBase='http://127.0.0.1:'+str(peerPort)
  storeRoot=root/'object-store';storeRoot.mkdir()
  for name in ['data','certs','tmp','profile','appdata','localappdata']:(storeRoot/name).mkdir()
  objectAccess='own-'+nonce[:16];minio=c.Q/'runtime/minio/minio.exe';assert c.sha(minio)==c.read(c.Q/'payload-manifest.json')['files']['runtime/minio/minio.exe']['sha256']
  storeEnv={k:v for k,v in env.items()if k.upper()in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS']};storeEnv.update(PATH=str(Path(os.environ['SystemRoot'])/'System32'),TEMP=str(storeRoot/'tmp'),TMP=str(storeRoot/'tmp'),APPDATA=str(storeRoot/'appdata'),LOCALAPPDATA=str(storeRoot/'localappdata'),USERPROFILE=str(storeRoot/'profile'),MINIO_ROOT_USER=objectAccess,MINIO_ROOT_PASSWORD=password,MINIO_BROWSER='off',MINIO_UPDATE='off',MINIO_CALLHOME_ENABLE='off',GOMAXPROCS='2')
  storeLog=open(root/'minio.log','wb');logs.append(storeLog);store=subprocess.Popen([str(minio),'--quiet','--certs-dir',str(storeRoot/'certs'),'server','--address','127.0.0.1:'+str(objectPort),'--console-address','127.0.0.1:'+str(consolePort),str(storeRoot/'data')],cwd=storeRoot,env=storeEnv,stdout=storeLog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);c.dump(root/'object-store-started.json',{'pid':store.pid});deadline=time.monotonic()+35
  while True:
   assert store.poll()is None and time.monotonic()<deadline
   try:
    with urllib.request.urlopen('http://127.0.0.1:'+str(objectPort)+'/minio/health/ready',timeout=2)as response:assert response.status==200
    break
   except OSError:time.sleep(.1)
  platformProps=platform_configuration(platform,native,port,cache.port,objectPort,password,objectAccess,owner);platformProps['security.SecurityKey']=frontend_wire_key();platformProps['context.initializer.classes']=','.join(n for n in platformProps['context.initializer.classes'].split(',')if n!='xnby.platform.OriginalTaskTokenBridgeSpringRegistration')
  for name in ['tmp','home','logs']:(platform/name).mkdir(exist_ok=True)
  callbacks=c.read(overlay/'callback-route-pins.json');assert len(callbacks)==7
  platformArguments=['-D'+k+'='+v for k,v in {'own.platform.root':str(platform),'own.platform.source.path':str(native),'own.platform.manage.id-generator-shutdown':'true','user.home':str(platform/'home'),'java.awt.headless':'true','LOG_PATH':str(platform/'logs'),'spring.cloud.bootstrap.enabled':'false','spring.cloud.discovery.enabled':'false','spring.cloud.nacos.discovery.enabled':'false','spring.cloud.nacos.config.enabled':'false'}.items()]
  nativeSpec={'configuration':{'platform':platformProps},'platformArguments':platformArguments};platformPackage=parameters.materialize(nativeSpec,side='platform',application=app,platform_run=platform,business_run=business,platform_data_owner=owner,run_owner=owner,database_uuid=own_uuid,database_port=port,redis_port=cache.port,object_port=objectPort,database_password=password,redis_password=password,object_access=objectAccess,object_secret=password,business_port=businessPort,callback_pins=callbacks)
  (platform/'application.properties').write_bytes(platformPackage['properties']);(platform/'callback-route-pins.json').write_bytes(platformPackage['callbackRoutingPinsBytes']);c.dump(root/'platform-production-input-pins.json',{str(p.relative_to(platform)):c.sha(p)for p in platform.rglob('*')if p.is_file()and p.suffix in ('.class','.jar')})
  cp8=';'.join(map(str,[platform/'wrapper-classes',platform/'persistent-launcher-classes',boundary,boot]));nativeOut=open(root/'identity.stdout.log','wb');nativeErr=open(root/'identity.stderr.log','wb');logs.extend([nativeOut,nativeErr]);identity=subprocess.Popen([str(java8),'-Xmx768m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8',*platformPackage['arguments'],'-cp',cp8,'xnby.platform.OriginalPersistentPlatformLaunch',str(native),str(platform)],cwd=platform,env=dict(env,TEMP=str(platform/'tmp'),TMP=str(platform/'tmp')),stdin=subprocess.DEVNULL,stdout=nativeOut,stderr=nativeErr,creationflags=subprocess.CREATE_NO_WINDOW);c.dump(root/'identity-started.json',{'pid':identity.pid,'actualPublishedFullPlatformMain':True,'adapterJarUnmodified':True,'syntheticNonAdministratorAccountsOnly':True});deadline=time.monotonic()+115
  while not((platform/'server-ready.txt').exists()and(platform/'password-identity-claims-ready.properties').exists()):
   assert identity.poll()is None,'NATIVE_PLATFORM_EXITED_BEFORE_READY';assert time.monotonic()<deadline,'NATIVE_PLATFORM_READY_TIMEOUT';time.sleep(.1)
  identityPort=int((platform/'server-http-port.txt').read_text());assert listener_owner(identityPort)==[('127.0.0.1',identity.pid)];peerBase='http://127.0.0.1:'+str(identityPort)
  props={'spring.application.name':'cqweh-endanger','server.address':'127.0.0.1','server.port':'0','server.servlet.context-path':'/serv','spring.main.banner-mode':'off','spring.main.allow-circular-references':'true','spring.cloud.bootstrap.enabled':'false','spring.cloud.discovery.enabled':'false','spring.cloud.nacos.discovery.enabled':'false','spring.cloud.nacos.config.enabled':'false','spring.jmx.enabled':'false','management.endpoints.enabled-by-default':'false','spring.datasource.dynamic.primary':'master','spring.datasource.dynamic.strict':'true','spring.datasource.dynamic.druid.initial-size':'0','spring.datasource.dynamic.druid.min-idle':'0','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.max-wait':'5000','spring.data.redis.host':'127.0.0.1','spring.data.redis.port':str(cache.port),'spring.data.redis.password':password,'spring.data.redis.database':'0','minio.url':'127.0.0.1','minio.port':str(objectPort),'minio.secure':'false','minio.accessKey':objectAccess,'minio.secretKey':password,'minio.bucket':'own-full-main','flow.url':peerBase,'flow.code':'OWN_FORM_CODE','context.initializer.classes':'xnby.replica.ServerLifecycleObservation','logging.level.root':'INFO','logging.file.name':str(business/'logs/business.log')}
  props.update({'context.listener.classes':'xnby.replica.OriginalPublicRiskObservation','safety.jnpfUrl':peerBase,'minio.bucketName':'own-full-main','flow.event-task-handle':'OWN_FORM_CODE','riskReportDb':'OWN_REPORT_DB','safetyEmergencyDb':'OWN_REPORT_DB'})
  for key in ['swagger.token','meteorological.token','riskReportToken','safetyEmergencyToken','workReportToken','otherWorkReportToken','otherRiskReportToken','otherThirdToken']:props[key]='OWN_'+uuid.uuid4().hex
  for key in ['meteorological.url','riskReportUrl','safetyEmergencyUrl','workReportUrl','otherWorkReportUrl','otherRiskReportUrl','otherThirdUrl']:props[key]=peerBase+'/own-unavailable'
  for name,db in [('master','tj_endanger'),('tow','jnpf')]:
   prefix='spring.datasource.dynamic.datasource.'+name+'.';props.update({prefix+'url':'jdbc:mysql://127.0.0.1:'+str(port)+'/'+db+'?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=15000',prefix+'username':'root',prefix+'password':password,prefix+'driver-class-name':'com.mysql.cj.jdbc.Driver'})
  spec={'configuration':{'business':props},'businessArguments':['-Down.direct.main=true','-Down.internal.platform.base=http://127.0.0.1:18990','-Djava.awt.headless=true','-Duser.home=${BUSINESS_RUN}/home']}
  package=parameters.materialize(spec,side='business',application=app,platform_run=platform,business_run=business,platform_data_owner=owner,run_owner=owner,database_uuid=own_uuid,database_port=port,redis_port=cache.port,object_port=objectPort,database_password=password,redis_password=password,object_access=objectAccess,object_secret=password,platform_port=identityPort,business_port=businessPort)
  (business/'application.properties').write_bytes(package['properties']);c.dump(root/'configuration-key-inventory.json',{'keys':sorted(package['configuration']),'credentialsSynthetic':True,'actualPublishedParameterSourceUsed':True,'originalPrivateConfigurationRead':False})
  flags={'own.fixture.snapshot.root':str(root),'own.fixture.snapshot.nonce':snapshotNonce,'own.fixture.risk.batch.verify':'true','own.fixture.risk.import.verify':'true','own.fixture.risk.import.atomic':'true','own.fixture.risk.sort.sha256':'636822c3930a036ddb294dac990c1b9f0f3f62e09baa40afdd46feddcc30070c','own.fixture.risk.import.controller.sha256':'7d866e4ca810f7de5de637964b38f1eecae1a0b3208ef03ebbe17d34f06fa33e'}
  out=open(root/'business.stdout.log','wb');err=open(root/'business.stderr.log','wb');logs.extend([out,err]);command=[str(java),'-Xmx512m','-XX:ActiveProcessorCount=2','--add-opens','java.base/java.lang=ALL-UNNAMED','--add-opens','java.base/java.io=ALL-UNNAMED','--add-opens','java.rmi/sun.rmi.transport=ALL-UNNAMED','-Dfile.encoding=UTF-8',*package['arguments'],*['-D'+k+'='+v for k,v in flags.items()],'-cp',cp,'xnby.replica.OriginalPublicRiskObservation',str(business)]
  process=subprocess.Popen(command,cwd=business,env=dict(env,TEMP=str(business/'tmp'),TMP=str(business/'tmp')),stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW);c.dump(root/'business-started.json',{'pid':process.pid,'actualPublishedLauncherRequested':True});deadline=time.monotonic()+110
  while not(business/'public-risk-chain-result.json').exists():
   if(business/'public-risk-chain-observation-failed.json').exists():raise RuntimeError('ADDITIONAL_PUBLIC_CHAIN_OBSERVER_REJECTED')
   assert process.poll()is None,'PUBLISHED_MAIN_EXITED_BEFORE_PROOF';assert time.monotonic()<deadline,'PUBLISHED_MAIN_PROOF_TIMEOUT';time.sleep(.1)
  assert listener_owner(businessPort)==[('127.0.0.1',process.pid)]
  with urllib.request.urlopen('http://127.0.0.1:'+str(businessPort)+'/serv/riskLevel/getModel',timeout=8)as response:
   body=json.loads(response.read(65536));assert response.status==200 and body['code']==600
  c.dump(root/'unauthenticated-template-probe.json',{'HTTP':200,'code':600,'noBusinessRecordsRead':True})
  for name in ['public-risk-chain-result.json','risk-batch-service-integration.json','risk-whole-import-integration.json','public-chain-native-risk-template.xlsx']:shutil.copyfile(business/name,root/name)
  from original_public_risk_login_http_r22_20261101 import run_cases
  from original_public_risk_portal_chain_r22_20261101 import run as risk_portal
  run_cases(root,identityPort,businessPort,login_snapshot,lambda request,headers:risk_portal(root,request,headers,identityPort,businessPort,login_snapshot,password))
 except BaseException as error:
  failure=error;c.dump(root/'failure.json',{'type':type(error).__name__,'message':str(error)if isinstance(error,AssertionError)else'OWN_PUBLIC_CHAIN_FAILURE'})
 finally:
  if process:
   (business/'own-stop-requested.txt').write_text('OWN_NORMAL_STOP\n');process.wait(timeout=40);c.dump(root/'business-stopped.json',{'pid':process.pid,'exitCode':process.returncode,'normalContextClosed':(business/'server-context-closed.txt').exists(),'forced':False})
  if identity:
   (platform/'own-stop-requested.txt').write_text('OWN_NORMAL_PLATFORM_STOP\n');identity.wait(timeout=40);c.dump(root/'identity-stopped.json',{'pid':identity.pid,'exitCode':identity.returncode,'normalContextClosed':(platform/'server-context-closed.txt').exists(),'forced':False,'actualPublishedPlatformMain':True})
  if peer:peer.shutdown();peer.server_close();thread.join(timeout=5)
  if store:
   stop=None
   if store.poll()is None:stop=stop_owned_provider(objectPort,objectAccess,password);assert stop['status']==200;store.wait(timeout=25)
   c.dump(root/'object-store-stopped.json',{'pid':store.pid,'exitCode':store.returncode,'signedNormalStop':stop,'forced':False})
  if mysql:
   if (root/'restore-schema-evidence.json').exists():schema('snapshot','snapshot')
   stopped=False
   if mysql.poll()is None:schema('stop','stop');mysql.wait(timeout=35);stopped=True
   c.dump(root/'mysql-stopped.json',{'pid':mysql.pid,'exitCode':mysql.returncode,'sqlShutdownConfirmed':stopped,'forced':False})
  if cache:cache.close()
  for log in logs:log.close()
 assert observe()==before and c.protected()==held
 if failure:raise RuntimeError('OWN_PUBLIC_CHAIN_NOT_PASSED:'+type(failure).__name__)from None
 for component in ['business','identity','mysql','object-store','own-redis']:
  result=c.read(root/(component+'-stopped.json'));assert result['exitCode']==0 and not result.get('forced',False)and not result.get('forcedJobClosure',False)
  if component in ['business','identity']:assert result['normalContextClosed']
 assert c.read(root/'restore-schema-evidence.json')['definitions']==c.read(root/'snapshot-schema-evidence.json')['definitions'],'ORIGINAL_398_MODELS_MUST_STAY_EXACT'
 c.dump(root/'stage-result.json',{'actualPublishedBusinessMain':True,'actualR21ParameterSourceUsed':True,'R10TaskAuthCacheLifecycleFontPrototypesAbsent':True,'riskBatchTimeAndWholeFileRollbackPassed':True,'nativeEmptyTemplateGenerated':True,'originalMissingAuthHTTPPassed':True,'allComponentsNormalClosed':True,'originalNativeLoginAndMergedProductionPortalPassed':True,'fullTaskWorkflowRegressionStillPending':True,'formalOrPublicInstalled':False});print('OWN_FULL_NATIVE_PUBLIC_RISK_PORTAL_PASSED')
if __name__=='__main__':main()
