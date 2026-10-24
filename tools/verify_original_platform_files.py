"""Validate persistent platform ownership and exact Java8 runtime/file/port scope, without Spring."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid
from original_platform_files import OwnedPlatformFiles


def verify(workspace, output):
    workspace, output = Path(workspace).resolve(strict=True), Path(output).resolve()
    app = workspace.parents[1]
    if output.exists() or not output.is_relative_to(workspace):
        raise ValueError('FRESH_OWN_VERIFICATION_ROOT_REQUIRED')
    output.mkdir();(output / 'classes').mkdir()
    meta = json.loads((workspace / 'own-pboot-r32/preparation.json').read_bytes())
    guard = Path(meta['guardJar']);sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    if sha(guard) != '799d1289e3122b0e73ef4b6a3c9639bc5c59d820c7670800c673a1b7acd5a508':
        raise ValueError('EXISTING_JAVA8_GUARD_PIN_REQUIRED')
    for name,pin in meta['platformRuntimePins'].items():
        if sha(Path(meta['platformJavaHome'])/name)!=pin:raise ValueError('EXISTING_JAVA8_RUNTIME_PIN_MISMATCH')
    if sha(meta['bootstrapParentJar'])!=meta['bootstrapParentJarSHA256']:raise ValueError('ORIGINAL_BOOTSTRAP_PIN_MISMATCH')
    for name,pin in meta['preflightRelevantClassesSHA256'].items():
        if sha(workspace/'own-pboot-r32'/name)!=pin:raise ValueError('KNOWN_PLATFORM_HELPER_PIN_MISMATCH')
    here = Path(__file__).resolve().parent
    sources = [here / 'java' / name for name in ('OriginalPlatformStorageScope.java', 'PlatformPersistentScopeFixture.java', 'OriginalPersistentPlatformLaunch.java')]
    cp = os.pathsep.join(map(str,[output / 'classes',guard,meta['bootstrapParentJar'],workspace / 'own-pboot-r32/wrapper-classes']))
    env = {k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
    def run(command,name):
        r=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
        (output/(name+'.private.log')).write_bytes(r.stdout+r.stderr)
        if r.returncode!=0:raise RuntimeError('PERSISTENT_PLATFORM_'+name.upper()+'_FAILED')
        return r.stdout
    run([Path(meta['javaHome'])/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-cp',cp,'-d',output/'classes',*sources],'compile')
    fixture_app=output/'Application';(fixture_app/'tools').mkdir(parents=True);(fixture_app/'tools/reference_flat_runtime.py').write_bytes((app/'tools/reference_flat_runtime.py').read_bytes())
    names=['own-j'+str(n) for n in range(9901,10000) if not (fixture_app/'UserData/TianjinOriginalPlatform/runs'/('j'+str(n))).exists()]
    if len(names)<2:raise ValueError('FRESH_SELF_TEST_RUNTIME_NAMES_REQUIRED')
    first=OwnedPlatformFiles(fixture_app,names[0]).acquire();checks=0;sentinel=None
    try:
        before=first.observation();checks+=1
        contender=OwnedPlatformFiles(fixture_app,names[1]);rejected=False
        try:contender.acquire()
        except OSError:rejected=True
        if not rejected:contender.release();raise ValueError('CONCURRENT_PLATFORM_OWNER_ACCEPTED')
        assert not contender.run_root.exists();checks+=2
        sentinel=first.files/('own-lifecycle-'+str(uuid.uuid4())+'.txt');payload=('own-persistent-platform:'+first.identity['ownerId']).encode('ascii');sentinel.write_bytes(payload);checks+=1
        raw=run([Path(meta['platformJavaHome'])/'bin/java.exe','-Xmx64m','-Djava.io.tmpdir='+str(first.run_root),'-cp',cp,'xnby.platform.PlatformPersistentScopeFixture',first.run_root,first.identity['ownerId'],output/'outside-probe-must-not-exist.txt'],'actual-scope')
        assert b'PERSISTENT_PLATFORM_SCOPE_CHECKS=30' in raw;checks+=1
        assert not (output/'outside-probe-must-not-exist.txt').exists();checks+=1
    finally:first.release()
    second=OwnedPlatformFiles(fixture_app,names[1]).acquire()
    try:
        after=second.observation();assert before['dataOwnerId']==after['dataOwnerId'] and before['identitySHA256']==after['identitySHA256'];checks+=2
        assert sentinel.read_bytes()==payload;checks+=1
        sentinel.unlink();assert not sentinel.exists();checks+=1
    finally:second.release()
    result={'ownerLifecycleChecks':checks,'actualJava8ScopeChecks':30,'sourceSHA256':{p.name:sha(p) for p in sources},'dataIdentityStableAcrossOwnerRestart':True,'concurrentOwnerRejectedBeforeRuntimeCreated':True,'onlyOwnedSentinelDeleted':True,'testDataRootIsIsolatedFixtureApplication':True,'actualCandidateDataLockBypassed':False,'originalGuardModified':False,'originalApplicationStarted':False,'sourceDatabaseConnected':False,'springContextStarted':False,'fullCloneReady':False}
    (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(verify(a.workspace,a.output)))


if __name__=='__main__':main()
