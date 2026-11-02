# BC7小mip分区编码实验阶段（2026-10-27）

现用LOD预览仍为http://127.0.0.1:65357/ ，近景29根约508MiB；本阶段未把压缩纹理接入场景或公网。中远景完整清晰仍未通过，实验工具不能作为LOD问题已彻底解决的证明。

在已有Mode1/6上增加显式mode0-1-2-6配置：面积≤262144的小mip搜索Mode0三分区16布局、Mode2三分区64布局，保留Mode1/6作为基线，只在拟合RGB平方误差降低时替代。RGBA在内存，固定原JPEG SHA，完整mip逐级Pillow独立解码，仍要求40dB/P99≤16/最大误差≤96。任何一级失败，整图accepted=false，不能进入GPU验证或纹理仓库。边缘复制参与块拟合，逐块不回退回归针对完整块；非完整边缘最终仍以真实尺寸独立解码质量门槛控制。

另提供显式mode0-1-2-3-6配置，在面积≤16384的极小mip尝试Mode3的64个两分区、高精度端点和2位索引。原mode0-1-2-6默认不启用Mode3，原mode1-6配方仍可使用。三图v2最低PSNR与v1相同，未将“增加模式”描述为实际画质验收成功。

固定三图结果：

| 原根 | v3两模式最低PSNR | 新三分区最低PSNR | 新完整链结果 |
| --- | --- | --- | --- |
| 141 | 38.5095dB | 38.8890dB | 失败，5/6/7/9级低于40dB |
| 96 | 39.6409dB | 40.0565dB | 通过 |
| 345 | 41.4297dB | 42.5579dB | 通过 |

低mip像素本就很少，单一全图PSNR不能被其它大mip平均掩盖。141的P99/最大值虽在门槛内，PSNR仍失败，保留失败状态，不调低40dB以放行。Mode3后复测三图相同最低PSNR；96/345的Mode3版本仅保存质量报告，不另写重复压缩载荷。

数字分区及明确A32/A33表来自[Khronos BPTC格式表](https://raw.githubusercontent.com/KhronosGroup/DataFormat/main/bptc.txt)，SHA c4d68c53a07464bc546cc4a584a6fd1a605d10b79e675bc9bc4f78e28b29482f；各anchor实际归属及标准partition6/index9示例均核对。[Microsoft模式参数](https://learn.microsoft.com/en-us/windows/win32/direct3d11/bc7-format-mode-reference)。新增Mode0的16布局、Mode2的64布局、Mode3的64布局，共144布局均与Pillow和独立参考解码逐字节一致。最初Mode3回归64次错误来自Python参考漏读4个P位，原失败与修正前参考单独保留；修正后全过，没有放宽编码质量或修改Pillow结果。

最终Python15项、Node5项共20项通过。新测试覆盖144格式布局、明确anchor、标准示例、混合完整块平方误差不回退、实际新模式被选用、确定性、非二次幂边缘不透明；既有完整mip源SHA、大小/alpha边界、报告不发布及GPU拒绝失败清单继续通过。

一次独立RTX5080 WebGL2实测新v1合格96样本1552×1560、11级、3,230,032字节；载荷确实含Mode0/2。11级GPU渲染读回SHA全部与Pillow一致，GL清理0、自有GPU对象释放，console警告/错误0。只证明BPTC UNORM+NEAREST+RGBA8单图字节解码，不代表SRGB场景外观、全场景显存/加载效率或Mode3实际显卡覆盖。自有43164/59246服务120秒正常退出、测试标签关闭。用户65357/业务18891保持200，未重启或切换。

运行测试：`node --test tools/test_bc7_mode6_encoder.mjs`；tools中`python -B -m unittest test_bc7_three_subset_encoder test_bc7_opaque_encoder test_bc7_gpu_probe`。准备工具只接受显式profile、固定SHA、新输出目录和既有Node；report-only不发布载荷。GPU服务仅接受全部级别合格且逐文件/逐mip SHA正确的完整链，限时绑定回环，不自动修复失败清单。

下一优先：为141等低mip多方向颜色研究独立通道编码（Mode4/5）或经完整预算/着色器边界验证的RGBA尾链保真回退，不能用大mip均值掩盖低mip失败。样本全链通过后，再发布只读纹理索引并接场景，实际比较同相机中景5/20/40秒、SRGB、512MiB峰值、移镜取消和父层保留；阶段内未完成这一步。

源码仅本地检查点，未推远端、未改公网或252。原始GIS、源JPEG、用户DLG/JSON、正式HEAD/索引及27保护文件保持；原生360隔离/读取器限制保持，没有恢复/重编译或运行原生编码器。设计/部署/使用/验收配套记录已更新，源与执行先归档逐SHA核验，再清自有临时副本和两份失败141载荷。现用work/native_rectangular_resources_0_9_12为运行依赖，不能按旧重复计划删除。
