from pathlib import Path
import importlib.util,json,ast
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).parent;D=R/'Document/Deployment/original_mapper_product_verified_r272_20261103';J=lambda p:json.loads(p.read_bytes())
cleanup=J(D/'own-browser-cleanup-result.json');assert cleanup['passed']and cleanup['profilesRemoved']==10 and not cleanup['processesTerminated']
extra='\nR272收尾：清理r131/r132已退出、无活动引用/无重解析的10个自有Chrome配置，2105文件/逻辑112784092B，观察D空闲+109273088B不独占归因；源码、结果、数据库、上传和用户浏览器保持。当前无本轮测试运行，r131/r132均终态0并精确恢复。\n'
for p in [D/'阶段说明.md',A/'deploy/handbook/mapper_product_lifecycle_r272_20261103.md',R/'Document/Engine/project/原SQL产品代码运行R272_20261103.md',R/'Document/Engine/showcase_demo_completion.md']:p.write_bytes(p.read_bytes()+extra.encode())
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:
 raw=p.read_bytes();i=raw.index(b'\n\n');p.write_bytes(raw[:i]+extra.encode()+raw[i:])
stage=J(D/'local-stage-files.json')
for name in ['prepare_product_browser_cleanup_r272.py','cleanup_product_browsers_r272.ps1','finalize_mapper_product_r272.py']:
 p=A/'tools'/name;assert not p.exists();p.write_bytes((V/name).read_bytes());stage['application'].append('tools/'+name)
rel='deploy/verification/mapper_product_browser_cleanup_r272_20261103.json';(A/rel).write_text(json.dumps(cleanup,indent=2)+'\n',encoding='utf-8');stage['application'].append(rel)
(D/'local-stage-files.json').write_text(json.dumps(stage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('local_review',V/'commit_r18_local_review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ab='review/workplace-r19-live-local-20261031';eb='review/workplace-r19-live-progress-local-20261031'
assert m.run(A,['rev-parse','refs/heads/'+ab]).decode().strip()=='4e0f59fae1b71529f8f5e5b6ad26ff652d2aad01'
assert m.run(E,['rev-parse','refs/heads/'+eb]).decode().strip()=='cc3bc5a823c0125d5ae7b8ddd1957ae9a8379089'
assert(E/'docs').resolve()==(R/'Document/Engine').resolve();held=m.sha(A/'native/main.cpp')
for rel in stage['application']:
 if rel.endswith('.py'):ast.parse((A/rel).read_text(encoding='utf-8-sig'))
 elif rel.endswith('.json'):J(A/rel)
a=m.commit(A,'refs/heads/'+ab,ab,stage['application'],'r272-app','Run product mapper defaults and final declaration adapter through native workflows',True)
e=m.commit(E,'refs/heads/'+eb,eb,stage['engine'],'r272-engine','Record product mapper lifecycle completion and remaining transport work',True)
assert m.sha(A/'native/main.cpp')==held
proof={'application':a,'engine':e,'heldNativeUnchanged':True,'publicGitPushed':False,'productPublicDeployed':False,'actualProductParameterAndFinalAdapterLifecyclePassed':True,'newPublicTransportContractPending':True}
(D/'local-review-git.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
