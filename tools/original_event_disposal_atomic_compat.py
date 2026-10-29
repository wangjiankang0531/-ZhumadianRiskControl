"""Create an isolated transaction candidate for the exact original disposal service."""
from hashlib import sha256
from pathlib import Path
PIN='656df65971b68f1719d94fa4ef4141455b13d854cde531f36593acd1195d9738'
ANNOTATION='    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)\n'
def adapt(raw):
 if sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_EVENT_DISPOSAL_SERVICE_REQUIRED')
 nl='\r\n' if b'\r\n' in raw else '\n';s=raw.decode('utf8').replace('\r\n','\n');start='    public boolean saveRecord(EventDisposalRecord record){\n';old='''        infoMapper.update(updateWrapper);
        return save(record);
'''
 if s.count(start)!=1 or s.count(old)!=1:raise ValueError('EXACT_EVENT_DISPOSAL_WRITE_ANCHORS_REQUIRED')
 s=s.replace(start,ANNOTATION+start+'''        if(record == null || record.getEventId() == null || record.getEventId().isBlank()) return false;
''',1).replace(old,'''        int changed = infoMapper.update(updateWrapper);
        if(changed == 0){
            EventInfo current = infoMapper.selectById(record.getEventId());
            if(current == null || !"2".equals(current.getResearchStatus())) return false;
        }
        boolean saved = save(record);
        if(!saved){
            org.springframework.transaction.interceptor.TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
        }
        return saved;
''',1)
 return s.replace('\n',nl).encode('utf8')
def build(source,output):
 source,output=Path(source),Path(output)
 if output.exists() or output.is_symlink() or source.resolve()==output.resolve():raise ValueError('FRESH_SEPARATE_DISPOSAL_CANDIDATE_REQUIRED')
 raw=adapt(source.read_bytes());output.parent.mkdir(parents=True,exist_ok=True)
 with output.open('xb') as stream:stream.write(raw)
 return {'originalSourceSHA256':PIN,'candidateSourceSHA256':sha256(raw).hexdigest(),'referenceChanged':False,'installed':False,'allChangesInsideSaveRecordOrItsTransactionAnnotation':True}
