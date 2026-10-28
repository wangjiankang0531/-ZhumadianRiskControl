# PNG2完整EXE、文件对话框与网页互通体验版（2026-10-27）

交付目录Application/Packages/candidates/NativeEditor_PNG_20261027_Preview，0.9.8-preview.2，27文件/8,996,890字节。EXE SHA256 c15079681dd32b99aedd590186e72544848906bcecf0fa3c93cef20a735d3339；manifest SHA256 3bc2fe2ff198e00871245b6a227b9ac7ef8b9b109fdaffc2c421318448186218。独立新项目Assets/DLG/NativePNGPreview_20261027/驻马店PNG图标体验.json，状态Application/UserData/NativePNGPreview_20261027；旧体验包、用户项目、250业务及公网均未替换或重启。

## 构建及固定输入

继续使用已同步PNG阶段源码。旧固定Git输入导出391源，PNG容器及选择前完整像素解码补丁生成392源；native_png_dialog_probe_patch.py仅扩展显式静态验收探针的PNG/Open及SaveAs流程，普通手动入口不执行探针。完整Release构建使用VS18/v145、SDK10.0.26100.0，恢复既有准确ABI的34个离线缓存包（1738文件/123743016字节），无网络下载或GIS复制，未编入14个held原生修改。

新增prepare_native_png_preview_source.py串联既有两阶段导出和本阶段探针补丁，输出392份编译源码及png-dialog-source-receipt.json；只准备源码，不恢复SDK、不构建、不启动图形、文件对话框或读取器。它与实际成功构建输入逐SHA一致。运行时输出目录须不存在且位于两仓库外，父目录须已存在：

```powershell
python -I -B D:\Project\Zhumadian\Application\tools\prepare_native_png_preview_source.py --application-repository D:\Project\Zhumadian\Application --engine-repository D:\Project\Zhumadian\XNBYEngine --output D:\Temp\ZmdPNG2Source
```

随后按native_capacity_isolated_build_20261025.md的固定工具链/离线依赖准备，以Source/Application为CMake源目录，构建xnby_zmd_editor。实际configure/build命令、每阶段PID/退出码、源及运行库SHA在Document/Deployment/native_png_editor_20261027，不将其私有环境路径/SDK/二进制作为源码载荷。

## 失败、定位与修正

第一次新EXE fa205完整编译，但自动文件对话框验收未完成，26.266秒正常退出1。独立Open组件确认：此机文件名为ComboBoxEx32/ComboBox/Edit ID1148，旧edt1/CDM消息没设置它；改为自身控件WM_SETTEXT，携带实际确认按钮句柄后，组件精确返回合成PNG路径。

第一次驱动增量构建退出0但EXE SHA未变。日志有MSB8029（临时目录影响增量），新inl时间晚于main.obj却未重编。该结果被SHA检查拒绝，没有运行旧二进制冒称新驱动通过；保留收据后只删除自建build中的main.obj，重新编译主TU并要求日志包含main.cpp且EXE SHA变化，得到faa5。

第二个不同EXE faa5的PNG选择文本/提交成功，但SaveAs未完成，20.844秒正常退出1。独立SaveAs组件确认其文件名Edit ID1001，与Open1148不同。早期对“新目标已显示”的判断来自Open证据，不能用于SaveAs，文档按最终控件日志更正。独立组件因未改到文件名产生了本轮合成输入的覆盖确认；没有批准覆盖。

标准IDNO控件查找、普通Button消息和一次不支持的UIA Invoke均未使该确认关闭，不计成功；PowerShell最后一行的成功文字不能覆盖前面的Unsupported Pattern错误。最终根据实际CommandButton_7和Windows文档化TDM_CLICK_BUTTON，明确选择“否”，再取消外层，组件正常退出，未强杀、未写文件。新增组件准确设置Edit1001后，正常返回新的中文目标，未再出现确认。

最终探针分别处理Open1148/旧edt1及SaveAs1001，只枚举当前测试PID直接拥有的对话框，验证文本等于合成目标才提交；新目标须不存在，异常嵌套提示一律拒绝，不操作用户窗口或全局鼠标键盘。按同样规则确实重编主TU得到新c150，未对失败的未变EXE盲目重试。前两份EXE、源码、日志及所有收据保留。

## 最终实际验收

c150仅启动一次显式静态图形验收，PID32468，20.640秒exit0，无观察超时或强制终止。RTX5080、preset=zhumadian，9,584,599顶点/11,668,083索引；独立惠炼/信能设备源模型计数0，不请求原生细层service、旧0.9.7 EXE或ETW。七组检查通过：点标绘；线型/宽度/颜色/透明度；区域闭合及填充；真实PNG选择/原字节嵌入/96px与75%/两阶段撤销重做；新建命名图层及移动线；锁定拒绝及显隐；真实中文路径另存为并重新读取。

PNG和SaveAs对话框均有自身PID/命令/文件名精确匹配/提交成功且未取消的记录。图形捕获可见原红白PNG、虚线和填充区域；捕获仅渲染视口，不含GDI面板。原合成输入SHA保持。真实保存PNG标注保存重开.json SHA为7e28ee3d52ce367736e5e5385c0f95ab33d27fb901a9995b0fd1329f43393a52，2层3要素，嵌入PNG与选择文件逐字节相同。

独立网页服务直接返回这份原生保存JSON的同一SHA；Chrome实际观察custom图标、75%不透明度、同一局部坐标和地景中PNG，错误0。浏览器截图受加载时序影响展示总览角度，不能据此声称与原生截图的相机或像素一致；证明范围为同一数据/样式与PNG可见。测试标签和服务正常结束、停止键移除、原生保存文件SHA保持。

完整EXE纯CLI又分别验证有效PNG保存重开等同、Hello伪PNG被拒且无输出；均在图形入口前结束。最终包普通--editor-static-preview模式以额外8帧限额读取新中文项目，5.719秒正常退出，automatic_probe=false，项目不变。正式快捷方式没有帧限额。全部属于自动化验收，人工鼠标/文件选择体验仍交用户复核，不改写为人工通过。

## 交付、使用和运维

三个快捷方式由既有UTF8-BOM Windows PowerShell工具生成并读回。第一次打开本包“1_编辑图层（基础地景体验）”，选“应急图标示例”并用自定义PNG按钮选图，包内图标样例可用。保存关闭重开，再用“2_网页查看当前图层”和“读取编辑端保存”对照；结束Web服务用第三入口。新项目只首次创建，启动不重置用户数据。

另存为会改变编辑器当前文件；网页快捷入口仍固定原体验项目。查看另存的新文件时，在网页“打开图层文件”手工选择新JSON。本阶段没有新增自动跟随另存路径协议，不把指定文件直接互通记作该功能已实现。

包内Web包含前阶段已720回归及真实浏览器验证的PNG修正；其JS/worker按SHA从验证归档恢复，HTML沿用本机模式说明和公网门户链接，保留Three许可。新包仍复用Packages/versions/0.9.7的Python及基础地景资源，不是可直接复制到252的便携包。resource-references.private.json明确禁止清理该依赖根。没有启动新的长期用户进程，旧编辑器/网页/业务保持供用户自行切换；可按本包说明手动体验。

回退只需保存并关闭本包编辑器、用第三入口正常停止本包Web，继续使用旧入口；不要覆盖或删除Assets中的用户新项目。运行包/用户DLG/GIS/SDK/截图不上传Git，源码按独立评审分支同步，不合并main、不部署公网。源/执行逐SHA归档后清本轮临时源、依赖、对象和组件诊断副本，候选及必要失败证据保留。

PNG容器检查仍不等于任意像素数据完整性，旧PNG阶段损坏zlib样本未触发Chrome onerror的边界保持；原生导入恶意/坏像素恢复及全部格式兼容性不据本轮几个样本宣称完成。完整细层/20秒外围、UE效果效率、252新包、人工完整流程及天津B/S/H5复刻继续，完整目标active。
