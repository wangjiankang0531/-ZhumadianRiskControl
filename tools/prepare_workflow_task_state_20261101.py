"""Restore the provided backend's existing status-2 label in both task views."""
from pathlib import Path
import copy,hashlib,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';B=R/'work/user_feedback_20261031/emergency-workflow-source-r4';N=B.with_name('emergency-workflow-source-r5')
read=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert read(B/'independent-build-verification.json')['undeclaredSourceDifferences']==0 and not N.exists()
entity=R/'Application/work/tianjin_native_20261023/business_java/src/main/java/com/iemp/endanger/server/emergencyResponse/entity/EventTask.java'
assert '任务状态：0-待处置，1-已处置,2 处置中' in entity.read_text(encoding='utf-8')
excluded={'node_modules','dist','.git','.cache','.vite','coverage'}
for folder,dirs,files in os.walk(B/'source',followlinks=False):
    dirs[:]=[n for n in dirs if n not in excluded]
    for name in dirs+files:assert not(Path(folder)/name).lstat().st_file_attributes&0x400
N.mkdir();shutil.copytree(B/'source',N/'source',copy_function=os.link,ignore=lambda folder,names:[n for n in names if n in excluded or '.timestamp-' in n])
metadata=copy.deepcopy(read(B/'source-closure.json'));adaptations={}
for relative in ['src/views/emergencyResponse/taskSend/index.vue','src/views/emergencyResponse/taskSend/info/detail.vue']:
    origin=B/'source'/relative;raw=origin.read_bytes();text=raw.decode('utf-8');nl='\r\n' if '\r\n' in text else '\n';text=text.replace('\r\n','\n')
    old='{ label: "待处置", value: "0" }';new=old+',\n      { label: "处置中", value: "2" }'
    assert text.count(old)==1;changed=text.replace(old,new,1)
    assert changed.replace(new,old,1).replace('\n',nl).encode('utf-8')==raw
    p=N/'source'/relative;p.unlink();p.write_bytes(changed.replace('\n',nl).encode('utf-8'))
    own=T/'frontend/emergency-workflow-task-state'/relative;own.parent.mkdir(parents=True,exist_ok=True);assert not own.exists();own.write_bytes(p.read_bytes())
    assert sha(origin)==hashlib.sha256(raw).hexdigest()
    adaptations[relative]={'baseSourceSHA256':sha(origin),'adaptedSHA256':sha(p),'declaredChanges':1,'reverseByteExact':True,'existingStateValue':'2','label':'处置中','sourceEntitySHA256':sha(entity),'persistentSchemaOrStateValueChanged':False}
metadata['runtimeSourceAdaptations'].update(adaptations);metadata['taskStateDisplayAdaptations']=adaptations;metadata['sourceRevision']='r5'
(N/'source-closure.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
builder=T/'build_emergency_workflow_source_20261101.mjs';s=builder.read_bytes().decode('utf-8');assert s.count("['r1','r2','r3','r4']")==1;builder.write_bytes(s.replace("['r1','r2','r3','r4']","['r1','r2','r3','r4','r5']").encode('utf-8'))
verifier=T/'verify_emergency_workflow_source_20261101.py';s=verifier.read_bytes().decode('utf-8');assert s.count("['r1','r2','r3','r4']")==1;s=s.replace("['r1','r2','r3','r4']","['r1','r2','r3','r4','r5']")
old="'auditSubmitDeclaredChangedFiles':len(c.get('runtimeSourceAdaptations',{}))";assert s.count(old)==1;s=s.replace(old,"'auditSubmitDeclaredChangedFiles':sum(p.endswith('/auditForm.vue')for p in c.get('runtimeSourceAdaptations',{})),'taskStateDisplayDeclaredChangedFiles':len(c.get('taskStateDisplayAdaptations',{}))")
verifier.write_bytes(s.encode('utf-8'))
print('WF5_EXISTING_STATE_2_LABEL_PREPARED_TWO_FILES_NO_PERSISTENT_STATE_CHANGE')
