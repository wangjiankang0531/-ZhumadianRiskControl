"""Regenerate schema-derived database documentation alongside manually reviewed concepts."""
import argparse, hashlib, json, sqlite3, sys, tempfile
from contextlib import closing
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.database import SQLiteDatabase,SCHEMA_VERSION,SCHEMA_SQLITE
from services.database_transfer import TABLES
from services.focus import STATES,FLAGS,RESULTS
from services.focus_materials import MATERIAL_LIMIT,MATERIAL_JSON_LIMIT,ISSUE_MATERIAL_LIMIT,ISSUE_MATERIAL_COUNT,TYPES

DESCRIPTIONS={"issue_materials":"不可变照片/截图/PDF材料与摘要；通过问题版本外键绑定成功审计事件，载荷存于SQLite BLOB", "issues":"园区重点问题当前快照；不替代企业一般隐患台账","events":"逐版本追加的业务变更/反馈/复查及成功写入审计","requests":"按租户、操作者及幂等键保存重复提交结果","dlg_documents":"当前用户DLG文档及原始UTF8字节","dlg_versions":"DLG完整历史快照及SHA256","dlg_layers":"可查询的图层分组、顺序、名称和显隐/锁定","dlg_features":"可查询的点线面要素、绘制顺序、企业及完整几何样式"}

DESCRIPTIONS.update({
 'gas_alerts':'公共区域气体异常当前快照与公共点位索引；独立于企业重点问题，不伪造企业归属',
 'gas_history':'每个气体异常连续版本的命令与结果状态SHA；保留来源浓度/单位/时区原文',
 'gas_requests':'气体命令幂等键与提交版本；重放仍按当前授权投影，不冒充最新版本',
 'gas_outbox':'同事务冻结的应急转办包、目标系统、投递租约和重试状态；发送不等于业务接收',
 'gas_materials':'不可变公共/企业气体佐证材料BLOB；与同版本气体材料历史绑定',
 'gas_delivery_attempts':'逐次追加投递尝试、租约摘要及完成结果；不保存明文租约令牌'
})

def mysql_type(table,name,sqlite_type):
    if sqlite_type=="BLOB":return "LONGBLOB"
    if name in ("revision","source_revision","sort_index","bytes","attempt","attempts"):return "INT UNSIGNED"
    if name in ("visible","locked"):return "TINYINT UNSIGNED"
    if name=="tenant":return "VARBINARY(128)"
    if name=="document_id":return "VARBINARY(128)"
    if name in ("id","issue","key","event_id","request_id"):return "CHAR(32) CHARACTER SET ascii COLLATE ascii_bin"
    if name in ("source_sha256","state_sha256","package_sha256","lease_sha256","digest","sha256"):return "CHAR(64) CHARACTER SET ascii COLLATE ascii_bin"
    if name in ("at","updated","created","claimed_at","finished_at","lease_until","next_attempt_at"):return "VARCHAR(40) CHARACTER SET ascii COLLATE ascii_bin"
    if name in ("media_type","last_error","error_code"):return "VARCHAR(64) CHARACTER SET ascii COLLATE ascii_bin"
    if name in ("kind","scope","delivery_state","outcome"):return "VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin"
    if name=="geometry_type":return "VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin"
    if name=="policy":return "VARBINARY(128)"
    if name in ("enterprise","source_system","source_id","actor","layer_id","feature_id","spatial_id","target_system"):return "VARBINARY(256)"
    if name=="name":return "VARCHAR(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"
    return "LONGTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin"

def generate(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256(SCHEMA_SQLITE.encode()).hexdigest()
    model={"schemaVersion":SCHEMA_VERSION,"schemaDefinitionSHA256":digest,"states":sorted(STATES),"focusFlags":sorted(FLAGS),"reviewResults":sorted(RESULTS),"materialPolicy":{"maxBytes":MATERIAL_LIMIT,"maxJsonBytes":MATERIAL_JSON_LIMIT,"maxIssueBytes":ISSUE_MATERIAL_LIMIT,"maxIssueCount":ISSUE_MATERIAL_COUNT,"mediaTypes":sorted(TYPES),"immutable":True},"tables":{}}
    physical=["# 数据库物理模型（当前SQLite及目标MySQL）", "",f"模型版本：{SCHEMA_VERSION}。以Application/services/database.py为实际结构源；本文件由tools/generate_database_docs.py生成。", "",f"DDL定义SHA256：`{digest}`。", "", "SQLite是当前已实现存储；MySQL建表脚本是迁移目标，未在MySQL服务器运行验证。", ""]
    ddl=[f"-- XNBY business schema v{SCHEMA_VERSION}; MySQL 8.4/InnoDB target. NOT live-server validated.","-- Run in an empty staging database. DDL and data import are separate steps.","SET NAMES utf8mb4;", "CREATE TABLE `xnby_schema` (`id` INT PRIMARY KEY, `version` INT NOT NULL) ENGINE=InnoDB;", f"INSERT INTO `xnby_schema` VALUES (1,{SCHEMA_VERSION});"]
    with tempfile.TemporaryDirectory() as temporary:
        store=SQLiteDatabase(Path(temporary)/"schema.sqlite")
        with closing(store.connect()) as db:
            for table in TABLES:
                info=list(db.execute("PRAGMA table_info("+table+")"));foreign=list(db.execute("PRAGMA foreign_key_list("+table+")"));indexes=[]
                physical += ["## "+table,"",DESCRIPTIONS[table],"","| 字段 | SQLite类型 | 非空 | 主键序号 | MySQL目标类型 |","| --- | --- | --- | --- | --- |"]
                defs=[]
                for row in info:
                    _,name,kind,notnull,default,pk=row;target=mysql_type(table,name,kind)
                    physical.append(f"| {name} | {kind} | {'是' if notnull or pk else '否'} | {pk or '—'} | {target} |")
                    defs.append("  `"+name+"` "+target+(" NOT NULL" if notnull or pk else " NULL"))
                primary=[r[1] for r in sorted(info,key=lambda x:x[5]) if r[5]];defs.append("  PRIMARY KEY ("+",".join("`"+k+"`" for k in primary)+")")
                for idx in db.execute("PRAGMA index_list("+table+")"):
                    index_names=[r[2] for r in db.execute("PRAGMA index_info('"+idx[1]+"')")]
                    indexes.append({"name":idx[1],"unique":bool(idx[2]),"columns":index_names})
                    if idx[3]=="pk":continue
                    index_name="ix_"+table+"_"+str(len(indexes))
                    defs.append("  "+("UNIQUE KEY" if idx[2] else "KEY")+" `"+index_name+"` ("+",".join("`"+k+"`" for k in index_names)+")")
                groups={}
                for f in foreign:groups.setdefault(f[0],[]).append(f)
                for n,rows in groups.items():
                    rows.sort(key=lambda f:f[1]);target=rows[0][2]
                    defs.append("  CONSTRAINT `fk_"+table+"_"+str(n)+"` FOREIGN KEY ("+",".join("`"+r[3]+"`" for r in rows)+") REFERENCES `"+target+"` ("+",".join("`"+r[4]+"`" for r in rows)+")")
                if table in {'issue_materials','gas_materials'}:defs.extend([f"  CHECK (`bytes` > 0 AND `bytes` <= {MATERIAL_LIMIT})","  CHECK (OCTET_LENGTH(`payload`) = `bytes`)"])
                if table=='gas_materials':defs.append("  CHECK ((`scope` = 'public' AND `enterprise` IS NULL) OR (`scope` = 'enterprise' AND `enterprise` IS NOT NULL))")
                for name in ("payload","result"):
                    match=next((r for r in info if r[1]==name),None)
                    if match and match[2]!="BLOB":defs.append("  CHECK (JSON_VALID(`"+name+"`))")
                ddl.append("CREATE TABLE `"+table+"` (\n"+",\n".join(defs)+"\n) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;")
                model["tables"][table]={"description":DESCRIPTIONS[table],"columns":[{"name":r[1],"sqliteType":r[2],"notNull":bool(r[3]),"primaryOrder":r[5],"mysqlType":mysql_type(table,r[1],r[2])} for r in info],"indexes":indexes,"foreignKeys":[list(r) for r in foreign]}
                physical += ["","索引：`"+json.dumps(indexes,ensure_ascii=False)+"`。",""]
    physical += ["## JSON及二进制字段口径","","issues.payload：enterpriseId、sourceSystem、sourceId、title（最多256 UTF8字节）、description（4000字节）、level、flags、dueDate、可选spatialId、status、revision、createdAt、updatedAt、latestFeedback、latestReview。", "", "latestFeedback：cause、measures、plan、completion、improvement、materialVersion（各2000字节）及服务端时间/人员；材料版本说明仍保留；附件字节独立存于issue_materials，不嵌入问题快照或事件JSON。latestReview：result、note（4000字节）、时间、人员。", "", "events.payload保存本次命令内容；同一issue的revision从1连续增加。requests.result是当次幂等响应，可能为旧版本，不能当作最新问题快照。", "", "dlg_documents/versions.payload为原始JSON字节BLOB（含BOM/空白），SHA按原始字节计算；MySQL映射LONGBLOB。dlg_layers.payload保留除features外的完整层属性；dlg_features.payload保留完整几何/图标/线型/颜色/宽度/透明度/文字和业务关联，不缩减为少数字段。", "", "企业和身份编号采用UTF8字节完全相等；MySQL索引字段使用VARBINARY以避免默认大小写或重音折叠。时间使用UTC ISO8601文本并保留精度。所有业务表使用InnoDB事务、唯一约束及必要外键。", "", "状态与标记常量见schema_manifest.json。超期是查询时按服务器日期、期限与本地复查结论计算的辅助指标，不是源系统认定。", "", "MySQL实际导入、数据库驱动/连接池、锁等待/死锁重试、并发与容量、恢复以及国产化验证仍待部署环境验收。"]
    from services.gas_domain import CLASSIFICATIONS,CONCLUSIONS,COOPERATION,ACTIVITIES,UNITS
    model['gasPolicy']={'classifications':sorted(CLASSIFICATIONS),'conclusions':sorted(CONCLUSIONS),'cooperation':sorted(COOPERATION),'activities':sorted(ACTIVITIES),'units':sorted(UNITS),'maxMaterials':ISSUE_MATERIAL_COUNT,'maxMaterialBytes':MATERIAL_LIMIT,'maxEventMaterialBytes':ISSUE_MATERIAL_LIMIT,'maxDeliveryAttempts':10,'leaseSeconds':[5,300],'trustedSourceAndResultSubjectsMustDiffer':True,'networkDispatchImplemented':False}
    physical += ["", "## 气体异常与转办", "", "v4增量添加6张gas表，与原issues/DLG/issue_materials独立。公共点位采用服务器白名单和公共访问权限，企业说明/材料再检查企业范围。快照、逐版本命令、幂等结果、材料或转办包同一事务；新材料或分类使旧核实失效。", "", "gas_history.state_sha256对规范JSON结果计算；备份时逐版本重放核对快照、材料SHA和版本绑定、幂等提交、全部历史转办ID唯一和包身份。离线重放使用验证主体，不代表历史授权已被密码学证明。", "", "gas_outbox.payload为冻结业务包，package_sha256不随重试变化；租约仅存SHA，明文令牌只交当前工作者。投递UTC时间固定微秒精度。pending/inflight/awaiting-result/failed是传输状态，accepted/rejected/completed必须由固定身份和目标系统的真实结果命令推进；代码已有显式配置的JWT/策略HTTP接口，尚未接气体页面；活动服务未启用气体功能，仍无网络投递器。", "", "gas_materials.scope=public时enterprise必须NULL；enterprise范围材料必须有归属。核实材料引用在同事务核对同事件、旧版本和当前授权。企业不可通过历史/幂等重放/材料引用读取其它企业材料；保留原始BLOB而非base64文本。", "", "旧v2七表、v3八表归档按各自精确DDL指纹恢复为v4新库，6张gas表初始为空。迁移只在新副本验证，不自动升级活动用户库；MySQL目标DDL未在服务器执行。"]
    physical += ["", "## 材料字节与授权", "",f"单个材料上限{MATERIAL_LIMIT}字节，单问题最多{ISSUE_MATERIAL_COUNT}个、总量{ISSUE_MATERIAL_LIMIT}字节。支持PNG/JPEG/PDF，签名和扩展名一致性是格式检查，不是恶意内容扫描。所有下载强制attachment、nosniff/no-store，并重新检查当前租户/企业授权。", "", "issue_materials.payload为原始BLOB；bytes/sha256与原始字节对应，name保留原文件名而不当作文件路径。revision关联events(tenant,issue,revision)中的material事件。新增材料、问题版本、旧复查结论失效、事件及幂等结果同一事务；旧复查结论仍在历史。无修改/删除材料API；归档问题须重新关注才可新增。", "", "v3只添加材料表，构造器可执行事务增量升级；本阶段不对正式旧库运行新构造器。正式部署先在线备份并运行upgrade-copy到全新目标，核对后再切换配置。旧v2/v3导出归档可恢复为v4新库；v3材料原字节保留，新增gas表为空。MySQL/Apache仍需真实环境验收。"]
    (output/"物理模型.md").write_text("\n".join(physical)+"\n",encoding="utf-8")
    (output/f"schema_sqlite_v{SCHEMA_VERSION}.sql").write_text("-- Generated from actual application schema\n"+SCHEMA_SQLITE+f"\nPRAGMA user_version={SCHEMA_VERSION};\n",encoding="utf-8")
    (output/f"schema_mysql_v{SCHEMA_VERSION}.sql").write_text("\n\n".join(ddl)+"\n",encoding="utf-8")
    (output/"schema_manifest.json").write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding="utf-8")
    return model

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[2]/"Document/Database");p.add_argument("--publish-source",action="store_true");a=p.parse_args();m=generate(a.output)
    if a.publish_source:
        import shutil
        target=Path(__file__).resolve().parents[1]/"deploy/database";target.mkdir(parents=True,exist_ok=True)
        for name in (f"schema_mysql_v{SCHEMA_VERSION}.sql","schema_manifest.json"):shutil.copy2(a.output/name,target/name)
    print(json.dumps({"version":m["schemaVersion"],"tables":len(m["tables"]),"sha256":m["schemaDefinitionSHA256"]}))
