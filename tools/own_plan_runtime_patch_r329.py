from pathlib import Path
import argparse,hashlib,json,os,subprocess,zipfile

R=Path('D:/Project/Zhumadian');A=R/'_g/Application'
C=R/'work/event_delivery_consistency_20261030/full-controller-r163'
REL='payload/business/run-template/classes/com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class'
CLASS='com/iemp/endanger/server/emergency/service/impl/EmergencyPlanServiceImpl.class'
PIN='384462cf7671955a1c9aa1fe37b4f2a1ac85d747ec396247af219211f79e682b'
ORIGINAL='3015417dfedfd3a2d0c139f79d7f1f4f5391f3919c9ce9b853a7aee8a8d744ce'
candidate=R/'work/emergency_plan_report_20261030/compile-v4/candidate-classes'/CLASS
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','restore']);p.add_argument('--attempt',choices=['r143'],required=True)
o=p.parse_args();P=C/('prepared-'+o.attempt)
assert J(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
query='(Get-CimInstance Win32_Process -Filter "Name=\'python.exe\' OR Name=\'java.exe\' OR Name=\'mysqld.exe\' OR Name=\'minio.exe\' OR Name=\'chrome.exe\' OR Name=\'nginx.exe\' OR Name=\'redis-server.exe\'" | Where-Object {($_.CommandLine -replace \'\\\\\',\'/\').ToLowerInvariant().Contains(\'d:/project/zhumadian/_g/application\')} | Measure-Object).Count'
probe=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
assert probe.returncode==0 and probe.stdout.decode('utf-8-sig').strip()=='0','OWN_PLAN_FIXTURE_MUST_BE_STOPPED'
for rel in [REL,'payload-manifest.json','release-manifest.json']:
    target=A/rel;assert target.resolve()==target and target.is_relative_to(A)
    for ancestor in [target,*target.parents]:
        if ancestor.exists():assert not(ancestor.lstat().st_file_attributes&1024)
        if ancestor==A:break

if o.action=='prepare':
    assert P.is_dir()and not(C/o.attempt).exists()and not(P/'plan-runtime-scope.json').exists()
    assert not(A/REL).exists()and sha(candidate)==PIN
    with zipfile.ZipFile(A/'payload/business/application.jar')as archive:
        assert hashlib.sha256(archive.read(CLASS)).hexdigest()==ORIGINAL
    ready=J(P/'controller-fixture-ready.json');assert sha(A/'release-manifest.json')==ready['releaseSHA256']
    before={n:(A/n).read_bytes()for n in ['payload-manifest.json','release-manifest.json']}
    payload=J(A/'payload-manifest.json');release=J(A/'release-manifest.json')
    assert REL not in payload['files']and 'nativePlanAtomicCompatibility'not in release
    entry={'bytes':candidate.stat().st_size,'sha256':PIN}
    payload['files'][REL]=entry;payload_raw=enc(payload)
    release['payloadManifestSHA256']=hashlib.sha256(payload_raw).hexdigest()
    release['nativePlanAtomicCompatibility']={'schema':'xnby.native-plan-atomic.v1','javaMajor':61,
       'originalJarPlanClassSHA256':ORIGINAL,'candidateSourceSHA256':'5ad79c9bbbfcf2cce8488e28cad2fecf153b993e242c1e24a8c34a4b525d9fc6',
       'files':{REL:entry},'schemaOrOriginalJarOrAuthenticationChanged':False}
    after={REL:candidate.read_bytes(),'payload-manifest.json':payload_raw,'release-manifest.json':enc(release)}
    for name,raw in before.items():
        dst=P/'plan-runtime-before'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(raw)
    scope={'onlyOwnedStoppedSyntheticFixture':True,'oldFiles':{**{n:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}for n,v in before.items()},REL:None},
           'newFiles':{n:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest()}for n,v in after.items()},
           'originalJarSHA256':sha(A/'payload/business/application.jar'),'onlyClassAndTwoManifestsChanged':True,
           'databaseConfigAndAuthenticationChanged':False,'mustRestoreAfterActualDescendantsZero':True}
    (P/'plan-runtime-scope.json').write_bytes(enc(scope))
    for name,raw in after.items():
        dst=A/name;dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.exists():dst.unlink()
        dst.write_bytes(raw)
    ready['releaseSHA256']=sha(A/'release-manifest.json');ready['ownPlanRuntimeOverridePrepared']=True
    (P/'controller-fixture-ready.json').write_bytes(enc(ready))
    print(json.dumps({'prepared':True,'onlyOwnedSyntheticG':True,'candidatePlanClassBytes':entry['bytes'],'originalJarAndDataKept':True}))
else:
    terminal=J(C/o.attempt/'controller-terminal.json');outer=J(C/(o.attempt+'-outer-terminal.json'))
    receipt=J(C/o.attempt/'scoped-controller-receipt.json')
    assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose']and outer['actualDescendantsZeroBeforeClose']
    assert receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
    scope=J(P/'plan-runtime-scope.json')
    for name,pin in scope['newFiles'].items():assert sha(A/name)==pin['sha256'],'FOREIGN_PLAN_RUNTIME_DRIFT'
    for name,pin in scope['oldFiles'].items():
        if pin:assert sha(P/'plan-runtime-before'/name)==pin['sha256']
    assert sha(A/'payload/business/application.jar')==scope['originalJarSHA256']
    for name,pin in scope['oldFiles'].items():
        dst=A/name
        if pin is None:dst.unlink()
        else:
            temporary=dst.with_name(dst.name+'.own-plan-r329-restore.tmp');assert not temporary.exists()
            temporary.write_bytes((P/'plan-runtime-before'/name).read_bytes());os.replace(temporary,dst)
    assert all((sha(A/n)==pin['sha256']if pin else not(A/n).exists())for n,pin in scope['oldFiles'].items())
    proof={'passed':True,'exactPlanClassAbsenceAndManifestPreimagesRestored':True,'allActualDescendantsZero':True,
           'databaseSchemaConfigurationOriginalJarAndAuthUnchanged':True,'forceTerminationUsed':False}
    (P/'plan-runtime-restored.json').write_bytes(enc(proof));print(json.dumps(proof))
