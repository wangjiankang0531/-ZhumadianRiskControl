"""SHA-pinned, read-only prepared BC7 descriptors and complete mip payloads."""
import hashlib
import json
from pathlib import Path
import re
if __package__:
    from .readonly_landscape_store import duplicates, owned, read_bytes, require
else:
    from readonly_landscape_store import duplicates, owned, read_bytes, require

SHA = re.compile('[0-9a-f]{64}')


class ReadOnlyTextureStore:
    def __init__(self, configuration):
        config = json.loads(read_bytes(Path(configuration),1048576),object_pairs_hook=duplicates)
        require(config.get('schema')=='xnby.prepared_texture_index.v1','Invalid prepared texture index')
        self.root = Path(config['resourceRoot']).absolute()
        require(self.root.is_dir(),'Prepared texture root missing')
        records = config.get('entries')
        require(isinstance(records,list) and len(records)<=4096,'Prepared texture index exceeds limit')
        self.entries = {}
        for row in records:
            source,digest=row['sourceSHA256'],row['manifestSHA256']
            require(isinstance(source,str) and SHA.fullmatch(source) and isinstance(digest,str) and SHA.fullmatch(digest),'Invalid texture index digest')
            directory=row['directory']
            require(isinstance(directory,str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_-]{0,79}',directory) and source not in self.entries,'Invalid or duplicate texture directory')
            folder=owned(self.root,Path(directory))
            raw=read_bytes(owned(folder,Path('manifest.json')),1048576)
            require(hashlib.sha256(raw).hexdigest()==digest,'Prepared descriptor differs from pinned index')
            manifest=json.loads(raw,object_pairs_hook=duplicates)
            descriptor=self._descriptor(manifest,source)
            self.entries[source]=dict(folder=folder,manifestSHA256=digest,descriptor=descriptor)
            # Startup is validation only. No encoding, repair or writes.
            self.payload(source,descriptor['payloadSHA256'])

    @staticmethod
    def _descriptor(manifest,source):
        require(manifest.get('schema')=='xnby.bc7.mip_chain.v1' and manifest.get('format')=='BC7_UNORM_BLOCK' and manifest.get('sourceSHA256')==source,'Prepared descriptor source/format differs')
        size=manifest.get('sourceSize')
        require(isinstance(size,list) and len(size)==2 and all(type(v) is int and 0<v<=2048 and v%4==0 for v in size),'Invalid prepared dimensions')
        total=manifest.get('payloadBytes');digest=manifest.get('payloadSHA256')
        require(type(total) is int and 0<total<=32*1048576 and isinstance(digest,str) and SHA.fullmatch(digest),'Invalid prepared payload identity')
        rows=manifest.get('mips');require(isinstance(rows,list) and 0<len(rows)<=12,'Invalid mip count')
        width,height=size;offset=0;complete=False;mips=[]
        for i,row in enumerate(rows):
            count=((width+3)//4)*((height+3)//4)*16
            require(not complete and all(type(row.get(k)) is int for k in ('level','width','height','offset','bytes')) and (row['level'],row['width'],row['height'],row['offset'],row['bytes'])==(i,width,height,offset,count) and isinstance(row.get('sha256'),str) and SHA.fullmatch(row['sha256']),'Invalid complete mip layout')
            mips.append({k:row[k] for k in ('level','width','height','offset','bytes','sha256')})
            offset+=count;complete=width==height==1;width=max(1,width//2);height=max(1,height//2)
        require(complete and offset==total,'Incomplete mip chain')
        # Do not disclose producer paths, reference-image paths or timing fields.
        return dict(schema=manifest['schema'],format=manifest['format'],sourceSHA256=source,sourceSize=list(size),payloadBytes=total,payloadSHA256=digest,mips=mips)

    def _entry(self,source,digest):
        entry=self.entries.get(source)
        require(entry is not None and entry['descriptor']['payloadSHA256']==digest,'Prepared texture is not indexed')
        raw=read_bytes(owned(entry['folder'],Path('manifest.json')),1048576)
        require(hashlib.sha256(raw).hexdigest()==entry['manifestSHA256'],'Pinned prepared descriptor changed')
        return entry

    def index(self):
        return dict(schema='xnby.prepared_texture_index.v1',entries=[dict(sourceSHA256=source,payloadSHA256=row['descriptor']['payloadSHA256']) for source,row in sorted(self.entries.items())])

    def descriptor(self,source,digest):
        return self._entry(source,digest)['descriptor']

    def payload(self,source,digest):
        entry=self._entry(source,digest);descriptor=entry['descriptor']
        raw=read_bytes(owned(entry['folder'],Path('texture.bc7')),32*1048576)
        require(len(raw)==descriptor['payloadBytes'] and hashlib.sha256(raw).hexdigest()==digest,'Prepared payload changed')
        for row in descriptor['mips']:
            require(hashlib.sha256(raw[row['offset']:row['offset']+row['bytes']]).hexdigest()==row['sha256'],'Prepared mip changed')
        return raw
