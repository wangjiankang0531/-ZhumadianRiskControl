# 天津全面复刻研发与验收基线（2026-10-22）

用户明确要求原站界面和功能全面复刻。已发布R2只是部分PC/H5协同业务，不能视为该目标完成。完整基线见项目Document/Design/天津原站界面与功能全面复刻基线_20261022.md。

本阶段新增只读工具`tools/audit_tianjin_full_reference.py`与两个聚焦测试。调用：

```powershell
python -B -X utf8 tools/audit_tianjin_full_reference.py --reference D:/Project/Zhumadian/Reference --out <独立本地证据目录>
python -B -X utf8 -m unittest discover -s tools -p test_audit_tianjin_full_reference.py -v
```

工具只读取逻辑源文件和DOCX文件元信息，不运行参考代码、不加载.env或application配置、不调用来源服务器；输出源文件SHA、页面及组件字段按钮/绑定/事件/导入/API线索、控制器映射、实体字段与630行初始未验收矩阵。当前索引四前端630个页面/子组件，766个Java文件、86控制器、112表实体、9份DOCX。计数是检索范围，绝不是完成比例或菜单数。API正则/静态图不能替代动态菜单、运行行为、权限与事务的人工核对。

原站通过已登录UU只读核对，当前已有59处菜单/页面/页签/滚动分区记录。截图及完整源索引仅本地Document保存，不提交Git；不复制源账号、签字、个人资料或真实业务记录到驻马店库。不根据GET方法自动调用接口，部分参考GET有删除/上报副作用。

后续以原专有组件与Controller/Service/Mapper为依据，按每一业务域同时完成界面和后台；导航/表单/权限/状态/关联/Excel/附件/打印/统计/PC-H5均逐项验收。JNPF/设备/视频/地图等依赖逐项确认和适配，未实现明确报错，不能空成功。先独立候选验证，再备份部署，不把局部测试版标全量复刻。

本轮没有产品数据库结构或部署变化；新结构实际落地时同步数据库模型、生成器和备份恢复回归。未验证的作业票R3草稿已隔离保留，R2源码恢复，现网仍0.9.0-public.1。完整引擎/EXE/三维目标仍active，原held文件保持。
