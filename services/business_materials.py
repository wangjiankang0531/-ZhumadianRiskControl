"""Immutable case evidence, signed-in actor and same-transaction case audit."""
import base64,hashlib,json,re,uuid
from datetime import datetime,timezone
from contextlib import closing
from services.reference_errors import DemoError
from services.reference_plan_materials import checked,MAX_BYTES,MAX_JSON
MATERIAL_SCHEMA='''
CREATE TABLE IF NOT EXISTS wf_materials(
 id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES wf_cases(id), revision INTEGER NOT NULL,
 name TEXT NOT NULL, media_type TEXT NOT NULL, bytes INTEGER NOT NULL CHECK(bytes>0 AND bytes<=2097152),
 sha256 TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL, description TEXT NOT NULL,
 payload BLOB NOT NULL CHECK(length(payload)=bytes),
 FOREIGN KEY(case_id,revision) REFERENCES wf_actions(case_id,revision));
CREATE INDEX IF NOT EXISTS wf_case_materials ON wf_materials(case_id,revision);
'''
def meta(r):return {k:r[k] for k in ('id','case_id','revision','name','media_type','bytes','sha256','actor','created_at','description')}

class WorkflowMaterials:
 def add_material(self,actor,users,request_id,identity,revision,name,mediaType,base64Data,description):
  self.actor(actor,users)
  if type(revision) is not int or revision<1:raise DemoError(400,'记录版本无效')
  if not isinstance(description,str) or not description.strip() or len(description)>2000:raise DemoError(400,'请填写材料说明')
  if not isinstance(base64Data,str) or len(base64Data)>((MAX_BYTES+2)//3)*4:raise DemoError(400,'材料需为不超过2MiB的原文件')
  try:raw=base64.b64decode(base64Data,validate=True)
  except (ValueError,TypeError):raise DemoError(400,'材料编码无效')
  digest=checked(name,mediaType,raw)
  command=dict(identity=identity,revision=revision,name=name,mediaType=mediaType,sha256=digest,description=description)
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');request_digest,old=self.request(db,actor,request_id,command)
   if old:return self.detail(actor,users,old['case_id'])
   r=db.execute('SELECT * FROM wf_cases WHERE id=?',(identity,)).fetchone()
   if not r:raise DemoError(404,'业务记录不存在')
   r=dict(r)
   if r['revision']!=revision:raise DemoError(409,'记录已更新，请刷新后重新上传')
   if actor not in (r['reporter'],r['assignee'],r['reviewer']):raise DemoError(403,'仅本记录参与人可以添加材料')
   if r['state']=='closed':raise DemoError(409,'闭环记录不能追加材料')
   count,total=db.execute('SELECT count(*),coalesce(sum(bytes),0) FROM wf_materials WHERE case_id=?',(identity,)).fetchone()
   if count>=8 or total+len(raw)>16*1048576:raise DemoError(409,'每记录最多8份材料、总量16MiB')
   r['revision']+=1;r['updated_at']=datetime.now(timezone.utc).isoformat();material_id=uuid.uuid4().hex
   metadata=dict(id=material_id,name=name,mediaType=mediaType,bytes=len(raw),sha256=digest,description=description)
   db.execute('UPDATE wf_cases SET revision=?,updated_at=? WHERE id=?',(r['revision'],r['updated_at'],identity))
   self.audit(db,r,actor,'material',r['state'],description,metadata)
   db.execute('INSERT INTO wf_materials VALUES (?,?,?,?,?,?,?,?,?,?,?)',(material_id,identity,r['revision'],name,mediaType,len(raw),digest,actor,r['updated_at'],description,raw))
   db.execute('INSERT INTO wf_requests VALUES (?,?,?,?,?)',(actor,request_id,request_digest,identity,r['revision']));db.commit()
  return self.detail(actor,users,identity)
 def material(self,actor,users,identity,material_id):
  self.actor(actor,users)
  if not isinstance(material_id,str) or not re.fullmatch('[a-f0-9]{32}',material_id):raise DemoError(400,'材料编号无效')
  with closing(self.connect()) as db:r=db.execute('SELECT * FROM wf_materials WHERE case_id=? AND id=?',(identity,material_id)).fetchone()
  if not r:raise DemoError(404,'材料不存在或不属于该记录')
  raw=bytes(r['payload'])
  if len(raw)!=r['bytes'] or hashlib.sha256(raw).hexdigest()!=r['sha256']:raise DemoError(503,'材料校验失败，请联系运维')
  return raw,meta(r)
