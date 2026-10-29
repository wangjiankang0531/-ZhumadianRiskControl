"""Generate two actual exercise/file schemas and conceptual model without changing the database."""
from pathlib import Path
import datetime,hashlib,json,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');D=R/'Document/Deployment/emergency_exercise_atomic_20261029';W=R/'work/emergency_exercise_atomic_20261029/database-docs';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from verify_original_work_reservation_sql import run
from verify_event_disposal_local_state import current
from run_original_inventory_ownership_probe import state
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def main():
 assert not W.exists();before=current();c=state();W.mkdir();(W/'classes').mkdir();source=T/'java/OriginalEmergencyExerciseSchemaReadProbe.java';pin=sha(source);deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for name,row in deps['inputPins'].items():assert sha(name)==row['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];run(W,'compile-schema-read',[java.with_name('javac.exe'),'-J-Xmx128m','-proc:none','-encoding','UTF-8','-cp',deps['classpath'],'-d',W/'classes',source],35);secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode();out=D/'actual-two-table-schema.private.json';assert not out.exists()
 try:run(W,'read-two-schemas',[java,'-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(W/'classes')+';'+deps['classpath'],'xnby.replica.OriginalEmergencyExerciseSchemaReadProbe',str(c['databasePort']),c['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),out],35,secret)
 finally:del secret
 value=read(out);assert value['readOnlyConnection'] and not value['businessMethodsAuthenticationWritesOrHTTPInvoked'] and not value['rowValuesOutputOrCopied'];schemas=value['permanentTwoTables'];baseline=read(R/'work/emergency_exercise_atomic_20261029/sql-r4/candidate/result.private.json')['permanentBefore'];assert set(schemas)=={'emergency_exercise','base_file'}
 physical=['# 原应急演练与附件库物理模型','','由 `Application/tools/generate_emergency_exercise_database_docs.py` 从实际本机 MySQL 的两份只读 `SHOW CREATE TABLE` 自动生成。本文件对应原南港 MySQL，不对应项目早期 mock SQLite 模型。','','当前为离线事务候选，未安装、未重启、未发布公网。没有字段、索引、状态枚举、附件归属定义变更。真实 MySQL 临时表测试已经通过；实际应用装配、正常用户 HTTP 与角色验收仍待。','']
 for name,item in schemas.items():
  assert hashlib.sha256(item['DDL'].encode()).hexdigest()==item['schemaSHA256']==baseline[name]['schemaSHA256'];physical.extend(['## '+name,'','实际结构 SHA256：`'+item['schemaSHA256']+'`。','','```sql',item['DDL'],'```',''])
 files={'原应急演练与附件库物理模型.md':'\n'.join(physical),'原应急演练与附件库概念模型.md':'''# 原应急演练与附件库概念模型

`emergency_exercise` 保存原应急演练记录，沿用 `emergency_plan_id` 归属于原预案。共享附件索引表 `base_file` 使用原 `correlation_id` 关联记录标识，一个演练可以关联多份附件。该关联是原业务约定，不在本阶段新增数据库外键，也不把共享 `base_file` 变成演练专用表。

```mermaid
flowchart LR
  P["原应急预案标识"] -->|"emergency_plan_id"| E["emergency_exercise"]
  E -->|"id 对应 correlation_id，原业务关联"| F["共享 base_file"]
```

候选仅把 `save`、`saveEmergencyExerciseList`、`delete` 的主记录及附件索引写入纳入 REQUIRED/Exception 回滚事务，校验原来被忽略的 false/零影响写入。批量继续调用原 `saveOrUpdateBatch`，保留已有记录与新增记录混合、生成 ID、数据库排序规则下重复 ID 的最后一次值以及各输入附件追加；真实无变化零影响更新仍成功。

附件实体继续沿用原 correlation_id 绑定、重置客户端附件 ID 和既有 BaseFileService.save 行为；共享服务源文件未改。删除继续按原 correlation_id 关系删除索引，不删除磁盘或对象存储正文。缺少父记录时返回 false，不顺带清理未知索引。

正式两表分别9/137行，原/候选41场景前后全行多重集与DDL摘要保持。没有字段、索引、状态或归属定义变更；候选尚未安装，不据此声明真实业务HTTP、权限或完整B/S复刻通过。
'''};database=R/'Document/Database'
 for name,text in files.items():p=database/name;assert not p.exists();p.write_text(text+'\n',encoding='utf8')
 assert sha(source)==pin and current()==before;result={'at':datetime.datetime.now().astimezone().isoformat(),'sourceSHA256':pin,'readOnlyActualMySQLSchemas':2,'schemaHashesMatchBothSQLModesBeforeAndAfter':True,'noRowsReadOrCopiedBySchemaProbe':True,'noFieldIndexStateEnumOwnershipDefinitionChanges':True,'models':{name:sha(database/name) for name in files},'runtimeRestartedOrCandidateInstalled':False,'fullCloneReady':False};out=D/'database-model-verification.json';assert not out.exists();out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
