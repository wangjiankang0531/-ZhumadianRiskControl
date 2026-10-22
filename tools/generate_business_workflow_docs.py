"""Read actual empty workflow schema; generate model, SQL and maintenance notes."""
from pathlib import Path
from contextlib import closing
import argparse,hashlib,json,shutil,sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.business_workflow import WorkflowStore,SCHEMA,KINDS,STATES,WORK_TYPES,COORDINATE_SYSTEMS

def generate(output,publish_source=False):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 model={'schema':'xnby.business.workflow.database.v1','userVersion':2,'schemaSHA256':hashlib.sha256(SCHEMA.encode()).hexdigest(),'fixtureRecords':0,'kinds':KINDS,'states':STATES,'workTypes':WORK_TYPES,'coordinateSystems':COORDINATE_SYSTEMS,'tables':{}}
 notes=['# 业务协同库概念、物理模型与维护说明','','由 tools/generate_business_workflow_docs.py 从实际空库PRAGMA读取生成；与现有合成演示库及正式issues/DLG/gas库独立。无默认演示行，登录用户录入的测试记录共享于PC和H5。','','## 概念与归属','','wf_reviews按动作版本记录通过/退回、说明、账号和时间；整改预防措施单独字段，原v1升级增列默认空并保留历史，不伪造旧复核记录。撤回仅允许原上报人在待处理且没有整改历史时执行，原审计保留、旧执行人待办同事务失效。wf_cases为有类型的业务主记录。wf_actions逐版本审计、wf_requests按账号和请求键去重、wf_tasks跟踪阶段责任人；wf_points按任务/序号保存逐点结果与异常隐患外键；整改历史和作业前检查另表保存；物资、事件调拨、库存事件和物资登记幂等请求独立关系表。测试工作区共享读权限，写操作按创建人/执行人/复核人与状态检查；不能称为正式租户/组织/IAM完成。','','隐患reported→assigned→review→closed，退回复到assigned；巡检/排查planned→running→review→closed，逐点异常同事务创建关联hazard；作业draft→submitted→approved→active→acceptance→closed，审批退回draft、验收退回active；事件triage→responding→resolved→closed，未归还物资禁止结案。','','BEGIN IMMEDIATE、CAS revision、审计/下一待办/关联隐患/库存与幂等结果同事务。执行和复核账号不得相同，服务端从登录会话取actor，不能信任公网客户端传入actor。幂等重放核对完整命令摘要，并返回当前可访问详情，不能把旧提交版本当最新。','','每条任务完成都留wf_tasks历史；待办按assignee/status实时查询。期限逾期只作辅助统计，当前按服务器日期计算。采样检测内容目前是记录说明，不自动判定现场气体安全；完整采样指标/附件/签字/组织流程仍须扩展验收。','']
 with tempfile.TemporaryDirectory() as temp:
  store=WorkflowStore(Path(temp)/'schema.sqlite')
  with closing(store.connect()) as db:
   for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'wf_%' ORDER BY name"):
    columns=[dict(r) for r in db.execute('PRAGMA table_info('+name+')')];foreign=[dict(r) for r in db.execute('PRAGMA foreign_key_list('+name+')')];indexes=[]
    for index in db.execute('PRAGMA index_list('+name+')'):
     indexes.append({'name':index['name'],'unique':bool(index['unique']),'partial':bool(index['partial']),'columns':[r['name'] for r in db.execute('PRAGMA index_info('+index['name']+')')]})
    model['tables'][name]={'columns':columns,'foreignKeys':foreign,'indexes':indexes}
    notes+=['## '+name,'','|字段|类型|非空|主键顺序|','|---|---|---|---|']+[f"|{c['name']}|{c['type']}|{bool(c['notnull'] or c['pk'])}|{c['pk']}|" for c in columns]+['','索引：`'+json.dumps(indexes,ensure_ascii=False)+'`。','','外键：`'+json.dumps(foreign,ensure_ascii=False)+'`。','']
 notes+=['## 备份、恢复和发布','','升级不打开或覆盖原运行库。新版本只在新目录通过SQLite backup复制原合成库（包括已提交WAL），现有预案版本/附件一并保留；workflow侧库首次为空，后续升级也须各自在线backup。新版本切换前后核对两库绑定、逐表行/字节、连续revision、待办唯一性、外键及库存约束；保留旧包和旧上游端口用于回滚。运行包不包含业务数据库或凭据。','','备份恢复回归覆盖当前所有workflow表、行、外键；数据库文件禁止放在IIS静态目录。DB schema1只接受空库或1，未知版本拒绝，不在用户库上试错修复。备份应保存于仅服务器运维可访问的版本目录，不能上传源码仓库。','','MySQL及Linux/Apache仍需独立驱动和实机验收。尤其SQLite的wf_pending_task部分唯一索引须改为生成列/唯一索引等等价约束，不能直接执行SQLite DDL或声称MySQL已支持全部规则。原正式schema4及合成demo schema3生成物保持各自归属。','','## 参考使用与未完成范围','','依据Reference内移动端hazard/investigation/inspection/eventReport/allWork/todo接口与WorkServiceImpl开始作业检查实现本地事务；未连天津私网服务，未复制IgnoreAuth，不假称JNPF流程引擎已接入。材料支持PNG/JPEG/PDF原字节、摘要和参与人上传/项目工作区下载；每份2MiB、每记录8份/16MiB，格式标记校验不等于文档解析或病毒扫描。材料版本审计同事务、闭环后拒绝追加，不删历史。坐标手工录入、检查范围并保留坐标系，事件必须有坐标；未自动定位、未作坐标转换或地图选点。组织/租户授权、完整作业票明细、全部参考模块和正式业务验收仍应以逐项覆盖表为准。']
 files={'workflow_schema_sqlite_v2.sql':SCHEMA+'\nPRAGMA user_version=2;\n','workflow_schema_manifest.json':json.dumps(model,ensure_ascii=False,indent=2)+'\n','业务协同库模型与维护说明.md':'\n'.join(notes)+'\n'}
 for name,value in files.items():(output/name).write_text(value,encoding='utf-8')
 if publish_source:
  target=Path(__file__).resolve().parents[1]/'deploy/database';target.mkdir(parents=True,exist_ok=True)
  for name in files:shutil.copyfile(output/name,target/name)
 return model

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'Document/Database');p.add_argument('--publish-source',action='store_true');args=p.parse_args();m=generate(args.output,args.publish_source);print(json.dumps({'tables':len(m['tables']),'version':m['userVersion'],'sha256':m['schemaSHA256']}))
