# wwwroot公网部署规范

当前项目根C:/inetpub/wwwroot/Zhumadian，应用根Application，IIS指向Application/iis。runtime是包内运行环境；payload/frontend/tools是应用代码；private和UserData受保护。Application末级名称保留，以满足原版平台/事务/Finding根范围守护。旧C:/Zdm已经删除。

平台JVM临时目录为UserData/TianjinOriginalPlatform/t<运行数字>，业务为UserData/OriginalServer/runs/j<运行数字>/b/t，位于各自私有范围，最长79字符，原80字符限制保持。保留原Java/业务类与载荷/回调清单；本方控制器增加实际存储接口和桶就绪门禁，状态码及次数诊断不记录凭据或桶名称。

IIS只代理公开入口，阻止private/UserData/runtime/发布清单直接访问。5私有路径HEAD验证404且不读正文。仅驻马店映射更改，其余11映射保持。业务库/对象存储/平台文件/配置原卷移动后身份和元数据一致，没有另建一套数据。

发布与恢复使用新根。本次目录迁移备份和运行日志继续保留；不要用旧路径常规回滚脚本跨布局恢复。FTP退役上传记录归档在UserData/DeploymentArchive/ftp_20261030，48文件完整保留；当前/回退包与完整安装基线仍保留。归档不视作磁盘空间回收。OS重启自启未验收。具体实际记录见部署结果与原固定R17d清单。
