# 基础地景分批 GPU 上传与启动诊断（2026-10-21）

状态：静态几何核验通过，完整细层集成验收未完成。完整项目目标 active。源父提交24006167d33f2b0bc834731d1f6e1d95c5df36a9。未改公网、数据库、原始GIS、用户图层、默认入口或 native held。

## 诊断证据

W14=work/web_startup_profile_20261021，启动诊断复用临时 GL 方法包装，qa/profile 启用时限定30秒、32事件、16时间标记，同时记录模型等待的 wall time。没有新增 draw；方法内CPU时间可含驱动等待，不能当GPU elapsed。

实际RTX5080/ANGLE D3D11：卫片替换图4096×4096仍为HTMLImageElement，texSubImage2D152.1ms。倾斜摄影基础模型有9,165,843顶点、9,166,851索引，原bin329,974,380字节，包含位置、法线、UV、索引四数组；8192×8192 atlas 原先GLTFLoader已用ImageBitmap。首次基础绘制GL合计493ms，四次bufferData292.5ms（最大216.4），纹理200.5ms；render_submit max494.1、frameCPU495.1、frameInterval586.8ms。着色程序总0.5ms，非主要热点。

W14后续近景读取失败：reader37692第一次未得到有效响应，stdout关闭，成功响应计数requests0；26个计划失败，之后进入held/no automatic restart，保留基础层。requests在完整响应后才加1，因此不能仅据0判断是握手还是第一请求解码退出。没有原生exitCode/有效stderr，不能断言是源损坏、DLL或安全软件。只读Application事件检查未找到对应条目，不证明没有系统问题。该轮不算细层回归通过。service7412/session86311经owner204/exit0，reader最终closed且failed；未重试这个读取器。

## 实现

uploadStaticGeometry使用原CPU数组的视图，每批最多4MiB，预分配后与每批后让出一帧，原几何在全部缓冲完成且属性/版本一致后才安装并加入场景。没有重排、量化、删法线或改顶点/索引/UV。CPU数组与BufferAttribute读取方法保留；GPU通过Three已有外部缓冲属性契约引用。ArrayBuffer byteOffset正确保留。

使用COPY_WRITE_BUFFER上传并恢复此前绑定，不修改当前渲染VAO。索引需要先在临时VAO绑定ELEMENT_ARRAY_BUFFER分类，再通过COPY_WRITE上传，最后恢复原VAO；初版遗漏分类，实机出现GL错误，已保留失败包，不能算通过版本。[WebGL2规范的缓冲类型限制](https://registry.khronos.org/webgl/specs/latest/2.0/#5.1)说明初次COPY_WRITE会将未分类缓冲设为other-data，之后不能绑定索引目标。

取消/分配或读回失败/属性替换在提交前清理所有已分配缓冲，不安装半套属性。dispose监听在首次绘制前注册，先恢复原CPU属性、删除自有外部缓冲，再由Three释放几何的VAO状态，避免重复归属。静态模型长期驻留，与原512MiB细层账本的范围一致；本轮没有把全部静态GPU资源冒称纳入该账本。

## 测试及实际GPU核验

完整Web491项通过，新增启动诊断4项和几何分批5项。覆盖采样关闭/限时/有界历史/错误不重复绘制，以及完整源字节、非零数组视图语义、限批、索引类型与VAO恢复、取消、不符/GL错误、属性变化和释放顺序。不是所有变更分支都已有真实GPU故障注入。

修正版包使用显式staticOnly=1，暂停细层调度，geometryQA=1逐批getBufferSubData全量读回并逐字节比较，不采样抽查：

| 模型 | 原始/核验字节 | 批数 | 单批上传最大CPU ms | 最大分配CPU ms |
| --- | ---: | ---: | ---: | ---: |
| 卫片地形 | 17,187,360 | 5 | 1.4 | 0.1 |
| 完整倾斜摄影基础层 | 329,974,380 | 81 | 0.3 | 0.1 |

8个属性缓冲共347,161,740字节全部相同；画面2draw、3,668,177三角形。逐字节QA模式不等于正常帧性能；包含读回时render max179.1ms、frameInterval400.1ms，主要余峰为纹理。geometryQA关闭后的第二次静态采样：卫片批max1.6ms、基础批max0.3ms，首次render max153.2ms、frameInterval346.8ms，纹理max152.2ms。基础几何ready约2319.1ms、质量ready2530.2ms，原诊断约1212.9/1942.3ms；分批增加等待帧，尚不能声称整体加载更快。OS缓存未清，非冷20秒或受控全面性能结论。

首次绘制已不再集中bufferData基础几何；纹理/原bin获取解析/质量摘要等启动峰仍需后续处理。全量GPU几何字节同，不自动证明最终场景RGBA/深度/过滤采样等价；缺少细层替换/恢复与新外部缓冲的实机集成证据。

两个静态模式都通过显式“释放静态验收资源”清理，8属性恢复CPU归属、上传状态disposed、场景draw/triangle0。日志没有GL/渲染错误。reader starts0、store builds0，未通过新服务绕过W14读取器held来冒充恢复。

## 包、体验、运维与回滚

成功候选为Application/work/web_static_upload_20261021/fixed_mode/package。5840清单文件，继承前包逐文件校验，仅web/viewer.js与manifest记录变化；没有复制GIS或用户资料。identity ebea8af487ff949992cf234e8bb7c46394f7998463ba990bc39cf6e066340ca7；viewer6b78d924a6296fcbdd7e7d4fefdd7fc736516dbd6fb577a141eea95668d322f5。最终私有--check通过，冻结六源码/测试重建viewer同。初始失败包仍保留在上一级package，禁止把它当修正版。

修正版controller49600/service53704/port56171/session3781已经owner204/exit0；此前失败静态service43556/session58860也已owner204/exit0；W14service7412/session86311终态。临时tabs20/21/22/23均关闭。用户已有34268体验服务未触碰。

手动入口Application/实验入口/地景加载优化_20261020/启动Web基础几何核验.cmd，仅静态基础场景/全量GPU字节核验，不加载细层。未代运行。每次独立manual_runs、随机端口、所有者Job与30分钟上限。普通地景细层体验仍使用上轮“启动Web原始位图实验.cmd”，本轮不将静态模式作为完整应用新版本发布。当前包完整性验证不等于读取器功能验证。

## 后续与Git

优先1）补足读取器退出阶段与退出码证据，查清W14首个有效响应前退出原因，遵守失败hold不自动重启；2）按原尺寸与采样契约处理4096/8192纹理提交峰，保留像素证明；3）回归细层替换、覆盖与恢复集成；4）冷20秒/视口四周/全区/Web严格双轮/原始来源深度/8K与窗口DPI。UE引擎、EXE点线面图层、Web业务/IAM、261013/252需求和目录迁移完整目标不变。

本轮纯源码/测试/handbook仅本地提交，旧25已同步ed5fafc；旧14镜像固定5d→0925990仍待具体授权，不混新文件、不重复发问。本轮引擎master仍da9898f，无新增merge。native14 held、安全hold、原GIS/DLG/数据库保持。
