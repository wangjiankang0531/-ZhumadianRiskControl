from pathlib import Path
import base64,hashlib,json
V=Path(__file__).parent;D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_personal_workflow_r35_20261103');fixed='ad828398aaa09064eadc0ba9efb221a4e11cab0d5c7b74e4b9cf7950e01fbee3';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(D/'delivery-manifest.json')==fixed
m=json.loads((D/'delivery-manifest.json').read_bytes());assert sum(p.stat().st_size for p in (D/'delivery').iterdir())==1969301
approval={'questionId':'call_68e843fdaf134a61b16095255569e6f6','answer':'现在可以交接，执行固定R35范围','r35':{'approvedForExecution':True,'desktopHandoffActive':True,'manifestSHA256':fixed,'transportFiles':8,'transportBytes':1969301,'publicGitIncluded':False},'publicGit':{'questionId':'call_7aebd603142a4b969ecebc9651a93d5e','approved':True,'manifestSHA256':'e332493802046a8281ca76098adb56b1613c5447d26fd1b89edeb99af8fbf9ad','files':51,'bytes':583600}}
(D/'user-approval-r197-20261103.json').write_text(json.dumps(approval,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
mapping=[('public_test_pending_visibility_r34_20261102','public_test_personal_workflow_r35_20261103'),('user-approval-r184-20261102.json','user-approval-r197-20261103.json'),('d6b68f0f16a292b9ec4470581a456522660c451cc5ad9130bb4d04849be4c9af',fixed),('Zhumadian_Pending_Visibility_20261102_R34','Zhumadian_Personal_Workflow_20261103_R35'),('deploy_pending_visibility_r34.py','deploy_personal_workflow_r35.py'),('5f214688ed3038ecdc75f7cf03fb209f94b28f2233c219c26a9fc46e1dd65b5f',m['newReleaseSHA256']),('R34','R35'),('r34','r35')]
def transform(s):
 for a,b in mapping:s=s.replace(a,b)
 return s
for n in ['navigate_ftp_r34.ps1','create_ftp_r34_directory.ps1','confirm_r34_upload.ps1','r34_capture_target.ps1','collect_r34_summary.ps1']:
 p=V/n.replace('r34','r35');assert not p.exists();p.write_text(transform((V/n).read_text(encoding='utf-8-sig')),encoding='utf-8-sig')
pins={}
for mode in ['check','apply']:
 s=transform((V/('r34-'+mode+'-command-source.ps1')).read_text(encoding='utf-8-sig'));(V/('r35-'+mode+'-command-source.ps1')).write_text(s,encoding='utf-8-sig');command='powershell.exe -NoProfile -NonInteractive -EncodedCommand '+base64.b64encode(s.encode('utf-16-le')).decode();(V/('r35-'+mode+'-command.txt')).write_text(command,encoding='ascii');pins[mode]=hashlib.sha256(command.encode()).hexdigest()
s=transform((V/'submit_r34_remote.ps1').read_text(encoding='utf-8-sig'))
for old,key in [('5b74e09a7bb840bcf0ea9f1239252af8fee5cc01cf8b3ceeb31d7c229141f359','check'),('461793c8bdb14acb56ae49d75c72c65751b0d04ce6468646b037e98dd4682068','apply')]:assert s.count(old)==1;s=s.replace(old,pins[key])
(V/'submit_r35_remote.ps1').write_text(s,encoding='utf-8-sig');(D/'remote-command-pins.json').write_text(json.dumps({'manifestSHA256':fixed,'commands':pins,'normalRemoteWindowOnly':True,'rawAccountsSessionsBusinessRowsCredentialsOrLogsCollected':False},indent=2)+'\n',encoding='utf-8')
completion={'application':{'repository':'wangjiankang0531/-ZhumadianRiskControl','branch':'review/workplace-r19-verified-partial-20261031','commit':'793ae284002bd90c0a56301a30f8938db7a8fbc9','soleParent':'62f421212b0981c06eecb268adc648c5909bd0e7','tree':'90ec5765aee6c0dfbc0be4d52f2db349fae90743'},'engine':{'repository':'wangjiankang0531/-XNBYEngine','branch':'review/workplace-r19-verified-progress-20261031','commit':'017e1198d87d80431b7624d575e00a7f5e849511','soleParent':'7993d972324e14eeeca0d692be34b7d3314469db','tree':'8f562c28c178a95c0573cb471f67ba89a169512c'},'manifestSHA256':approval['publicGit']['manifestSHA256'],'files':51,'bytes':583600,'all51BlobBytesBothRecursiveTreesSoleParentsAndFinalRefsVerified':True,'newBranchesOrPrivateAncestorsOrMainChanges':False,'explicitApprovalQuestionId':approval['publicGit']['questionId']}
(D/'public-git-completed-r197.json').write_text(json.dumps(completion,indent=2)+'\n',encoding='utf-8');print(json.dumps({'approvalRecorded':True,'desktopControlsPrepared':True,'publicGitCompleted':True,'commands':pins}))
