"""Generate isolated risk-unit schema documentation from an actual empty store."""
from pathlib import Path
from contextlib import closing
import argparse,hashlib,json,shutil,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.replica_risk_units import RiskUnitStore,SCHEMA,SCHEMA_VERSION

def generate(output,publish_source=False):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 model={'schema':'xnby.replica.risk-units','userVersion':SCHEMA_VERSION,'schemaSHA256':hashlib.sha256(SCHEMA.encode()).hexdigest(),'defaultRecords':0,'tables':{},'networkDeliveryImplemented':False,'authenticationTransportImplemented':False}
 concept='''# 全面复刻：风险分析单元库概念模型

本库独立于正式 schema4、演示 schema3 和协同 schema2，只在新候选目录创建，不打开或升级现有用户数据库。源定义为 services/replica_risk_units.py，生成入口 tools/generate_database_docs.py --publish-source。

项目和责任部门限定数据范围；责任人员、部门层级和风险字典来自服务端可信目录快照。提交同时核对稳定 ID 和显示名称，同名不自动猜测，责任人须在所选部门且启用。目录属于外部可信配置，本库没有组织人员表或其数据库外键；正式身份、角色分配和 HTTP 会话接入尚未完成，不能把测试主体当成生产 IAM。

rp_risk_units 保存当前快照、逻辑删除标记和版本；rp_risk_events 按版本保存操作人与策略/目录版本、完整记录和 SHA；rp_risk_requests 以项目、账号、请求键去重并关联当次审计；rp_risk_outbox 与每次操作审计对应，初始 pending。四者在同一 BEGIN IMMEDIATE 事务中写入；任意失败整体回滚，修改/删除使用 revision 防止覆盖并发修改。

原站六项必填为部门、负责人、风险分析对象、风险分析单元、风险等级、坐标。坐标保留文本及显式坐标系（默认待核实），另存经纬度用于范围检索准备；经纬度普通十进制最多 12 位小数，不接收 NaN、无穷或指数下溢。不进行坐标转换，不以默认待核实坐标绘制正式定位。

上级对接只落待发送包，尚无网络投递器、送达确认或五种原 Service 对接协议适配。原接口 Excel xls/xlsx 导入、模板、Excel 导出、地图点选、前端页面联调仍未验收。此阶段不能视为该模块全面等价或公网发布。
'''
 physical=['# 风险分析单元库物理模型','','自动从实际空库 PRAGMA 生成，不含业务行。',f"Schema {SCHEMA_VERSION}；定义 SHA256 `{model['schemaSHA256']}`。",'']
 with tempfile.TemporaryDirectory() as tmp:
  store=RiskUnitStore(Path(tmp)/'model.sqlite')
  with closing(store.connect()) as db:
   for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'rp_%' ORDER BY name"):
    columns=[dict(r) for r in db.execute('PRAGMA table_info('+name+')')];foreign=[dict(r) for r in db.execute('PRAGMA foreign_key_list('+name+')')];indexes=[]
    for idx in db.execute('PRAGMA index_list('+name+')'):
     indexes.append({'name':idx['name'],'unique':bool(idx['unique']),'origin':idx['origin'],'columns':[dict(r) for r in db.execute('PRAGMA index_xinfo('+idx['name']+')')]})
    model['tables'][name]={'columns':columns,'foreignKeys':foreign,'indexes':indexes}
    physical+=['## '+name,'','|字段|类型|非空|主键顺序|','|---|---|---|---|']+[f"|{r['name']}|{r['type']}|{bool(r['notnull'] or r['pk'])}|{r['pk']}|" for r in columns]+['','索引：`'+json.dumps(indexes,ensure_ascii=False)+'`。','','外键：`'+json.dumps(foreign,ensure_ascii=False)+'`。','']
 maintenance='''# 风险分析单元库维护说明

只部署到新候选独立 SQLite 路径，禁止放入静态文件目录。构造器仅接受空库 user_version=0 或精确匹配的 schema1；未知版本、其它表或结构不符均拒绝，不自动修复。SQLite WAL、FULL synchronous、foreign_keys=ON；所有查询和幂等重放重新核对当前项目/部门范围。旧请求回执仅代表当次版本，不能当最新记录。

备份须用 SQLite online backup，将已提交 WAL 一并复制到新目标；不能只复制活动 .sqlite 主文件。恢复先在新路径核对 integrity_check、foreign_key_check、四表逐行内容、逻辑删除及历史/请求/待发送关联，再用受控配置切换；保留原包和原库。测试已覆盖真实 online backup 后的新副本逐行比较，不代表服务器正式灾备演练完成。

审计摘要或请求回执与审计不符时返回 503，保留故障内容，不自动重写摘要。普通删除仅加标记并增加版本，审计及 pending 包保留。pending 不能解释为送达；未实现网络投递，不得手工把状态改为 delivered 作为验收。

发布前仍需正式会话/权限配置、项目组织目录、备份恢复操作脚本与运行监控验收。MySQL、Linux、Apache 和上级真实服务均未验证；本 SQL 是 SQLite 当前结构，不可直接当 MySQL DDL 执行。
'''
 files={'replica_risk_schema_sqlite_v1.sql':SCHEMA+f'\nPRAGMA user_version={SCHEMA_VERSION};\n','replica_risk_schema_manifest.json':json.dumps(model,ensure_ascii=False,indent=2)+'\n','风险分析单元库概念模型.md':concept,'风险分析单元库物理模型.md':'\n'.join(physical)+'\n','风险分析单元库维护说明.md':maintenance}
 for name,value in files.items():(output/name).write_text(value,encoding='utf-8')
 if publish_source:
  target=Path(__file__).resolve().parents[1]/'deploy/database';target.mkdir(parents=True,exist_ok=True)
  for name in files:shutil.copyfile(output/name,target/name)
 return model

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'Document/Database');p.add_argument('--publish-source',action='store_true');a=p.parse_args();m=generate(a.output,a.publish_source);print(json.dumps({'tables':len(m['tables']),'version':m['userVersion'],'sha256':m['schemaSHA256']}))
