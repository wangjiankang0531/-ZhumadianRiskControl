import argparse,datetime,hashlib,json,os,pathlib,re,subprocess,zipfile
p=argparse.ArgumentParser(description='Prepare the experimental startup-only orphan compatibility candidate')
p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--name',required=True);p.add_argument('--previous-receipt',type=pathlib.Path,required=True);args=p.parse_args()
W=args.workspace.resolve(strict=True);A=W.parents[1];P=pathlib.Path(__file__).parent
assert A.name=='Application' and (A/'tools/reference_flat_runtime.py').is_file(),'OWN_KNOWN_WORKSPACE_REQUIRED'
assert re.fullmatch(r'own-pboot-r[1-9][0-9]{1,3}',args.name),'OWN_NEW_RUN_NAME_REQUIRED'
assert not (W/args.name).exists(),'OWN_FRESH_RUN_ROOT_REQUIRED'
fixture=W/(args.name+'-bootstrap-build');assert not fixture.exists();fixture.mkdir();(fixture/'deps').mkdir();(fixture/'classes').mkdir()
meta=json.loads((W/'own-pboot-r29/preparation.json').read_bytes());inv=json.loads((W/'platform-module-linkage-r1_20261024/inventory.json').read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dependency=next(row for row in inv['libraries'] if row['member'].endswith('/spring-aop-5.3.31.jar'))
with zipfile.ZipFile(meta['sourceArchive']) as z:raw=z.read(dependency['member'])
assert hashlib.sha256(raw).hexdigest()==dependency['sha256'];aop=fixture/'deps/spring-aop-5.3.31.jar';aop.write_bytes(raw)
classpath=[row['file'] for row in meta['compileDependencies']]+[str(aop)];jdk=pathlib.Path(meta['javaHome']);java8=pathlib.Path(meta['platformJavaHome']);sources=[P/'java/OriginalBootstrapOrphanGuard.java',P/'java/BootstrapOrphanPolicyFixture.java']
for row in meta['compileDependencies']:assert sha(pathlib.Path(row['file']))==row['sha256']
run=subprocess.run([str(jdk/'bin/javac.exe'),'-proc:none','--release','8','-encoding','UTF-8','-cp',os.pathsep.join(classpath),'-d',str(fixture/'classes'),*map(str,sources)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
(fixture/'compile.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,'OWN_BOOTSTRAP_GUARD_COMPILE_FAILED'
run=subprocess.run([str(java8/'bin/java.exe'),'-Xmx128m','-cp',os.pathsep.join([str(fixture/'classes'),*classpath]),'xnby.platform.BootstrapOrphanPolicyFixture'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20)
(fixture/'fixture.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0 and b'ORPHAN_POLICY_FIXTURE_CHECKS=10' in run.stdout,'OWN_BOOTSTRAP_POLICY_FIXTURE_FAILED'
fixture_receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'policyChecks':10,'databaseConnected':False,'originalClassesInitialized':False,'springContextStarted':False,'sourceSHA256':{p.name:sha(p) for p in sources},'compileDependencySHA256':dependency['sha256']};(fixture/'receipt.json').write_text(json.dumps(fixture_receipt,indent=2),encoding='utf-8');print(json.dumps(fixture_receipt),flush=True)
root=W/args.name
run=subprocess.run(['python','-B',str(A/'tools/prepare_original_platform_lifecycle.py'),'--workspace',str(W),'--name',root.name,'--previous-receipt',str(args.previous_receipt.resolve())],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=40)
(fixture/'candidate-preparation.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,'OWN_BOOTSTRAP_CANDIDATE_PREPARATION_FAILED'
meta=json.loads((root/'preparation.json').read_bytes());oldjar=root/'own-platform-observation.jar';newjar=root/'own-platform-observation.with-bootstrap.jar'
with zipfile.ZipFile(oldjar) as old,zipfile.ZipFile(newjar,'w',zipfile.ZIP_DEFLATED) as new:
 for info in old.infolist():new.writestr(info,old.read(info))
 for path in (fixture/'classes/xnby/platform').glob('OriginalBootstrapOrphanGuard*.class'):new.write(path,path.relative_to(fixture/'classes').as_posix())
newjar.replace(oldjar);meta.update(lifecycleObservationJarSHA256=sha(oldjar),bootstrapGuardSourceSHA256=sha(sources[0]),bootstrapGuardExperimental=True)
meta['compileDependencies'].append({'file':str(aop),'sha256':dependency['sha256']});(root/'preparation.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
runner=A/'tools/verify_original_bootstrap_candidate.py'
(root/'bootstrap-preparation-receipt.json').write_text(json.dumps({'recordedAt':datetime.datetime.now().astimezone().isoformat(),'runnerSHA256':sha(runner),'guardSourceSHA256':sha(sources[0]),'originalClassesModified':False,'guardFiltersOnlyWithinOriginalBootstrapCall':True,'orphanRowsDeleted':False,'liveOrHistoricalReferencesCauseFailure':True,'originalPlatformStarted':False,'fullCloneReady':False},indent=2),encoding='utf-8')
print('BOOTSTRAP_COMPATIBILITY_CANDIDATE_PREPARED',flush=True)
