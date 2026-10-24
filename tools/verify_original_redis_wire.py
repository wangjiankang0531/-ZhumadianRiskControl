"""Verify original Redis wire compatibility with synthetic in-memory transport.

Runs two bounded JVMs with all network ports denied. Does not start Spring,
Redis or MySQL and never logs in, creates a JWT or reads business records.
Original runtime archives and existing dependencies are referenced in place.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

import reference_flat_runtime


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bounded_json(path: Path, limit=1024 * 1024):
    if path.stat().st_size > limit:
        raise ValueError('Input metadata exceeds size limit')
    return json.loads(path.read_text(encoding='utf-8-sig'))


def verify(output: Path, platform_metadata: Path, business_flat: Path, audit_receipts: list[Path]) -> dict:
    output=output.resolve();platform_metadata=platform_metadata.resolve(strict=True);business_flat=business_flat.resolve(strict=True)
    if output.exists():
        raise ValueError('A fresh fixture output directory is required')
    meta=bounded_json(platform_metadata)
    java17=Path(meta['javaHome']).resolve(strict=True);java8=Path(meta['platformJavaHome']).resolve(strict=True)
    source=Path(meta['sourceArchive']).resolve(strict=True);guard=Path(meta['guardJar']).resolve(strict=True)
    boot=Path(meta['bootstrapParentJar']).resolve(strict=True);wrappers=platform_metadata.parent/'wrapper-classes'
    source_files=[Path(__file__).with_name('java')/name for name in ('OriginalRedisWireProbe.java','OriginalRedisWireLaunch.java')]
    protected=[business_flat.parent,platform_metadata.parent,java17,java8,source.parent,guard.parent,*[path.parent for path in source_files]]
    if any(output.is_relative_to(path) or path.is_relative_to(output) for path in protected):
        raise ValueError('Fixture output must not overlap runtime, metadata or source inputs')
    for path in source_files:
        if not path.is_file():raise ValueError('Own fixture Java source missing')
    expected={}
    for path in audit_receipts:
        for row in bounded_json(path)['classes']:
            name=row['class'].replace('/','.').removesuffix('.class')
            if name in expected and expected[name]!=row['sha256']:
                raise ValueError('Conflicting original class pins')
            expected[name]=row['sha256']
    output.mkdir(parents=True)
    for name in ('classes','tmp','home'):(output/name).mkdir()
    result={'schema':'zhumadian.original.redis-wire.v1','startedAt':datetime.now(timezone.utc).isoformat(),
        'fixtureSources':{path.name:sha(path) for path in source_files},'platformMetadataSHA256':sha(platform_metadata),
        'platformSourceSHA256':meta['sourceJarSHA256'],'originalApplicationsStarted':False,
        'springContextStarted':False,'databaseConnected':False,'redisServerStarted':False,
        'networkPortsAllowed':[],'syntheticDataOnly':True,'loginOrJwtAttempted':False,
        'originalSerializationCompatibilityVerified':False,'authenticatedBusinessVerified':False,
        'fullCloneReady':False,'passed':False,'runs':[]}
    (output/'attempt_started.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    def save():
        (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    try:
        print('VERIFY_ORIGINAL_RUNTIME_PINS',flush=True)
        if sha(guard)!=meta['guardJarSHA256'] or sha(boot)!=meta['bootstrapParentJarSHA256']:
            raise ValueError('Own previously verified process boundary or loader pin mismatch')
        pins=meta['preflightRelevantClassesSHA256'];wrapper_count=0
        for name,pin in pins.items():
            if name.startswith('wrapper-classes/'):
                wrapper_count+=1
                if sha(platform_metadata.parent/name)!=pin:raise ValueError('Original loader wrapper pin mismatch')
        if not wrapper_count:raise ValueError('Verified loader wrapper pins required')
        if sha(source)!=meta['sourceJarSHA256']:raise ValueError('Original platform archive pin mismatch')
        for name,pin in meta['platformRuntimePins'].items():
            if sha(java8/name)!=pin:raise ValueError('Previously verified Java8 runtime pin mismatch')
        reference_flat_runtime.verify(business_flat)
        result['businessSourceSHA256']=bounded_json(business_flat/'receipt.json',16*1024*1024)['sourceArchiveSHA256']
        env={key:value for key,value in os.environ.items() if key.upper() not in
             ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH') and not key.upper().startswith('LOADER_')}
        env['TMP']=env['TEMP']=str(output/'tmp')
        classpath=[output/'classes',guard,wrappers,boot]
        compiler=subprocess.run([str(java17/'bin/javac.exe'),'-proc:none','--release','8','-encoding','UTF-8',
            '-cp',os.pathsep.join(map(str,classpath)),'-d',str(output/'classes'),*map(str,source_files)],
            cwd=output,env=env,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=30)
        (output/'compile.log').write_bytes(compiler.stdout+compiler.stderr)
        if compiler.returncode:raise ValueError('Own Java fixture compilation failed')
        (output/'logback.xml').write_text('<configuration><root level="OFF"/></configuration>',encoding='ascii')
        for mode,jdk,extra in [('platform-write',java8,[]),('business-read',java17,[business_flat/'application.jar'])]:
            print('RUNNING '+mode,flush=True)
            command=[str(jdk/'bin/java.exe'),'-Xmx128m','-XX:+PerfDisableSharedMem','-Dfile.encoding=UTF-8',
                '-Djava.io.tmpdir='+str(output/'tmp'),'-Duser.home='+str(output/'home'),
                '-Dlogback.configurationFile='+(output/'logback.xml').as_uri(),
                '-Down.platform.root='+str(output),'-Down.platform.source.path='+str(source),
                '-Down.platform.independent.jar.wrappers=true','-Djava.protocol.handler.pkgs=xnby.platform.protocol',
                '-cp',os.pathsep.join(map(str,classpath+extra)),'xnby.platform.OriginalRedisWireLaunch',
                str(source),str(output),mode]
            with (output/(mode+'.log')).open('wb') as log:
                process=subprocess.Popen(command,cwd=output,env=env,stdout=log,stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                run={'mode':mode,'pid':process.pid,'exited':False,'timeout':False};result['runs'].append(run)
                try:
                    try:run['exitCode']=process.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        run['timeout']=True;process.terminate();run['exitCode']=process.wait(timeout=10)
                finally:
                    run['exited']=process.poll() is not None;save()
            if not run['exited'] or run['exitCode'] or run['timeout']:
                raise ValueError('Original serializer fixture did not exit successfully: '+mode)
            if (output/(mode+'-boundary.txt')).read_text('utf-8').splitlines()!=['guardInstalled=true','{}']:
                raise ValueError('Process constraint was replaced or reported denied operations')
            rows=[line.split('\t') for line in (output/(mode+'-results.tsv')).read_text('utf-8').splitlines()]
            if len([row for row in rows if row[0]=='PASS'])!=6:raise ValueError('Synthetic fixture case count mismatch')
            result[mode+'Cases']=6
            if mode=='platform-write':
                if len((output/'synthetic-redis-wire.tsv').read_text('utf-8').splitlines())!=6:
                    raise ValueError('Synthetic wire row count mismatch')
                result['syntheticWireBytes']=(output/'synthetic-redis-wire.tsv').stat().st_size
                result['originalExpiryMilliseconds']=int(next(row[1] for row in rows if row[0]=='EXPIRATION_MILLISECONDS'))
            else:
                if len([row for row in rows if row[0]=='EXPECTED_REJECTION'])!=1:
                    raise ValueError('Original missing-cache rejection not observed')
                result['missingCacheEntryRejected']=True
            result[mode+'ResultsSHA256']=sha(output/(mode+'-results.tsv'))
        loaded=[]
        for mode in ('platform-write','business-read'):
            for line in (output/(mode+'-results.tsv')).read_text('utf-8').splitlines():
                row=line.split('\t')
                if row[0]!='CLASS':continue
                if row[1]=='com.cqweh.cloud.common.utils.Jsons':
                    matches=[]
                    for path in (business_flat.parent/'deps').glob('cqweh-cloud*.jar'):
                        with zipfile.ZipFile(path) as archive:
                            name='com/cqweh/cloud/common/utils/Jsons.class'
                            if name in archive.namelist():matches.append(hashlib.sha256(archive.read(name)).hexdigest())
                    if matches!=[row[2]]:raise ValueError('Original Jsons class provenance mismatch')
                elif expected.get(row[1])!=row[2]:
                    raise ValueError('Loaded original class pin missing or mismatched')
                loaded.append({'mode':mode,'class':row[1],'sha256':row[2],'originalProvenanceVerified':True})
        if len(loaded)!=7:raise ValueError('Original loaded class count mismatch')
        print('VERIFY_SOURCE_UNCHANGED',flush=True)
        if sha(source)!=meta['sourceJarSHA256']:raise ValueError('Original archive changed during fixture')
        result.update(completedAt=datetime.now(timezone.utc).isoformat(),loadedOriginalClasses=loaded,
            originalSerializationCompatibilityVerified=True,syntheticFieldComparisons=36,
            passed=True,sourceArchiveUnchanged=True)
        save();return result
    except BaseException:
        result['failedAt']=datetime.now(timezone.utc).isoformat();save();raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--platform-metadata',type=Path,required=True)
    parser.add_argument('--business-flat',type=Path,required=True)
    parser.add_argument('--audit-receipt',type=Path,action='append',required=True)
    args=parser.parse_args()
    result=verify(args.output,args.platform_metadata,args.business_flat,args.audit_receipt)
    print(json.dumps({'passed':result['passed'],'platformSyntheticCases':6,'businessSyntheticCases':6,
        'fieldComparisons':36,'missingCacheEntryRejected':True,'originalExpiryMilliseconds':result['originalExpiryMilliseconds'],
        'bothProcessesExitedZero':True,'originalApplicationsStarted':False,'networkPortsAllowed':[],
        'authenticatedBusinessVerified':False}))


if __name__=='__main__':main()
