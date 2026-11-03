from pathlib import Path
import ast,copy,hashlib,json,struct,subprocess,zipfile
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';V=Path(__file__).parent;W=R/'work/addsign-history-r180';OUT=W/'production-module-r199-r2';assert not OUT.exists();OUT.mkdir()
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
base=R/'Application/tools/java/public_emergency_workflow_async_r1/OriginalAsyncPersistentPlatformLaunch.java';s=base.read_text(encoding='utf-8').replace('OriginalAsyncPersistentPlatformLaunch','OriginalHistoryPersistentPlatformLaunch')
s=s.replace('private final Archive source,observation,support;','private final Archive source,observation,support,history;')
s=s.replace('Archive observation,Archive support){super(source);this.source=source;this.observation=observation;this.support=support;}','Archive observation,Archive support,Archive history){super(source);this.source=source;this.observation=observation;this.support=support;this.history=history;}')
s=once(s,'paths.add(support);return paths.iterator();','paths.add(support);paths.add(history);return paths.iterator();')
anchor='new OriginalHistoryPersistentPlatformLaunch(source,observation,new JarFileArchive(supportPath.toFile())).launch(new String[0]);'
new='''Path historyPath=root.resolve("own-before-addsign-history.jar");String historyExpected=System.getProperty("own.workflow.before-addsign.module.sha256");StringBuilder historyActual=new StringBuilder();for(byte value:digest.digest(Files.readAllBytes(historyPath)))historyActual.append(String.format(Locale.ROOT,"%02x",value&255));if(historyExpected==null||!historyExpected.matches("[0-9a-f]{64}")||!historyExpected.equals(historyActual.toString()))throw new IllegalStateException("EXACT_DECLARED_HISTORY_SUPPORT_REQUIRED");
  new OriginalHistoryPersistentPlatformLaunch(source,observation,new JarFileArchive(supportPath.toFile()),new JarFileArchive(historyPath.toFile())).launch(new String[0]);'''
s=once(s,anchor,new);src=OUT/'OriginalHistoryPersistentPlatformLaunch.java';src.write_text(s,encoding='utf-8');classes=OUT/'launcher-classes';classes.mkdir();template=A/'payload/platform/run-template'
cp=';'.join(str(p)for p in [A/'payload/platform/boot-loader.jar',A/'payload/platform/process-boundary.jar',template/'persistent-launcher-classes',template/'wrapper-classes',A/'payload/callback-overlay/20261026-password-identity/persistent-launcher-classes'])
r=subprocess.run([str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','8','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(classes),str(src)],capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
(OUT/'compile.stderr.private.log').write_bytes(r.stderr);assert r.returncode==0,'OWN_HISTORY_LAUNCHER_COMPILE_FAILED'
rows={}
for p in classes.rglob('*.class'):
 assert struct.unpack('>H',p.read_bytes()[6:8])[0]==52
 rows['payload/platform/run-template/persistent-launcher-classes/'+p.relative_to(classes).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
assert len(rows)==1
jar=OUT/'own-before-addsign-history.jar';native=W/'native-classes-r191';nativeclasses=sorted(native.rglob('*.class'));assert len(nativeclasses)==6
with zipfile.ZipFile(jar,'x',zipfile.ZIP_DEFLATED)as z:
 for p in nativeclasses:
  assert struct.unpack('>H',p.read_bytes()[6:8])[0]==52
  entry=zipfile.ZipInfo(p.relative_to(native).as_posix(),(2026,11,3,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;z.writestr(entry,p.read_bytes())
rows['payload/platform/run-template/own-before-addsign-history.jar']={'bytes':jar.stat().st_size,'sha256':sha(jar)}
contract={'revision':'native-before-addsign-original-date-history-v1','files':rows,'sameOriginalDynamicTransactionAndConnection':True,'originalNativeServiceCallGate':True,'originalJavaDateFieldsCopied':True,'newDatasourceDDLOrStatusCode':False,'originalAsyncAndAuthArchivesRetained':True}
helper=(V/'original_native_history_release_support_r199.py').read_text(encoding='utf-8');helper=once(helper,'CONTRACT=None  # Fixed by the artifact builder, together with the exact Java 8 code pins.','CONTRACT='+repr(contract));ast.parse(helper);hp=OUT/'original_native_history_release_support.py';hp.write_text(helper,encoding='utf-8')
controller=(A/'tools/serve_original_server_release.py').read_text(encoding='utf-8');original_controller=controller
controller=once(controller,'from original_platform_async_release_support import configure_platform, adapt_platform_launch','from original_platform_async_release_support import configure_platform, adapt_platform_launch\nfrom original_native_history_release_support import configure_history, adapt_history_launch')
controller=once(controller,'config=configure_platform(release,config,callback_enabled=callback is not None)','config=configure_platform(release,config,callback_enabled=callback is not None);config=configure_history(release,config)')
controller=once(controller,'prepared=adapt_platform_launch(app,release,platform,prepared);','prepared=adapt_platform_launch(app,release,platform,prepared);prepared=adapt_history_launch(app,release,platform,prepared);')
ast.parse(controller);cpfile=OUT/'serve_original_server_release.py';cpfile.write_text(controller,encoding='utf-8')
updater=(R/'Application/tools/original_public_test_update_r35_20261103.py').read_text(encoding='utf-8');original_updater=updater
constants='\nR36_HISTORY_FIELD = "nativeBeforeAddsignOpinionHistory"\nR36_HISTORY_CONTRACT = '+repr(contract)+'\nR36_HISTORY_CONTROLLER_PIN = '+repr({'bytes':cpfile.stat().st_size,'sha256':sha(cpfile)})+'\nR36_HISTORY_HELPER = "tools/original_native_history_release_support.py"\nR36_HISTORY_HELPER_SHA = '+repr(sha(hp))+'\n\n'
extra='''def history_declared(release):
    if R36_HISTORY_FIELD not in release:return False
    require(release[R36_HISTORY_FIELD] == R36_HISTORY_CONTRACT, 'EXACT_NATIVE_HISTORY_DESCRIPTOR_REQUIRED')
    require(release['controllerFiles'].get(R23_CONTROLLER) == R36_HISTORY_CONTROLLER_PIN['sha256'] and release['controllerFiles'].get(R36_HISTORY_HELPER) == R36_HISTORY_HELPER_SHA, 'EXACT_HISTORY_CONTROLLER_AND_HELPER_REQUIRED')
    return True

def pool_control_pins(release):
    pins=dict(R27_POOL_PINS)
    if history_declared(release):pins[R23_CONTROLLER]=R36_HISTORY_CONTROLLER_PIN
    return pins

def history_ready(app,row):
    release=read(regular(app,'release-manifest.json'))
    if not history_declared(release):return None
    payload=read(check_file(app,'payload-manifest.json',release['payloadManifestSHA256']))
    for name,pin in R36_HISTORY_CONTRACT['files'].items():
        require(payload['files'].get(name)==pin,'HISTORY_PAYLOAD_DECLARATION_REQUIRED')
        check_file(app,name,pin['sha256'],pin['bytes'])
    check_file(app,R36_HISTORY_HELPER,R36_HISTORY_HELPER_SHA)
    platform=regular(app,Path(row['platformRun']).absolute().relative_to(app).as_posix())
    require(platform.parent==app/'UserData/TianjinOriginalPlatform/runs' and re.fullmatch(r'j[1-9][0-9]{0,3}',platform.name),'OWN_HISTORY_PLATFORM_RUNTIME_REQUIRED')
    for name,pin in R36_HISTORY_CONTRACT['files'].items():check_file(platform,name.split('/run-template/',1)[1],pin['sha256'],pin['bytes'])
    report=regular(platform,'before-addsign-history-ready.properties')
    require(report.is_file() and report.stat().st_size<=4096,'BOUNDED_HISTORY_REPORT_REQUIRED')
    properties=dict(line.split('=',1)for line in report.read_text(encoding='ascii').splitlines()if '='in line)
    require(properties.get('installed')=='true' and properties.get('originalEntityMapperAndServicePinned')=='true' and properties.get('originalTransactionAndConnectionUsed')=='true' and properties.get('newDatasourceOrDDL')=='false' and properties.get('normalRoleUIAcceptanceProvenByStartup')=='false' and properties.get('factories','').isdigit() and 1<=int(properties['factories'])<=4,'EXACT_NATIVE_HISTORY_READY_REQUIRED')
    return {'exactNativeServiceGateAndSameTransactionHistoryModuleReady':True,'normalRoleAcceptanceClaimedByStartup':False,'newDatasourceOrDDL':False}

'''
updater=once(updater,'def runtime_pool_declared(release):',constants+extra+'def runtime_pool_declared(release):')
tree=ast.parse(updater)
for node in reversed(tree.body):
 if not isinstance(node,ast.FunctionDef)or node.name not in ['runtime_pool_declared','runtime_pool_ready','controller_pin_for','health']:continue
 segment=ast.get_source_segment(updater,node);changed=segment
 if node.name=='runtime_pool_declared':changed=once(changed,"controls.get(n)==p['sha256']for n,p in R27_POOL_PINS.items()","controls.get(n)==p['sha256']for n,p in pool_control_pins(release).items()")
 if node.name=='runtime_pool_ready':changed=once(changed,'for n,pin in R27_POOL_PINS.items():check_file','for n,pin in pool_control_pins(release).items():check_file')
 if node.name=='controller_pin_for':changed=changed.replace("    return R27_POOL_PINS", "    if history_declared(release):return R36_HISTORY_CONTROLLER_PIN['sha256']\n    return R27_POOL_PINS",1)
 if node.name=='health':changed=once(changed,'    async_ready(app, row)','    async_ready(app, row)\n    history_ready(app, row)')
 assert changed!=segment;updater=once(updater,segment,changed)
ast.parse(updater);up=OUT/'original_public_test_update.py';up.write_text(updater,encoding='utf-8')
functions=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
old,new=functions(original_updater),functions(updater);assert {n for n in old if old[n]!=new[n]}=={'runtime_pool_declared','runtime_pool_ready','controller_pin_for','health'}
assert all(old[n]==new[n]for n in ['normal_stop','launch','backup_code','replace_code','restore_code','apply_update','recover_pending','rollback_latest'])
proof={'prepared':True,'contract':contract,'controllerSHA256':sha(cpfile),'helperSHA256':sha(hp),'updaterSHA256':sha(up),'allOriginalAsyncAuthAndNativeArchivesKept':True,'privateConfigurationChanged':False,'onlyControllerMainFunctionAdapted':True,'existingUpdaterFunctionsChanged':['runtime_pool_declared','runtime_pool_ready','controller_pin_for','health'],'allStopLaunchBackupRestoreAndRecoveryFunctionsASTKept':True,'noPublicBundleOrNativeAcceptanceClaimed':True,'files':{p.relative_to(OUT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}for p in [src,hp,cpfile,up,jar,*classes.rglob('*.class')]}}
(OUT/'module-pins.json').write_bytes(enc(proof));print(json.dumps({k:v for k,v in proof.items()if k not in ['contract','files']}))
