# Web 启动诊断实验（2026-10-21）

源父24006167，完整491 Web测试包含后续分批候选。独立诊断包69d790207f0d290c5febf0ff15d386d0a1b1b06e802d247c6d63bad1375836d1，仅qa/profile前30秒有界记录静态渲染GL同步CPU。实际首次基础绘制493ms，其中buffer292.5ms、纹理200.5ms；卫片纹理152.1ms。不是GPU elapsed。

该诊断的读取子进程第一次有效响应前stdout关闭，后续held拒绝26计划；不算细层回归，不据requests0断言握手阶段或退出根因。服务7412/session86311已owner204/exit0。完整证据和修正版分批实现/限制见web_static_upload_20261021.md及Document/Deployment/web_startup_profile_20261021。不得重启覆盖原证据。完整项目goal active。
