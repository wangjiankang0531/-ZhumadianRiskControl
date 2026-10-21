# Web 原始 PNG 异步位图实验与验收记录（2026-10-21）

状态：实验阶段，供手动体验。完整项目目标保持 active；本阶段只处理原始 PNG 上传调用耗时。源父提交 4e8ee21f51802b365585227f208d56c42ff6b411。未发布公网，未替换用户正在运行的体验入口，未改数据库、用户图层或地景数据。

## 设计与实现

W12 诊断定位道路纹理 texSubImage2D 同步 CPU 调用最高 63.8ms。原始 PNG 原先经 HTMLImageElement 上传；本版异步 createImageBitmap 解码，显式 imageOrientation=from-image、premultiplyAlpha=none、colorSpaceConversion=none，不传 resize 参数。PNG 来自已有只读原始 RGBA 管线，不添加重采样、压缩或画布转换。选项语义依据 [HTML Standard](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html)。

prepared_source_page 在读取前仍申请原始 RGBA GPU 预算，保持长度/SHA、RGBA PNG 头及尺寸检查、完整父子 cut、2px 覆盖保护、512MiB 账本。flipY=false、SRGBColorSpace、wrap/filter、mipmap、裁切 UV 变换保持原契约；JPEG/BC7 路径保持原实现。浏览器不支持或解码失败时使用已有 HTMLImageElement 回退。

纹理拥有 decoded image；dispose 幂等关闭 bitmap。取消后的位图关闭且不转入回退。SourceFrontier 隐藏页释放识别托管图像，避免纹理 dispose 后再次 close。originalImages 只记录拥有权计数，不能据此推算浏览器进程堆内存或真实显存总量。

## 验证方法与证据

全部 482 项 Web 测试通过；新增 8 项覆盖原尺寸/解码选项、不可用与异常回退、尺寸不符、异步取消、开始前取消、旧解码失败、重复 dispose，以及真实 SourceFrontier 隐藏页释放。

独立 QA 模式 ?qa=1&profile=1&bitmapQA=1 跳过地景 boot，建立专用 WebGL2 上下文，逐个纹理上传、附着 framebuffer、readPixels 后释放，最终 loseContext。支持 CPU 参考清单输入，最多三个实际样本。tools/prepare_original_image_qa.py 只接受显式 loopback/匹配的只读 runtime identity，从带租约的实际 PNG 校验长度/SHA，再用私有 Python Pillow 解码整幅 RGBA 并计算参考 SHA；finally 释放租约，不落地图片。

本次真实根页 1024×512、真实 family 页 1024×1024，以及 9×7 合成方向/透明度图（54 个非完全不透明像素）共 1,572,927 个不同样本像素。旧 HTML 与新 bitmap 在 RGBA8、SRGB8_ALPHA8 两种格式下，完整 base-level 纹理读回均与独立 CPU RGBA SHA 相同，逐通道差异为 0，拥有图像最终 0。两个实际样本均不透明。证据 web_original_bitmap_pixels.json/png 和 cpu_rgba_expectations.json；未把这三个样本扩展为全 GIS、8K、所有浏览器或最终过滤后场景/深度等价。

实际 GPU：RTX 5080 / ANGLE D3D11。相同道路机位与 1280×573 视口，旧新各 218 页上传；436 次 texture 分组调用包括 texStorage2D 与 texSubImage2D，不是 436 页。最终 3 根的 id/visible/depth/bytes、3,858,445 三角形、36 draw、held 230,757,468 bytes 相同，11 次覆盖事件的 loss/parentPixels/region/尺寸/阈值逐项相同。

| 道路指标 | W12 HTML 基线 | W13 bitmap |
| --- | ---: | ---: |
| 218 页上传合计 CPU ms | 1397.2 | 206.1 |
| 单页上传最大 CPU ms | 64.2 | 11.0 |
| 纹理 GL 调用合计 CPU ms | 1335.4 | 155.9 |
| 纹理 GL 调用最大 CPU ms | 63.8 | 10.7 |
| 超过 16.67ms 的纹理调用 | 13 | 0 |
| 帧间隔最大 ms | 53.3 | 26.8 |

这是方法内同步 CPU 时间，可含驱动等待，不是纹理 GPU elapsed。OS 缓存未清、前序近景停留不同、没有固定完整加载 trace，不能作为冷 20 秒 SLA 或全场景同比提速。旧/新道路采样约 29.76/28.92 秒；W13 中景约 60.86 秒，130 根时仍 pending family，是阶段回归而非加载完成：310 页上传 max1.5ms，frameCPU max11.8ms、帧间隔 max26.7ms。前序近景回归 28.37 秒仍在加载，383 页上传 max5.5ms。初始基础场景 render_submit max321.3ms、frameCPU max322.2ms、帧间隔 max426.8ms，启动长帧仍待单独处理。

全程创建 1370 位图，HTML 回退 0，拥有峰 414；总览后全部 1370 关闭、owned0。累计覆盖 298 次、拒绝4、恢复请求4、恢复错误0、gain错误0；拒绝时保留完整父层。总览 roots/active/retained/coverage 为0，预算仅 upload_target1024；峰536865864≤536870912。中景/近景并未宣称画质或全区加载验收完成。

## 打包、运行与回滚

独立包 Application/work/web_original_bitmap_20261021/package，5840 个 manifest 文件；从 W12 逐文件校验复制，仅 web/viewer.js 的 manifest 记录改变，GIS 与 UserData 未复制。package identity f562447ac0898f866af728b021c59a4ea2e695ce1e373c8e9ef6f942eed3f6af；viewer SHA f0e96916f6c43e2f6956645f2c233fb2457469e2c899ad06f634428750ce16ed。

本轮 controller30840/service42752/port51980，session67898；所有者 API 正常关闭204，控制器 exit0，服务终态 stopped，worker closed、protectedWrites0；用户另一体验服务未触碰。最终私有 --check 通过（Python3.12.14/Pillow12.3.0/PNG roundtrip/原始样本 SHA），converterEnabled=false，冻结 8 个源码测试工具后重建 viewer 与已验收包逐字节相同。

手动体验：Application/实验入口/地景加载优化_20261020/启动Web原始位图实验.cmd。未代运行；每次独立随机端口、所有者与 manual_runs 日志，最长30分钟，通过 Ctrl+C/控制台结束会清理自有 Job。实验不自动替换旧入口，回滚可使用旧 Web 视口预算或覆盖扫描线入口。需要像素复核时，在本轮手动服务地址使用 QA 模式，先以私有 Python运行 prepare_original_image_qa.py --base http://127.0.0.1:实际端口 --identity 实际identity，将输出填入页面后执行核验。不得将旧端口/租约用于新会话。

## 文档、Git 与下一步

设计/阶段验收矩阵/部署运维/目标/断点/完成日志同步更新，无数据库结构变化。已批准旧25文件 main=ed5fafcff91e77fa5ba78fb292e3f921184d8ccf，本轮再次远端复核相同。此前已发具体授权的新14镜像 source5d541eb→0925990 仍待答，本次9文件不混入该镜像，仅本地提交。自动审批此前要求新增源码载荷与 main 目的地具体授权；不是本轮再次推送被拒。引擎上游 master 本轮仍 da9898f3054f898924dc1637771eb2947e2d5131，没有新提交需要 merge。

下一步优先针对原始启动长帧与冷20秒/视口外围层级覆盖建立可重复验收；完善不同窗口/DPI与更多相机的预算恢复、Web严格双轮、原始来源深度/过滤采样和8K。EXE点线面标注与图层、Web业务/IAM、261013/252需求、引擎UE对标及目录迁移完整目标保持；全部 native held 与既有安全 hold 保留，不把本阶段标为最终交付。
