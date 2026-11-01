from pathlib import Path
import hashlib,json,shutil
R=Path('D:/Project/Zhumadian');S=R/'work/user_feedback_20261031/r23-unified-candidate-r1'
ROOT=R/'work/event_delivery_consistency_20261030/full-controller-r117';app=R/'_b/Application'
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert read(ROOT/'r3/result.json')['allPassed']
assert read(ROOT/'r3/controller-terminal.json')['actualDescendantJobCountZeroBeforeClose']
assert read(R/'Document/Deployment/public_test_unified_r23_20261101/independent-package-and-runtime-verification.json')['all597TransportProgramFilesMatchActuallyExecutedApplication']
release=read(app/'release-manifest.json');payload=read(app/'payload-manifest.json')
assert sha(app/'payload-manifest.json')==release['payloadManifestSHA256']
for name,pin in release['controllerFiles'].items():assert sha(app/name)==pin
for name,pin in payload['files'].items():
    if name.startswith('seed/mysql/'):continue
    assert sha(app/name)==pin['sha256']and(app/name).stat().st_size==pin['bytes']
evidence=ROOT/'closed-controller-evidence';assert not evidence.exists();evidence.mkdir()
business=app/'UserData/OriginalServer/runs/j3/b';platform=app/'UserData/TianjinOriginalPlatform/runs/j3'
reports=[('business',n)for n in ['missing-auth-guard-ready.properties','native-session-guard-ready.properties',
 'own-finding-observer-ready.json','training-transaction-observation.json','work-safety-batch-observation.json',
 'emergency-team-transaction-observation.json','event-disposal-transaction-observation.json','emergency-exercise-transaction-observation.json']]
reports += [('platform','password-identity-claims-ready.properties'),('platform','async-request-snapshot-state.properties')]
pins={}
for side,name in reports:
    source=(business if side=='business'else platform)/name;assert source.is_file()and source.stat().st_size<=65536
    dest=evidence/side/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);pins[side+'/'+name]=sha(dest)
for source in(app/'UserData/OriginalServer/runs').glob('j*/receipt.json'):
    dest=evidence/source.parent.name/'receipt.json';dest.parent.mkdir();shutil.copyfile(source,dest)
config=read(app/'private/server-configuration.json')
(evidence/'configuration-key-inventory.json').write_text(json.dumps({'syntheticOnly':True,
 'businessContext':'/','platformKeys':sorted(config['configuration']['platform']),
 'businessKeys':sorted(config['configuration']['business']),'valuesSaved':False},indent=2),encoding='utf-8')
data=app/'UserData/OriginalServer/database/data';preserve=ROOT/'retained-synthetic-data';assert not preserve.exists()
preserved_bytes=sum(p.stat().st_size for p in data.rglob('*')if p.is_file())
changes=read(S/'sparse-graceful-update-preparation-r1/changes.json');tx=read(S/'sparse-graceful-update-preparation-r1/result.json')
targets=[]
def collect(root,mode):
    entries={}
    for file in [root,*root.rglob('*')]:
        assert not file.is_symlink()and not getattr(file.lstat(),'st_file_attributes',0)&0x400
        if not file.is_file():continue
        if mode=='runtime'and file.is_relative_to(data):continue
        name=file.relative_to(root).as_posix();pin=sha(file)
        if mode in ['app','foreign']:
            assert name in changes and(pin in [v for v in changes[name].values()if v is not None]or mode=='foreign'and pin==hashlib.sha256(b'own deliberately unrelated edit\n').hexdigest())
        elif mode=='backup':
            if name=='changes.json':assert read(file)==changes
            else:assert name.startswith('before/')and pin==changes[name.removeprefix('before/')]['before']
        elif mode=='factory':assert pin==changes[name]['before']
        entries[name]={'sha256':pin,'bytes':file.stat().st_size,'hardlinks':file.stat().st_nlink}
    targets.append({'path':str(root),'mode':mode,'files':entries})
for case in Path(tx['transactionEvidenceRoot']).iterdir():
    assert(case/'result.json').is_file();collect(case/'Application','foreign'if case.name=='foreign-file-drift'else'app');collect(case/'backup','backup')
collect(S/'sparse-graceful-update-preparation-r1/contract-Application','factory')
collect(R/'_b','runtime')
plan={'root':str(R),'targets':targets,'preserveDataSource':str(data),'preserveDataTarget':str(preserve),
      'preservedSyntheticDataBytes':preserved_bytes,'closedReportPins':pins,'hardlinkLogicalBytesNotFreed':True}
(S/'r117-fixture-cleanup-plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
print(json.dumps({'targets':len(targets),'files':sum(len(t['files'])for t in targets),'preservedSyntheticDataBytes':preserved_bytes,
                  'readinessReportsArchived':len(pins)}))
