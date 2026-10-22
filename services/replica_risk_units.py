"""Risk-analysis units from the reference RiskLevel contract.

The caller supplies a server-authenticated principal and project directory.
This module never accepts account identity or grants from a submitted form.
Regulator delivery is an explicit pending outbox, not a claimed successful send.
"""
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import hashlib, json, re, sqlite3, uuid
from services.reference_errors import DemoError

SCHEMA_VERSION=1
SCHEMA="""
CREATE TABLE IF NOT EXISTS rp_risk_units(
 project TEXT NOT NULL, id TEXT NOT NULL, department_id TEXT NOT NULL, person_id TEXT NOT NULL,
 department TEXT NOT NULL, person TEXT NOT NULL, analysis_object TEXT NOT NULL, analysis_unit TEXT NOT NULL,
 risk_level TEXT NOT NULL, coordinate TEXT NOT NULL, longitude REAL NOT NULL, latitude REAL NOT NULL,
 coordinate_system TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>0),
 deleted INTEGER NOT NULL CHECK(deleted IN (0,1)),created_at TEXT NOT NULL,created_by TEXT NOT NULL,updated_at TEXT NOT NULL,
 PRIMARY KEY(project,id));
CREATE INDEX IF NOT EXISTS rp_risk_unit_scope ON rp_risk_units(project,deleted,department_id,created_at DESC,id);
CREATE INDEX IF NOT EXISTS rp_risk_unit_level ON rp_risk_units(project,deleted,risk_level,created_at DESC,id);
CREATE TABLE IF NOT EXISTS rp_risk_events(
 project TEXT NOT NULL, unit_id TEXT NOT NULL, revision INTEGER NOT NULL,
 action TEXT NOT NULL CHECK(action IN ('create','update','delete')),
 actor TEXT NOT NULL,policy_version TEXT NOT NULL,at TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),sha256 TEXT NOT NULL,
 PRIMARY KEY(project,unit_id,revision),FOREIGN KEY(project,unit_id) REFERENCES rp_risk_units(project,id));
CREATE TABLE IF NOT EXISTS rp_risk_requests(
 project TEXT NOT NULL, actor TEXT NOT NULL,request_id TEXT NOT NULL,digest TEXT NOT NULL,
 unit_id TEXT NOT NULL,revision INTEGER NOT NULL,result TEXT NOT NULL CHECK(json_valid(result)),
 PRIMARY KEY(project,actor,request_id),FOREIGN KEY(project,unit_id,revision) REFERENCES rp_risk_events(project,unit_id,revision));
CREATE TABLE IF NOT EXISTS rp_risk_outbox(
 project TEXT NOT NULL,unit_id TEXT NOT NULL,revision INTEGER NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('pending','delivered','failed')),
 event TEXT NOT NULL,payload TEXT NOT NULL CHECK(json_valid(payload)),sha256 TEXT NOT NULL,created_at TEXT NOT NULL,
 PRIMARY KEY(project,unit_id,revision),FOREIGN KEY(project,unit_id,revision) REFERENCES rp_risk_events(project,unit_id,revision));
CREATE INDEX IF NOT EXISTS rp_risk_outbox_pending ON rp_risk_outbox(project,state,created_at,unit_id,revision);
"""

def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(v):return hashlib.sha256(canonical(v).encode('utf-8')).hexdigest()
def text(v,label,maximum=256):
 if not isinstance(v,str) or not v.strip() or len(v)>maximum or any(ord(c)<32 for c in v):raise DemoError(400,label+'无效')
 return v.strip()
def integer(v,label,minimum=1,maximum=1000000):
 if type(v) is not int or not minimum<=v<=maximum:raise DemoError(400,label+'无效')
 return v

@dataclass(frozen=True)
class RiskPrincipal:
 project:str
 subject:str
 permissions:frozenset
 departments:frozenset
 policy_version:str

class ProjectDirectory:
 """Authoritative project metadata; resolve stable IDs, including duplicate display names."""
 def __init__(self,project,departments,users,risk_levels,version):
  self.project=text(project,'项目标识',128);self.version=text(version,'目录版本',128)
  self.departments={};self.users={};self.risk_levels={}
  for item in departments:
   identity=text(item['id'],'部门标识',128)
   if identity in self.departments:raise ValueError('Duplicate department ID')
   self.departments[identity]=dict(id=identity,name=text(item['name'],'部门名称'),parent=item.get('parent'))
  for identity,item in self.departments.items():
   seen={identity};parent=item['parent']
   while parent:
    if parent not in self.departments or parent in seen:raise ValueError('Invalid department hierarchy')
    seen.add(parent);parent=self.departments[parent]['parent']
  for item in users:
   identity=text(item['id'],'账号标识',128);memberships=item['departments']
   if identity in self.users or not isinstance(memberships,list) or not memberships or len(set(memberships))!=len(memberships) or any(x not in self.departments for x in memberships) or type(item.get('enabled',True)) is not bool:raise ValueError('Invalid project user')
   self.users[identity]=dict(id=identity,name=text(item['name'],'人员名称'),departments=frozenset(memberships),enabled=item.get('enabled',True))
  for item in risk_levels:
   code=text(item['code'],'风险等级编码',64)
   if code in self.risk_levels:raise ValueError('Duplicate risk level code')
   self.risk_levels[code]=text(item['name'],'风险等级名称',128)
  if not self.risk_levels:raise ValueError('Risk dictionary is required')
 def require(self,principal,action):
  user=self.users.get(principal.subject)
  if principal.project!=self.project or not user or not user['enabled'] or not principal.departments<=self.departments.keys() or 'risk-unit:'+action not in principal.permissions:raise DemoError(403,'当前账号没有该项目操作权限')
  return principal.departments
 def resolve(self,identity,name,collection,label):
  if identity is not None and identity!='':
   identity=text(identity,label+'标识',128)
   row=collection.get(identity)
   if not row or row['name']!=name:raise DemoError(400,label+'标识与名称不一致')
   return row
  matches=[x for x in collection.values() if x['name']==name]
  if len(matches)!=1:raise DemoError(400,label+'名称无法唯一确定，请重新选择')
  return matches[0]
 def form(self,principal,value):
  allowed={'department','person','departmentId','personId','analysisObject','analysisUnit','riskLevel','coordinate','coordinateSystem'}
  if not isinstance(value,dict) or set(value)-allowed:raise DemoError(400,'风险单元存在未知字段')
  department=self.resolve(value.get('departmentId'),text(value.get('department'),'责任部门'),self.departments,'责任部门')
  if department['id'] not in principal.departments:raise DemoError(403,'不允许操作此部门的数据')
  person=self.resolve(value.get('personId'),text(value.get('person'),'部门责任人'),self.users,'部门责任人')
  if not person['enabled'] or department['id'] not in person['departments']:raise DemoError(400,'责任人不属于所选部门或账号已停用')
  level=text(value.get('riskLevel'),'风险等级',64)
  if level not in self.risk_levels:raise DemoError(400,'风险等级不在当前项目字典内')
  coordinate=text(value.get('coordinate'),'坐标',160);parts=coordinate.split(',')
  try:
   if len(parts)!=2:raise InvalidOperation()
   if any(not re.fullmatch(r'[+-]?(?:\d{1,3}(?:\.\d{1,12})?|\.\d{1,12})',part.strip(),flags=re.ASCII) for part in parts):raise InvalidOperation()
   lon,lat=(Decimal(part.strip()) for part in parts)
   if not lon.is_finite() or not lat.is_finite() or not -180<=lon<=180 or not -90<=lat<=90:raise InvalidOperation()
  except InvalidOperation:raise DemoError(400,'坐标需为有限的经度,纬度数值')
  system=value.get('coordinateSystem','待核实')
  if system not in ('待核实','WGS84','CGCS2000','GCJ02','BD09'):raise DemoError(400,'坐标系无效')
  return dict(departmentId=department['id'],department=department['name'],personId=person['id'],person=person['name'],analysisObject=text(value.get('analysisObject'),'风险分析对象'),analysisUnit=text(value.get('analysisUnit'),'风险分析单元'),riskLevel=level,coordinate=coordinate,longitude=float(lon),latitude=float(lat),coordinateSystem=system)

class RiskUnitStore:
 def __init__(self,path):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
  with closing(self.connect()) as db:
   version=db.execute('PRAGMA user_version').fetchone()[0]
   if version not in (0,SCHEMA_VERSION):raise ValueError('Unsupported risk-unit database')
   actual={(r['type'],r['name']):r['sql'] for r in db.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")}
   with closing(sqlite3.connect(':memory:')) as template:
    template.executescript(SCHEMA)
    expected={(r[0],r[1]):r[2] for r in template.execute("SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%'")}
   if (version==0 and actual) or (version==SCHEMA_VERSION and actual!=expected):raise ValueError('Risk-unit schema does not match; automatic repair is disabled')
   db.execute('PRAGMA journal_mode=WAL')
   if version==0:db.executescript('BEGIN IMMEDIATE;'+SCHEMA+f'PRAGMA user_version={SCHEMA_VERSION};COMMIT;')
 def connect(self):
  db=sqlite3.connect(self.path,timeout=5,isolation_level=None);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');db.execute('PRAGMA synchronous=FULL');return db
 @contextmanager
 def transaction(self,write=False):
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
   try:yield db;db.commit()
   except Exception:db.rollback();raise
 @staticmethod
 def row(row):
  return dict(id=row['id'],departmentId=row['department_id'],department=row['department'],personId=row['person_id'],person=row['person'],analysisObject=row['analysis_object'],analysisUnit=row['analysis_unit'],riskLevel=row['risk_level'],coordinate=row['coordinate'],coordinateSystem=row['coordinate_system'],revision=row['revision'],deleted=bool(row['deleted']),createTime=row['created_at'],createBy=row['created_by'],updateTime=row['updated_at'])
 @staticmethod
 def scope(principal):
  ids=sorted(principal.departments)
  return ('department_id IN ('+','.join('?' for _ in ids)+')',ids) if ids else ('0=1',[])
 def get(self,principal,directory,identity):
  directory.require(principal,'read');text(identity,'单元标识',64)
  with self.transaction() as db:return self.read(db,principal,identity)
 def read(self,db,principal,identity,*,include_deleted=False):
  clause,args=self.scope(principal);row=db.execute('SELECT * FROM rp_risk_units WHERE project=? AND id=? AND '+clause+('' if include_deleted else ' AND deleted=0'),[principal.project,identity,*args]).fetchone()
  if not row:raise DemoError(404,'风险分析单元不存在或不在当前数据范围内')
  return self.row(row)
 def query(self,principal,directory,filters=None,current=1,size=10,*,export=False):
  directory.require(principal,'export' if export else 'read');integer(current,'页码',1,1000000);integer(size,'每页条数',1,100)
  filters={} if filters is None else filters
  if not isinstance(filters,dict) or set(filters)-{'department','departmentId','analysisObject','analysisUnit','riskLevel'}:raise DemoError(400,'查询条件无效')
  clause,args=self.scope(principal);clauses=['project=?','deleted=0',clause];args=[principal.project,*args]
  for key,column in [('department','department'),('analysisObject','analysis_object'),('analysisUnit','analysis_unit'),('riskLevel','risk_level'),('departmentId','department_id')]:
   value=filters.get(key)
   if value is None or value=='':continue
   value=text(value,key)
   if key in ('riskLevel','departmentId'):clauses.append(column+'=?');args.append(value)
   else:clauses.append('instr('+column+',?)>0');args.append(value)
  where=' AND '.join(clauses)
  with self.transaction() as db:
   total=db.execute('SELECT count(*) FROM rp_risk_units WHERE '+where,args).fetchone()[0]
   if export and total>10000:raise DemoError(413,'导出超过10000条，请缩小筛选范围')
   rows=db.execute('SELECT * FROM rp_risk_units WHERE '+where+' ORDER BY created_at DESC,id LIMIT ? OFFSET ?',args+([10000,0] if export else [size,(current-1)*size])).fetchall()
  return dict(records=[self.row(x) for x in rows],total=total,current=current,size=size)
 def save(self,principal,directory,key,value,*,identity=None,revision=None):
  directory.require(principal,'update' if identity else 'create');normalized=directory.form(principal,value)
  if identity:text(identity,'单元标识',64);integer(revision,'单元版本')
  payload=dict(action='update' if identity else 'create',id=identity,revision=revision,form=value)
  with self.transaction(True) as db:
   old=self.replay(db,principal,key,payload)
   if old is not None:return old
   at=datetime.now(timezone.utc).isoformat();unit_id=identity or uuid.uuid4().hex
   if identity:
    current=self.read(db,principal,identity)
    if current['revision']!=revision:raise DemoError(409,'风险单元已更新，请刷新后重新编辑')
    self.write_update(db,principal.project,identity,revision,normalized,at)
   else:
    db.execute('INSERT INTO rp_risk_units VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(principal.project,unit_id,normalized['departmentId'],normalized['personId'],normalized['department'],normalized['person'],normalized['analysisObject'],normalized['analysisUnit'],normalized['riskLevel'],normalized['coordinate'],normalized['longitude'],normalized['latitude'],normalized['coordinateSystem'],1,0,at,principal.subject,at))
   result=self.read(db,principal,unit_id);self.event(db,principal,key,payload,result,directory.version,at);return result
 @staticmethod
 def write_update(db,project,identity,revision,value,at):
  result=db.execute('UPDATE rp_risk_units SET department_id=?,person_id=?,department=?,person=?,analysis_object=?,analysis_unit=?,risk_level=?,coordinate=?,longitude=?,latitude=?,coordinate_system=?,revision=revision+1,updated_at=? WHERE project=? AND id=? AND revision=? AND deleted=0',(value['departmentId'],value['personId'],value['department'],value['person'],value['analysisObject'],value['analysisUnit'],value['riskLevel'],value['coordinate'],value['longitude'],value['latitude'],value['coordinateSystem'],at,project,identity,revision))
  if result.rowcount!=1:raise DemoError(409,'风险单元版本冲突')
 def delete(self,principal,directory,key,identity,revision):
  directory.require(principal,'delete');text(identity,'单元标识',64);integer(revision,'单元版本');payload=dict(action='delete',id=identity,revision=revision)
  with self.transaction(True) as db:
   old=self.replay(db,principal,key,payload)
   if old is not None:return old
   current=self.read(db,principal,identity)
   if current['revision']!=revision:raise DemoError(409,'风险单元已更新，请刷新后重新删除')
   at=datetime.now(timezone.utc).isoformat();db.execute('UPDATE rp_risk_units SET deleted=1,revision=revision+1,updated_at=? WHERE project=? AND id=? AND revision=?',(at,principal.project,identity,revision))
   result=self.read(db,principal,identity,include_deleted=True);self.event(db,principal,key,payload,result,directory.version,at);return result
 def replay(self,db,principal,key,payload):
  if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{32}',key):raise DemoError(400,'请求幂等键无效')
  old=db.execute('SELECT * FROM rp_risk_requests WHERE project=? AND actor=? AND request_id=?',(principal.project,principal.subject,key)).fetchone()
  if old:
   if old['digest']!=digest(payload):raise DemoError(409,'相同请求键不能提交不同内容')
   self.read(db,principal,old['unit_id'],include_deleted=True)
   event=db.execute('SELECT payload,sha256 FROM rp_risk_events WHERE project=? AND unit_id=? AND revision=?',(principal.project,old['unit_id'],old['revision'])).fetchone()
   if not event or hashlib.sha256(event['payload'].encode('utf-8')).hexdigest()!=event['sha256']:raise DemoError(503,'审计摘要不一致，请联系运维')
   result=json.loads(old['result']);record=json.loads(event['payload'])['record']
   if result!=record:raise DemoError(503,'请求回执与审计记录不一致，请联系运维')
   if record['departmentId'] not in principal.departments:raise DemoError(404,'风险分析单元不存在或不在当前数据范围内')
   return result
  return None
 @staticmethod
 def event(db,principal,key,payload,result,directory_version,at):
  event=dict(record=result,actor=principal.subject,policyVersion=principal.policy_version,directoryVersion=directory_version,action=payload['action']);raw=canonical(event);sha=hashlib.sha256(raw.encode('utf-8')).hexdigest()
  db.execute('INSERT INTO rp_risk_events VALUES (?,?,?,?,?,?,?,?,?)',(principal.project,result['id'],result['revision'],payload['action'],principal.subject,principal.policy_version,at,raw,sha))
  db.execute('INSERT INTO rp_risk_requests VALUES (?,?,?,?,?,?,?)',(principal.project,principal.subject,key,digest(payload),result['id'],result['revision'],canonical(result)))
  db.execute('INSERT INTO rp_risk_outbox VALUES (?,?,?,?,?,?,?,?)',(principal.project,result['id'],result['revision'],'pending','risk-unit.'+payload['action'],raw,sha,at))
 def history(self,principal,directory,identity):
  directory.require(principal,'audit')
  with self.transaction() as db:
   self.read(db,principal,identity,include_deleted=True);result=[]
   for row in db.execute('SELECT * FROM rp_risk_events WHERE project=? AND unit_id=? ORDER BY revision',(principal.project,identity)):
    if hashlib.sha256(row['payload'].encode('utf-8')).hexdigest()!=row['sha256']:raise DemoError(503,'审计摘要不一致，请联系运维')
    result.append({**dict(row),'payload':json.loads(row['payload'])})
   return result
