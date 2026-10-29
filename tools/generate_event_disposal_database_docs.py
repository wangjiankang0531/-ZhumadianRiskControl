"""Generate the actual disposal MySQL model from two read-only SHOW CREATE TABLE results."""
from pathlib import Path
import datetime,hashlib,json,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');D=R/'Document/Deployment/event_disposal_atomic_20261029';W=R/'work/event_disposal_atomic_20261029/database-docs';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from verify_original_work_reservation_sql import run
from run_original_inventory_ownership_probe import state
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def main():
 assert not W.exists();before=sha(Q/'UserData/OriginalServer/current-run.json');c=state();assert c['controllerPID']==30892 and Path(c['run']).name=='j58';W.mkdir();(W/'classes').mkdir();source=T/'java/OriginalEventDisposalSchemaReadProbe.java';pin=sha(source);deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for name,row in deps['inputPins'].items():assert sha(name)==row['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];run(W,'compile-schema-read',[java.with_name('javac.exe'),'-J-Xmx128m','-proc:none','-encoding','UTF-8','-cp',deps['classpath'],'-d',W/'classes',source],35);secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode();out=D/'actual-two-table-schema.private.json';assert not out.exists()
 try:run(W,'read-two-schemas',[java,'-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(W/'classes')+';'+deps['classpath'],'xnby.replica.OriginalEventDisposalSchemaReadProbe',str(c['databasePort']),c['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),out],35,secret)
 finally:del secret
 value=read(out);assert value['readOnlyConnection'] and not value['businessMethodsAuthenticationWritesOrHTTPInvoked'] and not value['rowValuesOutputOrCopied'];schemas=value['permanentTwoTables'];baseline=read(R/'work/event_disposal_lifecycle_20261029/prepared.json')['baselineProjection']['permanentEventTables'];assert set(schemas)=={'event_info','event_disposal_record'}
 physical=['# 原事件处置库物理模型','','本文件由 `Application/tools/generate_event_disposal_database_docs.py` 从当前本机 MySQL 的两份只读 `SHOW CREATE TABLE` 结果生成。该结构已经在真实 MySQL 校验，不能据此声称全部业务 HTTP、角色或 Apache 环境已验收。','','事务修正前后两表全行与 DDL 摘要相同；没有字段、索引、状态枚举或归属定义增量。目标状态仍是原 `research_status=2`，失败时同事务撤销状态与新处置记录。','']
 for name,item in schemas.items():
  assert hashlib.sha256(item['DDL'].encode()).hexdigest()==item['schemaSHA256']==baseline[name]['schemaSHA256'];physical.extend(['## '+name,'','原实例结构 SHA256：`'+item['schemaSHA256']+'`。','','```sql',item['DDL'],'```',''])
 database=R/'Document/Database';files={'原事件处置库物理模型.md':'\n'.join(physical),'原事件处置库概念模型.md':'''# 原事件处置库概念模型

事件 `event_info` 和处置记录 `event_disposal_record` 通过原事件标识关联：一个事件可以有多条处置记录；服务接收原 `EventDisposalRecord.eventId`。本阶段沿用现有字段、索引、状态枚举与归属定义，实际结构见自动生成的同名物理模型。

```mermaid
flowchart LR
  E["事件 event_info"] -->|"id 对应 event_id，业务关联"| R["处置记录 event_disposal_record"]
```

`saveRecord` 把原有“事件状态更新为2”和“保存处置记录”放入同一个 REQUIRED 事务。空事件标识或缺少父事件返回 false；父事件原本已经为2时，MySQL 零影响更新仍可继续保存。保存返回 false 时标记整个事务回滚；数据库异常或真实重复主键1062也回滚。其它业务方法、状态取值及 HTTP 参数保持原契约。

原/候选各11真实 MyBatis/MySQL 连接内临时表场景验证上述边界，完整正式两表行与结构摘要保持；真实登录、权限、业务 HTTP 仍待。具体维护及回退边界见 `原事件处置事务维护_20261029.md`。
'''}
 for name,text in files.items():p=database/name;assert not p.exists();p.write_text(text+'\n',encoding='utf8')
 assert sha(source)==pin and sha(Q/'UserData/OriginalServer/current-run.json')==before;result={'at':datetime.datetime.now().astimezone().isoformat(),'sourceSHA256':pin,'readOnlyActualMySQLSchemas':2,'schemaHashesMatchBeforeAndAfterInstall':True,'noRowsReadOrCopied':True,'noFieldIndexStateEnumOwnershipDefinitionChanges':True,'models':{name:sha(database/name) for name in files},'runtimeRestarted':False,'fullCloneReady':False};p=D/'database-model-verification.json';assert not p.exists();p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
