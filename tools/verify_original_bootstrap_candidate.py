"""One bounded original JNPF run on a verified writable owned clone and own Redis."""
import argparse,datetime,hashlib,http.client,json,msvcrt,os,pathlib,re,secrets,shutil,socket,subprocess,time,traceback
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workspace',type=pathlib.Path,required=True);parser.add_argument('--name',required=True);parser.add_argument('--independent-wrappers',action='store_true');parser.add_argument('--probe-login-image-on-ready',action='store_true');parser.add_argument('--probe-admin-config-on-ready',action='store_true');args=parser.parse_args();assert re.fullmatch(r'own-pboot-r[1-9][0-9]*',args.name)
W=args.workspace.resolve(strict=True);root=W/args.name;runtime=W/'mysql-8.0.46-original-restore-runtime_20261024'
assert W.parents[1].name=='Application' and (W.parents[1]/'tools/reference_flat_runtime.py').is_file(),'OWN_KNOWN_WORKSPACE_REQUIRED'
meta=json.loads((root/'preparation.json').read_bytes());jdk=pathlib.Path(meta['javaHome']);source=pathlib.Path(meta['sourceArchive'])
dbroot=pathlib.Path(meta['ownedDatabaseRoot']).resolve(strict=True)
assert dbroot.parent==W and dbroot.name=='own-mysql-r27','OWN_VERIFIED_WRITABLE_CLONE_REQUIRED'
platform_jdk=pathlib.Path(meta.get('platformJavaHome',meta['javaHome']));platform_java_major=meta.get('platformJavaMajor',17)
parent_jar=pathlib.Path(meta.get('bootstrapParentJar') or source)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not (root/'attempt_started.json').exists(),'Own original platform attempt already exists; inspect instead of repeat'
assert sha(root/'own-platform-observation.jar')==meta['lifecycleObservationJarSHA256']
assert sha(source)==meta['sourceJarSHA256']
for relative,pin in meta.get('platformRuntimePins',{}).items():assert sha(platform_jdk/relative)==pin
if platform_java_major==8:
 assert meta['java8Fixture']['passedCases']>=25 and meta['java8Fixture']['outsideCanaryUnchanged']
 preflight_root=pathlib.Path(meta.get('preflightEvidenceRoot',str(root)))
 for relative,pin in meta.get('preflightRelevantClassesSHA256',{}).items():assert sha(root/relative)==pin and sha(preflight_root/relative)==pin
 for name,count,pin in [('component',2501,'3de893888ccaf0a67538faea221645d6e420aed6ad8eb57598b09446ae10ce15'),('xmllogical',14,'988ebcd928eeb4e3af71294502ec8794ba7e7eff13b276d19286cb1677cdcfad')]:
  receipt=json.loads((preflight_root/name/'classloader-only-receipt.json').read_bytes());rows=(preflight_root/name/'spring-metadata-only-results.tsv').read_text().splitlines()
  assert receipt['exitCode']==0 and receipt['platformJavaMajor']==8 and receipt['guardJarSHA256']==meta.get('preflightGuardSHA256',meta['guardJarSHA256'])
  assert len([line for line in receipt['rows'] if '\tPASS\t' in line])==5
  assert 'fullComponentScanResources\t'+str(count) in rows and 'componentResourceUrlsSHA256\t'+pin in rows
  assert 'scriptEngine\tjdk.nashorn.api.scripting.NashornScriptEngine\tPASS' in rows
assert shutil.disk_usage(W).free>=32*1024**3
for item in meta['compileDependencies']:assert sha(pathlib.Path(item['file']))==item['sha256']
assert sha(pathlib.Path(meta['guardJar']))==meta['guardJarSHA256'] and sha(pathlib.Path(meta['yamlJar']))==meta['yamlJarSHA256']
if meta.get('bootstrapParentJar'):assert sha(parent_jar)==meta['bootstrapParentJarSHA256']
if meta.get('classpathPreflightEnabled'):assert sha(pathlib.Path(meta['preflightSpec']))==meta['preflightSpecSHA256']
prior=json.loads((W/'own-dbboot-r5/receipt.json').read_bytes());assert prior['ownMySQLExited'] and prior['ownMySQLExitCode']==0 and prior['ownRedisExited'] and prior['ownRedisExitCode']==0
if meta.get('previousControlledAttempt'):
 previous=json.loads((pathlib.Path(meta['previousControlledAttempt'])/'receipt.json').read_bytes())
 assert previous['ownMySQLExited'] and previous['ownMySQLExitCode']==0 and previous['ownRedisExited'] and previous['ownRedisExitCode']==0
dbspec=json.loads((dbroot/'receipt.json').read_bytes());dbconf=dict(line.split('=',1) for line in (dbroot/'own-connection.properties').read_text(encoding='ascii').splitlines())
assert dbconf['serverUUID']==dbspec['ownServerUUID']
assert json.loads((dbroot/'completed-offline-verification.json').read_bytes())['passed']
assert dbspec['ownServerUUID']==meta['ownedDatabaseUUID']
exe=runtime/'bin/mysqld.exe';assert sha(exe)=='47ffd2c32f36e5cb79f78bed0ff5272d7559c383f88c43c753470d5a5dfbe8a0'
env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')};env['TEMP']=env['TMP']=str(root/'tmp');flags=subprocess.CREATE_NO_WINDOW
def port():
 with socket.socket() as s:s.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);s.bind(('127.0.0.1',0));return s.getsockname()[1]
dbport,redisport=port(),port();assert dbport!=redisport
secret=secrets.token_hex(16);redis_password=secrets.token_urlsafe(32)
public_key=dbroot/'data/public_key.pem';assert public_key.is_file() and public_key.stat().st_size<=4096
own={'mysqlPort':str(dbport),'mysqlPassword':dbconf['password'],'mysqlPublicKeyPath':public_key.as_posix(),'redisPort':str(redisport),'redisPassword':redis_password,'ownSecret':secret}
(root/'own-integration.properties').write_text('\n'.join(k+'='+v for k,v in own.items())+'\n',encoding='ascii')
(root/'own-logback.xml').write_text('<configuration><appender name="OWN" class="ch.qos.logback.core.ConsoleAppender"><encoder><pattern>%date %level %logger - %msg%n</pattern></encoder></appender><logger name="druid.sql" level="OFF"/><logger name="org.apache.ibatis" level="WARN"/><root level="WARN"><appender-ref ref="OWN"/></root></configuration>\n',encoding='ascii')
build_config=subprocess.run([str(jdk/'bin/java.exe'),'-Xmx128m','-Djava.io.tmpdir='+str(root/'tmp'),'-cp',os.pathsep.join([str(root/'builder-classes'),meta['yamlJar']]),'xnby.platform.OriginalPlatformConfigBuilder',str(source),str(root)],cwd=root,env=env,capture_output=True,creationflags=flags,timeout=30)
(root/'configuration-builder.private.log').write_bytes(build_config.stdout+build_config.stderr);assert build_config.returncode==0,'OWN_PLATFORM_CONFIG_BUILD_FAILED'
with (root/'application.properties').open('a',encoding='ascii') as own_config:own_config.write('\ncontext.initializer.classes=xnby.platform.PlatformStartupObservation,xnby.platform.PlatformWritableObservation,xnby.platform.OriginalIdGeneratorShutdown,xnby.platform.OriginalBootstrapOrphanGuard\n')
policy=root/'own-process-only.policy';policy.write_text('grant { permission java.security.AllPermission; };\n',encoding='ascii')
result={'startedAt':datetime.datetime.now().astimezone().isoformat(),'sourceJarSHA256':meta['sourceJarSHA256'],'sourceDatabaseConnected':False,
 'originalJarCopiedToD':False,'originalClassesModified':False,'sourceCredentialsUsedForExternalAccess':False,
 'ownMySQLSuperReadOnly':False,'originalPlatformReady':False,'fullCloneReady':False,'publicDeployed':False,'windowsServiceInstalled':False}
result['independentResourceWrappers']=args.independent_wrappers
result['ownJVMOpenedModules']=['java.base/java.lang'] if platform_java_major>=17 else []
result['platformJavaMajor']=platform_java_major
result['ownMySQLPublicKeySHA256']=sha(public_key)
(root/'attempt_started.json').write_text(json.dumps(result),encoding='utf-8')
db=redis=platform=None;handles=[]
controller_lock=(dbroot/'own-joint-controller.lock').open('a+b');controller_lock.seek(0);controller_lock.write(b'0');controller_lock.flush();controller_lock.seek(0);msvcrt.locking(controller_lock.fileno(),msvcrt.LK_NBLCK,1)
def start(command,log):
 f=(root/log).open('wb');handles.append(f);return subprocess.Popen(command,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=flags)
def resp(stream,*words):
 parts=[str(x).encode('ascii') for x in words];stream.write(b'*'+str(len(parts)).encode()+b'\r\n'+b''.join(b'$'+str(len(x)).encode()+b'\r\n'+x+b'\r\n' for x in parts));stream.flush()
 line=stream.readline();kind,value=line[:1],line[1:-2]
 if kind==b'+':return value.decode('ascii')
 if kind==b':':return int(value)
 if kind==b'-':return {'error':value.decode('ascii')}
 if kind==b'$':
  count=int(value);assert 0<=count<=1024**2;raw=stream.read(count);assert stream.read(2)==b'\r\n';return raw.decode('ascii')
 raise RuntimeError('OWN_REDIS_REPLY')
def redis_session():
 s=socket.create_connection(('127.0.0.1',redisport),timeout=3);return s,s.makefile('rwb')
try:
 db=start([str(exe),'--no-defaults','--no-monitor','--basedir='+str(runtime),'--datadir='+str(dbroot/'data'),
  '--lower-case-table-names=1','--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M',
  '--innodb-data-file-path=ibdata1:12M:autoextend:max:256M','--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M',
  '--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL',
  '--super-read-only=OFF','--read-only=OFF','--transaction-read-only=OFF','--bind-address=127.0.0.1','--port='+str(dbport),
  '--pid-file='+str(dbroot/'own-mysqld.pid'),'--console','--max-connections=16','--skip-slave-start'],'mysql.private.log')
 for _ in range(300):
  assert db.poll() is None,'OWN_MYSQL_EXITED'
  if (root/'mysql.private.log').exists() and 'ready for connections' in (root/'mysql.private.log').read_text(encoding='utf-8',errors='replace'):break
  time.sleep(.1)
 else:raise RuntimeError('OWN_MYSQL_READY_TIMEOUT')
 assert int((dbroot/'own-mysqld.pid').read_text().strip())==db.pid
 (root/'previous-mysql-owner.json').write_bytes((dbroot/'own-server-process.json').read_bytes())
 (dbroot/'own-server-process.json').write_text(json.dumps({'pid':db.pid,'host':'127.0.0.1','port':dbport,'serverUUID':dbspec['ownServerUUID']}),encoding='utf-8')
 (dbroot/'own-connection.properties').write_text('port='+str(dbport)+'\npassword='+dbconf['password']+'\nserverUUID='+dbspec['ownServerUUID']+'\n',encoding='ascii')
 result.update(ownMySQLPID=db.pid,ownMySQLPort=dbport)
 redis_exe=W/'own-redis-runtime_20261024/redis-server.exe';redis_spec=json.loads((redis_exe.parent/'receipt.json').read_bytes());assert sha(redis_exe)==next(x['sha256'] for x in redis_spec['files'] if x['file']=='redis-server.exe')
 (root/'redis-data').mkdir()
 conf=root/'own-redis.conf';conf.write_text('\n'.join(['bind 127.0.0.1','port '+str(redisport),'protected-mode yes','requirepass '+redis_password,
  'maxmemory 64mb','maxmemory-policy noeviction','persistence-available no','dir "'+(root/'redis-data').as_posix()+'"','logfile "'+(root/'redis.private.log').as_posix()+'"','loglevel notice'])+'\n',encoding='ascii')
 redis=start([str(redis_exe),str(conf)],'redis-process.private.log')
 for _ in range(60):
  assert redis.poll() is None,'OWN_REDIS_EXITED'
  try:
   with socket.create_connection(('127.0.0.1',redisport),timeout=.2):break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('OWN_REDIS_READY_TIMEOUT')
 s,stream=redis_session()
 with s,stream:
  assert resp(stream,'AUTH',redis_password)=='OK' and resp(stream,'PING')=='PONG' and resp(stream,'DBSIZE')==0
  info=dict(x.split(':',1) for x in resp(stream,'INFO','server').splitlines() if ':' in x);assert int(info['process_id'])==redis.pid
  assert resp(stream,'CONFIG','SET','save','')=='OK'
 result.update(ownRedisPID=redis.pid,ownRedisPort=redisport)
 java_args=['-Xmx512m',*(['--add-opens=java.base/java.lang=ALL-UNNAMED'] if platform_java_major>=17 else []),'-Djava.awt.headless=true','-Dfile.encoding=UTF-8','-Djava.io.tmpdir='+str(root/'tmp'),'-Duser.home='+str(root/'home'),'-Djdk.net.unixdomain.tmpdir='+str(root/'tmp'),
  '-Djava.security.policy=='+policy.as_uri(),'-Down.platform.root='+str(root),'-Down.allowed.loopback.ports='+str(dbport)+','+str(redisport),
  '-Down.boundary.trace='+str(meta.get('boundaryTraceEnabled',False)).lower(),
  '-Down.platform.preflight='+str(meta.get('classpathPreflightEnabled',False)).lower(),'-Down.platform.preflight.spec='+meta.get('preflightSpec',''),
  '-Down.platform.cached.resources='+str(meta.get('cachedResourcesEnabled',False)).lower(),'-Down.platform.source.path='+str(source),
  '-Down.platform.independent.jar.wrappers='+str(args.independent_wrappers).lower(),
  *(['-Djava.protocol.handler.pkgs=xnby.platform.protocol'] if meta.get('globalCachedProtocolEnabled') else []),
  '-Down.platform.rehydrate-existing-definitions=true','-Down.platform.manage.id-generator-shutdown=true','-Down.expected.database.uuid='+dbspec['ownServerUUID'],'-Down.expected.database.port='+str(dbport),'-Dspring.config.location='+(root/'application.properties').as_uri(),'-Dlogging.config='+(root/'own-logback.xml').as_uri(),
  '-Dspring.cloud.bootstrap.enabled=false','-Dspring.profiles.active=own-platform-isolation',
  *(['-Xlog:class+load=info:file='+(root/'loaded-classes.private.log').as_posix(),
  '-Xlog:exceptions=info:file='+(root/'exceptions.private.log').as_posix()+':none:filecount=2,filesize=8m'] if platform_java_major>=17 else ['-verbose:class']),
  '-cp',os.pathsep.join([str(parent_jar),str(root/'wrapper-classes'),meta['guardJar']]),'xnby.platform.OriginalPlatformLaunch',str(source),str(root)]
 argfile=root/'own-java-arguments.txt';argfile.write_text('\n'.join('"'+a.replace('\\','\\\\').replace('"','\\"')+'"' for a in java_args)+'\n',encoding='utf-8')
 platform=start([str(platform_jdk/'bin/java.exe'),*(['@'+str(argfile)] if platform_java_major>=17 else java_args)],'platform-startup.private.log');result['ownPlatformPID']=platform.pid
 started=time.monotonic();stop_at=None;last=-30;failure_seen=None;login_probe_done=False;admin_probe_done=False
 while platform.poll() is None:
  assert db.poll() is None and redis.poll() is None,'OWN_DEPENDENCY_EXITED'
  size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());assert size<=128*1024**2,'OWN_PLATFORM_RUN_STORAGE_LIMIT'
  if time.monotonic()-started-last>=30:print(json.dumps({'phase':'original_platform_startup','elapsedSeconds':round(time.monotonic()-started),'ownRunMiB':round(size/1024**2,2),'readyObserved':(root/'own-platform-ready.txt').exists()}),flush=True);last=time.monotonic()-started
  if (root/'original-failure-before-reporting.private.log').exists():
   if failure_seen is None:failure_seen=time.monotonic();result['originalStartupFailureObserved']=True
   elif time.monotonic()-failure_seen>20:
    result['ownFailedContextCleanupTimedOut']=True;result['ownPlatformTerminationReason']='ApplicationFailedEvent followed by 20 seconds without process exit';break
  if args.probe_login_image_on_ready and not login_probe_done and (root/'own-platform-ready.txt').exists():
   login_probe_done=True;webport=int((root/'own-platform-http-port.txt').read_text());nonce=str(int(time.time()*1000))
   image_path='/api/oauth/ImageCode/4/'+nonce
   c=http.client.HTTPConnection('127.0.0.1',webport,timeout=8);c.request('GET',image_path);response=c.getresponse();raw=response.read(2*1024**2+1);assert len(raw)<=2*1024**2
   kind='PNG' if raw.startswith(b'\x89PNG\r\n\x1a\n') else 'JPEG' if raw.startswith(b'\xff\xd8\xff') else 'GIF' if raw.startswith((b'GIF87a',b'GIF89a')) else None
   image={'pathTemplate':'/api/oauth/ImageCode/4/<nonce>','status':response.status,'contentType':response.getheader('Content-Type'),'bodyBytes':len(raw),'bodySHA256':hashlib.sha256(raw).hexdigest(),'imageSignature':kind,'captchaSolved':False}
   (root/'original-login-image.private.bin').write_bytes(raw);c.close()
   c=http.client.HTTPConnection('127.0.0.1',webport,timeout=8);c.request('GET','/api/oauth/CurrentUser?systemCode=safety');response=c.getresponse();raw=response.read(2*1024**2+1);assert len(raw)<=2*1024**2
   (root/'unauthenticated-current-user.private.json').write_bytes(raw)
   try:body=json.loads(raw);code=body.get('code');data_is_null=body.get('data') is None
   except (ValueError,AttributeError):code=None;data_is_null=False
   current={'path':'/api/oauth/CurrentUser?systemCode=safety','status':response.status,'applicationCode':code,'dataIsNull':data_is_null,'bodySHA256':hashlib.sha256(raw).hexdigest()};c.close()
   result['originalLoginImageProbe']={'image':image,'unauthenticatedCurrentUser':current,'loginAttemptPerformed':False,'imageAndAuthBoundaryPassed':image['status']==200 and kind is not None and code==600 and data_is_null}
   (root/'original-login-image-probe.json').write_text(json.dumps(result['originalLoginImageProbe'],indent=2),encoding='utf-8')
  if args.probe_admin_config_on_ready and not admin_probe_done and (root/'own-platform-ready.txt').exists():
   admin_probe_done=True;webport=int((root/'own-platform-http-port.txt').read_text());observations=[]
   for path,name in [('/api/oauth/getLoginConfig','actual-admin-login-config'),('/api/oauth/CurrentUser?systemCode=mainSystem','admin-unauthenticated-current-user')]:
    connection=http.client.HTTPConnection('127.0.0.1',webport,timeout=8)
    try:
     connection.request('GET',path);response=connection.getresponse();raw=response.read(2*1024**2+1);assert len(raw)<=2*1024**2
     (root/(name+'.private.json')).write_bytes(raw)
     try:value=json.loads(raw);code=value.get('code');data=value.get('data')
     except (ValueError,AttributeError):code=None;data=None
     observations.append({'path':path,'status':response.status,'applicationCode':code,'dataKeys':sorted(data) if isinstance(data,dict) else [],'dataIsNull':data is None,'redirect':data.get('redirect') if isinstance(data,dict) else None,'bodyBytes':len(raw),'bodySHA256':hashlib.sha256(raw).hexdigest()})
    finally:connection.close()
   result['actualAdminLoginConfigProbe']={'results':observations,'loginAttemptPerformed':False,'credentialsUsed':False,'captchaRequested':False,'loginConfigAccessible':observations[0]['status']==200 and observations[0]['applicationCode']==200,'originalMainReturned':(root/'original-platform-main-returned.txt').exists(),'fullCloneReady':False}
   (root/'actual-admin-login-config-probe.json').write_text(json.dumps(result['actualAdminLoginConfigProbe'],indent=2),encoding='utf-8')
   print(json.dumps({'phase':'actual_admin_login_config_checked','port':webport,'applicationCode':observations[0]['applicationCode'],'originalMainReturned':(root/'original-platform-main-returned.txt').exists()}),flush=True)
   result['adminProbeCompletedBeforeBootstrap']=True
  if admin_probe_done and stop_at is None and ((root/'original-platform-main-returned.txt').exists() or (root/'bootstrap-rehydration-observation.properties').exists()):
   (root/'own-stop-requested.txt').write_text('finish-owned-bootstrap-candidate\n',encoding='ascii')
  if args.probe_admin_config_on_ready and (root/'own-stop-requested.txt').exists() and stop_at is None:
   result['controlledContextStopRequested']=True;stop_at=time.monotonic()+20
  if (root/'own-platform-ready.txt').exists() and (root/'original-platform-main-returned.txt').exists() and stop_at is None:
   result['originalPlatformReady']=True
   webport=int((root/'own-platform-http-port.txt').read_text());result['ownPlatformHTTPPort']=webport
   observations=[]
   for path in ('/api/oauth/Config','/api/oauth/GetConfig'):
    c=http.client.HTTPConnection('127.0.0.1',webport,timeout=8);c.request('GET',path);response=c.getresponse();body=response.read(2*1024**2+1);assert len(body)<=2*1024**2
    item={'path':path,'status':response.status,'bodyBytes':len(body),'bodySHA256':hashlib.sha256(body).hexdigest(),'loginAttemptPerformed':False};observations.append(item)
    (root/('probe'+str(len(observations))+'.private.json')).write_bytes(body);c.close()
   result['unauthenticatedConfigurationProbes']=observations
   (root/'own-stop-requested.txt').write_text('finish-owned-platform-startup\n',encoding='ascii');stop_at=time.monotonic()+20
  if time.monotonic()-started>180 or stop_at is not None and time.monotonic()>stop_at:result['ownPlatformTimedOut']=True;break
  time.sleep(.2)
 if platform.poll() is None:platform.terminate();platform.wait(timeout=15);result['ownPlatformTerminated']=True
 result['ownPlatformExitCode']=platform.returncode
 original_failure=root/'original-failure-before-reporting.private.log'
 text=(original_failure if original_failure.exists() else root/'platform-startup.private.log').read_text(encoding='utf-8',errors='replace')
 result['failureObservationSource']='original-failure-before-reporting' if original_failure.exists() else 'startup-log'
 result.update(failedBeanNames=sorted(set(re.findall(r"Error creating bean with name '([A-Za-z0-9_.$-]+)'",text))),
  exceptionClasses=sorted(set(re.findall(r'Caused by: ([\w.$]+)',text))),missingPropertyNames=sorted(set(re.findall(r"Could not resolve placeholder '([^']+)'",text))),
  boundaryDenialKinds=sorted(set(re.findall(r'OWN_PROCESS_BOUNDARY_[A-Z_]+',text))),
  originalMainRequested=(root/'original-platform-main-requested.txt').exists(),originalMainReturned=(root/'original-platform-main-returned.txt').exists(),
  applicationReadyEventObserved=(root/'own-platform-ready.txt').exists(),contextRefreshed=(root/'own-platform-context-refreshed.txt').exists(),contextClosed=(root/'own-platform-context-closed.txt').exists())
except Exception as error:
 (root/'controller-failure.private.log').write_text(traceback.format_exc(),encoding='utf-8');result['failureType']=type(error).__name__;result['failureCode']=str(error) if str(error).startswith('OWN_') else 'Private details retained'
finally:
 if platform is not None and platform.poll() is None:platform.terminate();platform.wait(timeout=15);result['ownPlatformTerminated']=True
 if redis is not None and redis.poll() is None:
  try:
   s,stream=redis_session()
   with s,stream:
    assert resp(stream,'AUTH',redis_password)=='OK';parts=[b'SHUTDOWN',b'NOSAVE'];stream.write(b'*2\r\n'+b''.join(b'$'+str(len(x)).encode()+b'\r\n'+x+b'\r\n' for x in parts));stream.flush()
  except OSError:pass
  try:redis.wait(timeout=8)
  except subprocess.TimeoutExpired:redis.terminate();redis.wait(timeout=10);result['ownRedisTerminated']=True
 if db is not None and db.poll() is None:
  rowmeta=json.loads((W/'own-mysql-r13/fixture_compile.json').read_bytes());cp=[str(W/'own-dbboot-r5/classes'),str(W/'own-mysql-r26/classes'),str(dbroot/'classes')]+[rowmeta[k] for k in ('exporterJar','yamlJar','mysqlConnectorJar')]+rowmeta['additionalClasspath']
  stop=subprocess.run([str(jdk/'bin/java.exe'),'-Xmx128m','-cp',os.pathsep.join(cp),'xnby.export.OwnedRestoredServerShutdown',str(dbroot),str(root)],cwd=root,env=env,capture_output=True,creationflags=flags,timeout=30)
  (root/'mysql-shutdown.private.log').write_bytes(stop.stdout+stop.stderr);result['mysqlShutdownJVMExitCode']=stop.returncode
  try:db.wait(timeout=30)
  except subprocess.TimeoutExpired:db.terminate();db.wait(timeout=10);result['ownMySQLTerminated']=True
 for f in handles:f.close()
 result.update(finishedAt=datetime.datetime.now().astimezone().isoformat(),ownMySQLExited=db is None or db.poll() is not None,ownMySQLExitCode=db.returncode if db else None,
  ownRedisExited=redis is None or redis.poll() is not None,ownRedisExitCode=redis.returncode if redis else None,sourceDatabaseConnected=False,
  fullCloneReady=False,originalLoginOrBusinessFlowsVerified=False,publicDeployed=False)
 for filename,key in [('actual-writable-datasource.properties','actualWritableDataSource'),('id-worker-ready-observation.properties','idWorkerReady'),('id-worker-close-observation.properties','idWorkerClose'),('bootstrap-rehydration-observation.properties','bootstrapRehydration')]:
  path=root/filename
  if path.exists():result[key]=dict(line.split('=',1) for line in path.read_text('ascii').splitlines() if line and not line.startswith(('#','!')))
 close=result.get('idWorkerClose',{});state=result.get('actualWritableDataSource',{})
 result['platformJVMExitedNaturally']=bool(platform is not None and platform.poll() is not None and not result.get('ownPlatformTerminated'))
 ready=root/'id-worker-ready-observation.properties'
 ready_values=result.get('idWorkerReady',{})
 result['lifecycleCloseVerified']=bool(result.get('contextClosed') and result['platformJVMExitedNaturally'] and result.get('ownMySQLExitCode')==0 and result.get('ownRedisExitCode')==0 and close.get('originalOwnerClassPinned')=='true' and close.get('normalShutdownRequested')=='true' and close.get('terminatedWithinTwoSeconds')=='true' and ready_values.get('startupBehaviorModified')=='false' and ready_values.get('originalPoolShutdownBefore')=='false' and state.get('uuidMatches')=='true' and state.get('portMatches')=='true' and state.get('databaseMatches')=='true' and state.get('jdbcReadOnly')=='false' and state.get('transactionReadOnly')=='0' and state.get('serverSuperReadOnly')=='0')
 result['platformStartupVerified']=bool(result.get('originalMainReturned') and result.get('ownPlatformExitCode')==0)
 bootstrap=result.get('bootstrapRehydration',{})
 result['originalPlatformReady']=result['platformStartupVerified']
 result['bootstrapCandidateVerified']=bool(result['platformStartupVerified'] and result['lifecycleCloseVerified'] and bootstrap.get('originalBootstrapMethodCompleted')=='true' and bootstrap.get('outsideBootstrapCriticalFieldsSignaturePreserved')=='true' and int(bootstrap.get('validRowsPassedToOriginalInit','0'))>0)
 result['originalLegacyDataAnomaliesRemain']=True
 (root/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False),flush=True)
 controller_lock.seek(0);msvcrt.locking(controller_lock.fileno(),msvcrt.LK_UNLCK,1);controller_lock.close()


raise SystemExit(0 if result.get("bootstrapCandidateVerified") else 1)
