# 新EXE编辑命令、保存重开与真实网页互读（2026-10-27）

2026-10-27T05:53:50.863502+08:00。候选EXE SHA 380c23aa1809bd2c6e75bf24a8d3e9dea334054c0125cc1d5fe2cd27da322e12。父固定源为上一轮static-shell的390文件，加入1份探针及显式入口共391文件；默认运行不变，仍不编入14held修改。不是正式便携交付或用户人工操作验收。

## 实现与启动约束

native_annotation_probe_patch.py只接受固定静态源main SHA f5fd75da，添加--editor-annotation-probe、成员方法与显式循环调用，沿用--editor-static-shell-qa跳过原生细层service。只允许窗口探针和标注探针二选一，标注探针必须静态模式，原禁止混用/结果路径非空约束保持。测试实现native_annotation_probe.inl不编入当前正式原生工作树。通过Win32控件赋值、实际editorCommand/editorClick/editorLiveStyle及地景拾取执行，不预先拼出最终feature文档。

Release首次构建exit0但未执行：检查发现现有recordSwapchainCapture只覆盖shell探针，新探针无法得到帧。补入新标志后只增量编译main，第二次exit0；原收据/前一主源保留。最终唯一实际图形执行PID40124，6.765秒exit0，无超时、强杀、WM_CLOSE干预。读取现有驻马店基础地景，不启动旧0.9.7、原生读取器或ETW，不复制GIS。新建1个空测试层是输入，结果与截图只写独立目录；输入SHA保持。

## 七组真实编辑路径

1. 切换近景，通过实际地景拾取点击提交警示点，控件图标warning、尺寸40、颜色#FFAA00、alpha0.65。
2. 两次真实拾取落点并调用完成，生成dash线、宽7.5、颜色#EE2233、alpha0.4，两个顶点。
3. 四次落点再点回首顶点，生成4顶点region，不保存重复闭合顶点；dot边界、宽3.5、#22DD88/alpha0.8、填色#0088FF/alpha0.25。
4. 点改名QA-native-point-edited、square图标、紫色#BB22FF/alpha0.5，ID/几何保持；调用实际撤销/重做恢复完整文档。
5. 实际新增、命名QA-native-target并移动线；源层余2项、目标1项，移动前后线对象完整相同。
6. 锁层后live-style拒绝修改且完整文档不变；解锁、隐藏、恢复，feature数据保持。没有用会弹模态框的锁定删除/移动负例，不泛称所有锁定操作通过。
7. 实际保存命令写native_roundtrip.json，编辑器dirty清除，原生load重开与内存文档完全一致。

每组分开在8帧间隔运行，避免把单帧代码批量提交当真实输入时序。测试以程序设置现有控件并调用同一处理方法，未覆盖用户鼠标键盘消息路由、文件选择/另存为对话框或人工可用性。捕获native_annotation_frame.png已实际查看，包含新点线面和地景。点名称修改后原独立label.text仍为QA-native-point，本测试不声称修改了标牌文本。

## 原生输出到网页

实际输出SHA58e2308e8b51248f9040c0742024610f3cd38814b3c3407b21f2d1e6ad54be0e，2层3要素。既有Web validate原对象返回/JSON全结构不变；检查点名称/图标颜色alpha、线7.5/dash/alpha、区域4顶点/dot/填色alpha、线所属目标层及解锁/显隐状态均保持。

限定127.0.0.1的自有静态服务直接把这个文件作为layers/default.json，不改写字节，不使用文件选择权限绕过。Chrome加载原viewer构建、现有驻马店基础地景与该输出，实际逐个点击点、线、区域查看详情：square/#BB22FF/50%；QA-native-target/dash7.5/#EE2233/40%；region4顶点/dot3.5/#0088FF填色25%。2层/3要素、ID及数值匹配。页面控制台错误0，最终图片native-web-roundtrip.jpg；首张快照还显示上一次点详情，后来滚到实际区域样式位置的新截图作为最终图，不混称同一状态。

原页面释放图形资源、关闭自有测试标签，回环服务正常结束，未请求/api/lod。前后native_roundtrip SHA一致。网页仅显示已保存文档，不宣称反向Web编辑/EXE导回或任意文件三端完全兼容。

## 未完成与交付边界

未验收：自定义PNG文件选择、负例模态框、图层删除、人工鼠标全操作、千层性能、完整LOD/20秒外围清晰度、250/252目标机及完整便携包。旧0xC0000043没有重试或解决。图形执行6.76秒不是首屏/交互性能；Web后台标签低帧率不是受控性能对比。UE长期目标与严格天津B/S/H5/业务闭环不因本轮通过。

候选work/native_annotation_20261027/candidate保留16运行库/版权文件；无GIS、无默认快捷方式切换。不要无参数双击并认为原生细层已禁用。复现从本阶段source.private.zip恢复391文件、核SHA，使用原精确ABI缓存和保留的configure/build/build-capture命令。运行一次历史计划在graphical-plan.private.json，已完成，不重复执行；新验收要新空结果目录/合成输入。现有正式包、业务库、附件、用户DLG及回滚资料保持，无本次正式部署回滚需求。

3份自有探针/源码补丁/handbook独立本地Git，父2ff7f238，HEAD/index/27保护保持，无push或旧载荷变更。250仍j40/PID44620/18891/release3f1ee528，公网R5不变。源/执行证据和SHA先归档，确认构建、EXE和测试服务终态后清本轮可重建build/dependencies/source和已归档TMP重复物，保留候选与两张可看图片、真实输出及日志。全目标active/fullCloneReady=false。
