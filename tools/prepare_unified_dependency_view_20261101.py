"""Resolve exact installed program bytes without reading private configuration or seed data."""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, re, shutil, stat, subprocess, sys

sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');Q=Path('D:/Zqa20261025/Application');W=R/'work/user_feedback_20261031'
S=W/'r23-unified-candidate-r1';T=R/'Application/tools'
parser=argparse.ArgumentParser();parser.add_argument('--revision',default='r1');args=parser.parse_args()
assert re.fullmatch(r'r[1-9][0-9]{0,3}',args.revision)
OUT=R/'work'/('r23pv-'+args.revision);assert not OUT.exists();OUT.mkdir()
read=lambda p:json.loads(p.read_bytes())
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
old=read(S/'r21-base-release-manifest.json');payload=read(S/'r21-base-payload-manifest.json')
checks=read(S/'sparse-update-preparation-r2/result.json');assert checks['compositionContractsPassed']
sources=[Q,R/'Document/Deployment/server_directory_migration_20261030_r17d/delivery/payload',
    R/'Document/Deployment/public_test_workplace_r19_20261031/bundle/payload',
    R/'Document/Deployment/public_test_workflow_r21_20261031/bundle/payload',
    W/'public-r21-template-recovery-r1',S/'public-control',R/'Application']
roots_checked=set();hash_cache={};pins={};missing=[];skipped_seed=0;private_names=[]
def plain(path):
    for item in [path,*path.parents]:
        text=str(item)
        if text in roots_checked:continue
        if not item.exists():return False
        attrs=item.lstat().st_file_attributes
        assert not item.is_symlink()and not attrs&0x400,'REDIRECTED_PROGRAM_SOURCE_REFUSED'
        roots_checked.add(text)
    return path.is_file()
def match(p,pin,size=None):
    if not p.is_file()or(size is not None and p.stat().st_size!=size):return False
    if not plain(p):return False
    key=str(p)
    if key not in hash_cache:hash_cache[key]=sha(p)
    return hash_cache[key]==pin
def relative(name):
    p=PurePosixPath(name)
    assert not p.is_absolute()and str(p)==name and '..'not in p.parts
    assert not re.search(r'[\\:\x00-\x1f]',name)
    return name
for name,row in payload['files'].items():
    relative(name)
    if name.startswith('seed/mysql/'):
        skipped_seed+=1;continue
    if name.startswith('private/'):
        private_names.append(name);continue
    candidates=[]
    if name.startswith('frontend/security_pc/'):
        candidates.append(W/'workplace-security-build-r21-workflow/build/dist'/name.removeprefix('frontend/security_pc/'))
    if name.startswith('frontend/emergency_pc/'):
        candidates.append(W/'published-emergency-frontend-r1/frontend'/name.removeprefix('frontend/emergency_pc/'))
    candidates.extend(root/name for root in sources)
    found=next((p for p in candidates if match(p,row['sha256'],row['bytes'])),None)
    if found:pins[name]={'source':str(found),**row}
    else:missing.append({'relative':name,'bytes':row['bytes'],'sha256':row['sha256']})
assert private_names==['private/server-configuration.json']
controllers={}
for name,pin in old['controllerFiles'].items():
    relative(name)
    candidates=[root/name for root in sources]
    if name=='iis/Global.asax':candidates.append(R/'Application/deploy/iis_canonical_home/Global.asax')
    found=next((p for p in candidates if match(p,pin)),None)
    if found:controllers[name]={'source':str(found),'sha256':pin,'bytes':found.stat().st_size}
    else:missing.append({'relative':name,'controller':True,'sha256':pin})
disk=shutil.disk_usage(W)
result={'schema':'xnby.r23.program-dependency-resolution.v1','revision':args.revision,
        'originalPayloadFiles':len(payload['files']),'resolvedProgramFiles':len(pins),
        'resolvedProgramBytes':sum(v['bytes']for v in pins.values()),'resolvedControllers':len(controllers),
        'skippedSeedDatabaseFiles':skipped_seed,'excludedRealPrivateConfiguration':private_names,
        'realPrivateConfigurationRead':False,'realSeedOrBusinessDataRead':False,
        'freeBytesBefore':disk.free,'plannedHardlinkViewLogicalBytes':sum(v['bytes']for v in pins.values()),
        'plannedAdditionalAllocatedBytesUpperBound':128*1024**2,
        'programs':pins,'controllers':controllers,'missing':missing,'allResolved':not missing,
        'materialized':False,'fullInstalledLoadBundlePassed':False,'publicChanged':False}
assert disk.free>1024**3
(OUT/'dependency-resolution.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items()if k not in ['programs','controllers','missing']}))
print(json.dumps({'missing':missing[:25],'missingCount':len(missing)}))
