"""Persist already verified receiver acknowledgements, no server/Git action."""
from pathlib import Path
import datetime,hashlib,json
V=Path(__file__).resolve().parent
R=Path('D:/Project/Zhumadian')
J=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
audit=V/'d75-d76-receiver-review-r1016.json'
assert J(audit)['passed']
messages=[R/'Document/Coordination/交接消息'/n for n in [
 '驻马店三维同层对象协同合并_给驻马店3_20261105_d75.json',
 '驻马店三维冲突逐项比较选择接口_给驻马店3_20261105_d76.json']]
for message,receipt in zip(messages,J(audit)['receipts']):
 assert sha(message)==receipt['messageSHA256']
 h=J(message)
 for key in ['sourceArchive','runtimeArchive']:assert sha(h[key])==h[key+'SHA256']
targets=J(V/'d75-d76-ack-drafts-r1017/manifest.json')['drafts']
assert all(not Path(row['intendedSharedTarget']).exists() for row in targets)
results=[]
for row in targets:
 draft=Path(row['draft']);assert sha(draft)==row['sha256'];value=J(draft)
 target=Path(row['intendedSharedTarget'])
 assert target.parent==R/'Document/Coordination/交接消息'
 assert all(not x.is_symlink() and not (x.exists() and x.lstat().st_file_attributes&0x400) for x in [target,*target.parents])
 value['at']=datetime.datetime.now().astimezone().isoformat()
 value['sharedReceiverAcknowledgementWritten']=True
 value.pop('draftOnlyUntilNormalProjectWriteApproval')
 value['quotaRecoveredByUserNoticeAndNormalApprovalUsed']=True
 raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8')
 with target.open('xb') as f:f.write(raw)
 assert target.read_bytes()==raw
 results.append({'path':str(target),'sha256':sha(target)})
out={'sharedAcknowledgementsWritten':results,'otherThreadRealtimeNotificationClaimed':False,
     'noServerInstallationOrGitPush':True}
(V/'d75-d76-acks-persisted-r1019.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'acknowledgements':len(results),'serverChanged':False}))
