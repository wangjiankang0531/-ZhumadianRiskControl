"""Generate isolated demo DB physical schema and portable MySQL target DDL."""
import json,sqlite3,tempfile,sys,hashlib
from contextlib import closing
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.reference_demo import SCHEMA,MODULES,DemoStore

def generate(out):
 out.mkdir(parents=True,exist_ok=True);manifest={'scope':'isolated synthetic demo only','version':1,'schemaSHA256':hashlib.sha256(SCHEMA.encode()).hexdigest(),'modules':len(MODULES),'initialRecords':12*len(MODULES),'tables':{}}
 rows=['# 模拟业务库概念与物理模型','','本文件由 tools/generate_reference_demo_docs.py 根据实际SQLite结构生成。','','此库只保存合成验收数据。它与正式业务库 issues/events/requests 及 DLG 空间业务库分开；不能作为生产业务域建模已完成的证据。','','概念关系：业务模块（entity）包含多条模拟记录（entity,id）；记录以 revision 乐观并发控制，状态推进与逐版本处理事件处于同一事务。记录负载保留模块字段字典，便于继续对照参考页面。真实身份、权限及各业务专有约束仍在既定正式服务范围继续研发。','']
 mysql=['-- Synthetic demo only; MySQL target preparation, NOT MySQL-server validated.','SET NAMES utf8mb4;']
 with tempfile.TemporaryDirectory() as temporary:
  store=DemoStore(Path(temporary)/'demo.sqlite')
  with closing(store.connect()) as db:
   for table in ('demo_records','demo_events'):
    columns=list(db.execute('PRAGMA table_info('+table+')'));indices=[];definitions=[]
    rows+=['## '+table,'','| 字段 | SQLite类型 | 非空 | 主键序号 | MySQL目标 |','| --- | --- | --- | --- | --- |']
    types={}
    for c in columns:
     name=c['name'];kind=('INT UNSIGNED' if name=='revision' else 'VARBINARY(128)' if name in ('entity','id') else 'VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin' if name in ('enterprise','state','kind','date','at') else 'LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin');types[name]=kind
     rows.append(f"| {name} | {c['type']} | 是 | {c['pk']} | {kind} |")
     definitions.append('  `'+name+'` '+kind+' NOT NULL')
    primary=[c['name'] for c in sorted(columns,key=lambda x:x['pk']) if c['pk']];definitions.append('  PRIMARY KEY ('+','.join('`'+x+'`' for x in primary)+')')
    if table=='demo_records':definitions.append('  KEY `demo_query` (`entity`,`enterprise`,`state`,`date`)')
    else:definitions.append('  CONSTRAINT `fk_demo_record` FOREIGN KEY (`entity`,`id`) REFERENCES `demo_records` (`entity`,`id`)')
    definitions.append('  CHECK (JSON_VALID(`payload`))');mysql.append('CREATE TABLE `'+table+'` (\n'+',\n'.join(definitions)+'\n) ENGINE=InnoDB;')
    manifest['tables'][table]={'columns':[dict(c) for c in columns],'mysqlTypes':types};rows+=['','payload 为UTF8 JSON，时间统一UTC ISO8601；所有状态推进与新增均以事务写入，并追加事件。','']
 rows+=['## 维护与迁移说明','','默认库：候选根目录 Assets/Demo/reference_demo.sqlite；仅绑定127.0.0.1的8791端口。程序重启保留新增/已处理数据，种子按模块及ID去重；字段扩展追加事件，不删除旧字段。','','备份应使用SQLite在线backup，或者停止服务后复制sqlite及其配套WAL；不要在运行中只复制主文件。备份/恢复已在单元测试中实际核对。不得用此库覆盖正式业务或用户DLG库。','','Linux/Apache：Python服务与静态文件均无Windows专用依赖；Apache可通过同源反向代理托管。Windows快捷方式仅用于本机测试入口。真实Apache部署、HTTPS、身份适配、MySQL驱动与事务并发尚待环境验收。目标DDL不等于MySQL已运行；迁移需导出独立演示数据、按entity/id/revision导入、检查行数/状态/审计链，再切换驱动。','','HTTP接口：GET /api/demo/catalog；GET /api/demo/records?entity=...&q=...&state=...&enterprise=...&page=...；GET加id查询详情；POST /api/demo/create 和 /api/demo/transition。写入要求同源Origin和本进程临时demo令牌，非生产登录凭据。默认只允许localhost/127.0.0.1及实际端口Host。']
 (out/'模拟业务库模型与维护说明.md').write_text('\n'.join(rows)+'\n',encoding='utf-8');(out/'demo_schema_sqlite_v1.sql').write_text(SCHEMA+'\nPRAGMA user_version=1;\n',encoding='utf-8');(out/'demo_schema_mysql_v1.sql').write_text('\n\n'.join(mysql)+'\n',encoding='utf-8');(out/'demo_schema_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return manifest
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1];manifest=generate(root.parent/'Document/Database');source=root/'deploy/database';source.mkdir(parents=True,exist_ok=True)
 import shutil
 for name in ('demo_schema_mysql_v1.sql','demo_schema_manifest.json'):shutil.copy2(root.parent/'Document/Database'/name,source/name)
 print(json.dumps(dict(modules=manifest['modules'],initialRecords=manifest['initialRecords'],sha256=manifest['schemaSHA256'])))
