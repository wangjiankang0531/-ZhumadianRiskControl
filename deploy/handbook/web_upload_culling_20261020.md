# Web 地景上传预热裁剪状态恢复

状态：2026-10-20本机实验修复，完整项目目标 active。承接 web_indexed_cut_20261020；该阶段的混合层级、原始源SHA/租约、完整cut、2像素覆盖保护和预算保持。

## 问题与实现

旧 uploadSourceModel 为确保预热上传，把所有细层 mesh.frustumCulled 设为false，上传结束没有恢复；此后正常场景渲染继续提交屏幕外网格，增加不必要的GPU工作。本轮提取 source_upload.js，逐网格保存原值，预热时临时关闭，在finally中恢复每个原值、移除临时Scene归属并恢复renderer原target。原值false的网格仍保持false。入口要求模型尚未挂入live scene，避免预热搬走当前画面对象。

恢复成功路径、GPU render抛错、setRenderTarget抛错和已挂live scene拒绝共4项测试，使用真实Three Group/Mesh/Camera/Frustum；恢复后离屏网格重新被实际Frustum判为不相交。全部Web427项通过。没有提高显存预算、减少覆盖检查或改变原始地景内容。

## 精确候选与实际验证

独立包 work/web_upload_culling_20261020/package，5840声明文件，只替换web/viewer.js；不复制GIS或旧UserData。父manifest92fce4ef182616d3bf9f3be676985cffa8c8ce3c147b76b2eac942c4fbc84251；本轮实测manifest a3c581b9f41cc7fc5cba786930b0bd3bcf2078ccad2b584f65ce2c55bb4cd6e3，viewer SHA256 606d18a2e05311968d4e7fdaeb91a00626e41c6eb4b88d098643f5facd0f4219。

实际IAB四站：近100米→中350米→道路10米→总览。近景18根、最高depth7；中景31根、depth7；道路3根、depth6。累计76次GPU覆盖检查、4次缺口拒绝，1次真实恢复、0恢复错误。细层峰536852948字节<512MiB；回总览roots0、active/retained0、coverage目标0、held1024、textures4/geometries2。最后浏览器warn/error日志为空。完整JSON和截图在Document/Deployment/web_upload_culling_20261020。

服务与reader正常owner204关闭，exit0、reader closed、protectedWrites0；整会话141.937秒含多个机位和空闲，不能作为加载耗时。停止后相同manifest私有Python --check通过，私有运行时、Pillow、PNG roundtrip及原始样本SHA正确、转换禁用。

中景截图UI显示39FPS，近景/道路截图75FPS；这不是同硬件固定条件、固定加载进度的配对性能测试，不能据此前阶段9FPS截图量化提速。当前4站也不是严格Web两轮16站或冷20秒SLA验收。原始细层覆盖不足仍保父层，不宣称全部纹理/画面问题解决。

## 手动体验与运维

入口Application/实验入口/地景加载优化_20261020/启动Web裁剪恢复实验.cmd，未代用户启动。私有Python -I -B、回环随机端口、自动打开系统浏览器，每次独立manual_runs，Ctrl+C/关闭控制台停止，最长30分钟owner关闭/Job回收。前两个Web入口和已验收包保留，回滚使用前入口；公网、正式包、EXE、业务数据库没有切换。

本轮精确4文件本地提交：web/src/source_upload.js、web/src/viewer.js、web/tests/source_upload.test.mjs、deploy/handbook/web_upload_culling_20261020.md。源和测冻结于本轮frozen_application并记录SHA；原14held保持，不含GIS、索引数据、运行包、图片、用户库或凭据。旧11授权同步96c2ad02已经远端核验，本轮属于独立新载荷。

## 后续验收

继续做不松覆盖准则的ROI优化、满预算resize回收、父层不可见但后代可见的覆盖桥接、冷启动20秒/全区长稳、Web严格两轮和独立原始OSGB CPU/GPU来源深度、最细8K。此前Web混合cut的7站和本轮4站各有版本，不能合称同版本两轮通过。长期UE/EXE/Web业务/IAM/261013/252实机/迁移目标仍active。引擎master最后复核da9898f无新提交；不能把有限适配称全量合并。
