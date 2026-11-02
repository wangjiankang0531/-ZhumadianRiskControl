"""Strict BC7 prefix + exact RGBA tail; never accepts an incomplete BC7 chain."""
from pathlib import Path
import copy,hashlib,json,re
if __package__:
    from .readonly_landscape_store import duplicates,owned,read_bytes,require
    from .bc7_quality_contract import validate_bc7_quality,QUALITY_POLICY
else:
    from readonly_landscape_store import duplicates,owned,read_bytes,require
    from bc7_quality_contract import validate_bc7_quality,QUALITY_POLICY
SHA=re.compile('[0-9a-f]{64}')
SCHEMA='xnby.bc7_rgba_tail.v1'
FORMAT='BC7_PREFIX_RGBA8_TAIL'
FILES={'bc7':'prefix.bc7','rgba8':'tail.rgba'}
def describe_hybrid(manifest,source_sha):
    require(isinstance(manifest,dict) and manifest.get('schema')==SCHEMA and manifest.get('format')==FORMAT and manifest.get('sourceSHA256')==source_sha and isinstance(source_sha,str) and SHA.fullmatch(source_sha),'Invalid hybrid identity')
    quality=validate_bc7_quality(manifest)
    size=manifest.get('sourceSize');require(isinstance(size,list) and len(size)==2 and all(type(v) is int and 0<v<=2048 and v%4==0 for v in size),'Invalid hybrid source size')
    rows=manifest['mips'];start=manifest.get('tailStartLevel');require(type(start) is int and 0<start<len(rows),'Hybrid requires nonempty prefix and tail')
    components=manifest.get('components');require(isinstance(components,dict) and set(components)=={'bc7','rgba8'},'Invalid hybrid components')
    safe_components={}
    for kind in FILES:
        item=components[kind];require(isinstance(item,dict) and item.get('file')==FILES[kind] and type(item.get('bytes')) is int and 0<item['bytes']<=8*1048576 and isinstance(item.get('sha256'),str) and SHA.fullmatch(item['sha256']),'Invalid hybrid component identity')
        safe_components[kind]={k:item[k] for k in ('file','bytes','sha256')}
    total=manifest.get('payloadBytes');digest=manifest.get('payloadSHA256');require(type(total) is int and total==sum(x['bytes'] for x in safe_components.values()) and isinstance(digest,str) and SHA.fullmatch(digest),'Invalid hybrid total identity')
    width,height=size;offsets={'bc7':0,'rgba8':0};complete=False;safe=[];original_bytes=0
    for level,row in enumerate(rows):
        kind='bc7' if level<start else 'rgba8';count=((width+3)//4)*((height+3)//4)*16 if kind=='bc7' else width*height*4
        require(not complete and all(type(row.get(k)) is int for k in ('level','width','height','offset','bytes')) and (row['level'],row['width'],row['height'],row['offset'],row['bytes'])==(level,width,height,offsets[kind],count) and row.get('format')==kind,'Invalid hybrid mip layout')
        require(isinstance(row.get('sha256'),str) and SHA.fullmatch(row['sha256']) and isinstance(row.get('decodedRgbaSHA256'),str) and SHA.fullmatch(row['decodedRgbaSHA256']),'Invalid hybrid mip proof')
        if kind=='rgba8':require(row['decodedRgbaSHA256']==row['sha256']==row.get('sourceRgbaSHA256') and all(quality['mips'][level][k]==v for k,v in [('rgbPSNR',999.0),('rgbChannelP99',0),('rgbMaxError',0)]),'RGBA tail must preserve the original mip bytes exactly')
        safe.append(dict({k:row[k] for k in ('level','width','height','offset','bytes','format','sha256','decodedRgbaSHA256')},accepted=True,quality=quality['mips'][level]))
        offsets[kind]+=count;original_bytes+=width*height*4;complete=width==height==1;width=max(1,width//2);height=max(1,height//2)
    require(complete and all(offsets[k]==safe_components[k]['bytes'] for k in FILES) and total<original_bytes,'Hybrid chain incomplete, trailing or not smaller than RGBA')
    return dict(schema=SCHEMA,format=FORMAT,sourceSHA256=source_sha,sourceSize=list(size),tailStartLevel=start,components=safe_components,payloadBytes=total,payloadSHA256=digest,mips=safe,accepted=True,qualityThresholds=quality['thresholds'],qualityPolicy=QUALITY_POLICY)

class ReadOnlyHybridTexture:
    def __init__(self,folder,manifest_sha256):
        self.folder=Path(folder).absolute();self.pin=manifest_sha256
        raw=read_bytes(owned(self.folder,Path('manifest.json')),1048576);require(hashlib.sha256(raw).hexdigest()==self.pin,'Hybrid manifest SHA mismatch')
        manifest=json.loads(raw,object_pairs_hook=duplicates);self._descriptor=describe_hybrid(manifest,manifest.get('sourceSHA256'))
        prefix=self.payload('bc7');tail=self.payload('rgba8');require(hashlib.sha256(prefix+tail).hexdigest()==self._descriptor['payloadSHA256'],'Hybrid combined payload mismatch')
    def descriptor(self):return copy.deepcopy(self._descriptor)
    def payload(self,kind):
        require(kind in FILES,'Unknown hybrid component')
        raw=read_bytes(owned(self.folder,Path('manifest.json')),1048576);require(hashlib.sha256(raw).hexdigest()==self.pin,'Pinned hybrid manifest changed')
        component=self._descriptor['components'][kind];data=read_bytes(owned(self.folder,Path(FILES[kind])),8*1048576)
        require(len(data)==component['bytes'] and hashlib.sha256(data).hexdigest()==component['sha256'],'Hybrid component changed')
        if kind=='rgba8':require(all(v==255 for v in data[3::4]),'Hybrid tail is not opaque')
        for row in self._descriptor['mips']:
            if row['format']==kind:require(hashlib.sha256(data[row['offset']:row['offset']+row['bytes']]).hexdigest()==row['sha256'],'Hybrid mip payload changed')
        return data
