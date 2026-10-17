"""Archive only verified installation records, hashing every streamed input and ZIP byte."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import time
import zipfile


class DigestSink:
    def __init__(self,path):
        self.file=Path(path).open('xb');self.digest=hashlib.sha256();self.count=0
    def write(self,data):
        count=self.file.write(data)
        if count!=len(data):raise OSError('Short archive write')
        self.digest.update(data);self.count+=count;return count
    def tell(self):return self.count
    def seek(self,*args):raise io.UnsupportedOperation('Forward-only archive')
    def flush(self):self.file.flush()
    def close(self):
        self.file.flush();os.fsync(self.file.fileno());self.file.close()


def archive(root,output,evidence):
    root=Path(root).resolve();output=Path(output).resolve();evidence=Path(evidence)
    if output.exists() or output.with_suffix(output.suffix+'.partial').exists() or evidence.exists():
        raise ValueError('Use fresh archive/evidence paths')
    installation=json.loads((root/'installation.json').read_text('utf8'));package=root/installation['package']
    if not installation.get('localRuntimeVerified'):raise ValueError('Actual relocated runtime verification required')
    release=json.loads((package/'package.json').read_text('utf8'));dataset=json.loads((package/'dataset_manifest.json').read_text('utf8'))
    package_prefix=installation['package']+'/'
    records=[dict(r) for r in installation['outerFiles']]
    records += [dict(r,path=package_prefix+r['path']) for r in release['files']+installation.get('packageExtraFiles',[])+dataset['sourceFiles']]
    for p in [package/'package.json',root/'installation.json']:
        raw=p.read_bytes();records.append({'path':p.relative_to(root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    assert len({r['path'] for r in records})==len(records)
    output.parent.mkdir(parents=True,exist_ok=True);partial=output.with_suffix(output.suffix+'.partial');started=time.time()
    record={'status':'archiving','pid':os.getpid(),'root':str(root),'output':str(output),'expectedEntries':len(records),'checkedEntries':0,'sourceBytes':0,'allInputHashesChecked':True,'archiveShaComputedWhileWriting':True}
    def save():evidence.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    save();sink=DigestSink(partial)
    try:
        with zipfile.ZipFile(sink,'w',compression=zipfile.ZIP_STORED,allowZip64=True) as zipped:
            for index,r in enumerate(records,1):
                relative=Path(r['path']);assert not relative.is_absolute() and '..' not in relative.parts
                path=root/relative;assert not path.is_symlink() and not path.is_junction() and path.stat().st_size==r['bytes']
                when=time.localtime(path.stat().st_mtime)[:6]
                if not 1980<=when[0]<=2107:when=(1980,1,1,0,0,0)
                info=zipfile.ZipInfo(root.name+'/'+relative.as_posix(),when);info.compress_type=zipfile.ZIP_STORED;info.file_size=r['bytes'];info.external_attr=0o100644<<16
                digest=hashlib.sha256();size=0
                with path.open('rb') as source,zipped.open(info,'w',force_zip64=r['bytes']>=2**31) as target:
                    for block in iter(lambda:source.read(4*1048576),b''):
                        target.write(block);digest.update(block);size+=len(block)
                if size!=r['bytes'] or digest.hexdigest()!=r['sha256']:raise ValueError('Changed installation file: '+r['path'])
                record['checkedEntries']=index;record['sourceBytes']+=size
                if index%20000==0:save();print('ARCHIVED',index,flush=True)
        sink.close()
        with zipfile.ZipFile(partial) as zipped:
            contents=zipped.infolist();assert len(contents)==len(records)
            actual={item.filename:item for item in contents};assert len(actual)==len(records)
            for r in records:assert actual[root.name+'/'+r['path']].file_size==r['bytes']
        assert partial.stat().st_size==sink.count
        partial.replace(output)
        record.update(status='ready',archiveBytes=sink.count,archiveSha256=sink.digest.hexdigest(),centralDirectoryValidated=True,fullArchiveReadbackCrc=False,elapsedSeconds=time.time()-started);save()
    except BaseException as error:
        if not sink.file.closed:sink.close()
        record.update(status='failed',error=str(error),elapsedSeconds=time.time()-started);save();raise
    print(json.dumps(record,ensure_ascii=False),flush=True);return record


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();archive(a.root,a.output,a.evidence)


if __name__=='__main__':main()
