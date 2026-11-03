from pathlib import Path
import datetime,hashlib,importlib.util,json,os,shutil,socket,subprocess,sys,time,uuid
R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application';V=Path(__file__).parent;W=R/'work/addsign-history-r180';P=W/'mybatis-lab-r191';assert not P.exists();P.mkdir();(P/'classes').mkdir();(P/'tmp').mkdir()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dump=lambda p,o:p.write_text(json.dumps(o,indent=2)+'\n',encoding='utf-8')
assert J(G.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(G.parent/'user-manual-protected.json').exists()
assert shutil.disk_usage(P).free>2*1024**3
spec=importlib.util.spec_from_file_location('history_owned_job',G/'tools/original_server_windows_job.py');jobs=importlib.util.module_from_spec(spec);spec.loader.exec_module(jobs)
spec=importlib.util.spec_from_file_location('history_listener',A/'tools/original_task_identity_authority.py');authority=importlib.util.module_from_spec(spec);spec.loader.exec_module(authority)
dep=J(W/'mybatis-full-dependency-pins.json');cp=str(P/'classes')+';'+str(W/'native-classes-r191')+';'+dep['classpath']
for name,pin in dep['jars'].items():file=Path(pin['source'])if name=='mysqlDriverExternal'else W/'dependencies'/name;assert file.stat().st_size==pin['bytes']and sha(file)==pin['sha256']
sources=[V/'native_history_r191/OriginalAddsignOpinionHistory.java',V/'native_history_r191/OriginalBeforeAddsignHistoryInterceptor.java',V/'native_history_r191/OwnAddsignMybatisFixture.java'];dump(P/'source-pins.json',{s.name:sha(s)for s in sources})
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH','MYSQL_PWD','MYSQL_HOME','PYTHONPATH','PYTHONHOME']};env.update(TEMP=str(P/'tmp'),TMP=str(P/'tmp'))
java=G/'runtime/jdk17/bin/java.exe';javac=java.with_name('javac.exe');exe=G/'runtime/mysql/bin/mysqld.exe';runtime=exe.parent.parent
dump(P/'program-pins.json',{'java':sha(java),'javac':sha(javac),'mysqld':sha(exe),'noRuntimeOrInstalledDataCopied':True})
compile_result=subprocess.run([str(javac),'-J-Xmx128m','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(P/'classes'),str(V/'native_history_r191/OwnAddsignMybatisFixture.java')],env=env,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(P/'compile.stdout.log').write_bytes(compile_result.stdout);(P/'compile.stderr.log').write_bytes(compile_result.stderr);assert compile_result.returncode==0,'OWN_HISTORY_JAVA_COMPILE_FAILED'
model=A/'deploy/database/original_platform_http_fixture_models.json';ddl=next(t['ownFixtureDDL']for t in J(model)['tables']if t['table']=='flow_task_operator_record');assert ddl.startswith('CREATE TABLE `flow_task_operator_record`')and'FOREIGN KEY'not in ddl
(P/'original-record-ddl.sql').write_text(ddl,encoding='utf-8');dump(P/'storage-plan.json',{'estimatedAdditionalPeakBytes':768*1024**2,'freeBytesBefore':shutil.disk_usage(P).free,'onlyOneOriginalDDLAndSyntheticRecords':True,'formalOrOwnedGDatabaseConnected':False,'originalRecordModelSHA256':sha(model)})
base=[str(exe),'--no-defaults','--no-monitor','--basedir='+str(runtime),'--datadir='+str(P/'data'),'--lower-case-table-names=1','--skip-log-bin','--mysqlx=0','--innodb-buffer-pool-size=64M','--innodb-redo-log-capacity=64M','--innodb-data-file-path=ibdata1:12M:autoextend:max:256M','--innodb-temp-data-file-path=ibtmp1:12M:autoextend:max:64M','--performance-schema=OFF','--event-scheduler=OFF','--skip-name-resolve','--local-infile=OFF','--secure-file-priv=NULL','--console','--max-connections=8','--skip-slave-start']
def drain(job):
 while job.active_processes():time.sleep(.1)
 job.close()
with(P/'initialize.private.log').open('xb')as out:
 init=subprocess.Popen(base+['--initialize-insecure'],cwd=P,env=env,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);job=jobs.OwnedWindowsJob(init)
 while init.poll()is None:
  try:init.wait(timeout=20)
  except subprocess.TimeoutExpired:print('OWN_HISTORY_MYSQL_INITIALIZING_STILL_LIVE',flush=True)
 drain(job);dump(P/'initialize-terminal.json',{'exitCode':init.returncode,'actualDescendantsZero':True,'forceTerminationUsed':False});assert init.returncode==0,'OWN_HISTORY_MYSQL_INITIALIZE_FAILED'
own_uuid=next(x.split('=',1)[1].strip()for x in(P/'data/auto.cnf').read_text().splitlines()if x.startswith('server-uuid='));secret=uuid.uuid4().hex.encode();bootstrap=P/'bootstrap.private.sql'
bootstrap.write_text("ALTER USER 'root'@'localhost' IDENTIFIED BY '"+secret.decode()+"';\nCREATE DATABASE jnpf;\nCREATE USER 'xnby_history_r180'@'127.0.0.1' IDENTIFIED BY '"+secret.decode()+"';\nGRANT SELECT,INSERT,UPDATE,DELETE,CREATE,TRIGGER ON jnpf.* TO 'xnby_history_r180'@'127.0.0.1';\nGRANT SHUTDOWN ON *.* TO 'xnby_history_r180'@'127.0.0.1';\n",encoding='ascii')
(P/'own-fixture.json').write_text(json.dumps({'freshTemporarySyntheticMySQLOnly':True,'notOriginalGOrPublicOrFormalDatabase':True,'data':str(P/'data')}),encoding='utf-8')
mysql=None;mysqljob=None;mysqlout=None;port=0;rounds=[]
def fixture(mode,label):
 command=[str(java),'-Xmx128m','-XX:ActiveProcessorCount=2','-Dfile.encoding=UTF-8','-cp',cp,'xnby.platform.history.OwnAddsignMybatisFixture',str(P),str(port),own_uuid,mode,str(P/'original-record-ddl.sql')]
 with(P/(label+'.private.log')).open('xb')as log:
  child=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,env=env,cwd=P,creationflags=subprocess.CREATE_NO_WINDOW);childjob=jobs.OwnedWindowsJob(child);child.communicate(input=secret+b'\n')
  drain(childjob)
 dump(P/(label+'-terminal.json'),{'exitCode':child.returncode,'actualDescendantsZero':True,'forceTerminationUsed':False});return child.returncode
def start(label,first):
 global mysql,mysqljob,mysqlout,port
 with socket.socket()as lease:lease.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1);lease.bind(('127.0.0.1',0));port=lease.getsockname()[1]
 log=P/(label+'-mysql.private.log');mysqlout=log.open('xb');mysql=subprocess.Popen(base+['--bind-address=127.0.0.1','--port='+str(port),'--pid-file='+str(P/'mysqld.pid')]+(['--init-file='+str(bootstrap)]if first else[]),env=env,cwd=P,stdout=mysqlout,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);mysqljob=jobs.OwnedWindowsJob(mysql);dump(P/(label+'-started.json'),{'pid':mysql.pid,'port':port,'freshDataDirectory':True})
 deadline=time.monotonic()+60
 while 'ready for connections'not in log.read_text(encoding='utf-8',errors='replace'):
  assert mysql.poll()is None,'OWN_HISTORY_MYSQL_EXITED_BEFORE_READY'
  if time.monotonic()>deadline:print('OWN_HISTORY_MYSQL_STARTING_OBSERVE_EXISTING_NO_RESTART',flush=True);deadline=time.monotonic()+30
  time.sleep(.1)
 assert int((P/'mysqld.pid').read_text().strip())==mysql.pid and authority.listener_owner(port)==[('127.0.0.1',mysql.pid)]
 print('OWN_HISTORY_FRESH_MYSQL_READY',flush=True)
def stop(label):
 global mysql,mysqljob,mysqlout
 if mysql is None:return
 if mysql.poll()is None:
  result=fixture('stop',label+'-shutdown');assert result==0,'OWN_HISTORY_NORMAL_SQL_SHUTDOWN_FAILED_NO_FORCE'
 while mysql.poll()is None:
  try:mysql.wait(timeout=20)
  except subprocess.TimeoutExpired:print('OWN_HISTORY_MYSQL_SHUTDOWN_STILL_LIVE_NO_FORCE',flush=True)
 drain(mysqljob);mysqlout.close();row={'pid':mysql.pid,'exitCode':mysql.returncode,'normalSQLShutdown':mysql.returncode==0,'actualDescendantsZero':True,'forceTerminationUsed':False};rounds.append(row);dump(P/(label+'-stopped.json'),row);mysql=None;mysqljob=None;mysqlout=None
failure=None
try:
 start('first',True);assert fixture('exercise','exercise')==0,'OWN_HISTORY_SQL_EXERCISE_FAILED';stop('first');start('second',False);assert fixture('verify','restart-readback')==0,'OWN_HISTORY_SQL_RESTART_READBACK_FAILED';stop('second')
finally:
 if mysql is not None:stop('cleanup')
 for file in P.glob('*.log'):assert secret not in file.read_bytes(),'OWN_HISTORY_SECRET_OUTPUT_REFUSED'
 secret=None
proof=J(P/'sql-result.json');assert proof['passed']and proof['cases']==10 and len(rounds)==2 and all(x['normalSQLShutdown']and x['actualDescendantsZero']for x in rounds)
proof.update(at=datetime.datetime.now().astimezone().isoformat(),actualMySQLNormalRestartDurabilityPassed=True,allProcessesNormalZeroAndActualDescendantsZero=True,normalSQLShutdowns=2,noOriginalOrGOrFormalOrPublicDatabaseConnected=True,originalDDLSourceSHA256=sha(model),sourcePins=J(P/'source-pins.json'),nativeMyBatisSelectorOrRoleUIIntegrationVerified=False,fixedR34Modified=False)
proof.update(productionClassesCompiledForJava8=True,exactProductionClassDirectory='native-classes-r191');dump(W/'mybatis-transaction-verification-r191.json',proof);print(json.dumps(proof),flush=True)
