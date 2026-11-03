from pathlib import Path
import hashlib,json
import commit_r18_local_review as helper
R=Path('D:/Project/Zhumadian');D=R/'Document/Deployment/native_plan_six_relations_r372_20261103'
J=lambda p:json.loads(p.read_bytes())
scope=J(D/'local-stage-files-r383.json')
assert not(D/'local-review-git-r384.json').exists()
assert len(scope['application'])==33 and len(scope['engine'])==4
assert hashlib.sha256((R/'Application/native/main.cpp').read_bytes()).hexdigest()==scope['heldNativeSHA256']
result={}
for role,folder,branch,parent in [
 ('application','Application','review/workplace-r19-live-local-20261031','41abeb392c33a3ac889d74c376233e8a183e48e5'),
 ('engine','XNBYEngine','review/workplace-r19-live-progress-local-20261031','29c0ed126d8f3d02e65bd41f1c94adf6d1abb40a')]:
 assert helper.run(R/folder,['rev-parse','refs/heads/'+branch]).decode().strip()==parent
 result[role]=helper.commit(R/folder,parent,branch,scope[role],role+'-r384',
   'fix(emergency): preserve resource selection on cancelled deletion; record verified build and remaining six-relation acceptance',update_existing=True)
assert hashlib.sha256((R/'Application/native/main.cpp').read_bytes()).hexdigest()==scope['heldNativeSHA256']
result.update(publicPushed=False,native29Pending=True)
(D/'local-review-git-r384.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
