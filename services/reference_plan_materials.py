"""Version-scoped synthetic-plan attachments. Payloads are immutable and local to SQLite."""
import base64,hashlib,re,unicodedata,uuid
from contextlib import closing
from services.reference_errors import DemoError
MAX_BYTES=2*1048576
MAX_JSON=((MAX_BYTES+2)//3)*4+32768
MAX_ACTIVE=8
MAX_PLAN_BYTES=32*1048576
MAX_PLAN_FILES=32
TYPES={'application/pdf':('.pdf',),'image/png':('.png',),'image/jpeg':('.jpg','.jpeg')}
MATERIAL_TABLES=('demo_plan_materials','demo_plan_version_materials','demo_plan_review_materials')
MATERIAL_SCHEMA="""
CREATE TABLE IF NOT EXISTS demo_plan_materials (
 entity TEXT NOT NULL, id TEXT NOT NULL, material_id TEXT NOT NULL, record_revision INTEGER NOT NULL,
 name TEXT NOT NULL, media_type TEXT NOT NULL, bytes INTEGER NOT NULL CHECK(bytes>0 AND bytes<=2097152),
 sha256 TEXT NOT NULL, created_at TEXT NOT NULL, description TEXT NOT NULL, payload BLOB NOT NULL CHECK(length(payload)=bytes),
 PRIMARY KEY(entity,id,material_id), FOREIGN KEY(entity,id,record_revision) REFERENCES demo_events(entity,id,revision));
CREATE TABLE IF NOT EXISTS demo_plan_version_materials (
 entity TEXT NOT NULL, id TEXT NOT NULL, version INTEGER NOT NULL, material_id TEXT NOT NULL,
 PRIMARY KEY(entity,id,version,material_id), FOREIGN KEY(entity,id,version) REFERENCES demo_plan_versions(entity,id,version),
 FOREIGN KEY(entity,id,material_id) REFERENCES demo_plan_materials(entity,id,material_id));
CREATE TABLE IF NOT EXISTS demo_plan_review_materials (
 entity TEXT NOT NULL, id TEXT NOT NULL, record_revision INTEGER NOT NULL, material_id TEXT NOT NULL,
 PRIMARY KEY(entity,id,record_revision,material_id), FOREIGN KEY(entity,id,record_revision) REFERENCES demo_plan_reviews(entity,id,record_revision),
 FOREIGN KEY(entity,id,material_id) REFERENCES demo_plan_materials(entity,id,material_id));
"""

def policy():return dict(maxBytes=MAX_BYTES,maxActive=MAX_ACTIVE,maxPlanBytes=MAX_PLAN_BYTES,maxPlanFiles=MAX_PLAN_FILES,mediaTypes=list(TYPES),payloadImmutable=True,downloadDisposition='attachment')

def checked(name,media_type,raw):
 if not isinstance(name,str) or not 1<=len(name.encode('utf8'))<=256 or name!=name.strip() or name.startswith('.') or name.endswith('.') or any(c in name for c in '<>:"/\\|?*') or any(unicodedata.category(c) in ('Cc','Cf') for c in name):raise DemoError(400,'附件文件名无效')
 if not isinstance(media_type,str) or media_type not in TYPES or not name.casefold().endswith(TYPES[media_type]):raise DemoError(400,'附件仅支持PDF、PNG、JPEG且扩展名需一致')
 if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_BYTES:raise DemoError(400,'附件大小需在1字节至2MiB之间')
 match={'application/pdf':raw.startswith(b'%PDF-') and raw.rstrip().endswith(b'%%EOF'),'image/png':raw.startswith(b'\x89PNG\r\n\x1a\n') and raw.endswith(b'IEND\xaeB`\x82'),'image/jpeg':raw.startswith(b'\xff\xd8\xff') and raw.endswith(b'\xff\xd9')}
 if not match[media_type]:raise DemoError(400,'附件格式标记与声明不符')
 return hashlib.sha256(raw).hexdigest()

def metadata(row):return {k:row[k] for k in ('material_id','record_revision','name','media_type','bytes','sha256','created_at','description')}

class PlanMaterialsMixin:
 def _plan_material_list(self,db,identity,version):
  return [metadata(r) for r in db.execute('SELECT m.* FROM demo_plan_materials m JOIN demo_plan_version_materials v ON v.entity=m.entity AND v.id=m.id AND v.material_id=m.material_id WHERE v.entity=? AND v.id=? AND v.version=? ORDER BY m.record_revision,m.material_id',('plans',identity,version))]

 def add_plan_material(self,identity,revision,name,mediaType,base64Data,description):
  if not isinstance(base64Data,str) or len(base64Data)>((MAX_BYTES+2)//3)*4:raise DemoError(400,'附件编码或大小无效')
  try:raw=base64.b64decode(base64Data,validate=True)
  except (ValueError,TypeError):raise DemoError(400,'附件Base64编码无效')
  digest=checked(name,mediaType,raw)
  if not isinstance(description,str) or not description.strip() or len(description)>2000:raise DemoError(400,'请填写1至2000字附件说明')
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');row,plan,current=self._plan_checked(db,identity,revision);version=plan['currentVersion']
   if current['status']!='draft':raise DemoError(409,'仅编制中的预案版本支持上传附件')
   if len(current['materials'])>=MAX_ACTIVE:raise DemoError(409,'当前版本最多8份附件')
   count,size=db.execute('SELECT count(*),coalesce(sum(bytes),0) FROM demo_plan_materials WHERE entity=? AND id=?',('plans',identity)).fetchone()
   if count>=MAX_PLAN_FILES or size+len(raw)>MAX_PLAN_BYTES:raise DemoError(409,'预案保留附件已达容量限制')
   material_id=uuid.uuid4().hex;revision+=1
   at=self._plan_event(db,identity,revision,'plan_material_add',description,version,metadata=dict(material_id=material_id,name=name,bytes=len(raw),sha256=digest))
   db.execute('INSERT INTO demo_plan_materials VALUES (?,?,?,?,?,?,?,?,?,?,?)',('plans',identity,material_id,revision,name,mediaType,len(raw),digest,at,description,raw))
   db.execute('INSERT INTO demo_plan_version_materials VALUES (?,?,?,?)',('plans',identity,version,material_id))
   db.execute('UPDATE demo_records SET revision=? WHERE entity=? AND id=?',(revision,'plans',identity));db.commit()
  return self.detail('plans',identity)

 def remove_plan_material(self,identity,revision,materialId):
  if not isinstance(materialId,str) or not re.fullmatch('[a-f0-9]{32}',materialId):raise DemoError(400,'附件标识无效')
  with closing(self.connect()) as db:
   db.execute('BEGIN IMMEDIATE');row,plan,current=self._plan_checked(db,identity,revision);version=plan['currentVersion']
   if current['status']!='draft':raise DemoError(409,'仅草稿支持移除附件关联')
   if not any(m['material_id']==materialId for m in current['materials']):raise DemoError(404,'附件不属于当前草稿')
   revision+=1;self._plan_event(db,identity,revision,'plan_material_remove','从草稿移除附件关联；原载荷和评审引用保留',version,metadata=dict(material_id=materialId))
   db.execute('DELETE FROM demo_plan_version_materials WHERE entity=? AND id=? AND version=? AND material_id=?',('plans',identity,version,materialId))
   db.execute('UPDATE demo_records SET revision=? WHERE entity=? AND id=?',(revision,'plans',identity));db.commit()
  return self.detail('plans',identity)

 def plan_material(self,identity,version,materialId,reviewRevision=None):
  if not isinstance(identity,str) or not 1<=len(identity)<=128 or not isinstance(materialId,str) or not re.fullmatch('[a-f0-9]{32}',materialId):raise DemoError(400,'附件标识无效')
  if type(version) is not int or not 1<=version<=2147483647 or (reviewRevision is not None and (type(reviewRevision) is not int or not 1<=reviewRevision<=2147483647)):raise DemoError(400,'附件版本无效')
  with closing(self.connect()) as db:
   db.execute('BEGIN')
   if reviewRevision is None:
    linked=db.execute('SELECT 1 FROM demo_plan_version_materials WHERE entity=? AND id=? AND version=? AND material_id=?',('plans',identity,version,materialId)).fetchone()
   else:
    linked=db.execute('SELECT 1 FROM demo_plan_review_materials m JOIN demo_plan_reviews r ON r.entity=m.entity AND r.id=m.id AND r.record_revision=m.record_revision WHERE m.entity=? AND m.id=? AND r.version=? AND m.record_revision=? AND m.material_id=?',('plans',identity,version,reviewRevision,materialId)).fetchone()
   if linked is None:raise DemoError(404,'该版本或评审不包含此附件')
   row=db.execute('SELECT * FROM demo_plan_materials WHERE entity=? AND id=? AND material_id=?',('plans',identity,materialId)).fetchone()
   try:
    if row is None or row['bytes']!=len(row['payload']) or checked(row['name'],row['media_type'],row['payload'])!=row['sha256']:raise ValueError()
   except (ValueError,TypeError,DemoError):raise DemoError(503,'附件完整性核对失败，未修改原文件') from None
   return row['payload'],metadata(row)
