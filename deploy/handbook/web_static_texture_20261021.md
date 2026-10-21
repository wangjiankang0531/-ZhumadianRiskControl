# Web 基础大纹理分批上传（2026-10-21）

状态：全量base-level像素核验与正常细层阶段回归通过，实验阶段。完整目标active；不当冷20秒、全区、Web严格双轮或原始OSGB最终场景深度/过滤采样验收。源父7a76f883574812f5d18b9ca6875defb2cf9f1400。

## 问题、实现与保真范围

前次静态几何已按4MiB分批，但4096卫片与8192基础atlas纹理仍分别出现约150/200ms同步上传调用。static_texture_upload使用Three公开Source.dataReady=false配合initTexture预分配原尺寸/原mip存储，再以公开copyTextureToTexture逐原始行区域提交，每批最多4MiB、批间让出一帧；没有Canvas、resize、重新压缩、量化或改UV。4096分16批，8192分64批，全部完成才加入场景。

分块复制期间关闭重复生成mipmaps，最后一次数据复制恢复原generateMipmaps进行完整mip生成；初始化预分配阶段可能额外生成空mip链，未将整个过程声称为只生成一次。完成后恢复source.dataReady与原generateMipmaps，不再次设置needsUpdate，避免首次主绘制重新整图上传。原Texture版本/尺寸、SRGB、flipY、wrap/filter、anisotropy、UV保持最终契约。取消、GL错误或像素不符释放未完成纹理，参考纹理和QA render target在finally释放。

GLTFLoader本已使用ImageBitmap。卫片原先额外加载context_colormatched.jpg并通过HTMLImageElement替换：现在静态专用LoadingManager仅把context.jpg重定向到同一个校色JPEG，避免先取原图再丢弃；其最终wrap ClampToEdge、anisotropy1、SRGB、flipY=false按旧替换路径设置。基础atlas保持原GLTF位图与采样。两者仍是已有派生静态JPEG资源；本轮无新增损失，不把它们当作原始OSGB全部质量的证明。

## 测试与独立GPU参考

完整Web497项通过（新增6项），包含8K全域行覆盖与短尾行、预分配不传图、最后一次复制生成mips、Texture版本和采样保持、独立Source不复用目标GPU存储、取消/GL错误清理，以及独立旧解码像素不符确实失败。32项Python读取/内存存储测试也通过。

QA模式staticOnly=1&textureQA=1：独立参考使用新的Source和单独GPU存储，整图上传后与分批目标通过同一个小render target逐行读取比较；每次两CPU读回数组合计最多8MiB，临时QA target不超过4MiB。参考GPU纹理额外包含完整原mip存储，只在QA存在，不能把QA峰值算作正常模式。没有将目标本身作为参考。

4096卫片采用旧TextureLoader HTML解码的同一校色JPEG作为独立整图GPU参考；8192采用同一原位图的独立整图上传。实测RTX5080/ANGLE D3D11：

| 纹理 | 原尺寸 | 分批数 | 完整核验像素 | 通道差异 | QA单批最大CPU ms |
| --- | --- | ---: | ---: | ---: | ---: |
| 校色卫片 | 4096×4096 | 16 | 16,777,216 | 0 | 2.1 |
| 基础atlas | 8192×8192 | 64 | 67,108,864 | 0 | 2.0 |

共83,886,080像素/335,544,320 base-level字节全比较。contextRedirects1，服务请求日志实际为context_colormatched.jpg。完整mip各级未逐像素读回，只保留原mip与采样参数并按原生成函数从完整base-level生成；最终过滤后RGBA、场景深度及其它GPU/浏览器未据此宣称等价。首版使用相同位图参考已通过，后续增强HTML旧路径参考的最终版本是legacy_reference目录，两个包与证据均保留。

## 正常模式结果及限制

同一最终包关闭staticOnly/textureQA，启用完整LEVEL索引/混合cut、原PNG细层位图路径与原512MiB细层预算。

正常初始采样约36.926秒：contextReady571.6ms、baseReady3292.3ms、baseQualityReady3503.3ms；4096/8192单批max2.1/2.2ms，分配max0.9/0.1ms。render_submit max6.3ms，frameInterval max213.4ms；此前几何分批但整图纹理版本静态采样分别153.2/346.8ms，W14原集中上传494.1/586.8ms。缓存未清、模式/前序不同，不当受控全机同比提速。分批增加等待帧，基础质量ready比前版约2530ms更晚；整体加载速度不能据此声称改善。余峰来自启动其它工作，后续要定位原bin读/解析、质量摘要及异步续体，不能只看主render。

近景采样19根/4,081,056三角形/361draw，仍在渐进加载；没有将它与另时刻21根结果称同画质提速。道路71.586秒：218页上传、单页max13ms/总203.1ms，最终3根/3,858,445三角形/36draw/held230,757,468；完整前沿id/visible/depth/bytes与11覆盖事件字段逐项同W12基线。中景67.904秒：103根/4,014,527三角形/414draw，单页max3.7ms，帧间隔max53.4ms；pending瞬时null不证明全区稳定完成，desired177仍是渐进调度范围。

累计覆盖268/拒绝4/恢复请求1/恢复错误0/gain错误0。峰536,869,332≤536,870,912；返回总览1226细层位图全部关闭，owned0、roots/active/retained/coverage0，细层账本只剩upload_target1024。此预算范围不含既有长期静态纹理/几何、浏览器堆或QA参考GPU存储。

reader44728只启动1次，530次尝试/有效响应全部成功，失败0、未重启；owner正常关闭后nativeExit0、ownerTerminated=false。旧W14首次退出未重现、原因仍未定；新增退出阶段/自然码与清理码诊断详见reader_exit_audit_20261021.md，不把成功回归冒称已查明旧根因。

## 包、体验和运维

最终Application/work/web_static_texture_20261021/legacy_reference/package，5840清单文件，仅viewer与带审计的Python模块相对先前包变化；25 reader EXE/DLL/插件SHA保持相同，GIS、用户图层和数据库未复制改写。identity94b3292659d06766ba749577cf390c6c906fb5558e51e768e7cce510b71dae0b，viewer b4d8992457d0ca18cb85d468baede765ef7ab3435eac3ca3a32dba99395471ac。最终私有--check及原始样本SHA/PNG roundtrip通过，冻结五源码/测试重建viewer逐字节一致。

controller51888/service44856/port54338/session41686已owner204/exit0，workerclosed/自然退出0/保护写0，tabs26/27关闭；首版texture service22092/session63847及reader审计service58352/session42487也终态，tabs24/25关闭。勿重启覆盖验收。用户既有体验服务未动。

手动入口Application/实验入口/地景加载优化_20261020/启动Web地景分批加载实验.cmd，正常完整细层模式，QA逐像素读取默认关闭；未代运行。独立随机端口、owner Job、manual_runs日志和30分钟上限。Ctrl+C/关闭控制台正常清理自有服务。回滚使用旧“启动Web原始位图实验.cmd”或“启动Web基础几何核验.cmd”（后者仅静态），原入口保留。本轮未发布公网、未替换正式版本。需像素复核可在手动服务URL加入staticOnly=1&textureQA=1，并使用页面释放按钮，不能把QA耗时当正常模式性能。

## 后续与文档/Git

设计、阶段验收、部署运维、目标/断点/完成日志同步更新；无数据库结构或归属变化。后续重点：1）有时间戳的20秒与视口外围覆盖/层级验收；2）拆分剩余启动主线程阻塞，评估几何与纹理有限并行以减少等待帧；3）Web严格两轮/更多机位/DPI/全区、原始来源场景深度/过滤RGBA与mip各级验证；4）旧读取退出若再现按审计定位，不自动重启；5）UE引擎/EXE点线面图层/Web业务IAM/261013/252需求/迁移完整目标不变。全部native14 held和既有安全hold保持。

本轮7个纯源码/测试/说明文件仅本地提交。旧25 main ed5fafc已再次核验；旧14镜像固定5d→0925990仍待已发具体授权，本轮不混入、不重复发问。引擎上游master本轮仍da9898f3054f898924dc1637771eb2947e2d5131，无新增merge。
