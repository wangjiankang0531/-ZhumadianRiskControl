"""Dedicated model database: cross-process CAS and bounded operation receipts."""
from pathlib import Path
from contextlib import contextmanager
import datetime,hashlib,json,os,re,sqlite3,stat
from services.common import ApiError,loads
from .validation import validate_state,catalog_versions,empty_state
APP_ID=0x584E534D;LIMIT=16*1048576;MAX_RECEIPTS=2048

def encode(value):return json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def checked_path(path,directory=False):
 for part in reversed([path,*path.parents]):
  info=part.lstat()
  if stat.S_ISLNK(info.st_mode)or getattr(info,'st_file_attributes',0)&0x400:raise ValueError('SCENE_STORAGE_REPARSE_POINT')
 if directory and not path.is_dir():raise ValueError('SCENE_STORAGE_DIRECTORY_REQUIRED')
 if not directory and(not path.is_file()or getattr(path.stat(),'st_nlink',1)!=1):raise ValueError('SCENE_STORAGE_REGULAR_FILE_REQUIRED')

class SceneModelRepository:
 def __init__(self,root,catalog):
  self.root=Path(root);self.catalog=catalog_versions(catalog)
  if not self.root.is_absolute():raise ValueError('EXPLICIT_SCENE_STORAGE_ROOT_REQUIRED')
  checked_path(self.root,directory=True);self.path=self.root/'scene-models.sqlite3'
  with self.transaction(write=True,initial=True)as db:
   app=db.execute('PRAGMA application_id').fetchone()[0];version=db.execute('PRAGMA user_version').fetchone()[0];tables={row[0]for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
   if app==0 and not tables and version==0:
    db.execute('CREATE TABLE scene_current(id INTEGER PRIMARY KEY CHECK(id=1),revision INTEGER NOT NULL,sha256 TEXT NOT NULL,updated TEXT NOT NULL,payload BLOB NOT NULL)')
    db.execute('CREATE TABLE scene_operations(account_key TEXT NOT NULL,operation_id TEXT NOT NULL,request_sha TEXT NOT NULL,base_revision INTEGER NOT NULL,revision INTEGER NOT NULL,sha256 TEXT NOT NULL,changed INTEGER NOT NULL,updated TEXT NOT NULL,sequence INTEGER NOT NULL,PRIMARY KEY(account_key,operation_id)) WITHOUT ROWID')
    db.execute('PRAGMA application_id='+str(APP_ID));db.execute('PRAGMA user_version=1')
   elif app!=APP_ID or version!=1 or tables!={'scene_current','scene_operations'}:raise ValueError('UNKNOWN_SCENE_STATE_DATABASE')
 @contextmanager
 def transaction(self,write=False,initial=False):
  checked_path(self.root,directory=True)
  if self.path.exists():checked_path(self.path)
  elif not initial:raise ApiError(503,'SCENE_STORAGE_UNAVAILABLE')
  for suffix in ['-journal','-wal','-shm']:
   side=Path(str(self.path)+suffix)
   if side.exists():checked_path(side)
  db=sqlite3.connect(str(self.path),timeout=5,isolation_level=None);db.row_factory=sqlite3.Row
  try:
   db.execute('PRAGMA busy_timeout=5000');db.execute('BEGIN IMMEDIATE'if write else'BEGIN')
   if not initial and(db.execute('PRAGMA application_id').fetchone()[0]!=APP_ID or db.execute('PRAGMA user_version').fetchone()[0]!=1):raise ApiError(503,'SCENE_STORAGE_INVALID')
   yield db;db.commit()
  except BaseException:db.rollback();raise
  finally:db.close()
 def current(self,db):
  row=db.execute('SELECT * FROM scene_current WHERE id=1').fetchone()
  if row is None:
   value=empty_state();return{'schema':'xnby.scene-model-snapshot.v1','scene':'zhumadian','revision':0,'sha256':hashlib.sha256(encode(value)).hexdigest(),'updatedAt':None,'document':value}
  raw=bytes(row['payload'])
  try:
   if len(raw)>LIMIT or hashlib.sha256(raw).hexdigest()!=row['sha256']or type(row['revision'])is not int or not 1<=row['revision']<=2**31-1:raise ValueError()
   value=validate_state(loads(raw))
  except(ValueError,TypeError,KeyError,UnicodeError):raise ApiError(503,'SCENE_STORAGE_INVALID')from None
  return{'schema':'xnby.scene-model-snapshot.v1','scene':'zhumadian','revision':row['revision'],'sha256':row['sha256'],'updatedAt':row['updated'],'document':value}
 def get(self):
  with self.transaction()as db:return self.current(db)
 def operation(self,operation_id,account_key):
  if not isinstance(operation_id,str)or not re.fullmatch('[0-9a-f]{32}',operation_id)or not isinstance(account_key,str)or not re.fullmatch('[0-9a-f]{64}',account_key):raise ValueError('INVALID_SCENE_OPERATION')
  with self.transaction()as db:
   self.current(db);row=db.execute('SELECT * FROM scene_operations WHERE account_key=? AND operation_id=?',(account_key,operation_id)).fetchone()
   if row is None:raise ApiError(404,'SCENE_OPERATION_NOT_FOUND')
   return{'schema':'xnby.scene-model-operation.v1','scene':'zhumadian','operationId':operation_id,'expectedRevision':row['base_revision'],'revision':row['revision'],'sha256':row['sha256'],'changed':bool(row['changed']),'updatedAt':row['updated']}
 def save(self,document,expected_revision,operation_id,account_key):
  if type(expected_revision)is not int or not 0<=expected_revision<2**31-1 or not isinstance(operation_id,str)or not re.fullmatch('[0-9a-f]{32}',operation_id)or not isinstance(account_key,str)or not re.fullmatch('[0-9a-f]{64}',account_key):raise ValueError('INVALID_SCENE_SAVE')
  checked=validate_state(document,self.catalog);raw=encode(checked)
  if len(raw)>LIMIT:raise ValueError('SCENE_STATE_TOO_LARGE')
  digest=hashlib.sha256(raw).hexdigest();request_sha=hashlib.sha256(encode({'expectedRevision':expected_revision,'sha256':digest})).hexdigest()
  with self.transaction(write=True)as db:
   current=self.current(db);receipt=db.execute('SELECT * FROM scene_operations WHERE account_key=? AND operation_id=?',(account_key,operation_id)).fetchone()
   if receipt:
    if receipt['request_sha']!=request_sha:raise ApiError(409,'SCENE_OPERATION_REUSED')
    return{'revision':receipt['revision'],'sha256':receipt['sha256'],'changed':bool(receipt['changed']),'operationId':operation_id,'replayed':True,'updatedAt':receipt['updated']}
   if current['revision']!=expected_revision:raise ApiError(409,'SCENE_REVISION_CONFLICT')
   changed=current['sha256']!=digest;revision=current['revision']+int(changed);updated=stamp()if changed else current['updatedAt']or stamp()
   if changed:db.execute('INSERT INTO scene_current VALUES(1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET revision=excluded.revision,sha256=excluded.sha256,updated=excluded.updated,payload=excluded.payload',(revision,digest,updated,raw))
   sequence=db.execute('SELECT COALESCE(MAX(sequence),0)+1 FROM scene_operations').fetchone()[0]
   db.execute('INSERT INTO scene_operations VALUES(?,?,?,?,?,?,?,?,?)',(account_key,operation_id,request_sha,expected_revision,revision,digest,int(changed),updated,sequence));db.execute('DELETE FROM scene_operations WHERE sequence NOT IN(SELECT sequence FROM scene_operations ORDER BY sequence DESC LIMIT ?)',(MAX_RECEIPTS,))
   return{'revision':revision,'sha256':digest,'changed':changed,'operationId':operation_id,'replayed':False,'updatedAt':updated}
