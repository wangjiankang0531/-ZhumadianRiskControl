from pathlib import Path
import json,hashlib,ast
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).parent;C=R/'work/event_delivery_consistency_20261030/full-controller-r163';D=R/'Document/Deployment/original_mapper_registration_verified_r264_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def enc(x):return(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
assert not D.exists();results={}
for attempt,mode in [('r129','baseline'),('r130','candidate')]:
 root=C/attempt;prep=C/('prepared-'+attempt);result=J(root/'result.json');outer=J(C/(attempt+'-outer-terminal.json'));receipt=J(root/'scoped-controller-receipt.json')
 assert result['allPassed']and result['mode']==mode and result['original398ModelsUnchanged']and result['connectionCapacityWithoutRefusals']
 assert outer['exitCode']==0 and outer['actualDescendantsZeroBeforeClose']and not outer['forceTerminationUsed']and receipt['allOwnedChildrenExited']and receipt['normalOwnedShutdown']and not receipt['forcedJobClosureComponents']and all(v==0 for v in receipt['exitCodesBeforeJobClose'].values())
 for name in ['mapper-observer-restored.json','history-runtime-restored.json','configuration-restored.json']:assert J(prep/name)['passed']
 report=J(root/'actual-mapper-registration.json');assert report['actualApplicationReadySpringFactoryObservation']and report['originalXMLResources']==96 and report['expectedOriginalXMLStatements']==226 and report['factoryCount']==1
 row=report['factories'][0];assert row['registeredOriginalXMLStatements']==(3 if mode=='baseline' else 226)and row['missingOriginalXMLStatements']==(223 if mode=='baseline' else 0)
 if mode=='candidate':
  assert J(prep/'frontend-restored.json')['passed']
  browser=J(root/'plan-browser/result.json');assert browser['passed']and len(browser['cases'])==11 and not browser['exceptions']
  terminal=J(root/'plan-browser/browser-terminal.json');assert terminal['normalBrowserClose']and terminal['chromeExitCode']==0 and not terminal['forceTerminationUsed']
 else:browser={'cases':[]}
 results[mode]={'attempt':attempt,'registeredOriginalXMLStatements':row['registeredOriginalXMLStatements'],'missingOriginalXMLStatements':row['missingOriginalXMLStatements'],'nativeBrowserCases':browser['cases'],'allOriginal398ModelsAndConnectionCapacityPassed':True,'normalSixComponentExitCodes':receipt['exitCodesBeforeJobClose'],'actualDescendantsZeroAndOriginalBytesRestored':True}
original=J(R/'work/event_delivery_consistency_20261030/full-controller-r152/candidate-install-r1/controller-fixture-ready.json')['releaseSHA256'];assert sha(R/'_g/Application/release-manifest.json')==original
pattern=J(V/'mapper-resource-pattern-r262/result.json');assert pattern['passed']and pattern['originalPatternResources']==96
renderer=J(R/'Document/Deployment/original_mapper_default_candidate_r263_20261103/source-and-renderer-verification.json');assert len(renderer['actualFrozenConfigurationRendererCases'])==8 and renderer['allOtherFunctionsASTIdentical']
failed=[]
for attempt in ['r123','r125','r127']:
 root=C/attempt;outer=J(C/(attempt+'-outer-terminal.json'));receipt=J(root/'scoped-controller-receipt.json');assert outer['actualDescendantsZeroBeforeClose']and not outer['forceTerminationUsed']and receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']
 for name in ['mapper-observer-restored.json','history-runtime-restored.json']:assert J(C/('prepared-'+attempt)/name)['passed']
 failed.append({'attempt':attempt,'failure':J(root/'failure.json'),'allActualDescendantsZero':True,'exactOwnCodeAndConfigurationRestored':True,'businessNormalStartup':receipt['normalOwnedShutdown'],'original398ModelComparisonReached':False})
proof={'schema':'xnby.r264.original-mapper-runtime-comparison.v1','actualRuntimeComparison':results,'resourcePatternProof':pattern,'productRendererCandidate':renderer,'failedObservationAttemptsPreserved':failed,'originalJarOrSQLBytesChanged':False,'publicServerMissingStatementCountDirectlyMeasured':False,'runtimeComparisonUsedTemporarySyntheticConfiguration':True,'productRendererHelperFullLifecycleStillPending':True,'wholeNangangBusinessAcceptancePassed':False,'publicOrDesktopOrFormalOrSceneChanged':False}
put(D/'verified-result.json',enc(proof));put(A/'deploy/verification/original_mapper_registration_r264_20261103.json',enc(proof))
text='''# 原业务SQL映射运行对照与修正候选（R255—R264，2026-11-03）

已定位整体XML扫描缺口。原业务Jar的96份xml/资源包含226条select/insert/update/delete语句；1319个离线完全限定注册名含框架自动注入，不能作为业务功能或原XML语句数。r129保持原Jar、SQL、R36原控制及原扫描设置，仅增加独立只读监听Jar，在实际Servlet业务容器ApplicationReady的唯一SqlSessionFactory内实测注册3条、缺223条。该结果来自自有合成运行环境，不冒称已直接测得公网服务器缺失数量。

r130仅将自有业务配置指向classpath*:/xml/**/*.xml，并安装已编译R224十四源码候选；运行工厂内226条原XML语句全部注册、缺失0。11项普通角色原生预案/演练新增、编辑、只读、空人员保存、实际选人、真实上传就绪/失败保留/一次重试/原锚点下载通过，零浏览器运行异常。未额外复制单个预案XML、未用旧R225更新器；原SQL字节及Jar保持。实际MP资源解析另核96资源逐字等原Jar、无重复，保留队伍成员XML与原Jar字节一致。原398模型、连接容量通过；r129/r130原六组件及候选Chrome全部正常0、实际后代零，诊断Jar/临时classpath/虚构配置/前端/历史模块/清单逐字恢复，_g原e9dcd876已核同。

R263产品源码候选仅在无显式MybatisPlus Mapper位置时给业务侧补原xml目录，平台不改。使用真实自有冻结配置的渲染器对照8项通过，显式kebab/camel/indexed/underscore、多路径及空值均原样保留；JVM参数、鉴权初始化器及其余配置相同，除materialize插入调用与新增纯函数外，其余函数AST一致。注意：r130执行的是等价临时配置，不是这份R263产品控制文件的独立完整生命周期；后者还需纳入固定候选/连接预算控制声明、完整运行/恢复和预检后才可发布，不以配置实验冒称产品包已部署。

观察工具失败如实保留：r123追加初始化器被原精确生命周期列表限制在原主程序前拒绝，没有修改或放宽原限制；业务退出1，其余正常0、实际后代零后按新旧SHA恢复本次类/配置。r125独立监听Jar因classpath占位符大小写错误未加载，原程序正常关闭后精确恢复；r127监听观察断言失败、未取得注册结论，同样全部退出并恢复。R260改为仅目标Servlet容器、按原226条精确核对，观察故障写失败报告交主验证器拒绝，不中断原程序；原鉴权类、精确初始化器及现有spring.factories均保持。原Spring加载器也已独立核诊断监听器恰好发现一次。前三轮未到达398比较，不记通过。

本结果证明原语句注册恢复及上述两模块路径，不证明226条SQL均已执行、所有页面或真实南港模板全验；也不能据此推断原测试业务数据被删除。下一步以实际R37静态性能基线组合产品默认扫描修正和R224前端，保留压缩/缓存/IIS、鉴权、原意见历史、上传、数据与三维，再完整验证和准备固定发布。R37已上传/预检通过但无部署完成回执；30文件公开Git仍待答，本阶段新源码仅本地分支，不夹入旧固定公开范围。完整UE效果效率引擎、EXE GIS/DLG点线面图层旗杆标牌多源绑定、Web3D及单系统多入口全南港B/S目标active/fullCloneReady=false；另一三维专属断点、8767/资产、正式18891保持。
'''
put(D/'阶段说明.md',text.encode());put(A/'deploy/handbook/original_mapper_registration_r264_20261103.md',text.encode());put(R/'Document/Engine/project/原SQL映射运行修正进展R264_20261103.md',text.encode())
entry='''## 2026-11-03 R264：实际工厂原XML从3/226到226/226；候选11项通过并全部恢复

r129原扫描/R36控制自有Servlet容器唯一工厂实测226原XML语句仅注册3、缺223；r130临时原xml扫描路径后226全注册/缺0，R224预案演练11浏览器阶段/零异常、原398模型及容量通过，六组件/Chrome正常0/后代零、所有代码/临时classpath/配置精确恢复，_g原e9dcd876。session65907/93919已终态0，不再轮询。不是公网缺失数量直接测量，也不把226语句计业务功能或全SQL执行验收。R263产品参数默认扫描源码真实冻结渲染8项通过、显式配置保持，但完整生命周期尚待；下一基于R37组合严格声明/预检/恢复再发布。原SQL/Jar、鉴权初始化器/旧spring.factories、数据和三维均保持。r123/125/127观察工具失败及恢复全部保留，未记398通过。R37待手动执行回执、30公开Git待答；本轮桌面未操作，未改公网/正式18891/8767/资产及另一三维断点。详Deployment/original_mapper_registration_verified_r264_20261103。完整长期目标active/fullCloneReady=false。

'''
for p in [R/'Document/Engine/project/当前工作断点.md',R/'Document/Engine/project/htengine_goal_state.md',R/'Document/Design/驻马店实施基线.md']:put(p,entry.encode()+p.read_bytes())
p=R/'Document/Engine/showcase_demo_completion.md';put(p,p.read_bytes()+('\n'+entry).encode())
names=[]
for rev in ['r255','r256','r257','r260']:
 pins=J(R/'Document/Deployment'/('original_mapper_registration_'+rev+'_20261103')/'preparation.json')['sources']
 for name,pin in pins.items():assert sha(A/'tools'/name)==pin;names.append('tools/'+name)
extras=['OwnMapperRegistrationObservationR255.java','OwnMapperRegistrationObservationR256.java','OwnMapperRegistrationObservationR257.java','OwnMapperRegistrationObservationR260.java','prepare_mapper_observation_suite_r255.py','prepare_mapper_fixture_r255.py','diagnose_observer_start_r255.py','recover_observer_failed_start_r255.py','prepare_mapper_listener_suite_r256.py','prepare_mapper_observation_suite_r256.py','prepare_mapper_fixture_r256.py','prepare_mapper_listener_retry_r257.py','prepare_mapper_observation_suite_r257.py','prepare_mapper_fixture_r257.py','diagnose_observer_start_r257.py','recover_mapper_listener_r259.py','prepare_mapper_servlet_observer_r260.py','prepare_mapper_observation_suite_r260.py','prepare_mapper_fixture_r260.py','verify_mapper_listener_classpath_r258.py','verify_original_mapper_resource_pattern_r262.py','prepare_original_mapper_defaults_r263.py','record_mapper_registration_r264.py']
for name in extras:
 p=A/'tools'/name;assert not p.exists();raw=(V/name).read_bytes()
 if name.endswith('.py'):ast.parse(raw.decode('utf-8'))
 put(p,raw);names.append('tools/'+name)
names+=['tools/original_server_release_parameters_r263_mapper_default.py','deploy/handbook/original_mapper_registration_r264_20261103.md','deploy/verification/original_mapper_registration_r264_20261103.json']
put(D/'local-stage-files.json',enc({'application':names,'engine':['docs/project/当前工作断点.md','docs/project/htengine_goal_state.md','docs/project/原SQL映射运行修正进展R264_20261103.md','docs/showcase_demo_completion.md']}))
print(json.dumps({'recorded':True,'baselineRegistered':3,'candidateRegistered':226,'candidateNativeCases':11,'normalRestorationPassed':True,'publicOrDesktopChanged':False,'applicationStageFiles':len(names)}))
