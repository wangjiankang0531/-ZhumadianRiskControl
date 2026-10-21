# 本地门户误连旧三维版本与企业图层恢复（实验阶段）

用户截图为127.0.0.1:8767，实际使用Packages/versions/0.9.7的Web0.8.5，main选择revision4、旧细层16根上限；其数据绑定Assets/DLG/驻马店图层.json仅含“道路”的两个点。企业原文件未丢失。另一个问题是主页“进入园区一张图”将URL.search整体清空，导致新入口的levelIndex/levelCut参数也被删除。

源码修复：本机HTML可用meta[name=xnby-local-command-url]显式指定本地commandURL；仅127.0.0.1/localhost且非public-business采用。URL仍只允许HTTP回环/根路径/合法端口、固定topic与mode，另外仅允许成对levelIndex=1&levelCut=1，无凭据/片段/额外token。园区入口仅删除topic/mode，保留索引参数。公网部署不采用本地HTML覆盖，不转发登录数据。

实际61058本地预览已备份后只更新HTML与JS。JS使用e66254d历史门户源码快照，加本轮3个入口模块改动编译，保持0.8.7前端/后端搭配；未将当前0.8.10业务代码混进旧服务。回滚：恢复work/web_entry_recovery_20261021/portal_backup内同名两文件；刷新门户即可。未改公网服务器、业务数据库、原8767版本及原企业数据。

新入口http://127.0.0.1:8768/?topic=emergency&mode=command&levelIndex=1&levelCut=1，包固定为W18 identity f6a5758586635b70025773c3e40083e0c51c7bc01cc02db74cf491233dd7293a。由tools/launch_indexed_web.py显式校验package/identity、独立端口、owner ready PID与HTTP identity后展示。仅持有自己创建的Job，禁止自动重启或替换其它端口服务。--stop-state再次核验HTTP PID/identity后仅发送该owner停止请求。8769独立生命周期验证owner204/exit0/保护写0；用户8768保留运行，当前controller52592/service45700，状态work/web_entry_recovery_20261021/validation/runtime.json。旧8767仍保留，避免停止用户服务。

浏览器端已从实际门户点击进入8768，验证14家企业（5/3/3/3分类）、14条发布本地台账、应急14/全部16；企业图层详情显示5个点标注，可总览查看全部企业标牌。数据仍标“资料估算点位/厂界与位置待核实”，未伪造应急资源。新页近景实际25/31根、约501MiB；截图只是当时画面，不是固定20秒达标证明。

入口与参数9项测试通过，完整Web513项通过。固定包私有Python/Pillow/PNG与原样本SHA预检通过。停止/重开用同一固定包与新状态文件；端口冲突必须报错，不能悄悄回退旧8767。复制验收目录到另一机器时先核对Data只读绑定和依赖，不能仅复制快捷方式。

证据Document/Deployment/web_entry_recovery_20261021，包含两个入口href、回滚文件路径及SHA、企业图层/标牌截图、完整测试日志和生命周期终态。此轮解决错误版本/图层绑定；外围清晰度仍未通过，后续继续按九宫格质量和退层验收。旧14文件mirror09259909已获用户授权并push/fetch/14blob全同；本轮及W9后续源码仍本地，不能声称已同步main。上游查询本次凭据读取失败，不能声称没有引擎新提交。
