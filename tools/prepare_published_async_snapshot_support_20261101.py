"""Compile bounded metadata support; append only owned helper classes to the owned observer JAR copy."""
from pathlib import Path
import hashlib,zipfile,io
import verify_emergency_business_http_20261030 as c

def prepare(root,native,platform,java,java8,seed_cp):
 T=c.T;classes=root/'native-async-classes';classes.mkdir();libs=root/'native-async-compile-libraries';libs.mkdir();cp=list(seed_cp);library_pins={}
 with zipfile.ZipFile(native) as archive:
  for entry in archive.namelist():
   if entry.startswith('BOOT-INF/lib/tomcat-embed-core-') and entry.endswith('.jar'):
    target=libs/Path(entry).name;target.write_bytes(archive.read(entry));cp.append(target);library_pins[entry]=c.sha(target)
 assert len(library_pins)==1;sources=[T/'java/original_platform_runtime8/normal_workflow_async_r1'/name for name in ['OriginalAsyncHttpMetadata.java','OriginalAsyncRequestSnapshotRegistration.java','OriginalAsyncHttpMetadataFixture.java']];classpath=';'.join(map(str,[classes,*cp]));c.run(root,'compile-native-async-metadata',[java.with_name('javac.exe'),'-J-Xmx192m','-source','8','-target','8','-encoding','UTF-8','-proc:none','-cp',classpath,'-d',classes,*sources],45)
 c.run(root,'native-async-metadata-fixture',[java8,'-Xmx128m','-Dfile.encoding=UTF-8','-cp',classpath,'xnby.platform.OriginalAsyncHttpMetadataFixture',root],30)
 fixture=(root/'async-metadata-fixture.properties').read_text(encoding='ascii');assert 'sourceReadsAfterRecycle=0' in fixture and 'normalAndExceptionCleanupPassed=true' in fixture
 jar=platform/'own-platform-observation.jar';base='eae7642792992da2ed4d2f6ff94f55001bda649888c754ffb0aeba4a39ae19d5';assert c.sha(jar)==base;support=platform/'own-platform-async-request.jar';assert not support.exists();added={}
 with zipfile.ZipFile(support,'w',zipfile.ZIP_DEFLATED)as archive:
  for path in classes.rglob('*.class'):
   if path.name.startswith('OriginalAsyncHttpMetadataFixture'):continue
   name=path.relative_to(classes).as_posix();archive.write(path,name);added[name]=c.sha(path)
 provenance=c.read(c.W/'original-normal-workflow-static-r5/inspection-provenance.json');pin=provenance['classes']['jnpf/config/AsyncConfig.class'];assert c.sha(native)==provenance['originalPlatformJarSHA256']
 with zipfile.ZipFile(native)as archive:
  with zipfile.ZipFile(io.BytesIO(archive.read(pin['nestedJar'])))as dependency:expected=hashlib.sha256(dependency.read('jnpf/config/AsyncConfig.class')).hexdigest()
 assert expected==pin['SHA256']
 assert c.sha(jar)==base;c.dump(root/'native-async-support-pins.json',{'originalAdapterJarSHA256':base,'originalAdapterJarUnchanged':True,'separateSupportJarSHA256':c.sha(support),'addedClasses':added,'sourcePins':{str(p):c.sha(p)for p in sources},'compileLibraries':library_pins,'originalAsyncConfigSHA256':expected,'oldR10TaskCacheAuthLifecycleLayersAbsent':True,'fixtureContainsRealAccountsOrTokens':False});return expected,c.sha(support)
