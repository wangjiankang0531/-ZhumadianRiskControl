from pathlib import Path
import importlib.util,json,ast
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).parent;D=R/'Document/Deployment/original_mapper_registration_verified_r264_20261103';J=lambda p:json.loads(p.read_bytes())
cleanup=J(D/'own-browser-cleanup-result.json');assert cleanup['passed']and cleanup['profilesRemoved']==1 and not cleanup['processesTerminated']
extra='\nR264收尾：本轮r130一份自有已退出Chrome配置经精确路径、零活动引用、无重解析核验后删除，240文件/逻辑11422528B，观察D空闲+11542528B不独占归因；源、结果、数据库、上传和用户浏览器保持。r129/r130已终态0并恢复，当前无本轮测试进程，不重复轮询65907/93919。\n'
for p in [D/'阶段说明.md',A/'deploy/handbook/original_mapper_registration_r264_20261103.md',R/'Document/Engine/project/原SQL映射运行修正进展R264_20261103.md',R/'Document/Engine/showcase_demo_completion.md']:p.write_bytes(p.read_bytes()+extra.encode())
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
 raw=p.read_bytes();i=raw.index(b'\n\n');p.write_bytes(raw[:i]+extra.encode()+raw[i:])
stage=J(D/'local-stage-files.json')
for name in ['cleanup_mapper_browser_r264.ps1','prepare_mapper_cleanup_r264.py','finalize_mapper_registration_r264.py']:
 p=A/'tools'/name;assert not p.exists();p.write_bytes((V/name).read_bytes());stage['application'].append('tools/'+name)
for folder,name in [('mapper-listener-classpath-r258','OwnMapperListenerClasspathR258.java'),('mapper-resource-pattern-r262','OwnMapperResourcePatternR262.java')]:
 rel='tools/java/mapper_validation_r264/'+name;p=A/rel;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((V/folder/name).read_bytes());stage['application'].append(rel)
rel='deploy/verification/original_mapper_browser_cleanup_r264_20261103.json';(A/rel).write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8');stage['application'].append(rel)
(D/'local-stage-files.json').write_text(json.dumps(stage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('local_review',V/'commit_r18_local_review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ab='review/workplace-r19-live-local-20261031';eb='review/workplace-r19-live-progress-local-20261031'
assert m.run(A,['rev-parse','refs/heads/'+ab]).decode().strip()=='7b36c60e6c16e6490fa3fc243e6682bbf3e3361c'
assert m.run(E,['rev-parse','refs/heads/'+eb]).decode().strip()=='80ba6c53389be0ce34ee79ab797af2b66c5a2a57'
assert(E/'docs').resolve()==(R/'Document/Engine').resolve();held=m.sha(A/'native/main.cpp')
for rel in stage['application']:
 if rel.endswith('.py'):ast.parse((A/rel).read_text(encoding='utf-8-sig'))
 elif rel.endswith('.json'):J(A/rel)
a=m.commit(A,'refs/heads/'+ab,ab,stage['application'],'r264-app','Verify all original XML statements and prepare explicit-preserving mapper default',True)
e=m.commit(E,'refs/heads/'+eb,eb,stage['engine'],'r264-engine','Record actual original SQL mapper registration comparison and release gaps',True)
assert m.sha(A/'native/main.cpp')==held
proof={'application':a,'engine':e,'heldNativeUnchanged':True,'publicGitPushed':False,'productPublicDeployed':False,'runtimeComparisonUsedTemporaryConfiguration':True,'productHelperCompleteLifecyclePending':True}
(D/'local-review-git.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
