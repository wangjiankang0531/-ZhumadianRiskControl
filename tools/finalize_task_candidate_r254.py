from pathlib import Path
import importlib.util,json,ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;A=R/'Application';E=R/'XNBYEngine'
D=R/'Document/Deployment/original_task_attachment_verified_r254_20261103'
J=lambda p:json.loads(p.read_bytes())
cleanup=J(D/'own-browser-cleanup-result.json');assert cleanup['passed']and cleanup['profilesRemoved']==11 and not cleanup['processesTerminated']
extra='\n本阶段清理r119/r120/r122已正常退出且无活动引用、无重解析的11个自有Chrome配置：2341文件、逻辑124185563字节；观察D空闲变化125390848字节，不作为独占释放量。源码、结果、数据库、附件、用户浏览器和资产保持。清理器首次因两套终态字段名不同在删除前拒绝，按各套实际字段精确校验后通过，未放宽退出约束。\n'
for p in [D/'阶段说明.md',A/'deploy/handbook/task_attachment_verified_r254_20261103.md',R/'Document/Engine/project/任务附件候选回归R254_20261103.md']:
 p.write_bytes(p.read_bytes()+extra.encode())
entry='\nR254收尾：11个自有已退出Chrome配置按精确路径/零引用/无重解析清理，2341文件逻辑124185563B，观察D+125390848B不独占归因；源码/验证结果/数据库/附件/用户浏览器保持。当前无本轮测试进程，r122已终态0并恢复，下一实际Spring逐原SQL映射观察，不重复已通过九阶段。\n'
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
 raw=p.read_bytes();i=raw.index(b'\n\n');p.write_bytes(raw[:i]+entry.encode()+raw[i:])
p=R/'Document/Engine/showcase_demo_completion.md';p.write_bytes(p.read_bytes()+entry.encode())
dst=A/'deploy/verification/task_attachment_browser_cleanup_r254_20261103.json';dst.write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8')
stage=J(D/'local-stage-files.json')
for name in ['cleanup_completed_browser_profiles_r254.ps1','finalize_task_candidate_r254.py']:
 p=A/'tools'/name;assert not p.exists();p.write_bytes((V/name).read_bytes());stage['application'].append('tools/'+name)
java=V/'mapper-offline-registration-r251-r2/OwnOriginalMapperRegistrationR251.java';dst=A/'tools/java/mapper_audit_r251/OwnOriginalMapperRegistrationR251.java';assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(java.read_bytes());stage['application'].append('tools/java/mapper_audit_r251/OwnOriginalMapperRegistrationR251.java')
stage['application'].append('deploy/verification/task_attachment_browser_cleanup_r254_20261103.json')
(D/'local-stage-files.json').write_text(json.dumps(stage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('local_review',V/'commit_r18_local_review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ab='review/workplace-r19-live-local-20261031';eb='review/workplace-r19-live-progress-local-20261031'
assert m.run(A,['rev-parse','refs/heads/'+ab]).decode().strip()=='6a2fc1b3688a457225611c8178d5eb11f9ce9982'
assert m.run(E,['rev-parse','refs/heads/'+eb]).decode().strip()=='1d78e44f9f2d0e161dfe2e73b365ba86d27820f1'
assert(E/'docs').resolve()==(R/'Document/Engine').resolve();held=m.sha(A/'native/main.cpp')
for rel in stage['application']:
 if rel.endswith('.py'):ast.parse((A/rel).read_text(encoding='utf-8-sig'))
 elif rel.endswith('.json'):J(A/rel)
a=m.commit(A,'refs/heads/'+ab,ab,stage['application'],'r254-app','Verify shared task upload and parallel workflow candidate; retain mapper audit gaps',True)
e=m.commit(E,'refs/heads/'+eb,eb,stage['engine'],'r254-engine','Record task candidate acceptance and scoped temporary browser cleanup',True)
assert m.sha(A/'native/main.cpp')==held
proof={'application':a,'engine':e,'heldNativeUnchanged':True,'publicGitPushed':False,'publicProductDeployment':False}
(D/'local-review-git.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
