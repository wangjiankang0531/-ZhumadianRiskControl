"""Offline original-pixel overlap publication; never converts native landscape."""
from pathlib import Path
import hashlib,json,io
from PIL import Image
if __package__:
    from .hybrid_texture import ReadOnlyHybridTexture
    from .readonly_landscape_store import read_bytes,owned,duplicates,require
    from .readonly_hybrid_store import overlap_descriptor
else:
    from hybrid_texture import ReadOnlyHybridTexture
    from readonly_landscape_store import read_bytes,owned,duplicates,require
    from readonly_hybrid_store import overlap_descriptor

def build_overlap(folder,manifest_sha256,source,output):
    folder=Path(folder);source=Path(source);output=Path(output).absolute();require(not output.exists(),'Fresh overlap directory required')
    store=ReadOnlyHybridTexture(folder,manifest_sha256);base=store.descriptor();proof=json.loads(read_bytes(owned(folder,Path('manifest.json')),1048576),object_pairs_hook=duplicates)
    raw=read_bytes(source,32*1048576);require(hashlib.sha256(raw).hexdigest()==base['sourceSHA256'],'Original source SHA differs')
    with Image.open(io.BytesIO(raw)) as loaded:
        require(loaded.mode=='RGB' and list(loaded.size)==base['sourceSize'],'Original source size differs');image=loaded.convert('RGBA')
    start=base['tailStartLevel']-2;require(start>=0,'Two original overlap levels unavailable');rows=[];pieces=[];offset=0
    try:
        for row in base['mips'][start:base['tailStartLevel']]:
            mip=image.resize((row['width'],row['height']),Image.Resampling.LANCZOS);data=mip.tobytes();mip.close();digest=hashlib.sha256(data).hexdigest();require(digest==proof['mips'][row['level']]['sourceRgbaSHA256'],'Original overlap pixel proof differs')
            rows.append(dict(level=row['level'],width=row['width'],height=row['height'],offset=offset,bytes=len(data),sha256=digest,sourceRgbaSHA256=digest,accepted=True,quality=dict(rgbPSNR=999,rgbChannelP99=0,rgbMaxError=0)));pieces.append(data);offset+=len(data)
    finally:image.close()
    payload=b''.join(pieces);manifest=dict(schema='xnby.bc7_rgba_overlap.v1',sourceSHA256=base['sourceSHA256'],basePayloadSHA256=base['payloadSHA256'],startLevel=start,payloadBytes=len(payload),payloadSHA256=hashlib.sha256(payload).hexdigest(),mips=rows)
    overlap_descriptor(base,proof,manifest);output.mkdir(parents=True);(output/'overlap.rgba').write_bytes(payload);(output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');return manifest
