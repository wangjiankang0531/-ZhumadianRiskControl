"""Generate actual isolated SQLite schema and explicit MySQL target preparation."""
import argparse,json,sqlite3,tempfile,sys,hashlib,shutil
from contextlib import closing
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.reference_demo import SCHEMA,MODULES,DemoStore
from services.reference_work_forms import catalog_schema
from services.reference_plans import plan_schema,PLAN_TABLES
TABLES=('demo_records','demo_events')+PLAN_TABLES

def mysql_type(c):
 n=c['name']
 if c['type']=='BLOB':return 'LONGBLOB'
 if c['type']=='INTEGER':return 'INT UNSIGNED'
 if n in ('entity','id','material_id'):return 'VARBINARY(128)'
 if n in ('form_sha256','sha256'):return 'CHAR(64) CHARACTER SET ascii COLLATE ascii_bin'
 if n in ('enterprise','state','kind','date','at','status','decision','created_at','published_at'):return 'VARCHAR(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin'
 return 'LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin'

def generate(out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True)
 model=dict(scope='isolated synthetic demo only',version=3,schemaSHA256=hashlib.sha256(SCHEMA.encode()).hexdigest(),modules=len(MODULES),initialRecords=len(MODULES)*12,workFormSchema=catalog_schema(),planSchema=plan_schema(),tables={})
 rows=['# 模拟业务库概念与物理模型','','由 tools/generate_reference_demo_docs.py 根据实际 SQLite 生成。当前 user_version=3；v1/v2 SQL 文件保留作历史，当前使用 v3 文件。','','本库与正式风险问题/DLG/气体业务库独立，只用于合成验收；正式库 schema v4 不变。','','业务记录(entity,id)与逐记录revision审计同事务。预案新增四个独立关系表：版本(1:N)、当前/有效版本指针(1:1)、有序处置阶段(1:N)、评审(1:N)。版本、阶段、评审业务字段各自有列；不把这些关系塞入通用payload。每次评审另保留该次审阅表单的规范UTF8原字节BLOB与SHA256，草稿退回重编仍能核对当时内容。','']
 mysql=['-- Synthetic demo schema v3. MySQL 8.4/InnoDB target; NOT server-validated.','-- Apply to an empty isolated staging database. Do not overwrite production databases.','SET NAMES utf8mb4;']
 with tempfile.TemporaryDirectory() as tmp:
  store=DemoStore(Path(tmp)/'schema.sqlite')
  with closing(store.connect()) as db:
   for table in TABLES:
    cols=[dict(r) for r in db.execute('PRAGMA table_info('+table+')')];foreign=[dict(r) for r in db.execute('PRAGMA foreign_key_list('+table+')')];indices=[];defs=[]
    rows+=['## '+table,'','| 字段 | SQLite | 非空 | 主键序号 | MySQL目标 |','| --- | --- | --- | --- | --- |']
    for c in cols:
     target=mysql_type(c);nullable=not(c['notnull'] or c['pk']);defs.append('  `'+c['name']+'` '+target+(' NULL' if nullable else ' NOT NULL'))
     rows.append(f"| {c['name']} | {c['type']} | {'否' if nullable else '是'} | {c['pk']} | {target} |")
    pk=[c['name'] for c in sorted(cols,key=lambda c:c['pk']) if c['pk']];defs.append('  PRIMARY KEY ('+','.join('`'+n+'`' for n in pk)+')')
    for index in db.execute('PRAGMA index_list('+table+')'):
     names=[r['name'] for r in db.execute('PRAGMA index_info('+index['name']+')')];indices.append(dict(name=index['name'],unique=bool(index['unique']),columns=names))
     if index['origin']!='pk':defs.append('  '+('UNIQUE KEY' if index['unique'] else 'KEY')+' `'+index['name']+'` ('+','.join('`'+n+'`' for n in names)+')')
    groups={}
    for f in foreign:groups.setdefault(f['id'],[]).append(f)
    for n,group in groups.items():
     group.sort(key=lambda f:f['seq']);defs.append('  CONSTRAINT `fk_'+table+'_'+str(n)+'` FOREIGN KEY ('+','.join('`'+f['from']+'`' for f in group)+') REFERENCES `'+group[0]['table']+'` ('+','.join('`'+f['to']+'`' for f in group)+')')
    if table in ('demo_records','demo_events'):defs.append('  CHECK (JSON_VALID(`payload`))')
    if table=='demo_plan_versions':defs+=['  CHECK (`entity` = BINARY \'plans\')','  CHECK (`version` > 0)',"  CHECK (`status` IN ('draft','review','approved','published','historical'))"]
    if table=='demo_plan_steps':defs.append('  CHECK (`position` >= 0)')
    if table=='demo_plan_materials':defs.extend(['  CHECK (`bytes` > 0 AND `bytes` <= 2097152)','  CHECK (OCTET_LENGTH(`payload`) = `bytes`)'])
    if table=='demo_plan_reviews':defs.append("  CHECK (`decision` IN ('approve','reject'))")
    mysql.append('CREATE TABLE `'+table+'` (\n'+',\n'.join(defs)+'\n) ENGINE=InnoDB;')
    model['tables'][table]=dict(columns=cols,mysqlTypes={c['name']:mysql_type(c) for c in cols},indexes=indices,foreignKeys=foreign)
    rows+=['','索引：'+json.dumps(indices,ensure_ascii=False),'','外键：'+json.dumps(foreign,ensure_ascii=False),'']
 rows+=['## 状态与事务','','draft编制→review提交→approved模拟通过→published发布；review可reject退回draft。退回保留评审记录和审阅快照。所有动作以demo_records.revision做CAS，BEGIN IMMEDIATE串行化并发，记录/版本/步骤/评审/指针/审计同事务。approve仍在列表待评审组，版本详情明确待发布，不冒充已发布。','','published创建修订草稿时原published_version保持；新版通过且显式publish时，旧版status转historical，新版才成为published_version。历史版本不提供编辑入口。旧v1种子仅作历史合成列表样本保留，不制造评审历史，不自动迁入新版本链。通用create/transition拒绝plans，不能绕过专用流程。','','## 模型维护、迁移与恢复','','SQLite 0/1/2自动创建新表并以事务升级user_version=3，3可重开，其它版本拒绝。旧记录、备注和事件保留。升级前由部署工具在线backup到新独立版本库；先在副本验收，不能原位覆盖正在使用的业务库。运行中备份使用SQLite backup（含WAL）；恢复须核对9表所有行及审阅BLOB/SHA、当前/有效版本、事件连续性和PRAGMA foreign_key_check。','','MySQL目标使用VARBINARY标识、InnoDB外键/事务、整数版本、LONGBLOB审阅原字节；业务文本保持UTF8，不做大小写折叠。迁移先导记录/事件，再版本/头/阶段/评审，保留NULL有效版本指针；校验指针状态、单一有效版本和BLOB SHA。DDL/数据导入器与真实MySQL并发/死锁重试尚未环境验收。Linux/Apache仍需同源HTTPS反代实际验证。','','HTTP专用：POST /api/demo/plan(form,enterprise,note,action,identity,revision)，action=draft/submit；POST /api/demo/plan-action(identity,revision,action,note,review)，action=approve/reject/publish/revise。GET详情包含plan的currentVersion/publishedVersion/versions/steps/reviews。仍由现有同源token或公网测试登录适配器保护，没有新增匿名写口。','','未完成范围：Office附件/内嵌预览、资源关系、正式权限/真实审批制度、独立预案业务日期筛选、删除/撤销、上级及企业预案独立视图、预案驱动应急事件和通信调度。不得用本阶段宣称261013预案全需求完成。','','八类作业workForm及记录日期统计延续原语义。payload为通用列表快照，workForm包含八类作业字段和人员组；未声称作业领域关系建模已全部完成。dateFrom/dateTo仍按记录UTC日期，而非编制或评审日期；列表状态facet保持其它筛选，summary采用完整筛选。']
 rows+=['','## v3预案附件关系与容量','','demo_plan_materials保存不可变原文件BLOB与SHA，通过record_revision关联创建审计；demo_plan_version_materials为版本引用；demo_plan_review_materials冻结当次评审引用。修订只复制引用，不重复载荷；草稿移除只删当前关联，原文件和此前评审引用保留，删除预案/数据清理仍未实现。','','PDF/PNG/JPEG扩展名与首尾格式标记一致；这不是完整文档解析或杀毒结论。每份2MiB、当前版本8份、每预案含历史保留最多32份/32MiB；保留载荷计入总容量，不因解除关联恢复容量。下载按预案+版本+可选评审revision验证引用，逐次检查长度/格式/SHA，错配503且不原位修复；仅attachment/octet-stream下载，不内嵌执行。','','上传/解除关联都要求现有同源写入token、公网登录及记录revision CAS。附件上传专用JSON上限约2.7MiB，其它接口仍128KiB。新表/键/外键/SQL由本生成器实际读取；MySQL LONGBLOB保留原字节，迁移次序记录/事件→版本/头/阶段/评审→附件→版本/评审关联。旧v2评审BLOB原样保持，新评审采用zhumadian.plan_review_snapshot.v2封套(form+materials)；不重写旧摘要。']
 outputs={'模拟业务库模型与维护说明.md':'\n'.join(rows)+'\n','demo_schema_sqlite_v3.sql':SCHEMA+'\nPRAGMA user_version=3;\n','demo_schema_mysql_v3.sql':'\n\n'.join(mysql)+'\n','demo_schema_manifest.json':json.dumps(model,ensure_ascii=False,indent=2)+'\n'}
 for name,value in outputs.items():(out/name).write_text(value,encoding='utf8')
 return model
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--publish-source',action='store_true');args=p.parse_args();root=Path(__file__).resolve().parents[1];m=generate(root.parent/'Document/Database')
 if args.publish_source:
  target=root/'deploy/database';target.mkdir(parents=True,exist_ok=True)
  for name in ('demo_schema_mysql_v3.sql','demo_schema_manifest.json'):shutil.copy2(root.parent/'Document/Database'/name,target/name)
 print(json.dumps(dict(version=m['version'],tables=len(m['tables']),sha256=m['schemaSHA256'])))
