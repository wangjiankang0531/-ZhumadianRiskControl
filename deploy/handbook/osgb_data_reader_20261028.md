# OSGB v80 纯数据读取与完整内存页验证（2026-10-28，实验阶段）

记录时间2026-10-28T02:31:32.893499+08:00。此前48个相机正权重缺口的原GIS已证明完整，但运行预览没有合格细层载荷；本阶段直接从原字节建立可审查的读取路线，不恢复、重编译或运行任何held原生读取器/隔离程序，不调用OSG DLL，不修改旧缓存准入。

独立Python解析器按公开OSG序列化布局读取little-endian、Scene类型、版本80、无自定义域/动态schema/二进制括号且未压缩的明确子集；只接受Group、PagedLOD、Geode、Geometry、StateSet、Material、Texture2D及内嵌JPEG。未知版本、类、结构、引用、越界/非有限数组、截断/尾随数据都失败，不跳过后继续给部分几何。名称原字节保留，类名和引用严格解析；内嵌图片名绝不作为外部路径读取。

全48区块6277文件1209845900B完整结构解析，约27.390s，全部消耗到尾；11038个几何/图片对象，顶点数、三角形数、完整几何范围、子节点引用均与封存原生LEVEL索引一致。这里证明这批实际数据可解析，不宣称通用OSGB支持，也未为全部后代执行新内存帧/材质适配；未知特性仍拒绝。

第三级前沿48节点原字节24990668B，48根/198原网格进一步通过PinnedOSGBDataReader、原有内存帧校验器及完整SourceForest页面构建器：382346三角形全部保留，完整前沿、数组、原始float32 XYZ/UV/uint32索引、原采样wrap以及P90边长/纹理密度均核对。纹理仅原JPEG解码后按OSG JPEG插件bottom-left行约定翻行，未重采样；封装PNG回读与本次解码的原RGBA逐字节一致。不是与历史原生JPEG解码结果逐字节比较，不宣称已做GPU逐像素质量验收。

正式固定读取器对Data根、tile/name、源大小/SHA、链接、读取前后内容、当前Python实现及Pillow图像/JPEG插件/codec文件SHA作校验。拒绝自定义回调、继承/遮罩状态、非白材质/附加颜色、非逐顶点绑定及未支持的采样；不为了通过而丢弃这些语义。内存帧仍复用既有parse_frame验证和原像素页面协议，不伪造旧native生产者证明。

正式读取接口批次约7.453s，累计编码交付字节125084076（约119.29MiB）、最大单根5824772B；仅RAM生成，持久化资产0B/原GIS复制0。该离线时间不含真实HTTP等待、GPU上传及画面验收，不能承诺浏览器7秒或20秒全幅。Pillow12.3.0/JPEG8.0，固定本批recipe 1a21796a23588383c22a4c0393be9c6dde2c60663b4fdd2994a98e928c377503。

本地及16文件独立源码副本各66项检查通过：新增18项含每个截断前缀、非法类/版本、NaN/Inf、索引/UV/颜色、采样边界、JPEG行方向/负零原位、非UTF8图片名不读外部文件、源SHA/大小/路径/源码变化拒绝与无子进程；其余原帧/页面/指标/alpha/有界RAM回归保持。独立副本使用当前依赖快照，不能扩称干净Git重建或实际WebGL通过。

首轮把所有OSG字符串假定UTF8，在内嵌图片名遇非法UTF8时拒绝；核对官方std::string字节语义后只对对象名/内嵌文件名保留原始字节，不用于外部IO；类名/引用不放宽。参考源首次.cpp路径不存在，改读实际官方.h，仅文本参考，不运行下载代码。

当前体验63393及65363/65258/50115/60297/18891均HTTP200，全部566既有marker和3原DLG/台账大小mtimeSHA保持；27保护文件/正式HEAD/index不改。新读取器未接任何现用服务，未改变公网/252/8767、角色、数据库或业务记录。运行版48载荷缺口仍记未解决，尚无新HTTP租约、取消/释放或浏览器GPU证明；完整UE/EXE/天津B/S/H5/20秒全视口目标active。

下一步以明确opt-in接入有界RAM计划/载荷/租约，再独立验证48区块加载、同机位5/20/40质量、取消恢复和整个预算；默认入口不直接切换。旧87已同步d89，旧aee索引4文件授权未变，本轮新源码仅本地、不push、不扩范围。

格式依据（只读取公开格式与原始字段语义，独立实现Python；参考文本保留在私有证据归档）：

- https://github.com/openscenegraph/OpenSceneGraph/blob/OpenSceneGraph-3.6.5/src/osgDB/InputStream.cpp
- https://github.com/openscenegraph/OpenSceneGraph/blob/OpenSceneGraph-3.6.5/src/osgPlugins/osg/BinaryStreamOperator.h
- https://github.com/openscenegraph/OpenSceneGraph/blob/OpenSceneGraph-3.6.5/src/osgWrappers/serializers/osg/Geometry.cpp
- https://github.com/openscenegraph/OpenSceneGraph/blob/OpenSceneGraph-3.6.5/src/osgPlugins/jpeg/ReaderWriterJPEG.cpp
