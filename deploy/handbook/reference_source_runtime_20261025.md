# 参考源码构建运行件与部署归档的明确选择

## 发现的问题

此前业务候选沿用共享部署归档的平铺运行件，虽然大多数类规范化后一致，但这不能代表严格使用Reference源码。参考随附包含220个依赖，部署归档含219个；同名共同依赖中6个字节不同，涉及cqweh公共、缓存、MyBatis、Redis、service和web支持。另有鉴权、Nacos、HttpClient等依赖版本或成员集合差异。不得混用仅凭文件名相同的依赖，也不把归档随附配置等同当前原站的实际有效配置。

用原DTO和合成数据实际检查：参考随附包、既有参考源码重编包的OtherWorkFileDock.files序列化为数组，部署归档为字符串；ThirdInfoDock1的companyName在参考/重编中存在、部署归档中不存在；ThirdInfoDock3/4参考/重编的username在部署归档中变成userName。参考与重编的这几项契约一致，部署归档不同。这只是明确DTO契约，不能扩展为全部业务行为等价，也未证明原站正在使用哪个版本。

## 实现

新增reference_business_runtime.py准备器与选择器：固定参考随附包SHA、既有重编包SHA，重新核验766个Java源文件和97个资源输入，在Reference和既有工作副本间全部逐SHA匹配。复用已有源码重编结果的768个class及其220个原配套依赖，不重新复制依赖。通过既有reference_flat_runtime逐项核验应用字节、资源、依赖、清单；新压缩应用运行件为1372608字节，包含私有原资源，只留本地。

prepare生成独立selection.json，内容包含源码输入聚合SHA、应用/运行清单SHA和依赖差异摘要。validate在工作目录内消费显式清单和SHA，再次核对源码、固定归档、全部实际运行字节。坏SHA、错误种类或依赖数、源码清单变化均拒绝。

serve_original_integrated_candidate.py新增成对参数--reference-business-runtime、--reference-business-runtime-sha256。只有明确请求原业务语义时才能选择参考源码运行件；错误参数在创建候选目录、获取持久锁或启动进程之前拒绝。启动结果记录实际业务运行件种类、源码/归档和依赖数；不再用部署归档固定SHA误标来源。未传新参数时继续选择既有219依赖部署归档，不热切当前服务。

## 已完成的验证

21项检查通过：固定参考运行件及默认分支、成对参数和SHA/清单/输入变化拒绝、已有输出拒绝、控制器错误flag在建目录前拒绝、CLI帮助，以及上述5项真实DTO契约。DTO检查只调用已核验的简单DTO构造/序列化和属性元数据，合成空附件列表、合成id，无原业务数据、服务调用、数据库或网络连接。

本轮没有重新构建整个业务应用；复用已核验的同源构建结果。参考随附包与重编包此前仍有45个规范化class差异；其中仅已查看的方法存在字符串拼接编译差异，本轮没有消除这些差异或宣告全行为等价。源版本选择明确，不以指纹或DTO绿色结果代替整套应用验收。

复现准备/校验（输出目录需不存在，清单SHA由实际文件取得）：

```powershell
python -B tools/reference_business_runtime.py prepare --workspace work/tianjin_native_20261023 --output work/tianjin_native_20261023/own-reference-business-runtime-new
python -B tools/reference_business_runtime.py validate --workspace work/tianjin_native_20261023 --receipt <selection.json> --receipt-sha256 <SHA256>
python -B tools/test_reference_business_runtime.py --workspace work/tianjin_native_20261023 --selection <selection.json> --output work/tianjin_native_20261023/own-reference-runtime-check-new
```

## 后续启用与回退

当前own-j11按其冻结旧控制器和部署归档继续运行，不把磁盘控制器源码更新当当前进程已切换。下一独立运行需先观察本轮完整正常退出、持久文件锁释放，再用显式清单选择参考源码运行件；管理文件108字节重启探针仍保留，必须按既有恢复门槛使用--platform-files-recover，不能删标记或复用已消费的旧恢复记录。

新运行件尚未启动整套Spring应用；220依赖下的Spring绑定、共享Redis/JNPF兼容、对象存储、正常登录/角色/业务流程、PC/H5、三维与公网同版均需重新验证。若失败保存真实收据，不能自动改回某些部署依赖后仍标“参考源码版”；需要回退时另起明确标识的219依赖版本，不混合运行件。

原数据、原资源、两UserData、身份/密钥和所有既有未完成修改保留。未改数据库字段/索引/业务归属，无需重生成模型。仅自有选择源码、控制器、验证器、Java DTO夹具和本说明同步Git；原Reference、JAR/class、依赖、选择清单、数据、配置和截图均不入Git。未发布公网，完整天津复刻和长期引擎/EXE/Web/图层/迁移目标active，fullCloneReady=false。


## 参考源码运行件下的原文件服务实测补充

verify_original_file_roundtrip.py增加同一成对的参考源码运行件参数，使用完整220配套依赖和同一已验证平铺应用，不从部署包抽取若干类混用。原默认219分支的固定应用SHA门槛保留；输出须位于工作目录内。错误清单参数在创建目录或启动提供器前拒绝。

实际使用固定已构建MinIO、独立自有回环端口/新临时桶完成48项检查：41字节中文名、51字节PDF测试流、0字节、6291713字节四组合成数据，经参考源码原上传服务、原下载方法和Base64回读均逐字节/SHA一致。3个原文件类实际来自所选固定源运行件，原Java边界保持。51字节流只用于二进制保真，不是可视PDF预览验收。

仅该自有桶/对象删除，签名管理停止HTTP200、Popen自然exit0、无强制。原Spring应用、登录HTTP、页面、历史附件未参与。另2个非法运行件flag和1个CLI帮助检查通过；规范测试入口为tools/test_reference_file_roundtrip_flags.py。测试结束只移除该已结束提供器的自有data目录，14个文件/6306084逻辑字节，D实增6320128字节，日志/class/收据、当前两UserData与密钥保持。

这说明220依赖源运行件的文件服务基础路径实际可用，不代表新版本的完整应用启动、共享Redis/JNPF、真实认证、全业务和手机网页已通过。下一步仍是当前实例正常关闭后启动明确标源版本的完整候选并重新验收。
