# 原业务方法级验证记录（非业务闭环验收）

2026-10-25。使用自有 OriginalBusinessMethodProbe.java，直接装载Reference所附原业务JAR中的两个服务类，给Mapper注入合成数据代理；未重编或修改原业务方法，未启动Spring、业务服务、数据库或三维读取器。该参考JAR不能直接等同于当前公网运行JAR。

实际首次有界运行于20:29:59正常退出，exit=0；JDK为17.0.20.1。13个特殊作业开始条件检查通过：5个拒绝条件与8种作业的接受分支；检查异常、内存写入次数、作业/预约状态及同一开始时间。4个隐患复查输入完成行为记录，均写成“已整改”，包括不同文本与空文本。这是原方法在合成夹具下的可复现行为，不代表此逻辑符合业务要求；暂不改变原方法，后续需对照原站实际流程和审批规则。

测试前3项进程内限制自检通过；实际调用中未观测到被禁止的网络、子进程、目录外写入或额外原生库加载尝试。限制采用既有JDK17机制，仅用于本次已知输入的测试，不作为生产隔离或通用安全沙箱。复用了219份已固定SHA的依赖，没有复制JAR或原库。

后续20:38对源码重建制品和原部署来源flat制品分别首次运行相同夹具，均正常退出0；三份输出JSON逐项相同，各13个特殊作业检查通过、4个隐患复查行为记录一致。该结果仅限所调用方法和合成输入，不代表三制品全部行为相同，也不是当前公网JAR的远程回读证明。24条GUI/数据库验收用例仍未执行。事务、鉴权、真实SQL、持久化、附件、异步对接和浏览器流程不在本测试证明范围。

自有辅助源码位于 tools/java/OriginalBusinessMethodProbe.java（package xnby.replica）。编译使用既有JDK17的javac -encoding UTF-8 -d <自有classes目录> <源码>；运行入口为 xnby.replica.OriginalBusinessMethodProbe，依次接收原业务JAR路径、每行一个既有依赖JAR绝对路径的UTF-8清单、独立输出目录内results.json路径。测试准备必须核对JDK/输入清单/辅助类SHA，并保留45秒有界运行、256MiB堆上限及独立临时目录；输入与私有依赖清单不上传Git。

详细过程、首次依赖路径预检失败、修正后的编译记录、制品/依赖SHA、进程终态和原始结果仅留本地Document/Deployment/original_method_probe_20261025。公网部署、业务数据库、原GIS、用户DLG以及14项未验收修改没有由本轮改变。fullCloneReady=false。

## 原页面实际审批入口补查

原PC的隐患待审批Reexamine组件中，直接reviewHidden对话框及API调用已注释；实际审批按钮由myDealtStatus控制，并携带业务ID、待办ID、flowId进入/workflow/flowTodo/detail。该详情组件使用共享workflow/info.vue，读取JNPF FlowBefore详情、表单和节点信息；业务表单还按后端componentUrl动态加载。因此此处13+4方法证据不能代替当前审批流程的测试，更不能据直接复查接口的合成结果擅改真实流程。

下一轮真实验收需沿“隐患列表→待办详情→动态业务表单→审批/退回→流程记录与隐患状态”核对；同时核对原审批权限和对应角色。该链路本轮只读源码，未提交任何审批请求。7份相关原前端文件SHA与三制品结果对照留本地three-artifact-comparison.private.json。
