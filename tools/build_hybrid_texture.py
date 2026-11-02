"""Offline preparation; recompute every reference mip before retaining BC7."""
from pathlib import Path
import hashlib,json
from PIL import Image
if __package__:
    from .build_bc7_mode6_texture import quality
    from .hybrid_texture import describe_hybrid,SCHEMA,FORMAT
    from .readonly_landscape_store import duplicates
else:
    from build_bc7_mode6_texture import quality
    from hybrid_texture import describe_hybrid,SCHEMA,FORMAT
    from readonly_landscape_store import duplicates
def sha(raw):return hashlib.sha256(raw).hexdigest()
def prepare_hybrid(source,source_sha,manifest_raw,manifest_sha,bc7_payload,output):
    source=Path(source).resolve(strict=True);output=Path(output).absolute()
    if output.exists():raise ValueError('Fresh hybrid output required')
    if len(manifest_raw)>1048576 or sha(manifest_raw)!=manifest_sha:raise ValueError('Hybrid reference manifest differs')
    if not isinstance(bc7_payload,bytes) or len(bc7_payload)>8*1048576:raise ValueError('Hybrid reference payload exceeds limit')
    manifest=json.loads(manifest_raw,object_pairs_hook=duplicates)
    if manifest.get('schema')!='xnby.bc7.mip_chain.v1' or manifest.get('format')!='BC7_UNORM_BLOCK' or manifest.get('sourceSHA256')!=source_sha or manifest.get('payloadBytes')!=len(bc7_payload) or manifest.get('payloadSHA256')!=sha(bc7_payload):raise ValueError('Hybrid reference identity differs')
    before=source.stat()
    if not 0<before.st_size<=32*1048576 or sha(source.read_bytes())!=source_sha:raise ValueError('Hybrid source SHA differs')
    with Image.open(source) as loaded:
        if loaded.format!='JPEG' or loaded.mode!='RGB' or list(loaded.size)!=manifest.get('sourceSize') or any(not 0<v<=2048 or v%4 for v in loaded.size):raise ValueError('Invalid hybrid original image')
        base=loaded.convert('RGBA')
    width,height=base.size;offset=0;complete=False;rows=[];tail=[];start=None;prefix_bytes=0;tail_offset=0
    old_rows=manifest.get('mips')
    if not isinstance(old_rows,list) or not 0<len(old_rows)<=12:raise ValueError('Invalid reference mip count')
    for level,old in enumerate(old_rows):
        count=((width+3)//4)*((height+3)//4)*16
        if complete or not all(type(old.get(k)) is int for k in ('level','width','height','offset','bytes')) or tuple(old.get(k) for k in ('level','width','height','offset','bytes'))!=(level,width,height,offset,count):raise ValueError('Invalid reference mip layout')
        block=bc7_payload[offset:offset+count]
        if len(block)!=count or sha(block)!=old.get('sha256'):raise ValueError('Reference mip SHA differs')
        image=base.copy() if level==0 else base.resize((width,height),Image.Resampling.LANCZOS);raw=image.tobytes()
        if sha(raw)!=old.get('sourceRgbaSHA256'):raise ValueError('Original reference mip differs')
        decoded=Image.frombytes('RGBA',(width,height),block,'bcn',(7,'BC7'));metrics=quality(image,decoded)
        accepted=metrics['rgbPSNR']>=40 and metrics['rgbChannelP99']<=16 and metrics['rgbMaxError']<=96
        if start is None and not accepted:start=level
        kind='bc7' if start is None else 'rgba8';payload=block if kind=='bc7' else raw
        if kind=='bc7':prefix_bytes+=count;row_offset=offset;decoded_sha=sha(decoded.tobytes())
        else:
            row_offset=tail_offset;tail.append(raw);tail_offset+=len(raw);decoded_sha=sha(raw);metrics=dict(rgbPSNR=999.0,rgbRMSE=0.0,rgbMeanAbsolute=0.0,rgbChannelP99=0,rgbMaxError=0)
        rows.append(dict(level=level,width=width,height=height,format=kind,offset=row_offset,bytes=len(payload),sha256=sha(payload),decodedRgbaSHA256=decoded_sha,sourceRgbaSHA256=sha(raw),accepted=True,quality=metrics))
        image.close();decoded.close();offset+=count;complete=width==height==1;width=max(1,width//2);height=max(1,height//2)
    if not complete or offset!=len(bc7_payload):raise ValueError('Reference chain incomplete or trailing')
    if start is None or start==0:raise ValueError('Hybrid needs a passing prefix and a failing tail')
    prefix=bc7_payload[:prefix_bytes];tail=b''.join(tail)
    result=dict(schema=SCHEMA,format=FORMAT,sourceSHA256=source_sha,sourceSize=list(base.size),tailStartLevel=start,components=dict(bc7=dict(file='prefix.bc7',bytes=len(prefix),sha256=sha(prefix)),rgba8=dict(file='tail.rgba',bytes=len(tail),sha256=sha(tail))),payloadBytes=len(prefix)+len(tail),payloadSHA256=sha(prefix+tail),mips=rows,accepted=True,qualityThresholds=dict(rgbPSNRMin=40.0,rgbChannelP99Max=16,rgbMaxErrorMax=96),recipe='xnby.hybrid_verified_prefix_exact_tail.v1',referenceManifestSHA256=manifest_sha,referencePayloadSHA256=manifest['payloadSHA256'],producerSHA256=sha(Path(__file__).read_bytes()),nativeEncoderExecuted=False,originalSourceModified=False)
    describe_hybrid(result,source_sha)
    after=source.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or sha(source.read_bytes())!=source_sha:raise ValueError('Hybrid original source changed')
    output.mkdir(parents=True);(output/'prefix.bc7').write_bytes(prefix);(output/'tail.rgba').write_bytes(tail);(output/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');base.close();return result
