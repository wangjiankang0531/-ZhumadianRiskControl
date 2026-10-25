"""Freeze a bounded, private input plan for the current original-system release.

No archive creation, source database access, service start, or source mutation.
The plan contains private configuration and must never be committed or served.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,subprocess,urllib.parse,zipfile

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application',type=Path,required=True)
    parser.add_argument('--prepared-properties',type=Path,required=True)
    parser.add_argument('--platform-arguments',type=Path,required=True)
    parser.add_argument('--lifecycle-classes',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();app=args.application.resolve(strict=True);w=app/'work/tianjin_native_20261023'
    assert app.name=='Application' and (w/'own-j18/ready.json').is_file()
    out=args.output.resolve();assert not out.exists() and not out.is_relative_to(w/'own-mysql-r26')
    assert shutil.disk_usage(out.parent).free>6*1024**3,'SIX_GIB_LOCAL_RELEASE_PEAK_REQUIRED'
    meta=json.loads((w/'own-pboot-r32/preparation.json').read_bytes())
    inventory=json.loads((w/'own-original-frontend-roots-r2/frontends.private.json').read_bytes())
    bindings=json.loads((w/'own-original-frontend-roots-r2/bindings.private.json').read_bytes())['roots']
    props=json.loads(args.prepared_properties.read_bytes())
    p=app/'UserData/TianjinOriginalPlatform/runs/j18';b=w/'own-j18/b';seed=w/'own-mysql-r26'
    assert digest(seed/'server-process.private.log')=='cfb0233f047959b6eaecf655ade2146ad634905a94d1fb351af37df5f59d0243'
    assert 'Shutdown complete' in (seed/'server-process.private.log').read_text(encoding='utf-8',errors='replace')
    # Capture only mysqld command lines; they contain explicit owned paths, not credentials.
    cmd="Get-CimInstance Win32_Process -Filter \"Name='mysqld.exe'\" | Select-Object ProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    r=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True,timeout=20)
    assert r.returncode==0,'MYSQL_OWNERSHIP_QUERY_REQUIRED'
    active=json.loads(r.stdout.decode('utf-8-sig'));active=active if isinstance(active,list) else [active]
    assert active and all(str(seed).lower() not in row['CommandLine'].lower() for row in active),'CLOSED_SEED_MUST_NOT_BE_IN_USE'
    assert any(str(w/'own-mysql-r27/data').lower() in row['CommandLine'].lower() for row in active),'CURRENT_CANDIDATE_IDENTITY_REQUIRED'
    own_connections=dict(line.split('=',1) for line in (seed/'own-connection.properties').read_text('ascii').splitlines() if '=' in line)
    assert own_connections['serverUUID']=='c0a47e62-cf57-11f1-9120-10ffe0e39b19'
    files={};source_roots=[]
    def regular(q):
        s=q.lstat();assert q.is_file() and not q.is_symlink() and not getattr(s,'st_file_attributes',0)&0x400,q
        return s
    def add(q,target):
        q=Path(q);s=regular(q);assert target not in files and not target.startswith('/') and '\\' not in target and '..' not in target.split('/')
        files[target]={'source':str(q),'bytes':s.st_size,'sha256':digest(q)}
    def tree(source,target,ignore=()):
        source=Path(source);assert source.is_dir() and not source.is_symlink()
        source_roots.append(str(source))
        for current,dirs,names in os.walk(source):
            dirs[:]=[n for n in dirs if n not in ignore and n!='__pycache__']
            for n in dirs:
                q=Path(current)/n;assert not q.is_symlink() and not getattr(q.lstat(),'st_file_attributes',0)&0x400
            for name in names:
                q=Path(current)/name;add(q,target+'/'+q.relative_to(source).as_posix())
    out.mkdir();print('FREEZE_OWNED_RELEASE_COMPONENTS',flush=True)
    tree(meta['javaHome'],'runtime/jdk17',('logs','tmp'))
    tree(meta['platformJavaHome'],'runtime/jdk8',('logs','tmp'))
    tree(app/'work/demo_20261024/local_scene/runtime/python','runtime/python')
    tree(w/'mysql-8.0.46-original-restore-runtime_20261024','runtime/mysql',('data','logs','tmp'))
    tree(w/'own-redis-runtime_20261024','runtime/redis',('logs','tmp','data'))
    tree(w/'local-gateway-runtime_20261024/nginx-1.31.8','runtime/nginx',('logs','temp','data'))
    provider=json.loads((w/'own-minio-source-build-r1/receipt.json').read_bytes());add(provider['binary'],'runtime/minio/minio.exe')
    assert files['runtime/minio/minio.exe']['sha256']==provider['binarySHA256']
    tree(w/'own-controlled-portable-selection-preflight-r1/payload','payload/business')
    assert digest(meta['sourceArchive'])==meta['sourceJarSHA256']=='294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8'
    add(meta['sourceArchive'],'payload/platform/original-platform.jar')
    add(meta['guardJar'],'payload/platform/process-boundary.jar')
    add(meta['bootstrapParentJar'],'payload/platform/boot-loader.jar')
    rows=json.loads((w/'own-mysql-r13/fixture_compile.json').read_bytes())
    add(rows['boundaryJar'],'payload/business/process-boundary.jar')
    add(w/'original-scheduling-isolation-fixture-r2_20261024/original-scheduled-isolation.jar','payload/business/scheduling-isolation.jar')
    tree(w/'own-dbboot-r5/classes','payload/business/legacy-classes')
    tree(b/'classes','payload/business/run-template/classes')
    for directory in ['wrapper-classes','persistent-launcher-classes']:
        tree(p/directory,'payload/platform/run-template/'+directory)
    for name in ['own-logback.xml','own-process-only.policy']:
        add(p/name,'payload/platform/run-template/'+name)
    add(b/'own-process-only.policy','payload/business/run-template/own-process-only.policy')
    lifecycle=[q for q in args.lifecycle_classes.rglob('*.class') if q.name.startswith('ServerLifecycleObservation')]
    assert lifecycle
    for q in lifecycle:add(q,'payload/business/run-template/classes/'+q.relative_to(args.lifecycle_classes).as_posix())
    jar=out/'server-platform-observation.jar'
    with zipfile.ZipFile(p/'own-platform-observation.jar') as original,zipfile.ZipFile(jar,'w',zipfile.ZIP_DEFLATED) as patched:
        for item in original.infolist():
            assert not item.filename.startswith('xnby/replica/ServerLifecycleObservation')
            patched.writestr(item,original.read(item))
        for q in lifecycle:patched.write(q,q.relative_to(args.lifecycle_classes).as_posix())
    add(jar,'payload/platform/run-template/own-platform-observation.jar')
    tree(w/'own-portable-admin-frontend-r1/payload','payload/admin')
    print('FREEZE_ORIGINAL_FRONTENDS_AND_CLOSED_RECONSTRUCTED_SEED',flush=True)
    for role,source in bindings.items():
        before=len(files);tree(source,'frontend/'+role)
        count=len(files)-before;expected=inventory['roles'][role]
        assert count==expected['fileCount'],role
        assert sum(row['bytes'] for key,row in files.items() if key.startswith('frontend/'+role+'/'))==expected['bytes']
    tree(seed/'data','seed/mysql')
    seed_bytes=sum(row['bytes'] for key,row in files.items() if key.startswith('seed/mysql/'))
    assert seed_bytes==723048578,'RECONSTRUCTED_SEED_SIZE_CHANGED'
    add(app/'deploy/branding/zhumadian-emergency.svg','deploy/branding/zhumadian-emergency.svg')
    # Keep all secret-bearing prepared values in this private plan, never stdout or Git.
    pa=json.loads(args.platform_arguments.read_bytes())[1:]
    ba=[json.loads(line) for line in (b/'java-arguments.private.txt').read_text('utf-8').splitlines() if line]
    mapping={str(p):'${PLATFORM_RUN}',str(b):'${BUSINESS_RUN}',str(app/'UserData/TianjinOriginalPlatform'):'${PLATFORM_DATA}',str(app):'${APP}',str(meta['sourceArchive']):'${APP}/payload/platform/original-platform.jar',str(meta['guardJar']):'${APP}/payload/platform/process-boundary.jar',str(meta['bootstrapParentJar']):'${APP}/payload/platform/boot-loader.jar',str(w/'own-dbboot-r5/classes'):'${APP}/payload/business/legacy-classes',str(rows['boundaryJar']):'${APP}/payload/business/process-boundary.jar',str(w/'original-scheduling-isolation-fixture-r2_20261024/original-scheduled-isolation.jar'):'${APP}/payload/business/scheduling-isolation.jar',str(w/'own-controlled-portable-selection-preflight-r1/payload'):'${APP}/payload/business'}
    variants={}
    for old,new in mapping.items():
        for value in {old,old.replace('\\','/'),urllib.parse.quote(old.replace('\\','/'),safe=''),urllib.parse.quote(old,safe='')}:
            variants[value]=new
    def replace(value):
        for old,new in sorted(variants.items(),key=lambda row:len(row[0]),reverse=True):value=value.replace(old,new)
        return value
    configs={side:{key:replace(value) for key,value in values.items()} for side,values in props.items()}
    for side in configs:
        configs[side]['context.initializer.classes']=('xnby.platform.PlatformStartupObservation,xnby.platform.PlatformWritableObservation,xnby.platform.OriginalIdGeneratorShutdown,xnby.platform.OriginalBootstrapOrphanGuard,' if side=='platform' else '')+'xnby.replica.ServerLifecycleObservation'
        configs[side]['server.port']='0'
    private={'schema':'zhumadian.original.server.private-inputs.v1','platformArguments':[replace(s) for s in pa],'businessArguments':[replace(s) for s in ba],'configuration':configs,'seedRootPassword':own_connections['password'],'seedServerUUID':own_connections['serverUUID'],'sourceDatabaseConnected':False,'currentCandidateRestarted':False,'originalProcessesAtFreeze':active,'files':files}
    # Retarget at runtime using explicit connection fields, not arbitrary business data replacement.
    private['runtimeOverrideRequired']=True;private['launchable']=False
    (out/'release-inputs.private.json').write_text(json.dumps(private,ensure_ascii=False,indent=2),encoding='utf-8')
    public={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'schema':'zhumadian.original.server.inputs-summary.v1','files':len(files),'payloadBytes':sum(row['bytes'] for row in files.values()),'databaseSeedBytes':seed_bytes,'privatePlanSHA256':digest(out/'release-inputs.private.json'),'archiveCreated':False,'originalProcessesStarted':False,'sourceDatabaseConnected':False,'fullGISIncluded':False,'privatePlanMustNotBeCommitted':True,'runtimeOverrideRequired':True,'launchable':False,'publicDeployed':False}
    (out/'summary.json').write_text(json.dumps(public,indent=2),encoding='utf-8');print(json.dumps(public),flush=True)

if __name__=='__main__':main()
