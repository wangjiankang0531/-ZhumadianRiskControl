"""Bounded opt-in BC7 preparation using pure JS and independent Pillow decoding.

No native encoder/reader process, raw RGBA files, source edits, or implicit index
publication. Output is a fresh directory. Failed quality stays unaccepted.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct
import subprocess
import time
from PIL import Image, ImageChops, __version__ as pillow_version


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def quality(reference, decoded):
    if decoded.mode != 'RGBA' or decoded.size != reference.size or decoded.getextrema()[3] != (255,255):
        raise ValueError('Independent BC7 decoder changed size or opacity')
    difference=ImageChops.difference(reference.convert('RGB'),decoded.convert('RGB'))
    histogram=difference.histogram();counts=[sum(histogram[c*256+v] for c in range(3)) for v in range(256)]
    count=reference.width*reference.height*3
    mse=sum(v*v*n for v,n in enumerate(counts))/count
    absolute=sum(v*n for v,n in enumerate(counts))/count
    cumulative=0;p99=0
    for v,n in enumerate(counts):
        cumulative+=n
        if cumulative>=math.ceil(count*.99):p99=v;break
    maximum=max(i for i,n in enumerate(counts) if n)
    return dict(rgbPSNR=999.0 if mse==0 else 10*math.log10(255*255/mse),rgbRMSE=math.sqrt(mse),rgbMeanAbsolute=absolute,rgbChannelP99=p99,rgbMaxError=maximum)


def prepare(source, expected_sha256, output, node, *, profile="mode6", persist_payload=True):
    if profile not in ("mode6","mode1-6","mode0-1-2-6","mode0-1-2-3-6","mode0-1-2-3-4-5-6"):raise ValueError("Unknown BC7 profile")
    if type(persist_payload) is not bool:raise ValueError("Invalid payload persistence")
    source=Path(source).resolve(strict=True);output=Path(output).absolute();node=Path(node).resolve(strict=True)
    if output.exists():raise ValueError('Fresh output required; preserve all prior results')
    before=source.stat()
    if not 0<before.st_size<=32*1048576:raise ValueError('Source exceeds encoded image window')
    raw=source.read_bytes()
    if sha(raw)!=expected_sha256:raise ValueError('Source SHA mismatch')
    with Image.open(source) as loaded:
        if loaded.format!='JPEG' or loaded.mode!='RGB' or any(not 0<v<=2048 or v%4 for v in loaded.size):
            raise ValueError('Only bounded original-size opaque derived JPEG accepted')
        base=loaded.copy()
    images=[];width,height=base.size;rows=[];pixels=[]
    while True:
        image=base.copy() if not rows else base.resize((width,height),Image.Resampling.LANCZOS)
        image=image.convert('RGBA');images.append(image);pixels.append(image.tobytes());rows.append(dict(level=len(rows),width=width,height=height))
        if width==height==1:break
        width=max(1,width//2);height=max(1,height//2)
    header=json.dumps(rows,separators=(',',':')).encode()
    batch=b'MB7R'+struct.pack('<I',len(header))+header+b''.join(pixels)
    if len(batch)>24*1048576:raise ValueError('Decoded image batch exceeds CPU window')
    script=Path(__file__).with_name('bc7_mode6_cli.mjs');encoder=script.with_name("bc7_mode6_encoder.mjs" if profile=="mode6" else "bc7_opaque_encoder.mjs" if profile=="mode1-6" else "bc7_three_subset_encoder.mjs" if profile in ("mode0-1-2-6","mode0-1-2-3-6") else "bc7_separated_encoder.mjs")
    started=time.perf_counter()
    run=subprocess.run([str(node),str(script),"--profile="+profile],input=batch,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180,creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess,'CREATE_NO_WINDOW') else 0)
    if run.returncode:raise RuntimeError('Pure JS encoder failed: '+run.stderr.decode('utf-8',errors='replace')[:2000])
    payload=run.stdout;expected=sum(((r['width']+3)//4)*((r['height']+3)//4)*16 for r in rows)
    if len(payload)!=expected or len(payload)>8*1048576:raise ValueError('BC7 output size mismatch')
    elapsed=time.perf_counter()-started;offset=0;mips=[]
    thresholds=dict(rgbPSNRMin=40.0,rgbChannelP99Max=16,rgbMaxErrorMax=96)
    for row,image in zip(rows,images):
        size=((row['width']+3)//4)*((row['height']+3)//4)*16;block=payload[offset:offset+size]
        decoded=Image.frombytes('RGBA',image.size,block,'bcn',(7,'BC7'))
        metrics=quality(image,decoded)
        accepted=metrics['rgbPSNR']>=thresholds['rgbPSNRMin'] and metrics['rgbChannelP99']<=thresholds['rgbChannelP99Max'] and metrics['rgbMaxError']<=thresholds['rgbMaxErrorMax']
        mips.append(dict(**row,offset=offset,bytes=size,sha256=sha(block),sourceRgbaSHA256=sha(image.tobytes()),pillowDecodedSHA256=sha(decoded.tobytes()),quality=metrics,accepted=accepted));offset+=size
        decoded.close();image.close()
    after=source.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns) or sha(source.read_bytes())!=expected_sha256:
        raise ValueError('Source changed during preparation')
    result=dict(schema='xnby.bc7.mip_chain.v1',format='BC7_UNORM_BLOCK',sourceSHA256=expected_sha256,sourceSize=list(base.size),payloadBytes=len(payload),payloadSHA256=sha(payload),mips=mips,recipe='xnby.opaque_bc7_mode6.pca_ls3_spread4.v2' if profile=='mode6' else 'xnby.opaque_bc7_modes1_6.partition64_small_spread4_ls3.v3' if profile=='mode1-6' else 'xnby.opaque_bc7_modes0_1_2_6.small_mips_ls5.v1' if profile=='mode0-1-2-6' else 'xnby.opaque_bc7_modes0_1_2_3_6.tiny_mips_ls5.v2' if profile=='mode0-1-2-3-6' else 'xnby.opaque_bc7_modes0_1_2_3_4_5_6.separated_small_valid_ls5.v1',encoderSHA256=sha(encoder.read_bytes()),cliSHA256=sha(script.read_bytes()),pillowVersion=pillow_version,encodedSeconds=elapsed,qualityThresholds=thresholds,accepted=all(r['accepted'] for r in mips),sourceModified=False,nativeEncoderExecuted=False,rawImageFilesWritten=False)
    result['encoderDependencies']={name:sha(script.with_name(name).read_bytes()) for name in ['bc7_mode6_encoder.mjs','bc7_opaque_encoder.mjs','bc7_partitions.mjs','bc7_three_subset_encoder.mjs','bc7_three_subset_partitions.mjs','bc7_separated_encoder.mjs']}
    result['payloadSaved']=persist_payload
    output.mkdir(parents=True)
    if persist_payload:(output/'texture.bc7').write_bytes(payload)
    (output/'manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    base.close()
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--node',type=Path,required=True);parser.add_argument('--profile',choices=['mode6','mode1-6','mode0-1-2-6','mode0-1-2-3-6','mode0-1-2-3-4-5-6'],default='mode6');args=parser.parse_args()
    result=prepare(args.source,args.sha256,args.output,args.node,profile=args.profile)
    print(json.dumps({k:result[k] for k in ('sourceSHA256','sourceSize','payloadBytes','encodedSeconds','accepted')}))


if __name__=='__main__':main()
