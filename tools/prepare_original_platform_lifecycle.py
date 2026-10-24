"""Prepare an original-platform lifecycle trial from the pinned existing baseline only."""
import argparse,datetime,hashlib,json,os,pathlib,re,subprocess,zipfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--name',required=True);p.add_argument('--previous-receipt',type=pathlib.Path,required=True);a=p.parse_args()
W=a.workspace.resolve(strict=True);A=W.parents[1];assert A.name=='Application' and (A/'tools/reference_flat_runtime.py').is_file(),'OWN_KNOWN_WORKSPACE_REQUIRED'
assert re.fullmatch(r'own-pboot-r[1-9][0-9]{1,3}',a.name),'OWN_NEW_RUN_NAME_REQUIRED'
base=W/'own-pboot-r27';root=W/a.name;dbroot=W/'own-mysql-r27';assert not root.exists(),'OWN_FRESH_RUN_ROOT_REQUIRED'
previous=json.loads(a.previous_receipt.read_bytes());assert previous['ownMySQLExited'] and previous['ownMySQLExitCode']==0 and previous['ownRedisExited'] and previous['ownRedisExitCode']==0
assert a.previous_receipt.resolve().parent.parent==W,'OWN_PREVIOUS_RECEIPT_SCOPE'
proof=json.loads((dbroot/'completed-offline-verification.json').read_bytes());assert proof['passed'] and proof['ownServerExitCode']==0
meta=json.loads((base/'preparation.json').read_bytes());sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
for row in meta['compileDependencies']:assert sha(pathlib.Path(row['file']))==row['sha256']
for name,pin in meta['preflightRelevantClassesSHA256'].items():assert sha(base/name)==pin
assert sha(base/'own-platform-observation.jar')==next(row['sha256'] for row in meta['unchangedJavaPayloads'] if row['path']=='own-platform-observation.jar')
root.mkdir()
for folder in ('wrapper-classes','observer-classes','builder-classes'):
 for old in (base/folder).rglob('*'):
  if old.is_file():
   target=root/folder/old.relative_to(base/folder);target.parent.mkdir(parents=True,exist_ok=True);os.link(old,target)
for name in ('tmp','home','files','logs','lifecycle-classes'):(root/name).mkdir()
sources=[pathlib.Path(__file__).parent/'java'/name for name in ('PlatformWritableObservation.java','OriginalIdGeneratorShutdown.java')]
jdk=pathlib.Path(meta['javaHome']);run=subprocess.run([str(jdk/'bin/javac.exe'),'-proc:none','--release','8','-encoding','UTF-8','-cp',os.pathsep.join(row['file'] for row in meta['compileDependencies']),'-d',str(root/'lifecycle-classes'),*map(str,sources)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
(root/'lifecycle-compile.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,'OWN_LIFECYCLE_COMPILE_FAILED'
with zipfile.ZipFile(base/'own-platform-observation.jar') as old,zipfile.ZipFile(root/'own-platform-observation.jar','w',zipfile.ZIP_DEFLATED) as new:
 for info in old.infolist():new.writestr(info,old.read(info))
 for path in (root/'lifecycle-classes').rglob('*.class'):new.write(path,path.relative_to(root/'lifecycle-classes').as_posix())
meta.update(previousControlledAttempt=str(a.previous_receipt.resolve().parent),ownedDatabaseRoot=str(dbroot),ownedDatabaseUUID=proof['newOwnedUUID'],lifecycleAdapterSourceSHA256=sha(sources[1]),lifecycleObservationJarSHA256=sha(root/'own-platform-observation.jar'))
(root/'preparation.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'root':str(root),'ownSourceSHA256':{s.name:sha(s) for s in sources},'originalClassesModified':False,'sourceDatabaseConnected':False,'applicationStarted':False,'copiedOriginalJarOrFullDatabase':False,'fullCloneReady':False}
(root/'preparation-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt))
