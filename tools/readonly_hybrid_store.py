"""Pinned hybrid+overlap publication; existing source and payloads stay read-only."""
from pathlib import Path
from urllib.parse import urlsplit
import hashlib,json,re,copy
if __package__:
    from .readonly_landscape_store import duplicates,owned,read_bytes,require
    from .hybrid_texture import ReadOnlyHybridTexture
else:
    from readonly_landscape_store import duplicates,owned,read_bytes,require
    from hybrid_texture import ReadOnlyHybridTexture
SHA=re.compile('[0-9a-f]{64}');NAME=re.compile('[A-Za-z0-9][A-Za-z0-9_-]{0,79}')
SCENE_SCHEMA='xnby.prepared_hybrid_scene.v1'

def overlap_descriptor(base,proof,manifest):
    require(manifest.get('schema')=='xnby.bc7_rgba_overlap.v1' and manifest.get('sourceSHA256')==base['sourceSHA256'] and manifest.get('basePayloadSHA256')==base['payloadSHA256'],'Overlap base identity differs')
    start=base['tailStartLevel']-2
    require(start>=0 and type(manifest.get('startLevel')) is int and manifest['startLevel']==start and isinstance(manifest.get('mips'),list) and len(manifest['mips'])==2,'Invalid overlap levels')
    total=manifest.get('payloadBytes');digest=manifest.get('payloadSHA256')
    require(type(total) is int and 0<total<=8*1048576 and isinstance(digest,str) and SHA.fullmatch(digest),'Invalid overlap payload')
    rows=[];offset=0
    for i,row in enumerate(manifest['mips']):
        level=start+i;original=base['mips'][level];count=original['width']*original['height']*4
        require(all(type(row.get(k)) is int for k in ['level','width','height','offset','bytes']) and tuple(row[k] for k in ['level','width','height','offset','bytes'])==(level,original['width'],original['height'],offset,count),'Invalid overlap layout')
        expected=proof['mips'][level]['sourceRgbaSHA256']
        require(row.get('sha256')==row.get('sourceRgbaSHA256')==expected and isinstance(expected,str) and SHA.fullmatch(expected) and row.get('accepted') is True and row.get('quality')==dict(rgbPSNR=999,rgbChannelP99=0,rgbMaxError=0),'Overlap original proof differs')
        rows.append(dict(level=level,width=original['width'],height=original['height'],offset=offset,bytes=count,sha256=expected,sourceRgbaSHA256=expected,accepted=True,quality=dict(rgbPSNR=999,rgbChannelP99=0,rgbMaxError=0)));offset+=count
    require(offset==total,'Overlap trailing payload')
    original_total=sum(m['width']*m['height']*4 for m in base['mips'])
    require(base['payloadBytes']+total<original_total,'Overlap no longer smaller than original')
    return dict(schema='xnby.bc7_rgba_overlap.v1',sourceSHA256=base['sourceSHA256'],basePayloadSHA256=base['payloadSHA256'],startLevel=start,payloadBytes=total,payloadSHA256=digest,mips=rows)

class ReadOnlyHybridStore:
    def __init__(self,configuration):
        config=json.loads(read_bytes(Path(configuration),1048576),object_pairs_hook=duplicates)
        require(config.get('schema')=='xnby.prepared_hybrid_store.v1','Invalid hybrid store configuration')
        self.root=Path(config['resourceRoot']).absolute();self.overlap_root=Path(config['overlapRoot']).absolute();require(self.root.is_dir() and self.overlap_root.is_dir(),'Hybrid roots missing')
        entries=config.get('entries');require(isinstance(entries,list) and len(entries)<=4096,'Hybrid entries exceed limit');self.entries={}
        for row in entries:
            source=row.get('sourceSHA256');base_sha=row.get('manifestSHA256');overlap_sha=row.get('overlapManifestSHA256')
            require(all(isinstance(v,str) and SHA.fullmatch(v) for v in [source,base_sha,overlap_sha]) and source not in self.entries,'Invalid hybrid index digest')
            require(all(isinstance(row.get(k),str) and NAME.fullmatch(row[k]) for k in ['directory','overlapDirectory']),'Invalid hybrid index directory')
            folder=owned(self.root,Path(row['directory']));overlap_folder=owned(self.overlap_root,Path(row['overlapDirectory']))
            store=ReadOnlyHybridTexture(folder,base_sha);base=store.descriptor();require(base['sourceSHA256']==source,'Hybrid source differs')
            proof=json.loads(read_bytes(owned(folder,Path('manifest.json')),1048576),object_pairs_hook=duplicates)
            raw=read_bytes(owned(overlap_folder,Path('manifest.json')),1048576);require(hashlib.sha256(raw).hexdigest()==overlap_sha,'Pinned overlap manifest differs')
            overlap=overlap_descriptor(base,proof,json.loads(raw,object_pairs_hook=duplicates))
            entry=dict(store=store,overlapFolder=overlap_folder,overlapManifestSHA256=overlap_sha,overlap=overlap)
            pieces=[store.payload('bc7'),store.payload('rgba8'),self._overlap_payload(entry)]
            digest=hashlib.sha256(b''.join(pieces)).hexdigest();entry['descriptor']=dict(schema=SCENE_SCHEMA,format='BC7_RGBA_OVERLAP',sourceSHA256=source,sourceSize=base['sourceSize'],payloadBytes=sum(map(len,pieces)),payloadSHA256=digest,texture=base,overlap=overlap)
            self.entries[source]=entry
    @staticmethod
    def _overlap_payload(entry):
        raw=read_bytes(owned(entry['overlapFolder'],Path('manifest.json')),1048576);require(hashlib.sha256(raw).hexdigest()==entry['overlapManifestSHA256'],'Pinned overlap changed')
        descriptor=entry['overlap'];data=read_bytes(owned(entry['overlapFolder'],Path('overlap.rgba')),8*1048576)
        require(len(data)==descriptor['payloadBytes'] and hashlib.sha256(data).hexdigest()==descriptor['payloadSHA256'],'Overlap payload changed')
        for row in descriptor['mips']:
            chunk=data[row['offset']:row['offset']+row['bytes']];require(hashlib.sha256(chunk).hexdigest()==row['sha256'] and all(v==255 for v in chunk[3::4]),'Overlap mip or alpha changed')
        return data
    def _entry(self,source,digest):
        entry=self.entries.get(source);require(entry is not None and entry['descriptor']['payloadSHA256']==digest,'Hybrid texture not indexed')
        store=entry['store'];raw=read_bytes(owned(store.folder,Path('manifest.json')),1048576);require(hashlib.sha256(raw).hexdigest()==store.pin,'Pinned hybrid base changed');self._overlap_payload(entry);return entry
    def index(self):
        return dict(schema='xnby.prepared_texture_index.v2',entries=[dict(sourceSHA256=source,payloadSHA256=entry['descriptor']['payloadSHA256'],format='bc7_rgba_overlap') for source,entry in sorted(self.entries.items())])
    def descriptor(self,source,digest):return copy.deepcopy(self._entry(source,digest)['descriptor'])
    def payload(self,source,digest,name):
        entry=self._entry(source,digest)
        if name=='prefix.bc7':return entry['store'].payload('bc7')
        if name=='tail.rgba':return entry['store'].payload('rgba8')
        require(name=='overlap.rgba','Unknown hybrid component');return self._overlap_payload(entry)
    def handle(self,handler):
        if handler.command not in ['GET','HEAD']:return False
        path=urlsplit(handler.path).path
        if path=='/api/prepared-textures':handler.reply(200,json.dumps(self.index()).encode());return True
        match=re.fullmatch('/prepared-hybrid-textures/([0-9a-f]{64})/([0-9a-f]{64})/(manifest.json|prefix.bc7|tail.rgba|overlap.rgba)',path)
        if not match:return False
        source,digest,name=match.groups()
        try:
            if name=='manifest.json':handler.reply(200,json.dumps(self.descriptor(source,digest)).encode())
            else:handler.reply(200,self.payload(source,digest,name),'application/octet-stream')
        except (OSError,ValueError,KeyError,TypeError):handler.reply(409,b'{"error":"PREPARED_HYBRID_UNAVAILABLE"}')
        return True
