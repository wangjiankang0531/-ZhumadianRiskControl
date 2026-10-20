"""Normalized synthetic emergency-plan workflow; no real approval or communications."""
import json,uuid,hashlib
from contextlib import closing
from datetime import date,datetime,timezone
from services.reference_errors import DemoError
from services.reference_work_forms import ENTERPRISES
from services.reference_plan_materials import PlanMaterialsMixin,MATERIAL_SCHEMA,MATERIAL_TABLES,policy as material_policy

SCHEMA_ID='zhumadian.emergency_plan.v1'
FIELDS={'name':'预案名称','category':'预案类别','level':'预案等级','compiledDate':'编制日期','authorUnit':'编制单位','accidentType':'事故类型','scope':'适用场景','commander':'指挥长','contact':'模拟联系渠道'}
CATEGORIES=['综合应急预案','专项应急预案','现场处置预案','特殊时期/重大活动应急预案']
REVIEW_FIELDS={'reviewDate':'评审日期','opinion':'评审意见','notified':'风险是否告知周边单位','noticeUnits':'风险告知单位资料','filingDepartment':'备案部门','filingKind':'备案部门性质','evaluationStatus':'预案评估状态','evaluationCycle':'定期评估周期','evaluationOpinion':'评估意见','lastFiledDate':'最近备案日期','firstFiledDate':'初次备案日期','lastEvaluatedDate':'最近定期评估日期'}
PLAN_TABLES=('demo_plan_versions','demo_plan_heads','demo_plan_steps','demo_plan_reviews')+MATERIAL_TABLES
PLAN_SCHEMA="""
CREATE TABLE IF NOT EXISTS demo_plan_versions (
 entity TEXT NOT NULL CHECK(entity='plans'), id TEXT NOT NULL, version INTEGER NOT NULL CHECK(version>0),
 status TEXT NOT NULL CHECK(status IN ('draft','review','approved','published','historical')),
 name TEXT NOT NULL, category TEXT NOT NULL, level TEXT NOT NULL, compiled_date TEXT NOT NULL,
 author_unit TEXT NOT NULL, accident_type TEXT NOT NULL, scope TEXT NOT NULL, commander TEXT NOT NULL, contact TEXT NOT NULL,
 created_at TEXT NOT NULL, published_at TEXT NOT NULL,
 PRIMARY KEY(entity,id,version), FOREIGN KEY(entity,id) REFERENCES demo_records(entity,id));
CREATE TABLE IF NOT EXISTS demo_plan_heads (
 entity TEXT NOT NULL, id TEXT NOT NULL, current_version INTEGER NOT NULL, published_version INTEGER,
 PRIMARY KEY(entity,id), FOREIGN KEY(entity,id,current_version) REFERENCES demo_plan_versions(entity,id,version),
 FOREIGN KEY(entity,id,published_version) REFERENCES demo_plan_versions(entity,id,version));
CREATE TABLE IF NOT EXISTS demo_plan_steps (
 entity TEXT NOT NULL, id TEXT NOT NULL, version INTEGER NOT NULL, position INTEGER NOT NULL CHECK(position>=0),
 title TEXT NOT NULL, department TEXT NOT NULL, content TEXT NOT NULL,
 PRIMARY KEY(entity,id,version,position), FOREIGN KEY(entity,id,version) REFERENCES demo_plan_versions(entity,id,version));
CREATE TABLE IF NOT EXISTS demo_plan_reviews (
 entity TEXT NOT NULL, id TEXT NOT NULL, version INTEGER NOT NULL, record_revision INTEGER NOT NULL,
 at TEXT NOT NULL, decision TEXT NOT NULL CHECK(decision IN ('approve','reject')),
 review_date TEXT NOT NULL, opinion TEXT NOT NULL, notified TEXT NOT NULL, notice_units TEXT NOT NULL,
 filing_department TEXT NOT NULL, filing_kind TEXT NOT NULL, evaluation_status TEXT NOT NULL, evaluation_cycle TEXT NOT NULL,
 evaluation_opinion TEXT NOT NULL, last_filed_date TEXT NOT NULL, first_filed_date TEXT NOT NULL, last_evaluated_date TEXT NOT NULL,
 reviewed_form BLOB NOT NULL, form_sha256 TEXT NOT NULL,
 PRIMARY KEY(entity,id,record_revision), FOREIGN KEY(entity,id,version) REFERENCES demo_plan_versions(entity,id,version),
 FOREIGN KEY(entity,id,record_revision) REFERENCES demo_events(entity,id,revision));
"""
PLAN_SCHEMA+=MATERIAL_SCHEMA

def plan_schema():
 return dict(schema=SCHEMA_ID,fields=FIELDS,categories=CATEGORIES,reviewFields=REVIEW_FIELDS,maxSteps=24,
             materialPolicy=material_policy(),policy='独立模拟评审，不代表真实权限或审批制度；资源关联与正式身份仍待接续。')

def text(value,label,maximum=256,required=False):
 if not isinstance(value,str) or len(value)>maximum:raise DemoError(400,label+'格式无效或过长')
 value=value.strip()
 if required and not value:raise DemoError(400,'请填写'+label)
 return value

def day(value,label,required=False):
 value=text(value,label,10,required)
 if value:
  try:
   if date.fromisoformat(value).isoformat()!=value:raise ValueError()
  except ValueError:raise DemoError(400,label+'需为有效的YYYY-MM-DD日期')
 return value

def normalize(form,submit=False):
 if not isinstance(form,dict) or set(form)!={'schema','values','steps'} or form['schema']!=SCHEMA_ID:raise DemoError(400,'预案表单格式无效')
 if not isinstance(form['values'],dict) or set(form['values'])-set(FIELDS):raise DemoError(400,'预案存在未知字段')
 values={k:(day(form['values'].get(k,''),label,submit) if k=='compiledDate' else text(form['values'].get(k,''),label,2000 if k=='scope' else 256,submit)) for k,label in FIELDS.items()}
 if values['category'] and values['category'] not in CATEGORIES:raise DemoError(400,'预案类别无效')
 steps=form['steps']
 if not isinstance(steps,list) or len(steps)>24 or (submit and not steps):raise DemoError(400,'请添加1至24个应急处置阶段')
 result=[]
 for step in steps:
  if not isinstance(step,dict) or set(step)!={'title','department','content'}:raise DemoError(400,'处置阶段格式无效')
  result.append({k:text(step[k],{'title':'阶段名称','department':'接收部门','content':'救援内容'}[k],4000 if k=='content' else 256,submit) for k in step})
 return dict(schema=SCHEMA_ID,values=values,steps=result)

def review_values(value):
 if not isinstance(value,dict) or set(value)!=set(REVIEW_FIELDS):raise DemoError(400,'评审字段无效')
 result={k:(day(v,REVIEW_FIELDS[k],k=='reviewDate') if k.endswith('Date') else text(v,REVIEW_FIELDS[k],2000,k=='opinion')) for k,v in ((k,value[k]) for k in REVIEW_FIELDS)}
 if result['notified'] not in ('是','否'):raise DemoError(400,'请选择风险告知情况')
 if result['notified']=='是' and not result['noticeUnits']:raise DemoError(400,'请填写风险告知单位资料')
 return result

class PlanMixin(PlanMaterialsMixin):
 def _plan_load(self,db,identity):
  head=db.execute('SELECT * FROM demo_plan_heads WHERE entity=? AND id=?',('plans',identity)).fetchone()
  if head is None:return None
  versions=[]
  for row in db.execute('SELECT * FROM demo_plan_versions WHERE entity=? AND id=? ORDER BY version DESC',('plans',identity)):
   value=dict(row);number=row['version']
   values=dict(zip(FIELDS,[row[k] for k in ('name','category','level','compiled_date','author_unit','accident_type','scope','commander','contact')]))
   steps=[{k:r[k] for k in ('title','department','content')} for r in db.execute('SELECT * FROM demo_plan_steps WHERE entity=? AND id=? AND version=? ORDER BY position',('plans',identity,number))]
   reviews=[]
   for r in db.execute('SELECT * FROM demo_plan_reviews WHERE entity=? AND id=? AND version=? ORDER BY record_revision',('plans',identity,number)):
    data=dict(r);data['reviewed_form']=json.loads(data['reviewed_form']);reviews.append(data)
   versions.append(dict(version=number,status=row['status'],createdAt=row['created_at'],publishedAt=row['published_at'],form=dict(schema=SCHEMA_ID,values=values,steps=steps),materials=self._plan_material_list(db,identity,number),reviews=reviews))
  return dict(currentVersion=head['current_version'],publishedVersion=head['published_version'],versions=versions,synthetic=True)

 def _plan_checked(self,db,identity,revision):
  if not isinstance(identity,str) or not identity or len(identity)>128 or type(revision) is not int or revision<1:raise DemoError(400,'预案标识或记录版本无效')
  row=db.execute('SELECT * FROM demo_records WHERE entity=? AND id=?',('plans',identity)).fetchone()
  if row is None:raise DemoError(404,'预案不存在')
  if row['revision']!=revision:raise DemoError(409,'预案已更新，请重新打开详情')
  plan=self._plan_load(db,identity)
  if plan is None:raise DemoError(409,'旧合成样本需复制为新的结构化草稿')
  return row,plan,plan['versions'][0]

 def _plan_event(self,db,identity,revision,kind,note,version,metadata=None):
  at=datetime.now(timezone.utc).isoformat()
  db.execute('INSERT INTO demo_events VALUES (?,?,?,?,?,?)',('plans',identity,revision,at,kind,json.dumps(dict(note=note,version=version,actor='DEMO-OPERATOR',metadata=metadata),ensure_ascii=False)))
  return at

 def _plan_fields(self,form,identity,number):
  v=form['values']
  return {'应急预案名称':v['name'] or '未命名预案草稿','应急预案类型':v['category'],'事故类型':v['accidentType'],'指挥长':v['commander'],'指挥长电话':v['contact'],'是否备案':'未核实','所属部门':v['authorUnit'],'预案版本':'V'+str(number)}

 def _plan_insert_version(self,db,identity,number,form,status,at):
  values=form['values']
  db.execute('INSERT INTO demo_plan_versions VALUES ('+','.join('?'*15)+')',('plans',identity,number,status,*values.values(),at,''))
  db.executemany('INSERT INTO demo_plan_steps VALUES (?,?,?,?,?,?,?)',[('plans',identity,number,i,s['title'],s['department'],s['content']) for i,s in enumerate(form['steps'])])

 def save_plan(self,form,enterprise,note,action,identity,revision):
  if action not in ('draft','submit'):raise DemoError(400,'预案保存操作无效')
  if enterprise not in ENTERPRISES:raise DemoError(400,'只能选择模拟企业')
  note=text(note,'备注',2000);form=normalize(form,action=='submit')
  if identity is None and revision is not None:raise DemoError(400,'新预案不能携带记录版本')
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');number=1
   if identity is None:
    identity='DEMO-PLAN-'+uuid.uuid4().hex[:16];revision=1
    db.execute('INSERT INTO demo_records VALUES (?,?,?,?,?,?,?)',('plans',identity,1,enterprise,'编制中',datetime.now(timezone.utc).isoformat()[:10],'{}'))
   else:
    row,plan,current=self._plan_checked(db,identity,revision);number=plan['currentVersion']
    if current['status']!='draft':raise DemoError(409,'仅编制中的版本支持修改')
    if enterprise!=row['enterprise']:raise DemoError(409,'已建预案不可变更企业归属')
    revision+=1
    db.execute('DELETE FROM demo_plan_steps WHERE entity=? AND id=? AND version=?',('plans',identity,number))
    # A rejected draft can retain review history. Update scalar fields, never delete the version.
    names=('name','category','level','compiled_date','author_unit','accident_type','scope','commander','contact')
    db.execute('UPDATE demo_plan_versions SET '+','.join(k+'=?' for k in names)+' WHERE entity=? AND id=? AND version=?',(*form['values'].values(),'plans',identity,number))
   at=self._plan_event(db,identity,revision,'plan_submit' if action=='submit' else 'plan_draft_save',note,number)
   if revision==1:
    self._plan_insert_version(db,identity,number,form,'draft',at)
    db.execute('INSERT INTO demo_plan_heads VALUES (?,?,?,NULL)',('plans',identity,number))
   else:
    db.executemany('INSERT INTO demo_plan_steps VALUES (?,?,?,?,?,?,?)',[('plans',identity,number,i,s['title'],s['department'],s['content']) for i,s in enumerate(form['steps'])])
   status='review' if action=='submit' else 'draft';state='待评审' if action=='submit' else '编制中'
   db.execute('UPDATE demo_plan_versions SET status=? WHERE entity=? AND id=? AND version=?',(status,'plans',identity,number))
   payload=json.dumps(dict(fields=self._plan_fields(form,identity,number),note=note),ensure_ascii=False)
   db.execute('UPDATE demo_records SET revision=?,state=?,payload=? WHERE entity=? AND id=?',(revision,state,payload,'plans',identity));db.commit()
  return self.detail('plans',identity)

 def plan_action(self,identity,revision,action,note,review):
  if action not in ('approve','reject','publish','revise'):raise DemoError(400,'预案操作无效')
  note=text(note,'模拟处理说明',2000,True)
  if action in ('approve','reject'):review=review_values(review)
  elif review is not None:raise DemoError(400,'此操作不接受评审字段')
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');row,plan,current=self._plan_checked(db,identity,revision);number=plan['currentVersion'];revision+=1
   required={'approve':'review','reject':'review','publish':'approved','revise':'published'}[action]
   if current['status']!=required:raise DemoError(409,'当前版本状态不支持该操作')
   at=self._plan_event(db,identity,revision,'plan_'+action,note,number+1 if action=='revise' else number)
   if action in ('approve','reject'):
    status='approved' if action=='approve' else 'draft';state='待评审' if action=='approve' else '编制中'
    db.execute('UPDATE demo_plan_versions SET status=? WHERE entity=? AND id=? AND version=?',(status,'plans',identity,number))
    snapshot=json.dumps(dict(schema='zhumadian.plan_review_snapshot.v2',form=current['form'],materials=current['materials']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
    db.execute('INSERT INTO demo_plan_reviews VALUES ('+','.join('?'*20)+')',('plans',identity,number,revision,at,action,*review.values(),snapshot,hashlib.sha256(snapshot).hexdigest()))
    db.executemany('INSERT INTO demo_plan_review_materials VALUES (?,?,?,?)',[('plans',identity,revision,m['material_id']) for m in current['materials']])
   elif action=='publish':
    if plan['publishedVersion'] is not None:db.execute("UPDATE demo_plan_versions SET status='historical' WHERE entity=? AND id=? AND version=?",('plans',identity,plan['publishedVersion']))
    db.execute("UPDATE demo_plan_versions SET status='published',published_at=? WHERE entity=? AND id=? AND version=?",(at,'plans',identity,number))
    db.execute('UPDATE demo_plan_heads SET published_version=? WHERE entity=? AND id=?',(number,'plans',identity));state='已发布'
   else:
    number+=1;self._plan_insert_version(db,identity,number,current['form'],'draft',at)
    db.execute('INSERT INTO demo_plan_version_materials SELECT entity,id,?,material_id FROM demo_plan_version_materials WHERE entity=? AND id=? AND version=?',(number,'plans',identity,number-1))
    db.execute('UPDATE demo_plan_heads SET current_version=? WHERE entity=? AND id=?',(number,'plans',identity));state='编制中'
    payload=json.loads(row['payload']);payload['fields']=self._plan_fields(current['form'],identity,number)
    db.execute('UPDATE demo_records SET payload=? WHERE entity=? AND id=?',(json.dumps(payload,ensure_ascii=False),'plans',identity))
   db.execute('UPDATE demo_records SET revision=?,state=? WHERE entity=? AND id=?',(revision,state,'plans',identity));db.commit()
  return self.detail('plans',identity)
