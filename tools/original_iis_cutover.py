"""Small reversible IIS file cutover. No process start, credential lookup, or OS changes."""
from pathlib import Path
import hashlib,json,os,uuid

FILES=('App_Code/XnbyReferenceProxy.cs','web.config')
def sha(data):return hashlib.sha256(data).hexdigest()
def regular(path):
    p=Path(path)
    for q in [p,*p.parents]:
        if q.exists() and (q.is_symlink() or getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('IIS_PATH_REDIRECTION_REJECTED')
    return p
def atomic(path,data):
    p=regular(path);temp=p.with_name(p.name+'.'+str(uuid.uuid4())+'.pending')
    try:
        with temp.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(temp,p)
    finally:
        if temp.exists():temp.unlink()
def checked_current(root,expected):
    for rel,digest in expected.items():
        if sha(regular(Path(root)/rel).read_bytes())!=digest:raise ValueError('IIS_FILES_CHANGED_SINCE_SNAPSHOT')
def save_index(backup,index):atomic(Path(backup)/'transaction.private.json',json.dumps(index,indent=2).encode('utf-8'))
def apply(root,backup,new,validate):
    root=regular(root);backup=regular(backup)
    if set(new)!=set(FILES) or backup.exists() or root==backup or backup.is_relative_to(root):raise ValueError('FRESH_SEPARATE_IIS_BACKUP_REQUIRED')
    offline=root/'App_offline.htm'
    if offline.exists():raise ValueError('EXISTING_MAINTENANCE_FILE_NOT_OWNED')
    old={rel:regular(root/rel).read_bytes() for rel in FILES};before={k:sha(v) for k,v in old.items()};after={k:sha(v) for k,v in new.items()}
    backup.mkdir(parents=True)
    for rel,data in old.items():p=backup/rel;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(data)
    index={'schema':'zhumadian.original.iis.transaction.v1','root':str(root),'before':before,'after':after,'applied':False,'rolledBack':False,'oldBackendOrDatabaseChanged':False}
    maintenance=b'<!doctype html><meta charset="utf-8"><title>System update</title><p>System update in progress. Please refresh shortly.</p><!-- '+str(uuid.uuid4()).encode()+b' -->'
    def install_offline():
        with offline.open('xb') as f:f.write(maintenance)
    def remove_offline():
        if offline.exists():
            if offline.read_bytes()!=maintenance:raise ValueError('MAINTENANCE_FILE_OWNER_CHANGED')
            offline.unlink()
    save_index(backup,index)
    try:
        checked_current(root,before);install_offline();checked_current(root,before)
        for rel in FILES:atomic(root/rel,new[rel])
        remove_offline()
        if not validate():raise RuntimeError('IIS_POST_SWITCH_VALIDATION_FAILED')
        checked_current(root,after);index['applied']=True;save_index(backup,index)
    except BaseException:
        # Restore only known old/new bytes; never overwrite an unrelated concurrent edit.
        for rel in FILES:
            if sha((root/rel).read_bytes()) not in (before[rel],after[rel]):
                index['concurrentEditDetected']=True;save_index(backup,index);remove_offline();raise
        if not offline.exists():install_offline()
        for rel in FILES:atomic(root/rel,old[rel])
        index['rolledBack']=True;save_index(backup,index);remove_offline();raise
    finally:remove_offline()
    return index
def rollback(backup):
    backup=regular(backup);index=json.loads((backup/'transaction.private.json').read_bytes())
    if index['schema']!='zhumadian.original.iis.transaction.v1' or not index['applied'] or index['rolledBack']:raise ValueError('APPLIED_OWN_TRANSACTION_REQUIRED')
    root=regular(index['root']);checked_current(root,index['after'])
    offline=root/'App_offline.htm'
    if offline.exists():raise ValueError('EXISTING_MAINTENANCE_FILE_NOT_OWNED')
    for rel in FILES:
        if sha((backup/rel).read_bytes())!=index['before'][rel]:raise ValueError('IIS_BACKUP_CHANGED')
    mark=b'Own project rollback '+str(uuid.uuid4()).encode()
    with offline.open('xb') as f:f.write(mark)
    try:
        checked_current(root,index['after'])
        for rel in FILES:atomic(root/rel,(backup/rel).read_bytes())
        index['rolledBack']=True;index['applied']=False;save_index(backup,index)
    finally:
        if offline.exists() and offline.read_bytes()==mark:offline.unlink()
    return index
