from pathlib import Path
import hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r163';P=C/'prepared-r74'
read=lambda p:json.loads(p.read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
assert not P.exists()and not(C/'r74').exists()
assert read(A.parent/'own-fixture.json')['ownedSyntheticFixtureOnly']and not(A.parent/'user-manual-protected.json').exists()
for trial in ['r72','r73']:
    assert read(C/trial/'controller-terminal.json')['exitCode']==0
    assert read(C/(trial+'-outer-terminal.json'))['actualDescendantsZeroBeforeClose']
    assert read(C/('prepared-'+trial)/'configuration-restored.json')['exactOriginalBytesRestored']
assert read(C/'r72/state-reviewer-final.json')['pendingEngineTasks']==0 and read(C/'r72/state-reviewer-final.json')['originalEngineHistoryHasEndTime']
assert read(C/'r72/workflow-browser-operator-completed-readback/failure.json')['message']=='ORIGINAL_TRANSFER_RECORD_ACTOR_TIME_AND_OPINION_REQUIRED'
query="(Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='java.exe' OR Name='mysqld.exe' OR Name='chrome.exe' OR Name='minio.exe' OR Name='redis-server.exe' OR Name='nginx.exe'\" | Where-Object {($_.CommandLine -replace '\\\\','/').ToLowerInvariant().Contains('d:/project/zhumadian/_g/application')} | Measure-Object).Count"
q=subprocess.run(['powershell.exe','-NoProfile','-Command',query],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
assert q.returncode==0 and q.stdout.decode('utf-8-sig').strip()=='0'
scope=read(C/'prepared-r72/temporary-synthetic-config-scope.json');before={k:(A/k).read_bytes()for k in scope['files']}
assert all(sha(raw)==scope['files'][k]['beforeSHA256']for k,raw in before.items())
definition=read(C/'prepared-r72/own-serial-definition.json');cfg=json.loads(before['private/server-configuration.json']);business=cfg['configuration']['business']
assert business['flow.code']==business['flow.event-task-handle']=='OWN_FORM_CODE'
business['flow.code']=business['flow.event-task-handle']=definition['formBody']['enCode'];changed={'private/server-configuration.json':enc(cfg)}
payload=json.loads(before['payload-manifest.json']);payload['files']['private/server-configuration.json']={'bytes':len(changed['private/server-configuration.json']),'sha256':sha(changed['private/server-configuration.json'])};changed['payload-manifest.json']=enc(payload)
release=json.loads(before['release-manifest.json']);release['payloadManifestSHA256']=sha(changed['payload-manifest.json']);changed['release-manifest.json']=enc(release)
assert all(sha(raw)==scope['files'][k]['afterSHA256']for k,raw in changed.items())
P.mkdir()
for k,raw in before.items():p=P/'before'/k;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
for name in ['own-serial-definition.json','controller-fixture-ready.json','temporary-synthetic-config-scope.json']:(P/name).write_bytes((C/'prepared-r72'/name).read_bytes())
(P/'workflow-context.private.json').write_bytes((C/'r72/workflow-context.private.json').read_bytes())
for k,raw in changed.items():
    p=A/k;assert p.resolve()==p and not p.lstat().st_file_attributes&0x400;p.unlink();p.write_bytes(raw)
(P/'same-instance-readback.json').write_bytes(enc({'samePreviouslyCompletedR72Instance':True,'noWorkflowCreateOrAuditToBeReplayed':True,'independentOpinionGapNotHidden':True,'priorFailureRetained':True}))
print(json.dumps({'prepared':True,'sameCompletedBeforeAddsignInstance':True,'onlyReadbackExpected':True,'noProductOrPublicChange':True}))
