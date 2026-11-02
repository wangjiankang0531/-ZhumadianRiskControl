from pathlib import Path
import json,hashlib,datetime,base64
V=Path(__file__).parent;D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_pending_visibility_r34_20261102');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();fixed='d6b68f0f16a292b9ec4470581a456522660c451cc5ad9130bb4d04849be4c9af';assert sha(D/'delivery-manifest.json')==fixed
m=json.loads((D/'delivery-manifest.json').read_bytes());delivery=D/'delivery';assert set(p.name for p in delivery.iterdir())==set(m['files'])|{'delivery-manifest.json'}and sum(p.stat().st_size for p in delivery.iterdir())==1964748
for n,pin in m['files'].items():assert (delivery/n).stat().st_size==pin['bytes']and sha(delivery/n)==pin['sha256']
assert sha(delivery/'delivery-manifest.json')==fixed
approval={'at':datetime.datetime.now().astimezone().isoformat(),'questionId':'call_6ee29c944d81431da685bf5539ea79a3','answer':'现在可以交接，执行上述固定R34范围','r34':{'approvedForExecution':True,'desktopHandoffActive':True,'manifestSHA256':fixed,'transportFiles':8,'transportBytes':1964748,'publicGitIncluded':False}}
(D/'user-approval-r184-20261102.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping=[('public_test_project_header_r33_20261102','public_test_pending_visibility_r34_20261102'),('user-approval-r168-20261102.json','user-approval-r184-20261102.json'),('ac0c9b0fbd6f882399ba0c0ad82c96d9d78b1b79963b9def8ee25d3fa40044f5',fixed),('Zhumadian_Project_Header_Home_20261102_R33','Zhumadian_Pending_Visibility_20261102_R34'),('deploy_project_header_r33.py','deploy_pending_visibility_r34.py'),('330a513ce9c94759f74b9db54c09f3a30a7e7399142642443bd2937cef0d1e13',m['newReleaseSHA256']),('R33','R34'),('r33','r34')]
def transform(s):
 for old,new in mapping:s=s.replace(old,new)
 return s
for name in ['navigate_ftp_r33.ps1','create_ftp_r33_directory.ps1','confirm_r33_upload.ps1','r33_capture_target.ps1','collect_r33_summary.ps1']:
 p=V/name.replace('r33','r34');assert not p.exists();p.write_text(transform((V/name).read_text(encoding='utf-8-sig')),encoding='utf-8-sig')
pins={}
for mode in ['check','apply']:
 s=transform((V/('r33-'+mode+'-command-source.ps1')).read_text(encoding='utf-8-sig'));p=V/('r34-'+mode+'-command-source.ps1');p.write_text(s,encoding='utf-8-sig')
 command='powershell.exe -NoProfile -NonInteractive -EncodedCommand '+base64.b64encode(s.encode('utf-16-le')).decode();(V/('r34-'+mode+'-command.txt')).write_text(command,encoding='ascii');pins[mode]=hashlib.sha256(command.encode()).hexdigest()
s=transform((V/'submit_r33_remote.ps1').read_text(encoding='utf-8-sig')).replace('7d729a2afed3e1edf8f697dd8b952656449c9ee4c0a0a28b22a6fc3a1e4192708a',pins['check'])
# Use the actual previous reviewed command constants, each exactly once.
for old,key in [('7d729a2afed3e1edf8f697dd8b952656449c9ee4c0a28b22a6fc3a1e4192708a','check'),('030da2c433ab191cc1abf771bf762e85102887e6aa7fc7c297ef78e04a5ed1d5','apply')]:assert s.count(old)==1;s=s.replace(old,pins[key])
(V/'submit_r34_remote.ps1').write_text(s,encoding='utf-8-sig');(D/'remote-command-pins.json').write_text(json.dumps({'manifestSHA256':fixed,'commands':pins,'normalRemoteWindowOnly':True,'rawAccountsSessionsBusinessRowsCredentialsOrLogsCollected':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'fixedEightFilesVerified':True,'approvalRecorded':True,'desktopControlsPrepared':True,'files':8,'bytes':1964748,'manifestSHA256':fixed}))
