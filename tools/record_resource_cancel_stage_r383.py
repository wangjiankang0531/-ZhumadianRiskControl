from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_six_relations_r372_20261103';B=R/'work/user_feedback_20261031/plan-resource-cancel-r378/retry-r2'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def jout(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not(D/'local-stage-files-r383.json').exists();proof=J(D/'verified-component-and-build-r381.json');clean=J(D/'completed-fixture-cleanup-r382.json')
assert proof['passedComponentAndFullBuildStage']and clean['passed']and proof['full29CaseNormalRoleAcceptancePending']
assert sha(R/'_g/Application/release-manifest.json')=='e9dcd8761860dd4624daf4ee2093bb384062996b37c7c8a3af5ff020d50481e4'
held=A/'native/main.cpp';other=R/'Document/Engine/project/驻马店三维_当前工作断点.md';held_pin=sha(held);other_pin=sha(other)
app=[];engine=[];sourcepins=[]
names=['prepare_plan_six_relations_r372.py','plan_six_relations_inspect_r373.py','plan_six_relations_prepare_r373.py','plan_six_relations_run_r373.py','verify_native_plan_six_relations_r374.mjs',
 'verify_resource_cancel_component_r375.mjs','run_resource_cancel_component_r375.py','original_plan_resource_cancel_compat_r376.py','prepare_resource_cancel_candidate_r376.py',
 'build_plan_resource_cancel_r377.py','build_plan_resource_cancel_r377.mjs','prepare_scoped_cancel_build_r378.py','build_plan_resource_cancel_r378.py','build_plan_resource_cancel_r378.mjs',
 'prepare_cancel_build_retry_r379.py','build_plan_resource_cancel_r380.py','build_plan_resource_cancel_r380.mjs','prepare_resource_cancel_evidence_r381.py',
 'cleanup_resource_cancel_fixtures_r382.ps1','record_resource_cancel_stage_r383.py']
for name in names:
    raw=(V/name).read_bytes();raw.decode('utf-8-sig')
    if name.endswith('.py'):ast.parse(raw,filename=name)
    dst=T/name;assert not dst.exists();dst.write_bytes(raw);app.append(dst.relative_to(A).as_posix())
    sourcepins.append({'path':app[-1],'sha256':sha(dst),'neverRunOrSuperseded':name in {'plan_six_relations_run_r373.py','plan_six_relations_prepare_r373.py','build_plan_resource_cancel_r377.py','build_plan_resource_cancel_r378.py'}})
for rel in proof['fullBuild']['changedSourcePaths']:
    src=B/'compiled-inputs'/rel;dst=A/'source-review/plan-resource-cancel-r378'/rel;assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());app.append(dst.relative_to(A).as_posix())
    sourcepins.append({'path':app[-1],'sha256':sha(dst),'exactActualCompiledCandidateInput':True})
scoped_clean={k:v for k,v in clean.items()if k!='targets'};scoped_clean['targets']=[{k:v for k,v in row.items()if k!='path'}for row in clean['targets']]
jout(D/'scoped-cleanup-r383.json',scoped_clean);jout(D/'source-pins-r383.json',{'files':sourcepins,'native29CasesPending':True,'publicPushed':False})
guide=f'''# 六类预案关联核对与资源取消异常本地候选

## 原项目范围与当前证据

已从原服务和实体核对六类关联：副指挥长、其他成员、参与单位，以及应急物资、队伍和专家。前三类由原FormList录入，后三类从原资源列表选择。六类字段/表名和原服务SHA记录在verified-component-and-build-r381.json；当前编译的FormList仍逐字匹配Reference原文件。

准备的29项普通角色场景计划通过原资源save接口创建自有数据，检查六类新增、两条到一条的编辑、资源重复选择、删除取消/确认和只读回显，并保留原21场景。六组件准备最初在6GiB准入处拒绝，随后读数2.261GiB；未分配work/plan-six-relations-r373或r147，也没有启动服务。此旧运行驱动在新前端组合前已标记替代，不能内存恢复后直接盲重跑。

## 实际复现和修正

三份R224真实资源SFC配合真实Element Plus确认框，在独立无后端组件夹具中各执行取消、关闭、确认，共9项。原版取消/关闭合计6次未处理Promise拒绝，数据均保留；候选只捕获cancel和close，未知拒绝继续抛出，重复9项后未处理拒绝0、确认删除仍各一次。ProTable、字典和API明确为stub，不把这些组件结果称普通角色或真实后端通过。

仅goodsList.vue、teamsList.vue、expertsList.vue三处变更。完整前端按已有七层适配配方重建341文件，与实际R224编译输入相比只改变这三文件；其他R224登录、路由、工作流、附件、表单等输入一致。单组件实际通过的三份字节与完整编译输入相同。Node退出0、实际Job后代零，七层源码精确恢复；新完整编译前端尚未安装或上公网。

## 失败及资源处理记录

首次完整构建目录不在旧适配器允许的隔离前缀，Node前拒绝，已进入的头像覆写恢复；改用原允许的user_feedback目录，没有扩大守卫。768MiB堆的构建实际OOM退出134，后代零、七层源码已恢复；Node fatal退出使JS finally未移除依赖junction，核精确目标与无活动引用后，仅非递归移除连接本身，共享依赖及Vue包摘要保持。随后复用同一原像源树，构建堆2GiB、可用内存准入提高到6GiB，正常构建成功；未复制新的全源树或降低六组件门槛，没有关闭用户应用。

清{int(clean['removedFiles'])}临时文件、逻辑{int(clean['logicalBytes'])}B，D空闲变化{int(clean['observedDFreeDelta'])}B仅观察不独占归因。保留三份候选SFC、实际编译输入、完整341文件候选和小型结果；清理组件浏览器/站点、重复源副本，原Reference、依赖、资产、数据库/上传、正式18891/8767保持。

## 下一步与发布状态

为这三处新前端建立精确的新组合合同后，在实际六组件和普通角色上跑完29项六关联/演练/附件/旧详情场景，再制作下一固定发布。不能把单组件9项或完整构建当真实六关联业务已完成，也不能静默替换已固定R39。

R39八文件2165296B清单4c5a31aa246858bf8e49db4ae97520fb8c90989bc97e6343c14a198540d402de，及184文件公开清单c10870e318047506c1ca0de42467a4fd8be602e5f8a85d5a5f40f3a9bcfe7ed1均保持，相关桌面/公开范围答复仍待，未上传部署或新公开Git。R39已验证的双基线实际更新回滚/21场景结论没有被本轮重写；本轮修正仍单独本地候选。实际IIS/公网HTTPS/正常登录耗时及真实南港模板权限/跨入口仍待。

完整UE对标引擎、独立EXE GIS/DLG点线面图层旗杆多源标牌、Web3D及一套系统全南港B/S目标继续active/fullCloneReady=false，不给新百分比，不改另一三维会话断点。
'''
write(D/'六类关联与取消异常修正阶段说明.md',guide)
for name in ['prepared-r372.json','resource-cancel-candidate-r376.json','retained-build-scope-refusal-r377.json','retained-build-heap-refusal-r378.json',
 'owned-build-junction-cleanup-r379.json','verified-component-and-build-r381.json','r373-superseded-before-service.json','scoped-cleanup-r383.json','source-pins-r383.json']:
    dst=A/'deploy/verification/plan_six_relations_cancel_r383_20261103'/name;write(dst,(D/name).read_text(encoding='utf-8-sig'));app.append(dst.relative_to(A).as_posix())
hp=A/'deploy/handbook/plan_six_relations_cancel_r383_20261103.md';write(hp,guide);app.append(hp.relative_to(A).as_posix())
stage=f'''## 2026-11-03 R372—R383：资源取消异常真实复现并修正，完整前端通过，六关联29场景待跑

原服务/实体和成员表单核六类关联；准备29普通角色流程但最初6GiB守卫在分配前拒绝，随后2.261GiB，无自有运行根/新服务。旧R373驱动已在新前端合同前标替代，不因内存恢复盲重跑。单组件真实三SFC+Element Plus共9项：原取消/关闭6次未处理拒绝、候选0且确认仍正确；ProTable/字典/API为stub，不冒称普通角色后端通过。只处理cancel/close，未知错误保留。

完整341文件前端构建通过，仅3资源SFC改变、其他R224实际输入保持，组件与编译源字节相同，原成员表单仍逐字Reference。最初目录守卫Node前拒绝；768MiB堆OOM134但后代零/7层源码恢复，遗留只读junction按精确目标非递归清理，共享依赖保持；复用源树、2GiB堆/6GiB准入后正常0/后代零、7层恢复。清{int(clean['removedFiles'])}文件/逻辑{int(clean['logicalBytes'])}B、D变化{int(clean['observedDFreeDelta'])}B不独占归因，341候选/编译源/证据保留。

下一为新3前端建精确组合合同，再实际六组件普通角色29项及完整新发布验证。当前只是本地修正，R39固定4c5a31aa与公开184固定c10870e3均未改/未上传或新公开；待桌面及公开范围答复。R39双基线/21项旧结论保持，不把本组件/构建当六关联全流程通过。实际IIS/HTTPS/登录耗时/真实全南港权限模板跨入口仍待。全UE引擎/EXE DLG图层旗杆标牌/Web3D/单系统B/S目标active/fullCloneReady=false，资产/数据库/正式18891/8767/另一三维断点保持，无桌面输入，不报新百分比。

'''
for rel in ['Document/Engine/project/当前工作断点.md','Document/Engine/project/htengine_goal_state.md','Document/Design/驻马店实施基线.md']:
    p=R/rel;old=p.read_text(encoding='utf-8');assert not old.startswith(stage.split('\n',1)[0]);write(p,stage+old)
    if rel.startswith('Document/Engine/'):engine.append('docs/'+rel.removeprefix('Document/Engine/'))
log=R/'Document/Engine/showcase_demo_completion.md';old=log.read_text(encoding='utf-8');marker='## 2026-11-03 R383六关联核对与资源取消异常候选'
assert marker not in old;write(log,old+'\n\n'+marker+'\n\n'+stage.split('\n\n',1)[1]);engine.append('docs/showcase_demo_completion.md')
ep=R/'Document/Engine/project/六关联与取消异常候选_R383_20261103.md';write(ep,stage+guide);engine.append('docs/project/六关联与取消异常候选_R383_20261103.md')
assert sha(held)==held_pin and sha(other)==other_pin and len(app)==len(set(app))and len(engine)==len(set(engine))
jout(D/'local-stage-files-r383.json',{'application':app,'engine':engine,'heldNativeSHA256':held_pin,'other3DBreakpointSHA256':other_pin,'publicPushed':False,'native29Pending':True})
print(json.dumps({'recorded':True,'applicationFiles':len(app),'engineFiles':len(engine),'componentCasesEach':9,'fullBuildFiles':341,'native29Pending':True,'publicPushed':False}))
