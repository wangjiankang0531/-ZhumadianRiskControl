import datetime,hashlib,json,os,pathlib,subprocess,zipfile
import argparse
p=argparse.ArgumentParser(description='Verify provided bigscreen source/class equivalence without starting it.');p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--reuse-dependencies',type=pathlib.Path);args=p.parse_args();W=args.workspace.resolve(strict=True);A=W.parents[1];assert A.name=='Application';D=A.parent/'Document';manifest=json.loads((D/'Deployment/tianjin_native_replica_20261023/original_source_copies.json').read_bytes());ref=pathlib.Path(manifest['projects']['bigscreen_java']['reference']);archive=ref/'tjwhyq-base/target/tjwhyq-base.jar';root=args.output.resolve();assert root.is_relative_to(W) and not root.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(archive)=='97c2f1662a3a4494f01da4c2e83d7fa960e6832bda870e90424ffbaddf667cca'
sources=sorted((ref/'tjwhyq-base/src/main/java').rglob('*.java'));before={str(p.relative_to(ref)):sha(p) for p in sources};assert len(sources)>10
root.mkdir();(root/'deps').mkdir();(root/'classes').mkdir();(root/'tmp').mkdir();(root/'generated').mkdir();pins=[]
with zipfile.ZipFile(archive) as source:
 for entry in source.infolist():
  if entry.filename.startswith('BOOT-INF/lib/') and entry.filename.endswith('.jar'):
   assert entry.file_size<30*1024**2;raw=source.read(entry);target=root/'deps'/pathlib.Path(entry.filename).name
   if args.reuse_dependencies:
    existing=args.reuse_dependencies.resolve(strict=True)/target.name;assert existing.is_relative_to(W) and existing.is_file() and not existing.is_symlink() and sha(existing)==hashlib.sha256(raw).hexdigest();os.link(existing,target)
   else:target.write_bytes(raw)
   pins.append({'entry':entry.filename,'bytes':len(raw),'sha256':sha(target)})
 assert sha(root/'deps/sqlite-jdbc-3.36.0.3.jar')=='af3a3376391e186a0fed63ecd414b72a882bf452667b490a0be3abf85b637d3f'
 assert sha(root/'deps/lombok-1.18.2.jar')=='f13db210efa2092a58bb7befce58ffa502e5fefc5e1099f45007074008756bc0'
 meta=json.loads((W/'own-pboot-r32/preparation.json').read_bytes());java8=pathlib.Path(meta['platformJavaHome']);env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')};env['TMP']=env['TEMP']=str(root/'tmp')
 for name,pin in meta['platformRuntimePins'].items():assert sha(java8/name)==pin
 command=[str(java8/'bin/javac.exe'),'-J-Xmx256m','-J-Djava.io.tmpdir='+str(root/'tmp'),'-source','1.8','-target','1.8','-g','-encoding','UTF-8','-processorpath',str(root/'deps/lombok-1.18.2.jar'),'-processor','lombok.launch.AnnotationProcessorHider$AnnotationProcessor','-cp',os.pathsep.join(str(p) for p in sorted((root/'deps').glob('*.jar'))),'-d',str(root/'classes'),'-s',str(root/'generated'),*map(str,sources)]
 run=subprocess.run(command,cwd=root,env=env,capture_output=True,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW);(root/'compile.private.log').write_bytes(run.stdout+run.stderr)
 if run.returncode!=0:
  print(json.dumps({'compileExitCode':run.returncode,'log':str(root/'compile.private.log')}));raise SystemExit(1)
 rows=[]
 for path in sorted((root/'classes').rglob('*.class')):
  name=path.relative_to(root/'classes').as_posix();old=source.read('BOOT-INF/classes/'+name) if 'BOOT-INF/classes/'+name in source.namelist() else None;rows.append({'class':name,'compiledSHA256':sha(path),'originalSHA256':hashlib.sha256(old).hexdigest() if old else None,'exact':old==path.read_bytes()})
assert all(sha(ref/name)==pin for name,pin in before.items()) and sha(archive)=='97c2f1662a3a4494f01da4c2e83d7fa960e6832bda870e90424ffbaddf667cca'
receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'sourceArchiveSHA256':sha(archive),'javaSources':len(sources),'sourceSHA256':before,'dependencyCount':len(pins),'dependencyBytes':sum(p['bytes'] for p in pins),'dependencies':pins,'compiledClasses':len(rows),'byteExactClasses':sum(r['exact'] for r in rows),'classes':rows,'originalSourceOrJarModified':False,'originalApplicationStarted':False,'sourceDatabaseConnected':False,'fullCloneReady':False};(root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:receipt[k] for k in ('javaSources','dependencyCount','dependencyBytes','compiledClasses','byteExactClasses','originalSourceOrJarModified','originalApplicationStarted','fullCloneReady')}))

assert receipt['compiledClasses']==receipt['byteExactClasses']==27,'ALL_ORIGINAL_CLASSES_MUST_MATCH'
