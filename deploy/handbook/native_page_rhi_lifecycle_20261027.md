# 原生父页实际 RHI 释放与恢复组件验证（2026-10-27）

目的：推进完整地景合理层级与内存效率。在旧完整场景退休候选未通过运行验收的前提下，将封存的实际退休、身份与绘制门禁函数放入独立真实 RHI 程序，区分“逻辑 payload 已减”“真实子分配已回收”“驱动显存块已归还”。本阶段没有修改或推广生产调度策略，不是20秒全幅清晰度、完整异步父恢复或最终项目验收。

## 固定输入与边界

固定引擎 main 8966e32b370a10b1e8f5d4fba512f42f439c2451，只导出 core/rhi 及两个头文件共42源，不读引擎脏工作区。三份 production 名下的探针输入是20261026 r4封存函数原字节，SHA逐个与原清单相同；只是独立测试的冻结输入副本，不能把该目录名解释为已经部署到产品。加合成测试、CMake及两个shader共49源。旧r4的0xC0000043启动失败保留，本轮没有启动旧候选、原OSGB读取器/生产器/ETW，不读取或复制GIS，也不改已运行体验包、业务、数据库、角色或安全设置。

VS18/v145/SDK10.0.26100 Release构建，只使用既有34个离线缓存包的1738个文件；原包与恢复文件SHA核验，没有网络下载。构建在独立work目录，避开此前临时目录增量漏重编问题。两个不同组件程序均正常退出0，实际GPU为RTX5080，均约0.656秒；不是对同一失败EXE重试。首个4d0fac43验证基本物理生命周期；最终aceb00b9e96c9bda788ad351e598fb8fd48cfedf2eb0859c7af83e4a91d175e1增加共享页及逐轮块上限，最终源25f4a3ecf7986efe912ec66e89ae80e59bd7e51a5068e8a489cf7d29c46d13f1。

## 实测结果

实际创建Vulkan设备、64×64离屏目标、纹理/顶点/索引/描述符、管线，上传128×128红绿蓝合成页，提交后等待真实GPU fence/readback。直接调用封存retireHiddenBasePages、nativePageRestorePlan和nativeRetainedPageDrawRanges，不用虚假RHI句柄替代。

|时点|VMA实际分配数|分配字节|活描述符|VMA块字节|
|---|---:|---:|---:|---:|
|固定目标基线|2|32768|0|33554432|
|父与子都在|8|164144|2|134217728|
|父页退休后|5|98456|1|134217728|
|全部测试页清空|2|32768|0|134217728|

父页退休实际释放3个子分配（纹理/顶点/索引），65688字节及1个描述符；子页每像素仍是同一绿色。仍有上传占用时延后退休；可见父页不退；隐藏且已退休页不会绑定空描述符，若被当作可见页则在绑定前明确拒绝。共享物理页仍有可见兄弟source时保留，两个source都被完整子cut替代后才释放一次，两个子页绿色/蓝色读回正确。

身份校验拒绝像素变化的父页；相同父页通过恢复计划后真实重建资源，红色逐像素恢复。这里实际测试的是身份计划和物理上传/显示，productionAsynchronousRestoreControllerExercised=false：没有运行原完整异步恢复调度器、真实相机往返或多层地景。不能把手动执行物理提交的组件夹具说成完整controller已经通过。

32轮合成页上传→实际绘制→读回→等待→释放，每轮子分配数/字节/描述符都恢复固定目标基线，descriptorFreeFailures=0，块字节不超过已观测128MiB。VMA保留块作复用，最终块仍128MiB，不能说这些块归还给驱动或总显存回到32KiB；也不能把512MiB地景payload当总GPU上限。

运行环境没有枚举到VK_LAYER_KHRONOS_validation，validationLayerEnabled=false；没有安装或调整层配置。正常退出、实际分配与像素断言是本次证据，不能声称Vulkan validation层零错误或覆盖全部API规则。没有截图/人工视觉判定：输入为固定颜色，全部4096×4通道通过原RHI读回逐字节核对。

## 可复现源码与操作

新增tools/rhi_page_lifecycle_probe的7个固定输入、source_manifest.json和tools/prepare_native_page_rhi_probe.py。只准备源码：

```powershell
python -I -B D:\Project\Zhumadian\Application\tools\prepare_native_page_rhi_probe.py --application-repository D:\Project\Zhumadian\Application --engine-repository D:\Project\Zhumadian\XNBYEngine --output D:\Project\Zhumadian\work\PageRhiProbeSource
```

输出必须不存在、父目录已存在且位于两个仓库外。工具只读取42个固定Git blob及7个SHA固定测试文件，原子发布49源和收据；不恢复SDK、不构建、不启动图形/reader、不更改Git refs。实际重新生成49文件与已编译验证输入逐SHA相同；重复指定已有输出被拒且源不变。构建使用该输出根CMake和显式离线CMAKE_PREFIX_PATH、Vulkan_INCLUDE_DIR/Vulkan_LIBRARY、VS18/x64/v145及固定SDK；用已核glslc将两个合成shader转SPIRV。程序参数为vertex.spv、fragment.spv、result.json，另须在自身进程设置HT_NATIVE_RETAINED_PAGE_LIFECYCLE=1。构建/启动命令、依赖与二进制PIN见Document/Deployment/native_rhi_lifecycle_20261027；这些含机器路径的私有收据和运行包不进Git。

这是一项开发侧组件验收，不是普通用户入口。用户继续使用PNG2体验包；停止本探针无需关闭用户编辑器、网页或业务。完整地景候选只有在异步恢复、真实相机往返、多站原始来源/深度/纹理质量和5/20/40秒全幅门槛通过后才考虑默认提升。

## 失败及清理

首轮编译因测试源4处强类型枚举转换失败，未启动GPU；仅修测试转换后构建通过。clang-format22不认识仓库既有SpillCommentBeginsWith选项，格式化先停止，随后仅用工具官方unknown-warning模式保留其它格式规则，未改仓库.clang-format。现有getenv等编译警告保留，不声称零警告。

源码准备依次暴露-I同目录导入、误用仅允许Application/XNBYEngine根的公共发布函数、CRLF替换遗漏os/tempfile导入三项失败，均在写出有效源码前停止。最终补同目录路径、独立限定7文件布局的原子发布及统一新文件行尾；旧公共门禁不改。三份失败源/日志留存，成功收据仅指最终r4工具，不能把它们当产品运行失败或掩盖。

所有GPU/编译进程已终态后，源码和执行逐SHA归档，仅清本轮work/临时源/离线依赖副本。保留小型两组件候选与原失败收据，原离线缓存、用户Assets/DLG/GIS、0.9.7运行资源、业务/附件/回滚不动。无数据库结构/字段/索引/状态/归属变更，不重写数据库模型。完整引擎/独立EXE/网页/天津B/S/H5与迁移清理目标保持active。
