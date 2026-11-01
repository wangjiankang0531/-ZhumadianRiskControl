"""Inventory R23 source against the current public parents without publishing objects."""
from pathlib import Path
import ast,datetime,hashlib,json,re

R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools'
D=R/'Document/Deployment/public_test_unified_r23_20261101';OLD=R/'Document/Deployment/public_test_risk_r22_20261101'
S=R/'work/user_feedback_20261031/r23-unified-candidate-r1';G=S/'graceful-public-control'
read=lambda p:json.loads(p.read_bytes());sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
assert sha((D/'delivery-manifest.json').read_bytes())=='27c8a6514d887d94c6c2489b263c2d2e59b29fb395602cdd2621db1ce8fb6b41'
observed=read(D/'verified-public-parent-heads-r118.json')['refs']
bases=[read(OLD/'public-git-base-app.json'),read(OLD/'public-git-base-engine.json')]
assert {x['repo']:x['commit']for x in observed}=={x['repo']:x['commit']for x in bases}
assert {x['repo']:x['treeSHA']for x in observed}=={x['repo']:x['treeSHA']for x in bases}
known={x['path']:x['sha']for x in bases[0]['files']}
frozen=read(OLD/'public-git-sync-manifest.json');assert sha((OLD/'public-git-sync-manifest.json').read_bytes())=='df81999b5ff6c40aa476e89c457e633dbf29bf1f52436a05d102274e86e7f275'
frozen_app={row['path']:Path(row['snapshot'])for row in frozen['files']if row['repo']==bases[0]['repo']}
for row in frozen['files']:assert sha(Path(row['snapshot']).read_bytes())==row['sha256']
alias={'tools/'+name:G/'tools'/name for name in ['serve_original_server_release.py','original_server_windows_job.py',
 'original_public_test_update.py','original_platform_async_release_support.py','original_server_release_parameters.py','prepare_original_frontend_gateway.py']}
roots=[
 'build_published_emergency_login_query_20261101.py','build_published_emergency_disposal_busy_20261101.py',
 'prepare_published_async_snapshot_support_20261101.py','prepare_unified_r23_stage_20261101.py',
 'verify_unified_candidate_runtime_20261101.py','bootstrap_unified_candidate_runtime_20261101.py',
 'verify_platform_async_release_support_20261101.py','verify_graceful_controller_processes_20261101.py',
 'original_platform_async_release_support_20261101.py','serve_original_server_release_r23_20261101.py',
 'serve_original_server_release_r23_graceful_20261101.py','original_server_windows_job_graceful_20261101.py',
 'original_public_test_update_r23_20261101.py','original_public_test_update_r23_graceful_20261101.py',
 'verify_r23_update_contract_20261101.py','verify_r23_graceful_update_contract_20261101.py',
 'prepare_unified_r23_sparse_update_20261101.py','prepare_unified_graceful_sparse_update_20261101.py',
 'prepare_unified_dependency_view_20261101.py','verify_unified_full_dependency_preflight_20261101.py',
 'verify_unified_graceful_full_preflight_20261101.py','prepare_whole_controller_code_20261101.py',
 'prepare_whole_controller_fixture_20261101.py','verify_whole_graceful_controller_20261101.py',
 'prepare_whole_controller_fixture_cleanup_20261101.py','build_public_unified_r23_20261101.py',
 'verify_public_unified_r23_package_20261101.py','prepare_r23_public_source_closure_20261101.py',
 'prepare_r23_public_git_snapshot_20261101.py','verify_r23_public_git_snapshot_20261101.py']
active={'tools/'+n:T/n for n in roots}
# These are the actual source pins used for the last component browser/HTTP chain.
pins=read(R/'work/event_delivery_consistency_20261030/full-business-main-r114/source-pins.json')
for source,digest in pins.items():
    p=Path(source)
    if p.is_relative_to(A):
        assert sha(p.read_bytes())==digest,'COMPONENT_SOURCE_CHANGED:'+p.name
        active[p.relative_to(A).as_posix()]=p
extras=['tools/frontend/emergency-native-login-query.ts','tools/frontend/emergency-task-disposal-detail.vue',
 'tools/frontend/emergency-task-disposal-parent.vue','tools/cleanup_candidate_emergency_disposal_20261101.ps1',
 'tools/move_whole_controller_fixture_20261101.ps1','tools/cleanup_whole_controller_fixture_20261101.ps1',
 'tools/java/unified_controller_lifecycle_fixture_r1/OwnControllerSchemaSnapshot.java']
for rel in extras:active[rel]=A/rel
for folder in ['original_platform_runtime8/normal_workflow_async_r1','public_emergency_workflow_async_r1',
               'public_emergency_workflow_fixture_r1','public_disposal_workflow_fixture_r1','manual_disposal_fixture_r2']:
    for p in(T/'java'/folder).glob('*.java'):active[p.relative_to(A).as_posix()]=p
selected={};edges={};queue=list(frozen_app)+list(active)+list(alias)
def source_for(rel):return alias.get(rel)or active.get(rel)or frozen_app.get(rel)or A/rel
while queue:
    rel=queue.pop()
    if rel in selected:continue
    p=source_for(rel);assert p.is_file(),'MISSING_SOURCE:'+rel
    assert not set(Path(rel).parts).intersection({'Assets','Reference','UserData','private','.git','node_modules'})
    selected[rel]=p
    if p.suffix!='.py':continue
    dependencies=set()
    for n in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
        names=[x.name.split('.')[0]for x in n.names]if isinstance(n,ast.Import)else[n.module.split('.')[0]]if isinstance(n,ast.ImportFrom)and n.module else[]
        for name in names:
            target='tools/'+name+'.py'
            if target in alias or target in active or target in frozen_app or(T/(name+'.py')).is_file():dependencies.add(target)
    edges[rel]=sorted(dependencies);queue.extend(dependencies)
for rel in ['deploy/handbook/unified_emergency_r23_fixed_20261101.md',
 'deploy/verification/unified_emergency_r23_fixed_20261101.json',
 'deploy/releases/public_test_r23_20261101/delivery-manifest.json',
 'deploy/releases/public_test_r23_20261101/preparation-result.json']:
    selected[rel]=A/rel
patterns={'private-key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'github-token':r'\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}','openai-token':r'\bsk-[A-Za-z0-9_-]{24,}',
 'aws-access-key':r'\bAKIA[A-Z0-9]{16}\b','jwt-literal':r'[\"\']eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'}
rows=[];findings=[];identifiers=[]
for rel,p in sorted(selected.items()):
    raw=p.read_bytes();text=raw.decode('utf-8');assert text.encode('utf-8')==raw
    if known.get(rel)==blob(raw):continue
    for category,pattern in patterns.items():
        for m in re.finditer(pattern,text):findings.append({'path':rel,'category':category,'line':text[:m.start()].count('\n')+1})
    for m in re.finditer(r'(?i)\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',text):
        if not(m[0].lower().startswith(('a531','00000000','11111111','22222222'))or m[0].upper()=='96240625-934F-490B-8AA6-0BC775B18468'):
            identifiers.append({'path':rel,'line':text[:m.start()].count('\n')+1})
    rows.append({'path':rel,'source':str(p),'bytes':len(raw),'sha256':sha(raw),
                 'gitBlobSHA1':blob(raw),'oldPublicBlobSHA1':known.get(rel)})
result={'schema':'xnby.r23.public-source-closure-draft.v1','at':datetime.datetime.now().astimezone().isoformat(),
 'bases':[{k:b[k]for k in ['repo','branch','commit','treeSHA']}for b in bases],
 'sourceRoots':roots,'sourceFilesInspected':len(selected),'pythonImportEdges':edges,'files':rows,
 'differentFromPublicFiles':len(rows),'differentSourceBytes':sum(x['bytes']for x in rows),
 'aliases':{rel:str(p)for rel,p in alias.items()},'credentialPatternFindings':findings,
 'unknownIdentifierLiteralFindings':identifiers,'fixedSnapshot':False,'publicObjectsCreated':False}
(D/'public-source-closure-draft-r118.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:result[k]for k in ['sourceFilesInspected','differentFromPublicFiles','differentSourceBytes','credentialPatternFindings','unknownIdentifierLiteralFindings','publicObjectsCreated']}))
