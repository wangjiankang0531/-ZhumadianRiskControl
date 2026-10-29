"""Generate installed exercise MySQL models from fresh read-only DDL and verified lifecycle hashes."""
from pathlib import Path
import datetime,hashlib,json,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';Q=Path('D:/Zqa20261025/Application');D=R/'Document/Deployment/emergency_exercise_local_20261029';W=R/'work/emergency_exercise_integration_20261029/installed-models';L=R/'work/emergency_exercise_repair_lifecycle_20261029';sys.dont_write_bytecode=True;sys.path.insert(0,str(T))
from verify_original_work_reservation_sql import run
from verify_emergency_exercise_local_state import current
from run_original_inventory_ownership_probe import state
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def main():
 assert not W.exists();before=current();c=state();W.mkdir();(W/'classes').mkdir();source=T/'java/OriginalEmergencyExerciseSchemaReadProbe.java';deps=read(R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json')
 for name,row in deps['inputPins'].items():assert sha(name)==row['SHA256']
 java=Path(deps['java']);assert sha(java)==deps['javaSHA256'];run(W,'compile-schema',[java.with_name('javac.exe'),'-J-Xmx128m','-proc:none','-encoding','UTF-8','-cp',deps['classpath'],'-d',W/'classes',source],35);secret=read(Q/'private/server-configuration.json')['seedRootPassword'].encode();out=D/'actual-installed-two-table-schema.private.json';assert not out.exists()
 try:run(W,'read-two-schemas',[java,'-Xmx128m','-XX:ActiveProcessorCount=2','-cp',str(W/'classes')+';'+deps['classpath'],'xnby.replica.OriginalEmergencyExerciseSchemaReadProbe',str(c['databasePort']),c['databaseUUID'],str(Q/'UserData/OriginalServer/database/data'),out],35,secret)
 finally:del secret
 schemas=read(out)['permanentTwoTables'];baseline=read(L/'prepared.json')['baselineProjection']['permanentExerciseTables'];assert set(schemas)=={'emergency_exercise','base_file'};physical=['# 原应急演练与附件库物理模型','','由 `Application/tools/generate_installed_emergency_exercise_models.py` 从实际安装后的本机 MySQL 两份只读 SHOW CREATE TABLE 自动生成，对应原南港 MySQL。','','当前本机 '+before['currentBS']+'/controller'+str(c['controllerPID'])+'/release83de8d4e 已正常装配三方法事务及13字段NOT_NULL门禁。字段、索引、状态枚举与归属定义没有变化；正常账号HTTP、角色与完整B/S仍待。','']
 for name,item in schemas.items():
  assert hashlib.sha256(item['DDL'].encode()).hexdigest()==item['schemaSHA256']==baseline[name]['schemaSHA256'];physical.extend(['## '+name,'','结构 SHA256：`'+item['schemaSHA256']+'`。','','```sql',item['DDL'],'```',''])
 concept='''# 原应急演练与附件库概念模型

原 `emergency_exercise.emergency_plan_id` 关联所属应急预案。共享索引表 `base_file.correlation_id` 使用原演练ID关联附件，一条演练可以有多份索引；这是原业务约定，不新增外键，不把共享表变成演练专表。

```mermaid
flowchart LR
  P["原应急预案标识"] -->|"emergency_plan_id"| E["emergency_exercise"]
  E -->|"id 对应 correlation_id，原业务关联"| F["共享 base_file"]
```

单条保存、原 saveOrUpdateBatch 批量保存、删除现已在本机正常加载到 REQUIRED/Exception 事务代理。业务类字节与41+41真实MyBatis/MySQL临时表验证相同；附件失败false/数据库异常撤销整个父子写入，真实no-op、数据库排序规则等价ID、最后一次值与各输入附件追加保持。缺失父记录不顺带清理未知索引；不操作对象存储或磁盘正文。

实际Spring容器的13字段NOT_NULL且无updateFill策略已经核验；只规范合法一对反引号识别元数据列名，不改变实际SQL或数据库列。原共享BaseFile实现、字段、索引、状态及归属定义保持。当前正常停启前后9组样本和13完整表摘要保持，其中演练与共享索引两表9/137行；真实账户、业务HTTP、角色与H5仍待。
'''
 database=R/'Document/Database';oldPins=read(R/'Document/Deployment/emergency_exercise_atomic_20261029/database-model-verification.json')['models'];saved=D/'prior-models';saved.mkdir();files={'原应急演练与附件库物理模型.md':'\n'.join(physical),'原应急演练与附件库概念模型.md':concept}
 for name,text in files.items():p=database/name;assert sha(p)==oldPins[name];(saved/name).write_bytes(p.read_bytes());p.write_text(text+'\n',encoding='utf8')
 assert before==current();result={'at':datetime.datetime.now().astimezone().isoformat(),'sourceSHA256':sha(source),'generatorSHA256':sha(Path(__file__)),'actualPostInstallReadOnlyMySQLSchemas':2,'schemaHashesMatchInitialAndRepairLifecycle':True,'noRowValuesReadOrCopiedBySchemaProbe':True,'noFieldIndexStateOwnershipDefinitionChanges':True,'models':{name:sha(database/name) for name in files},'fullCloneReady':False};(D/'installed-database-model-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(result))
if __name__=='__main__':main()
