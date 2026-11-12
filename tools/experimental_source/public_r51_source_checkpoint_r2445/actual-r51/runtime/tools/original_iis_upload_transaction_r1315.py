"""Derive IIS limits inside the server and join the existing code transaction.

No configuration is staged in the transport. Original backup/restore functions
operate on the same before/after SHA row; private settings stay in the owned
server config and this attempt's private backup. No network or process calls.
"""
from pathlib import Path
import hashlib
PATH='iis/web.config'
POLICY={'revision':'server-only-two-upload-limit-numbers-v1','path':PATH,'oldHttpRuntimeKiB':102400,'oldRequestFilteringBytes':104857600,'newHttpRuntimeKiB':103424,'newRequestFilteringBytes':105906176,'allOtherBytesPreserved':True,'configurationBytesInTransport':False,'originalBackupAndRestoreUsed':True}

def need(ok,code):
    if not ok:raise ValueError(code)

def raw_config(m,app):
    path=m.regular(app,PATH)
    need(path.is_file()and path.stat().st_size<=1024*1024,'IIS_TRANSACTION_BOUNDED_EXISTING_CONFIG_REQUIRED')
    return path,path.read_bytes()

def inspect_config(m,limits,app,payload_files,transported_files):
    need(PATH not in payload_files and PATH not in transported_files,'IIS_TRANSACTION_CONFIG_MUST_NOT_BE_TRANSPORTED_OR_PAYLOAD_TRACKED')
    _,raw=raw_config(m,app);before=hashlib.sha256(raw).hexdigest();_,proof=limits.prepare(raw,before)
    row={PATH:{'before':before,'after':proof['afterSHA256']}}if proof['changed']else{}
    return row,proof

def bind_replace(m,limits):
    original=m.replace_code
    def replace(app,bundle,changes,after_each=None):
        if PATH not in changes:return original(app,bundle,changes,after_each=after_each)
        row=changes[PATH]
        need(set(row)=={'before','after'}and all(isinstance(row[k],str)and len(row[k])==64 for k in row),'IIS_TRANSACTION_EXACT_CHANGE_ROW_REQUIRED')
        # Check every target/source before the first write, including the derived
        # private config. Never create payload/iis/web.config as an intermediate.
        need(not m.regular(bundle/'payload',PATH).exists(),'IIS_TRANSACTION_PRIVATE_CONFIG_IN_TRANSPORT_REFUSED')
        for name,change in changes.items():
            path=m.regular(app,name)
            if change['before']is None:need(not path.exists(),'IIS_TRANSACTION_UNKNOWN_EXISTING_PATH')
            else:m.check_file(app,name,change['before'])
            if name!=PATH and change['after']is not None:m.check_file(bundle/'payload',name,change['after'])
        _,raw=raw_config(m,app);prepared,proof=limits.prepare(raw,row['before'])
        need(proof['afterSHA256']==row['after'],'IIS_TRANSACTION_RENDERED_SHA_MISMATCH')
        for name in sorted(changes,key=lambda n:(n=='release-manifest.json',n)):
            if name!=PATH:original(app,bundle,{name:changes[name]},after_each=after_each);continue
            target,current=raw_config(m,app)
            need(hashlib.sha256(current).hexdigest()==row['before'],'IIS_TRANSACTION_CONFIG_DRIFT_BEFORE_WRITE')
            # Recompute on the freshly verified bytes; never reuse a config
            # snapshot taken before backup/shutdown/concurrent source checks.
            prepared,proof=limits.prepare(current,row['before']);need(proof['afterSHA256']==row['after'],'IIS_TRANSACTION_RENDERED_SHA_MISMATCH')
            m.atomic(target,prepared);m.check_file(app,PATH,row['after'])
            if after_each:after_each(name)
    return replace
