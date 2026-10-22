"""Shared PC/H5 business transactions. No fixtures, no external Tianjin endpoints.

Reference: mobile hazard/investigation/inspection/eventReport/allWork/todo
services and WorkServiceImpl.startWork. This is an explicit local implementation,
not a claim to include the unavailable JNPF workflow engine or live telemetry.
"""
from contextlib import closing
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib, json, re, sqlite3, uuid, math
from services.business_materials import WorkflowMaterials,MATERIAL_SCHEMA,meta as material_metadata
from services.reference_errors import DemoError

SCHEMA = '''
CREATE TABLE IF NOT EXISTS wf_cases(
 id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('hazard','event','work','inspection','investigation')),
 title TEXT NOT NULL, enterprise TEXT NOT NULL, location TEXT NOT NULL,
 state TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
 reporter TEXT NOT NULL, assignee TEXT NOT NULL, reviewer TEXT NOT NULL,
 due_date TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 details TEXT NOT NULL CHECK(json_valid(details)), parent_id TEXT REFERENCES wf_cases(id));
CREATE INDEX IF NOT EXISTS wf_case_query ON wf_cases(kind,state,updated_at,id);
CREATE INDEX IF NOT EXISTS wf_case_assignee ON wf_cases(assignee,state,due_date);
CREATE TABLE IF NOT EXISTS wf_actions(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 actor TEXT NOT NULL, action TEXT NOT NULL, previous TEXT NOT NULL, state TEXT NOT NULL,
 note TEXT NOT NULL, at TEXT NOT NULL, data TEXT NOT NULL CHECK(json_valid(data)),
 PRIMARY KEY(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_requests(
 actor TEXT NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 PRIMARY KEY(actor,request_id));
CREATE TABLE IF NOT EXISTS wf_tasks(
 id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES wf_cases(id),
 revision INTEGER NOT NULL, assignee TEXT NOT NULL, action TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','done')), created_at TEXT NOT NULL, finished_at TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS wf_pending_task ON wf_tasks(case_id) WHERE status='pending';
CREATE INDEX IF NOT EXISTS wf_user_tasks ON wf_tasks(assignee,status,created_at);
CREATE TABLE IF NOT EXISTS wf_points(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), position INTEGER NOT NULL CHECK(position>=0),
 name TEXT NOT NULL, standard TEXT NOT NULL, result TEXT NOT NULL CHECK(result IN ('pending','normal','abnormal')),
 note TEXT NOT NULL, actor TEXT NOT NULL, at TEXT NOT NULL,
 issue_id TEXT REFERENCES wf_cases(id), PRIMARY KEY(case_id,position));
CREATE TABLE IF NOT EXISTS wf_hazard_corrections(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 department TEXT NOT NULL, actual_date TEXT NOT NULL, reason TEXT NOT NULL,
 description TEXT NOT NULL, cost TEXT NOT NULL, preventive_measures TEXT NOT NULL DEFAULT '',
 PRIMARY KEY(case_id,revision), FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_reviews(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 result TEXT NOT NULL CHECK(result IN ('pass','return')), description TEXT NOT NULL,
 actor TEXT NOT NULL, at TEXT NOT NULL,
 PRIMARY KEY(case_id,revision), FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_work_checks(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 kind TEXT NOT NULL, content TEXT NOT NULL, actor TEXT NOT NULL, at TEXT NOT NULL,
 PRIMARY KEY(case_id,revision,kind), FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE TABLE IF NOT EXISTS wf_resources(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL, warehouse TEXT NOT NULL,
 unit TEXT NOT NULL, quantity INTEGER NOT NULL CHECK(quantity>=0),
 reserved INTEGER NOT NULL CHECK(reserved>=0 AND reserved<=quantity), revision INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS wf_reservations(
 case_id TEXT NOT NULL REFERENCES wf_cases(id), resource_id TEXT NOT NULL REFERENCES wf_resources(id),
 quantity INTEGER NOT NULL CHECK(quantity>0), state TEXT NOT NULL CHECK(state IN ('reserved','returned')),
 actor TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY(case_id,resource_id));
CREATE TABLE IF NOT EXISTS wf_resource_requests(
 actor TEXT NOT NULL, request_id TEXT NOT NULL, digest TEXT NOT NULL,
 resource_id TEXT NOT NULL REFERENCES wf_resources(id), PRIMARY KEY(actor,request_id));
CREATE TABLE IF NOT EXISTS wf_stock_events(
 resource_id TEXT NOT NULL REFERENCES wf_resources(id), revision INTEGER NOT NULL,
 actor TEXT NOT NULL, action TEXT NOT NULL, quantity_delta INTEGER NOT NULL,
 reserved_delta INTEGER NOT NULL, case_id TEXT REFERENCES wf_cases(id), at TEXT NOT NULL,
 PRIMARY KEY(resource_id,revision));
'''
SCHEMA += MATERIAL_SCHEMA
KINDS = {'hazard':'隐患闭环','inspection':'智能巡检','investigation':'隐患排查','work':'特殊作业','event':'事件处置'}
STATES = {'reported':'待派发','assigned':'待处理','review':'待复查','closed':'已闭环','draft':'草稿','submitted':'待审批','approved':'待开工','active':'作业中','acceptance':'待验收','triage':'待研判','responding':'响应中','resolved':'待结案','planned':'待下发','running':'执行中'}
COORDINATE_SYSTEMS=('待核实','WGS84','CGCS2000','GCJ02','BD09')
WORK_TYPES=('动火作业','受限空间作业','盲板抽堵作业','高处作业','吊装作业','临时用电作业','动土作业','断路作业')
def now():return datetime.now(timezone.utc).isoformat()
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def text(v,label,limit=2000,required=True):
 if not isinstance(v,str) or len(v)>limit or required and not v.strip():raise DemoError(400,label+'无效')
 return v.strip()
def day(v,label):
 try:
  if not isinstance(v,str) or len(v)!=10 or date.fromisoformat(v).isoformat()!=v:raise ValueError()
 except ValueError:raise DemoError(400,label+'需为有效日期')
 return v
def keys(v,allowed,required=()):
 if not isinstance(v,dict) or set(v)-set(allowed) or set(required)-set(v):raise DemoError(400,'字段不完整或包含未知字段')
def integer(v,label,minimum=0,maximum=1000000000):
 if type(v) is not int or not minimum<=v<=maximum:raise DemoError(400,label+'无效')
 return v

class WorkflowStore(WorkflowMaterials):
 def __init__(self,path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with closing(self.connect()) as db:
   version=db.execute('PRAGMA user_version').fetchone()[0]
   if version not in (0,1,2):raise ValueError('Unsupported workflow database')
   columns={x[1] for x in db.execute('PRAGMA table_info(wf_hazard_corrections)')}
   migration="ALTER TABLE wf_hazard_corrections ADD COLUMN preventive_measures TEXT NOT NULL DEFAULT '';" if columns and 'preventive_measures' not in columns else ''
   db.execute('PRAGMA journal_mode=WAL');db.executescript('BEGIN IMMEDIATE;'+SCHEMA+migration+'PRAGMA user_version=2;COMMIT;')
 def connect(self):
  db=sqlite3.connect(self.path,timeout=5);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');return db
 @staticmethod
 def actor(actor,users):
  if actor not in users:raise DemoError(403,'处理账号不在当前项目中')
  return actor
 @staticmethod
 def row(r):return {**dict(r),'details':json.loads(r['details']),'stateName':STATES[r['state']],'isOverdue':bool(r['due_date'] and r['due_date']<date.today().isoformat() and r['state']!='closed'),'dataSource':'user_entered_test'}
 def catalog(self,actor,users):
  self.actor(actor,users)
  return dict(schema='xnby.business.workflow.v1',version='0.9.0',referenceRevision='20261022-r2',workflowSchemaVersion=2,user=actor,users=sorted(users),kinds=KINDS,states=STATES,workTypes=WORK_TYPES,coordinateSystems=COORDINATE_SYSTEMS,dataSource='user_entered_test',fixtureCount=0,scope='project_test_workspace')
 def list(self,actor,users,kind='',state='',q='',page=1,mine=False):
  self.actor(actor,users);text(q,'查询',128,False);integer(page,'页码',1,100000)
  if kind and kind not in KINDS or state and state not in STATES:raise DemoError(400,'类别或状态无效')
  conditions=['1=1'];args=[]
  for column,value in [('kind',kind),('state',state)]:
   if value:conditions.append(column+'=?');args.append(value)
  if q:conditions.append('(instr(title,?)>0 OR instr(enterprise,?)>0 OR instr(id,?)>0)');args.extend([q]*3)
  if mine:conditions.append("id IN (SELECT case_id FROM wf_tasks WHERE assignee=? AND status='pending')");args.append(actor)
  clause=' AND '.join(conditions)
  with closing(self.connect()) as db:
   total=db.execute('SELECT count(*) FROM wf_cases WHERE '+clause,args).fetchone()[0]
   rows=db.execute('SELECT * FROM wf_cases WHERE '+clause+' ORDER BY updated_at DESC,id LIMIT 20 OFFSET ?',args+[(page-1)*20]).fetchall()
  return dict(total=total,page=page,pageSize=20,records=[self.row(r) for r in rows])
 def detail(self,actor,users,identity):
  self.actor(actor,users)
  with closing(self.connect()) as db:
   r=db.execute('SELECT * FROM wf_cases WHERE id=?',(identity,)).fetchone()
   if not r:raise DemoError(404,'业务记录不存在')
   record=self.row(r);events=[{**dict(e),'data':json.loads(e['data'])} for e in db.execute('SELECT * FROM wf_actions WHERE case_id=? ORDER BY revision',(identity,))]
   points=[dict(p) for p in db.execute('SELECT * FROM wf_points WHERE case_id=? ORDER BY position',(identity,))]
   tasks=[dict(t) for t in db.execute('SELECT * FROM wf_tasks WHERE case_id=? ORDER BY created_at,id',(identity,))]
   corrections=[dict(c) for c in db.execute('SELECT * FROM wf_hazard_corrections WHERE case_id=? ORDER BY revision',(identity,))]
   checks=[dict(c) for c in db.execute('SELECT * FROM wf_work_checks WHERE case_id=? ORDER BY revision,kind',(identity,))]
   materials=[material_metadata(x) for x in db.execute('SELECT id,case_id,revision,name,media_type,bytes,sha256,actor,created_at,description FROM wf_materials WHERE case_id=? ORDER BY revision,id',(identity,))]
   resources=[dict(x) for x in db.execute('SELECT r.*,s.name,s.unit FROM wf_reservations r JOIN wf_resources s ON s.id=r.resource_id WHERE case_id=?',(identity,))]
   reviews=[dict(v) for v in db.execute('SELECT * FROM wf_reviews WHERE case_id=? ORDER BY revision',(identity,))]
  permitted=self.actions(record,actor)
  if corrections and 'withdraw' in permitted:permitted.remove('withdraw')
  return dict(record=record,events=events,points=points,tasks=tasks,corrections=corrections,reviews=reviews,checks=checks,resources=resources,materials=materials,actions=permitted)
 @staticmethod
 def actions(r,actor):
  owner=r['reporter']==actor;assigned=r['assignee']==actor;reviewer=r['reviewer']==actor;state=r['state'];kind=r['kind'];result=[]
  if kind=='hazard':
   if state=='reported' and owner:result=['dispatch']
   if state=='assigned' and assigned:result=['correct']
   if state=='assigned' and owner:result.append('withdraw')
   if state=='review' and reviewer:result=['approve','reject']
  elif kind in ('inspection','investigation'):
   if state=='planned' and owner:result=['dispatch']
   if state=='running' and assigned:result=['point','finish']
   if state=='review' and reviewer:result=['approve','reject']
  elif kind=='work':
   if state=='draft' and owner:result=['submit']
   if state=='submitted' and reviewer:result=['approve','reject']
   if state=='approved' and assigned:result=['measure','brief','gas','start']
   if state=='active' and assigned:result=['finish']
   if state=='acceptance' and reviewer:result=['approve','reject']
  elif kind=='event':
   if state=='triage' and owner:result=['dispatch']
   if state=='responding' and assigned:result=['progress','reserve','return','resolve']
   if state=='resolved' and reviewer:result=['approve','reject']
  return result
 def summary(self,actor,users):
  self.actor(actor,users)
  with closing(self.connect()) as db:
   counts={r['kind']:r['n'] for r in db.execute('SELECT kind,count(*) n FROM wf_cases GROUP BY kind')}
   pending=db.execute("SELECT count(*) FROM wf_tasks WHERE assignee=? AND status='pending'",(actor,)).fetchone()[0]
   overdue=db.execute("SELECT count(*) FROM wf_cases WHERE due_date<>'' AND due_date<? AND state<>'closed'",(date.today().isoformat(),)).fetchone()[0]
   states={r['state']:r['n'] for r in db.execute('SELECT state,count(*) n FROM wf_cases GROUP BY state')}
  return dict(total=sum(counts.values()),counts=counts,pending=pending,overdue=overdue,states=states,computedAt=now(),dataSource='user_entered_test')
 @staticmethod
 def audit(db,r,actor,action,previous,note,data):
  db.execute('INSERT INTO wf_actions VALUES (?,?,?,?,?,?,?,?,?)',(r['id'],r['revision'],actor,action,previous,r['state'],note,r['updated_at'],canonical(data)))
 @staticmethod
 def task(db,r,assignee,action):
  db.execute("UPDATE wf_tasks SET status='done',finished_at=? WHERE case_id=? AND status='pending'",(r['updated_at'],r['id']))
  if assignee:db.execute('INSERT INTO wf_tasks VALUES (?,?,?,?,?,?,?,?)',(uuid.uuid4().hex,r['id'],r['revision'],assignee,action,'pending',r['updated_at'],None))
 @staticmethod
 def request(db,actor,request_id,payload):
  if not isinstance(request_id,str) or not re.fullmatch('[a-f0-9]{32}',request_id):raise DemoError(400,'请求幂等键无效')
  digest=hashlib.sha256(canonical(payload).encode()).hexdigest();old=db.execute('SELECT * FROM wf_requests WHERE actor=? AND request_id=?',(actor,request_id)).fetchone()
  if old and old['digest']!=digest:raise DemoError(409,'相同请求键不能提交不同内容')
  return digest,old
 def create(self,actor,users,request_id,form):
  self.actor(actor,users);keys(form,['kind','title','enterprise','location','description','level','workType','dueDate','points','coordinates','eventType'],['kind','title','enterprise','location','description'])
  kind=form['kind']
  if kind not in KINDS:raise DemoError(400,'业务类别无效')
  title=text(form['title'],'标题',160);enterprise=text(form['enterprise'],'企业',160);location=text(form['location'],'位置',256);description=text(form['description'],'描述',4000)
  details={'description':description,'level':text(form.get('level','一般'),'级别',32),'source':'现场上报' if kind in ('hazard','event') else KINDS[kind]}
  if kind=='event':details['eventType']=text(form.get('eventType','未分类'),'事件类型',100)
  due=day(form['dueDate'],'期限') if form.get('dueDate') else ''
  coordinates=form.get('coordinates')
  if coordinates is not None:
   keys(coordinates,['longitude','latitude','system'],['longitude','latitude','system'])
   lon,lat=coordinates['longitude'],coordinates['latitude']
   if type(lon) not in (int,float) or type(lat) not in (int,float) or not math.isfinite(lon) or not math.isfinite(lat) or not -180<=lon<=180 or not -90<=lat<=90 or coordinates['system'] not in COORDINATE_SYSTEMS:raise DemoError(400,'坐标或坐标系无效')
   details['coordinates']=dict(longitude=lon,latitude=lat,system=coordinates['system'])
  elif kind=='event':raise DemoError(400,'事件上报需填写坐标及坐标系')
  if kind=='work':
   if form.get('workType') not in WORK_TYPES:raise DemoError(400,'作业类型无效')
   details['workType']=form['workType']
  points=form.get('points',[])
  if kind in ('inspection','investigation'):
   if not isinstance(points,list) or not 1<=len(points)<=100:raise DemoError(400,'巡检/排查需1至100个检查点项')
   for p in points:keys(p,['name','standard'],['name','standard'])
   points=[dict(name=text(p.get('name'),'检查点',160),standard=text(p.get('standard'),'检查标准',512)) for p in points]
   if len(points)!=len(form['points']):raise DemoError(400,'检查点格式无效')
  elif points:raise DemoError(400,'该类别不接受检查点')
  initial={'hazard':'reported','event':'triage','work':'draft','inspection':'planned','investigation':'planned'}[kind]
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');digest,old=self.request(db,actor,request_id,form)
   if old:return self.detail(actor,users,old['case_id'])
   at=now();identity=uuid.uuid4().hex
   db.execute('INSERT INTO wf_cases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(identity,kind,title,enterprise,location,initial,1,actor,'','',due,at,at,canonical(details),None))
   r=dict(db.execute('SELECT * FROM wf_cases WHERE id=?',(identity,)).fetchone());self.audit(db,r,actor,'create','',description,form);self.task(db,r,actor,'submit' if kind=='work' else 'dispatch')
   for n,p in enumerate(points):db.execute('INSERT INTO wf_points VALUES (?,?,?,?,?,?,?,?,?)',(identity,n,p['name'],p['standard'],'pending','','','',None))
   db.execute('INSERT INTO wf_requests VALUES (?,?,?,?,?)',(actor,request_id,digest,identity,1));db.commit()
  return self.detail(actor,users,identity)
 def command(self,actor,users,request_id,identity,revision,action,data):
  fields={'dispatch':['assignee','reviewer','dueDate'],'submit':['assignee','reviewer','dueDate'],'correct':['department','actualDate','reason','description','cost','preventiveMeasures'],'point':['position','result'],'reserve':['resourceId','quantity'],'return':['resourceId']}
  self.actor(actor,users);integer(revision,'记录版本',1);keys(data,['note']+fields.get(action,[]))
  payload=dict(identity=identity,revision=revision,action=action,data=data)
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');digest,old=self.request(db,actor,request_id,payload)
   if old:return self.detail(actor,users,old['case_id'])
   source=db.execute('SELECT * FROM wf_cases WHERE id=?',(identity,)).fetchone()
   if not source:raise DemoError(404,'业务记录不存在')
   r=dict(source);previous=r['state'];kind=r['kind']
   if r['revision']!=revision:raise DemoError(409,'记录已更新，请刷新后重新处理')
   if action not in self.actions(r,actor):raise DemoError(403,'当前账号或业务状态不允许此操作')
   note=text(data.get('note',''),'处理说明',2000);r['revision']+=1;r['updated_at']=now();next_user='';next_action=''
   if action in ('dispatch','submit'):
    assignee=self.actor(data.get('assignee'),users);reviewer=self.actor(data.get('reviewer'),users)
    if assignee==reviewer:raise DemoError(400,'执行人与复核人不能为同一账号')
    r.update(assignee=assignee,reviewer=reviewer,due_date=day(data.get('dueDate'),'期限'))
    r['state']='submitted' if action=='submit' else 'running' if kind in ('inspection','investigation') else 'responding' if kind=='event' else 'assigned'
    next_user=reviewer if action=='submit' else assignee;next_action='approve' if action=='submit' else 'execute'
   elif action=='withdraw':
    if db.execute('SELECT 1 FROM wf_hazard_corrections WHERE case_id=?',(identity,)).fetchone():raise DemoError(409,'已有整改历史，不能撤回派发')
    r['state']='reported';r['assignee']='';r['reviewer']='';next_user=r['reporter'];next_action='dispatch'
   elif action=='correct':
    text(data.get('preventiveMeasures',''),'预防措施',2000,False)
    for key,label in [('department','整改部门'),('reason','原因'),('description','整改情况')]:text(data.get(key),label,2000)
    day(data.get('actualDate'),'实际整改日期')
    try:
     cost=Decimal(data.get('cost',''));assert cost.is_finite() and 0<=cost<=Decimal('1000000000') and cost.as_tuple().exponent>=-2
    except (InvalidOperation,AssertionError,TypeError):raise DemoError(400,'整改费用需为至多两位小数的非负金额')
    r['state']='review';next_user=r['reviewer'];next_action='approve'
   elif action=='approve':
    r['state']='approved' if kind=='work' and previous=='submitted' else 'closed'
    if r['state']=='approved':next_user=r['assignee'];next_action='start'
    if r['state']=='closed' and db.execute("SELECT 1 FROM wf_reservations WHERE case_id=? AND state='reserved'",(identity,)).fetchone():raise DemoError(409,'仍有未归还调拨资源，不能结案')
   elif action=='reject':
    r['state']='draft' if kind=='work' and previous=='submitted' else 'active' if kind=='work' else 'running' if kind in ('inspection','investigation') else 'responding' if kind=='event' else 'assigned'
    next_user=r['reporter'] if r['state']=='draft' else r['assignee'];next_action='submit' if r['state']=='draft' else 'execute'
   elif action in ('measure','brief','gas','progress'):
    next_user=r['assignee'];next_action='start' if kind=='work' else 'execute'
   elif action=='start':
    completed={x[0] for x in db.execute('SELECT kind FROM wf_work_checks WHERE case_id=?',(identity,))};required={'measure','brief'}
    if json.loads(r['details'])['workType'] in ('动火作业','受限空间作业','临时用电作业'):required.add('gas')
    if required-completed:raise DemoError(409,'开工前需记录安全措施、安全交底及适用的采样检测')
    if r['due_date']<date.today().isoformat():raise DemoError(409,'作业期限已过，不能开工')
    r['state']='active';next_user=r['assignee'];next_action='finish'
   elif action=='point':
    position=integer(data.get('position'),'检查项序号',0,99);result=data.get('result')
    if result not in ('normal','abnormal'):raise DemoError(400,'检查结果无效')
    point=db.execute('SELECT * FROM wf_points WHERE case_id=? AND position=?',(identity,position)).fetchone()
    if not point:raise DemoError(404,'检查项不存在')
    if point['result']!='pending':raise DemoError(409,'该检查项已提交，不能覆盖原记录')
    issue=None
    if result=='abnormal':
     issue=uuid.uuid4().hex;parent_details=json.loads(r['details']);child_details={'description':note,'level':'一般','sourcePoint':position,'source':KINDS[kind],'checkStandard':point['standard']}
     if 'coordinates' in parent_details:child_details['coordinates']=parent_details['coordinates']
     details=canonical(child_details)
     db.execute('INSERT INTO wf_cases VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(issue,'hazard',point['name']+'检查异常',r['enterprise'],r['location'],'reported',1,actor,'','',r['due_date'],r['updated_at'],r['updated_at'],details,identity))
     child=dict(db.execute('SELECT * FROM wf_cases WHERE id=?',(issue,)).fetchone());self.audit(db,child,actor,'inspection_abnormal','',note,{'sourceCase':identity,'position':position});self.task(db,child,actor,'dispatch')
    db.execute('UPDATE wf_points SET result=?,note=?,actor=?,at=?,issue_id=? WHERE case_id=? AND position=?',(result,note,actor,r['updated_at'],issue,identity,position));next_user=r['assignee'];next_action='execute'
   elif action=='finish':
    if kind in ('inspection','investigation') and db.execute("SELECT 1 FROM wf_points WHERE case_id=? AND result='pending'",(identity,)).fetchone():raise DemoError(409,'所有检查项完成后才能提交复核')
    r['state']='acceptance' if kind=='work' else 'review';next_user=r['reviewer'];next_action='approve'
   elif action=='resolve':r['state']='resolved';next_user=r['reviewer'];next_action='approve'
   elif action in ('reserve','return'):
    resource=text(data.get('resourceId'),'资源编号',64);stock=db.execute('SELECT * FROM wf_resources WHERE id=?',(resource,)).fetchone()
    if not stock:raise DemoError(404,'物资不存在')
    existing=db.execute('SELECT * FROM wf_reservations WHERE case_id=? AND resource_id=?',(identity,resource)).fetchone()
    if action=='reserve':
     quantity=integer(data.get('quantity'),'数量',1)
     if stock['quantity']-stock['reserved']<quantity:raise DemoError(409,'可调拨库存不足')
     if existing:raise DemoError(409,'该事件已调拨过此物资，请先完成既有调拨')
     db.execute('UPDATE wf_resources SET reserved=reserved+?,revision=revision+1 WHERE id=?',(quantity,resource));db.execute('INSERT INTO wf_reservations VALUES (?,?,?,?,?,?)',(identity,resource,quantity,'reserved',actor,r['updated_at']))
    else:
     if not existing or existing['state']!='reserved':raise DemoError(409,'无待归还调拨')
     db.execute('UPDATE wf_resources SET reserved=reserved-?,revision=revision+1 WHERE id=?',(existing['quantity'],resource));db.execute("UPDATE wf_reservations SET state='returned' WHERE case_id=? AND resource_id=?",(identity,resource))
    db.execute('INSERT INTO wf_stock_events VALUES (?,?,?,?,?,?,?,?)',(resource,stock['revision']+1,actor,action,0,quantity if action=='reserve' else -existing['quantity'],identity,r['updated_at']))
    next_user=r['assignee'];next_action='execute'
   db.execute('UPDATE wf_cases SET state=?,revision=?,assignee=?,reviewer=?,due_date=?,updated_at=? WHERE id=? AND revision=?',(r['state'],r['revision'],r['assignee'],r['reviewer'],r['due_date'],r['updated_at'],identity,revision))
   self.audit(db,r,actor,action,previous,note,data)
   if action=='correct':db.execute('INSERT INTO wf_hazard_corrections VALUES (?,?,?,?,?,?,?,?)',(identity,r['revision'],data['department'],data['actualDate'],data['reason'],data['description'],str(cost),data.get('preventiveMeasures','')))
   if action in ('approve','reject'):db.execute('INSERT INTO wf_reviews VALUES (?,?,?,?,?,?)',(identity,r['revision'],'pass' if action=='approve' else 'return',note,actor,r['updated_at']))
   if action in ('measure','brief','gas'):db.execute('INSERT INTO wf_work_checks VALUES (?,?,?,?,?,?)',(identity,r['revision'],action,note,actor,r['updated_at']))
   self.task(db,r,next_user,next_action);db.execute('INSERT INTO wf_requests VALUES (?,?,?,?,?)',(actor,request_id,digest,identity,r['revision']));db.commit()
  return self.detail(actor,users,identity)
 def resources(self,actor,users):
  self.actor(actor,users)
  with closing(self.connect()) as db:rows=[dict(r) for r in db.execute('SELECT *,quantity-reserved available FROM wf_resources ORDER BY name,id')]
  return dict(records=rows)
 def create_resource(self,actor,users,request_id,form):
  self.actor(actor,users);keys(form,['name','category','warehouse','unit','quantity'],['name','category','warehouse','unit','quantity'])
  values=[text(form[k],k,160) for k in ('name','category','warehouse','unit')];quantity=integer(form['quantity'],'库存')
  identity=uuid.uuid4().hex
  if not isinstance(request_id,str) or not re.fullmatch('[a-f0-9]{32}',request_id):raise DemoError(400,'请求幂等键无效')
  digest=hashlib.sha256(canonical(form).encode()).hexdigest()
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');old=db.execute('SELECT * FROM wf_resource_requests WHERE actor=? AND request_id=?',(actor,request_id)).fetchone()
   if old:
    if old['digest']!=digest:raise DemoError(409,'相同请求键不能提交不同内容')
   else:
    db.execute('INSERT INTO wf_resources VALUES (?,?,?,?,?,?,?,?)',(identity,*values,quantity,0,1))
    db.execute('INSERT INTO wf_stock_events VALUES (?,?,?,?,?,?,?,?)',(identity,1,actor,'register',quantity,0,None,now()))
    db.execute('INSERT INTO wf_resource_requests VALUES (?,?,?,?)',(actor,request_id,digest,identity));db.commit()
  return self.resources(actor,users)
