# 异步父页恢复失败保留完整子层及真实地景对照（2026-10-27）

状态：生产函数已修正，10项真实RHI异步控制器场景以及新完整EXE的三种只读地景模式运行门禁通过；画质推广不通过，实验开关和日常体验包未替换，完整目标active。

## 问题与修正

原20261026 r4封存控制器，在父页已退休且恢复失败后，将所在完整root从resident和desired删除，连同仍可正确绘制的子cut一起丢失。新独立基线探针实际先绘制绿色完整子层，设置已知恢复失败，再调用原serviceRetainedParentPages；resident清空、payload归零、evictions=1，0.610秒正常退出。这里exit0表示缺陷复现成功，不表示原实现验收通过。未运行原r4失败二进制，旧0xC0000043故障原证据保留，不能把新EXE成功称为已定位或修复历史共享冲突。

原源码还允许同一帧开始时收集的restoreCandidates在后续解码/身份/GPU失败后再次入队：候选过滤没有重新检查刚更新的parentRestoreFailed。此第二路径按实际源码定位；本阶段没有单独对原实现运行“解码失败后重复两次”的基线，不把推断冒充该路径旧运行记录。

native_parent_restore_failure_patch.py只接受原函数SHA，生成两个修正：父恢复失败时保留当前完整child cut，普通可见性/预算驱逐仍负责root正常退出；进入实际调度前重新剔除parentRestoreFailed。没有扩大512MiB全局/384MiB单根预算、伪造缺失资源、绕过reader锁或承诺错误资源会自动修好。失败表仍属于固定准备资源快照的已有生命周期。

## 实际异步控制器与RHI

53源的独立探针调用实际封存serviceRetainedParentPages、sourceRecord/cancelFamily/resetFamilies/coarsenFamily、退休/身份/绘制门禁函数，修正只作用于恢复函数。只有OSGB解码边界替换为可控制完成时间的合成std::async结果；GPU上传、管线、fence和逐字节readback使用固定引擎8966e32b的真实RHI，不是手动模拟控制器提交。生产调度外围仍是夹具，不能等同完整pager相机往返。

修正EXE 7d36f9def34e5a5d4c855876814e3c446d65ba41f9293c81bc96ca8f69d7a1d9，PID31036/0，0.641秒正常退出。十场景：已知父恢复失败保留子cut且不解码；两页分帧上传全部完成才原子恢复；解码失败保留且同帧不重试；像素身份失败；source跨度变化失败；desired移除丢弃解码；cut对象身份变化丢弃旧结果；相机改变取消部分GPU上传；并发预算不足不上传且不盲重试；第二GPU页失败释放部分资源并保留子层。失败/取消后绿色子页逐像素保持；成功后红/蓝父页分别读回一致，所有场景结束子分配/描述符回基线。VMA块缓存仍可保留，validationLayerEnabled=false，未安装/变更层或安全配置。

## 新完整编辑器候选

将PNG2的392源与原409源退休候选按共同Git基线做main.cpp三方合并，0冲突；保留PNG2文档/编辑/真实文件对话框探针原字节，加入本轮恢复修正，形成411源。原14 held工作区没有编入；冻结三份退休函数与已验探针SHA一致。VS18/v145、SDK10.0.26100，沿用已有34离线缓存包/1738文件，无下载、GIS复制或原读取器调用。完整EXE SHA256 bb8743c037aec909e9a91d41ca2913f5a682e9e3fb0682bfd7a97ea01110f6a0，16运行成员及许可证保留于本轮full-candidate，没有覆盖Packages现用版本。

完整EXE纯CLI实际通过PNG保存文档同结构重开、Hello伪PNG拒绝且无输出。新完整EXE未重新运行鼠标/PNG文件对话框人工验收；PNG2既有七组结果和对应未改输入证据保持，不冒称又对新合并GUI测了一轮。

同一新EXE、1280×720、tile141/height100/focus(-317,-1988,43)、同一合成点/虚线/透明区域、同一只读挂载/131族索引、地景payload预算512MiB，三模式按前置成功门禁各启动一次，无重试/强杀：

|模式|PID/退出|进程秒|最终payload B|峰值payload B|根数|加权质量缺口|累计退页/恢复页|
|---|---|---:|---:|---:|---:|---:|---|
|页回收关闭基线|4968/0|14.563|526286052|534566632|18|2.6588544213|0/0|
|页回收|45496/0|12.281|509187468|523839228|18|2.5661209584|4/0|
|受控恢复诊断|40732/0|13.485|509187468|523839228|18|2.5661209584|5/1|

各自启动前文件就绪额外约1.015秒，不并入上述进程时间。基线根集/payload/缺口精确重现之前已验覆盖候选；三模式前后7039项准备缓存元数据及marker/锁SHA保持，候选和合成层不变，无原OSGB reader/生产器/ETW。全量GIS正文没有重新逐字节哈希。两帧离屏最终结果、固定顺序的一次对照，OS/GPU缓存未清，不是5/20/40秒冷启动时间线、稳定速度基准、真实相机往返或252验收。

页回收累计旧payload 61124944B=58.293MiB，实际RHI子分配回收66682584B=63.593MiB/4描述符。最终驻留净减少17098584B=16.306MiB（501.9→485.6MiB），部分回收空间已用来加载新细节。此前中间反馈把累计退页说成payload减少58.3MiB不够准确，以本表三种口径为准。峰值始终小于512MiB，但这是地景payload，不是总显存。恢复诊断明确started/done=true、failed=false、实际恢复1页，累计退5页/RHI回收83871080B，missingBasePageFallbacks=0；是受控组件恢复，不是相机自然往返已通过。

## 质量反证与推广决定

加权缺口整体下降约3.488%，29诊断点中8处来源变化：141四处、117三处由L19到L20；中央[32,27]的tile118从Tile_118_L21_0uuuu21.osgb变为Tile_118_L20_0uuuu2.osgb。四角样本没有新增空source，但较深层来源退为父层这一反证说明仍有细节取舍，不能用整体指标下降抵消局部退化。截图已实际查看，不能凭截图看似接近宣称无退化。拒绝默认提升，fullClarityAccepted/candidatePromotionAccepted保持false。

下一步约束可见局部质量退让，再做实际相机移动/往返、多站来源/深度/纹理质量及5/20/40秒完整时间线。当前仍有3类family_decode_error，现有只读资源缺口没有通过重跑原读取器或补造锁掩盖。14家真实企业图层、完整GUI消息路径、252和天津B/S/H5不按本轮合成标注/场景结果算通过。

## 源码重建、使用与回退

开发侧纯源码入口：

```powershell
python -I -B D:\Project\Zhumadian\Application\tools\prepare_native_async_restore_probe.py --application-repository D:\Project\Zhumadian\Application --engine-repository D:\Project\Zhumadian\XNBYEngine --output D:\Project\Zhumadian\work\AsyncProbeSource
python -I -B D:\Project\Zhumadian\Application\tools\prepare_native_async_candidate_source.py --application-repository D:\Project\Zhumadian\Application --engine-repository D:\Project\Zhumadian\XNBYEngine --output D:\Project\Zhumadian\work\AsyncFullSource
```

输出必须不存在、父目录已存在且在两个仓库外。第一入口可加--baseline-controller仅准备原问题函数源码；两版各53源，默认为修正。第二入口在固定PNG2源上应用精确27路径补丁，生成411源。三个实际导出均逐SHA等于相应已编译/实测输入；已有输出拒绝。工具不构建、不启动图形/reader、不复制SDK或GIS、不写当前Git索引/工作分支。

这是开发验收候选，不是新的普通用户启动入口。用户手动体验仍用已交付PNG2三入口，新用户Assets项目不重置；本轮未停止或重启原编辑/网页/业务/公网。可打开本阶段“地景页恢复与细节对照.html”拖动查看实际两张图；它只引用本轮已保存图像，没有在线服务或用户认证。候选未安装无需产品回滚；保留规范full-candidate与原失败证据。未来试装须使用独立项目和退出/回退流程，不能用本轮结果直接替换默认。

## 过程失败与存储

完整源准备的首次边界断言误查main.cpp，实际nativeRetainedPageDrawRanges位于pager.inl；在首次编译前停止，改正检查位置，生产输入不因此变化。首份可复现补丁继承全局autocrlf，将3个CRLF源上下文归一化，git apply --check拒绝，没应用半份补丁；保留原补丁后用显式core.autocrlf=false重生成，同411编译源字节不变，没有--ignore-whitespace放宽门槛。新补丁SHA15a6699766bf3839e13c532b181013a9a23378b5f7d60082fd7516b93be23fc8，27路径实际apply/check及全部411 SHA一致。格式工具既有未知项、getenv等警告如实保留，未修改仓库配置。

源码/执行/合并输入和失败记录逐SHA归档，确认本轮进程终态后，只清本轮work/Temp和三场景重复runtime/私有缓存；规范候选、三张截图/关键stats及原失败资料保留。原离线缓存、Assets/GIS/DLG、0.9.7运行资源、Reference、业务/附件/回滚不动。无数据库schema/字段/索引/状态/归属变更，不重写数据库模型。仅本轮10个纯源码/配方/handbook进入独立评审分支，不传运行包/截图/GIS/业务/凭据，不合并main或发布公网；HEAD/index/27保护保持。
