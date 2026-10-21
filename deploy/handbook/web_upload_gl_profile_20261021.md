# Web上传GL调用CPU分段诊断

日期2026-10-21。本机实验，完整目标active。承接e16f080，不修改原始纹理解码/格式/采样或资源预算。profileSourceUpload仅qa=1&profile=1下，在一次独立staging绘制期间临时包装指定WebGL方法，计量方法内部CPU耗时（包含可能驱动等待，不等同GPU elapsed）。完成/异常后恢复原自有/继承描述符；关闭时不触碰context或clock，诊断失败不重复执行绘制。固定方法集合、仅保留最高和最近慢样本，无无界历史。GL调用计时嵌套在source_upload内，不能重复相加。

474Web测试通过，新增5项：返回/Promise身份、receiver与参数/结果、描述符恢复、原错误保持和只执行一次、不可配置或不可扩展context回退、clock/记录异常不改GPU结果。

W12=Application/work/web_upload_gl_profile_20261021，manifest8b9067f9f80dabd60b4718e34231c9cd570e5601697f767cd6338f1ab07f700a，viewere374e3dc4e4905074e1cd00ee002b402e6c1ee507d4d2e5e65d82f93624c4a42。5840声明文件仅viewer变，外部Data只读。实际RTX5080/D3D11道路218页上传，总1397.2ms/max64.2ms；纹理GL调用总1335.4ms、最大一次texSubImage2D63.8ms，13个>16.67ms纹理样本；bufferData最大4.2ms、program最大0.1ms，无mipmap调用。最高慢样本原始图像HTMLImageElement2137×2001，30830顶点/104094索引。方法名证实峰值在DOM图像纹理传输，不能据此单独确定驱动内部拷贝/格式转换/等待分别占多少。

独立近景早期→道路→总览；道路快照约29.757s，随后停留并回收，包含前期近景41页的uploadGL累计samples259，不能混成259个道路页。道路仍3根/3858445三角形/36draw/held230757468。最终roots/coverage/active/retained0、held1024；service45264/session27976已owner204/exit0，worker closed/保护写0，运行228.235s含停留非加载时间。未重复做严格双轮、冷20秒、原始来源深度或全场景质量验收。

下一步尝试原始PNG异步位图解码，保留原尺寸/无预乘/采样参数；必须验证实际GPU原始像素、透明通道和方向，不能仅凭截图宣布相同。JPEG/BC7与普通资源契约不随意改变。旧25已同步ed5fafc，新14固定载荷仍等已发具体批准；新增诊断仅本地独立提交，不混入旧批准范围。
