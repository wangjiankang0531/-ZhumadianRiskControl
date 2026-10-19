"""Immutable issue evidence bytes, scoped by the existing issue authorization."""
import base64,hashlib,json,re,threading,unicodedata,uuid
from datetime import datetime,timezone
from .common import ApiError,fields,integer,text

MATERIAL_LIMIT=8*1048576
MATERIAL_JSON_LIMIT=((MATERIAL_LIMIT+2)//3)*4+32768
ISSUE_MATERIAL_LIMIT=128*1048576
ISSUE_MATERIAL_COUNT=64
TYPES={'application/pdf':('.pdf',),'image/png':('.png',),'image/jpeg':('.jpg','.jpeg')}

def material_name(name,media_type):
    text(name,256)
    if media_type not in TYPES or name!=name.strip() or any(c in name for c in '/\\:') or any(unicodedata.category(c)=='Cf' for c in name) or not name.casefold().endswith(TYPES[media_type]):raise ValueError('invalid material filename or type')
    return name

def checked_material(name,media_type,raw):
    material_name(name,media_type)
    if not isinstance(raw,bytes) or not 0<len(raw)<=MATERIAL_LIMIT:raise ValueError('invalid material size')
    signatures={'application/pdf':raw.startswith(b'%PDF-') and raw.rstrip().endswith(b'%%EOF'),'image/png':raw.startswith(b'\x89PNG\r\n\x1a\n') and raw.endswith(b'IEND\xaeB`\x82'),'image/jpeg':raw.startswith(b'\xff\xd8\xff') and raw.endswith(b'\xff\xd9')}
    if not signatures[media_type]:raise ValueError('material signature differs')
    return hashlib.sha256(raw).hexdigest()

def material_metadata(row):
    return {'id':row['id'],'revision':row['revision'],'name':row['name'],'mediaType':row['media_type'],'bytes':row['bytes'],'sha256':row['sha256'],'createdAt':row['created'],'actor':row['actor'],'description':row['description']}

def validate_stored_material(row):
    raw=row['payload']
    if type(row['bytes']) is not int or row['bytes']!=len(raw) or checked_material(row['name'],row['media_type'],raw)!=row['sha256']:raise ValueError('stored material differs')
    return raw

class MaterialsMixin:
    def __init__(self,path):
        super().__init__(path)
        self.material_slots=threading.BoundedSemaphore(2)

    def materials(self,principal,issue_id,query):
        with self.transaction() as db:
            issue,_=self.row(db,principal,issue_id)
            offset,limit=query.get('offset',0),query.get('limit',50)
            rows=db.execute('SELECT id,revision,name,media_type,bytes,sha256,created,actor,description FROM issue_materials WHERE tenant=? AND issue=? ORDER BY revision DESC,id LIMIT ? OFFSET ?',(principal.tenant,issue_id,limit,offset))
            items=[material_metadata(row) for row in rows]
            total=db.execute('SELECT count(*) FROM issue_materials WHERE tenant=? AND issue=?',(principal.tenant,issue_id)).fetchone()[0]
            return {'items':items,'total':total,'offset':offset,'limit':limit,'revision':issue['revision']}

    def material(self,principal,issue_id,material_id):
        with self.transaction() as db:
            self.row(db,principal,issue_id)
            row=db.execute('SELECT * FROM issue_materials WHERE tenant=? AND issue=? AND id=?',(principal.tenant,issue_id,material_id)).fetchone()
            if row is None:raise ApiError(404,'NOT_FOUND')
            try:raw=validate_stored_material(row)
            except (ValueError,TypeError):raise ApiError(503,'MATERIAL_UNAVAILABLE') from None
            return raw,material_metadata(row)

    def add_material(self,principal,issue_id,payload,request_key):
        principal.require('focus:read')
        if not principal.permissions&{'focus:track','focus:feedback'}:raise ApiError(403,'FORBIDDEN')
        if not re.fullmatch(r'[a-f0-9]{32}',request_key or ''):raise ApiError(400,'IDEMPOTENCY_KEY_REQUIRED')
        required=['revision','name','mediaType','base64','description'];fields(payload,required,required);integer(payload['revision'],1,2**31-1)
        note=payload['description']
        if not isinstance(note,str) or not note.strip() or len(note.encode('utf-8'))>4000 or re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',note):raise ValueError('invalid material description')
        if not isinstance(payload['base64'],str) or len(payload['base64'])>((MATERIAL_LIMIT+2)//3)*4:raise ValueError('material size exceeds bound')
        try:raw=base64.b64decode(payload['base64'],validate=True)
        except Exception:raise ValueError('invalid material encoding') from None
        sha=checked_material(payload['name'],payload['mediaType'],raw)
        encode=lambda v:json.dumps(v,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':'))
        digest=hashlib.sha256(encode([issue_id,'material',payload['revision'],payload['name'],payload['mediaType'],sha,len(raw),payload['description']]).encode()).hexdigest()
        with self.transaction(write=True) as db:
            _,issue=self.row(db,principal,issue_id)
            previous=db.execute('SELECT * FROM requests WHERE tenant=? AND actor=? AND key=?',(principal.tenant,principal.subject,request_key)).fetchone()
            if previous:
                self.access(principal,previous['enterprise'])
                if previous['digest']!=digest:raise ApiError(409,'IDEMPOTENCY_CONFLICT')
                return {**json.loads(previous['result']),'replayed':True}
            if payload['revision']!=issue['revision']:raise ApiError(409,'REVISION_CONFLICT')
            if issue['status']=='archived':raise ApiError(409,'ISSUE_ARCHIVED')
            if issue['revision']>=10000:raise ApiError(409,'ISSUE_HISTORY_LIMIT')
            count,size=db.execute('SELECT count(*),coalesce(sum(bytes),0) FROM issue_materials WHERE tenant=? AND issue=?',(principal.tenant,issue_id)).fetchone()
            if count>=ISSUE_MATERIAL_COUNT or size+len(raw)>ISSUE_MATERIAL_LIMIT:raise ApiError(409,'MATERIAL_CAPACITY')
            at=datetime.now(timezone.utc).isoformat();identity=uuid.uuid4().hex;issue['revision']+=1;issue['updatedAt']=at;issue['latestReview']=None
            metadata={'id':identity,'revision':issue['revision'],'name':payload['name'],'mediaType':payload['mediaType'],'bytes':len(raw),'sha256':sha,'createdAt':at,'actor':principal.subject,'description':payload['description']}
            db.execute('UPDATE issues SET revision=?,updated=?,payload=? WHERE tenant=? AND id=?',(issue['revision'],at,encode(issue),principal.tenant,issue_id))
            db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?)',(principal.tenant,issue_id,issue['revision'],at,principal.subject,principal.policy_version,'material',encode({'material':metadata})))
            db.execute('INSERT INTO issue_materials VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(principal.tenant,issue_id,identity,issue['revision'],payload['name'],payload['mediaType'],len(raw),sha,at,principal.subject,payload['description'],raw))
            result={'issue':self.public(issue),'material':metadata,'replayed':False}
            db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?)',(principal.tenant,principal.subject,request_key,digest,issue['enterpriseId'],encode(result)))
            return result
