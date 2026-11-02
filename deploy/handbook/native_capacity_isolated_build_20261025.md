# 千图层修复的隔离完整构建与单次EXE校验

2026-10-25。本阶段补齐前一千图层源码候选“完整编辑器尚未构建”的缺口。完整Release编译与链接退出0，新EXE已执行一次纯文档校验并正常退出。图形界面、GPU地景、实际编辑操作和目标机仍未验收，未替换250/252或公网。

## 固定输入与隔离方式

应用固定Git提交f5704147137a076d4064e87c1e0d1e51178e26d7，引擎固定提交b89578afd4374ae30c6a5ca0c16e26183026efd1（与此前核对的远端引擎内容树一致）。只导出应用native与CMake，以及引擎构建所需代码/头文件/CMake/着色器源码，共390文件、3608093字节；逐Git blob核同，仅叠加本轮native/landscape_document.hpp与landscape_editor.inl两个容量修复文件。

原14项应用held修改没有作为工作树源码编入，engine工作树的asset/CMake、测试及未提交BC7/分析等实验也不消费。源码导出使用固定Git对象；所有路径、SHA和两个覆盖文件在isolated-source-manifest.private.json中。GIS、Reference、用户图层和业务库未复制。

## 开发依赖缺口与恢复

首次CMake配置因Windows反斜杠进入try_compile的缓存字符串失败，保留configure-result；改正为正斜杠后，发现原备份依赖目录保留配置/头文件而开发lib缺失，SDL2配置引用SDL2.lib不存在。不是将该错误当源码修复成功。

本机安装记录的37个准确ABI都能匹配D:/DevCaches/vcpkg/binary-cache既有ZIP。核验CONTROL包名/架构/ABI及档案SHA，跳过spirv-tools、glslang、shaderc大型包、PDB和EXE，仅在新隔离dependencies恢复1738个必要文件共123743016字节，原备份未改。继续配置时缓存SDL2_DIR仍指向旧前缀，再只清除该明确键，第四份配置结果退出0；前面三份失败记录全部保留。没有网络安装、版本升级、修改认证或恢复整套GIS。

## 完整构建与产物

CMake Visual Studio 18 2026/v145、MSVC19.51、Windows SDK10.0.26100.0，Release目标xnby_zmd_editor，两个并行构建任务，MSBuild节点不复用。应用与相关引擎库全部从上述隔离源码重新编译，编译/链接退出0，实际用时约124秒。存在原有getenv/u8path等编译警告，完整日志保留，不声称无警告。

新EXE大小3017216字节，SHA256：79bd5f24bd844db59e29dd96de74bf92c468dd3f942545ba385fd8a52c1511c7。静态dumpbin核对EXE及9个传递运行库共10个PE，均AMD64，未解析非系统导入0；Windows系统/API-set仍依赖目标Windows，静态检查不证明所有机器加载成功。必要DLL分别来自同ABI缓存及现有冻结包清单核同的Microsoft CRT，现有版权文件一并收集。16个EXE/DLL/版权文件共7523044字节，另有小型候选说明与元数据。

候选位于work/native_capacity_isolated_build_20261025/candidate。候选清单保留最初静态检查清单SHA，后续新增纯校验结果；原静态记录和执行前计划不重写，不将“尚未启动”历史阶段误作当前状态。没有给当前默认选择创建新快捷方式。

## 新候选一次纯文档执行

核对main中--validate-layers分支在图形运行入口前返回后，先准备明确计划和已核SHA的1000层合成文件，再使用新EXE与自己的输出目录执行一次，15秒时限，不重试。实际退出0、约0.312秒，输出LANDSCAPE DOCUMENT VALIDATION PASS；保存后的完整JSON结构与输入相同，输入SHA、候选文件SHA和14held均未变。

文件包含隐藏/锁定层、首末层标注、点自定义图标、线型/宽度/独立透明度、凹区域与标牌数据。该结果证明这份1000层文件在完整EXE的文档分支中可往返，不证明每项UI操作、千层帧率或任意文件兼容。0.312秒包含该次进程启动与文件处理，不能当三维首屏/交互200ms指标。

没有执行旧0.9.7、原读取器、ETW、截图或GPU场景；旧0xC0000043失败证据SHA仍1d4a825ea688065e1840987ad3418c4badfdd8364ade8c50c2e5f7bbbc51edf7，原因仍未知，不能称旧故障修复。新候选的成功不覆盖旧失败。

## 重建与部署步骤

在无held修改的隔离源码树中准备Application和XNBYEngine，按上述固定提交与两修复文件SHA核对。已有完整ABI开发依赖前缀时可直接使用；本机被清理过的旧前缀不能当完整安装，需按dependency-restore-plan.private.json从本机缓存恢复到专用临时前缀。避免直接在当前混合工作树构建。

使用既有CMake和x64 MSVC，参数采用正斜杠：-S <隔离源>/Application、-B <新build>、-G "Visual Studio 18 2026"、-A x64、-T v145、-DCMAKE_PREFIX_PATH=<完整依赖前缀>、-DFETCHCONTENT_FULLY_DISCONNECTED=ON、-DHT_BUILD_TESTS=OFF、-DHT_BUILD_RENDER_REGRESSION_TESTS=OFF。Vulkan_INCLUDE_DIR、Vulkan_LIBRARY、STB_INCLUDE_DIRS、TINYGLTF_INCLUDE_DIRS、GLSLC路径按实际依赖前缀显式设置；完整已执行命令在configure-r4-result.json。生成后用cmake --build <build> --config Release --target xnby_zmd_editor --parallel 2 -- /nr:false /v:minimal。不要把Debug/旧ABI库混入。

后续正式交付还需绑定现有只读驻马店资源、形成明确运行包清单，做受控图形启动、真实点/线/面编辑、显隐/锁定/移动图层、保存重开、Web发布与250/252验证。当前目录不含GIS与用户DLG，尚不是完整便携包，也未更改Packages/active_release.json或现有用户服务。

## 存储、Git与验收

预留临时峰值2GiB，实际构建生成138337434字节；连临时开发依赖共清理262080450字节（逻辑大小，约250MiB）。先确认构建进程已终态、候选文件SHA全部核同、依赖文件集合/SHA完整、目录无重解析点且位于专用根内，再由同一PowerShell清理build与dependencies。保留候选约7.2MiB、隔离源约3.4MiB、日志/清单与本机原缓存；未为清理新建大备份。物理磁盘变化不作精确归因。

本说明作为新增本地handbook候选，既有容量4文件和SDK诊断2文件保持；Application HEAD仍f570414。待授权10文件镜像8fa1a840仍未推送，9文档SHA、14held与原生旧失败记录均核同。未向Git发送运行包、DLL、原SDK、GIS、业务数据或私有构建清单。

编译、静态依赖和单份纯DLG执行已验证；完整EXE/Web交付、地景20秒外围质量、天津已登录流程与历史附件、全部应用和UE长期目标仍未完成。
