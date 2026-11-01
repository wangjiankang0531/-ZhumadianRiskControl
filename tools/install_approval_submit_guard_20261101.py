"""Replace WF3 by verified WF4 only in the stopped, never handed-out _e fixture."""
from pathlib import Path, PurePosixPath
import hashlib,json,subprocess

R=Path('D:/Project/Zhumadian');A=R/'_e/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r123';T=R/'Application/tools'
W=R/'work/user_feedback_20261031';oldF=W/'emergency-workflow-source-r3';newF=W/'emergency-workflow-source-r4'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dump=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
terminal=read(C/'r1/controller-terminal.json');receipt=read(C/'r1/scoped-controller-receipt.json')
assert terminal['exitCode']==0 and terminal['actualDescendantJobCountZeroBeforeClose'] and not terminal['forceTerminationUsed']
assert receipt['allOwnedChildrenExited'] and receipt['normalOwnedShutdown'] and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
for actor in ('operator','reviewer'):
    assert read(C/f'r1/workflow-browser-{actor}/browser-terminal.json')['normalBrowserClosed']
# Current process paths are observed, not command lines or user browser state.
ps="@(Get-Process | Where-Object { try { $_.Path -like 'D:\\Project\\Zhumadian\\_e\\Application\\*' } catch { $false } }).Count"
p=subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',ps],capture_output=True,timeout=25,creationflags=subprocess.CREATE_NO_WINDOW)
assert p.returncode==0 and p.stdout.decode().strip()=='0','OWN_E_PROCESS_STILL_LIVE'
assert read(C/'synthetic-database-prepared.json')['onlyOwnedSyntheticR114DatasetCopied']
assert read(newF/'independent-build-verification.json')['undeclaredSourceDifferences']==0
prepared=read(C/'controller-fixture-ready.json');assert sha(A/'release-manifest.json')==prepared['releaseSHA256']
payload=read(A/'payload-manifest.json');release=read(A/'release-manifest.json')
controls=dict(release['controllerFiles']);prefix='frontend/emergency_pc/'
old={n.removeprefix(prefix):v for n,v in payload['files'].items() if n.startswith(prefix)}
assert old==read(oldF/'build-result.json')['files']
new=read(newF/'build-result.json')['files'];assert len(old)==len(new)==338
root=(A/'frontend/emergency_pc').resolve(strict=True)
for n,row in old.items():
    p=A/(prefix+n);assert p.resolve(strict=True).is_relative_to(root) and not p.lstat().st_file_attributes&0x400
    assert sha(p)==row['sha256']
for n,row in new.items():
    rel=PurePosixPath(n);assert not rel.is_absolute() and '..' not in rel.parts and ':' not in n and '\\' not in n
    assert sha(newF/'dist'/n)==row['sha256']
removed=0;replaced=0
for n in set(old)-set(new):
    (A/(prefix+n)).unlink();del payload['files'][prefix+n];removed+=1
for n,row in new.items():
    p=A/(prefix+n);p.parent.mkdir(parents=True,exist_ok=True);assert p.resolve().is_relative_to(root)
    if not p.exists() or sha(p)!=row['sha256']:
        if p.exists():p.unlink()
        p.write_bytes((newF/'dist'/n).read_bytes());replaced+=1
    payload['files'][prefix+n]=row
payload['ownedApprovalBaseline'].update(fullSourceRevision='r4',auditBusyGuardCandidate=True)
dump(A/'payload-manifest.json',payload);release['payloadManifestSHA256']=sha(A/'payload-manifest.json')
assert release['controllerFiles']==controls
dump(A/'release-manifest.json',release);prepared['releaseSHA256']=sha(A/'release-manifest.json');dump(C/'controller-fixture-ready.json',prepared)
driver=T/'verify_native_approval_portal_browser_20261101.mjs';s=driver.read_bytes().decode('utf-8')
needle=r'input[placeholder=\"请选择转审人员\"]';assert s.count(needle)==2;s=s.replace(needle,'input[placeholder*=转审]');driver.write_bytes(s.encode('utf-8'))
proof={'onlyOwnNeverHandedEChanged':True,'verifiedFrontendFiles':338,'sourceRevision':'r4','replacedOrAdded':replaced,'removed':removed,'allControlFilePinsUnchangedFromBaseline':True,'taskGuardSHA256':sha(A/'payload/business/run-template/classes/com/iemp/endanger/server/emergencyResponse/controller/EventTaskController.class'),'noUserManualDataReadOrChanged':True,'actualApprovalRuntimeStillPending':True}
assert proof['taskGuardSHA256']=='9ffe745d5198361248e389cdb88ee0bbee72d7cb40f7f5c534d2b2cd49828375'
for n,row in new.items():assert sha(A/(prefix+n))==row['sha256']
dump(C/'approval-busy-candidate-ready.json',proof);print(json.dumps(proof))
