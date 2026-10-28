"""Convert the explicitly supported OSGB data subset to a validated RAM frame.

Original float32 positions, UVs and triangle indices are copied unchanged.
JPEG rows follow OSG's bottom-left storage contract; no resampling or files.
"""
import hashlib
import io
import json
import re
import struct
from PIL import Image

from osgb_v80_data_reader import DataReader, UnsupportedOSGB
from osgb_memory_reader import parse_frame


def require(value,message):
    if not value:raise UnsupportedOSGB(message)


def _build_validated_frame(raw,node,maximum=128*1048576):
    match=re.fullmatch(r'Tile_([1-9][0-9]*)/(Tile_([1-9][0-9]*)_L[0-9]+_0[0-9u]+\.osgb)',node)
    require(match and match[1]==match[3],'Invalid pinned source node name')
    require(type(maximum) is int and 0<maximum<=128*1048576,'Invalid frame budget')
    reader=DataReader(raw);reader.parse()
    meshes=[v for v in reader.objects.values() if v['class']=='osg::Geometry']
    require(0<len(meshes)<=2048,'Unsupported empty or oversized mesh set')
    for out in reader.objects.values():
        require(out.get('userData') is None and all(out.get(k) is None for k in ('updateCallback','eventCallback','cullCallback','boundCallback','drawCallback','shape')),'Custom source callbacks or state require an adapter')
        if out['class'] in ('osg::Group','osg::PagedLOD','osg::Geode'):
            require(out['nodeMask']==0xffffffff and out['stateSet'] is None,'Inherited or masked source node requires an adapter')
        if out['class']=='osg::StateSet':
            require(not out['modes'] and out['textureModes']==[[(3553,1)]] and out['renderingHint']==0 and out['renderBinMode']==0 and out['binNumber']==0 and not out['binName'],'Unsupported source rendering state')
        if out['class']=='osg::Material':
            require(out['colorMode']==5635 and out['diffuse']==(True,(1.0,)*8),'Nonwhite source material requires an adapter')
    payload=bytearray();images=[];image_ids={};output_meshes=[]
    def append(data,count):
        while len(payload)%4:payload.append(0)
        require(0<len(data)<=maximum-len(payload),'OSGB frame exceeds memory budget')
        row=dict(offset=len(payload),bytes=len(data),count=count);payload.extend(data);return row
    for mesh in meshes:
        require(mesh['vertices'] and mesh['vertices']['indices'] is None and mesh['vertices']['binding']==4 and not mesh['vertices']['normalize'],'Unsupported vertex indices/binding/normalization')
        positions=mesh['vertices']['array'];require(positions and positions['kind']==16 and positions['count']>0,'Only original float32 XYZ positions supported')
        require(len(mesh['texCoords'])==1 and mesh['texCoords'][0]['indices'] is None and mesh['texCoords'][0]['binding']==4 and not mesh['texCoords'][0]['normalize'],'Unsupported UV layers, binding or indices')
        uv=mesh['texCoords'][0]['array'];require(uv and uv['kind']==15 and uv['count']==positions['count'],'Only matching original float32 UVs supported')
        require(mesh['colors'] is None and mesh['secondaryColors'] is None and mesh['fogCoords'] is None and not mesh['vertexAttributes'],'Additional source vertex attributes require an adapter')
        state=mesh['stateSet'];require(state and state['class']=='osg::StateSet' and len(state['textureAttributes'])==1 and len(state['textureAttributes'][0])==1,'One source texture unit is required')
        require(all(a['class']=='osg::Material' and mode==0 for a,mode in state['attributes']),'Unsupported nonmaterial source attributes')
        texture,flags=state['textureAttributes'][0][0]
        require(texture['class']=='osg::Texture2D' and flags==0,'Unsupported texture attribute override')
        require(texture['wrapS'] in (10496,10497,33071,33648) and texture['wrapT'] in (10496,10497,33071,33648) and texture['wrapR']==10496,'Unsupported source wrap')
        require(texture['minFilter']==9729 and texture['magFilter']==9729,'This adapter requires original nonmipmapped linear sampling')
        require(texture['borderColor']==(0.0,)*4 and texture['borderWidth']==0 and texture['internalFormatMode']==0 and texture['internalFormat'] is None and texture['sourceFormat'] is None and texture['sourceType'] is None and not texture['shadowComparison'] and texture['textureWidth']==texture['textureHeight']==0,'Source texture transforms/formats require an adapter')
        image=texture['image'];require(image and image['class']=='osg::Image','Original inline JPEG is required')
        if image['id'] not in image_ids:
            with Image.open(io.BytesIO(image['encoded'])) as encoded:
                require(encoded.format=='JPEG' and encoded.mode=='RGB' and 0<encoded.width*encoded.height*4<=32*1048576,'Unsupported original JPEG extent/color space')
                require(encoded.width*encoded.height*4<=maximum-len(payload),'Decoded JPEG exceeds remaining frame budget')
                encoded.load();flipped=encoded.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                try:
                    rgba=flipped.convert('RGBA')
                    try:pixels=rgba.tobytes();width,height=rgba.size
                    finally:rgba.close()
                finally:flipped.close()
            image_ids[image['id']]=len(images)
            images.append(dict(append(pixels,len(pixels)),width=width,height=height,format='rgba8',rowOrder='source_storage',sourceOrigin='bottom_left'))
        primitives=mesh['primitives'];require(primitives and all(p['kind']==54 and p['mode']==4 and p['count']>0 and p['count']%3==0 for p in primitives),'Only unchanged uint32 triangle lists supported')
        indices=b''.join(p['raw'] for p in primitives)
        require(all(v[0]<positions['count'] for v in struct.iter_unpack('<I',indices)),'Triangle index exceeds source vertex count')
        points=list(struct.iter_unpack('<fff',positions['raw']))
        low=[min(p[i] for p in points) for i in range(3)];high=[max(p[i] for p in points) for i in range(3)]
        output_meshes.append(dict(positions=append(positions['raw'],positions['count']*3),uv=append(uv['raw'],uv['count']*2),indices=append(indices,len(indices)//4),
            boundsMin=low,boundsMax=high,image=image_ids[image['id']],sampler={k:texture[k] for k in ('wrapS','wrapT','minFilter','magFilter')},unlit=True,vertexColorsWhite=True))
    descriptor=dict(schema='zhumadian.osgb.memory.v1',node=node,sourceBytes=len(raw),payloadBytes=len(payload),externalReadAttempts=0,writeAttempts=0,
        coordinates='source_local_metres',uv='source_unchanged',littleEndian=True,images=images,meshes=output_meshes,
        vertices=sum(m['positions']['count']//3 for m in output_meshes),triangles=sum(m['indices']['count']//3 for m in output_meshes))
    header=json.dumps(descriptor,separators=(',',':'),allow_nan=False).encode('utf-8')
    require(len(header)<=1048576,'Frame descriptor exceeds bound')
    frame=b'ZMDOSGB1'+struct.pack('<QQ',len(header),len(payload))+header+payload
    validated,view=parse_frame(frame,node,len(raw))
    return frame,validated,view


def build_frame(raw,node,maximum=128*1048576):
    """Preserve the complete packed-frame and audit API for existing callers."""
    frame,descriptor,payload=_build_validated_frame(raw,node,maximum)
    return frame,dict(sourceSHA256=hashlib.sha256(raw).hexdigest(),frameSHA256=hashlib.sha256(frame).hexdigest(),sourceBytes=len(raw),payloadBytes=len(payload),
        imageCount=len(descriptor['images']),meshCount=len(descriptor['meshes']),vertices=descriptor['vertices'],triangles=descriptor['triangles'],externalReadAttempts=0,writeAttempts=0)


def build_parsed_frame(raw,node,maximum=128*1048576):
    """Return the already validated descriptor and readonly immutable-frame view.

    Every structural/array/budget check still runs once on the exact packed
    frame. The view owns those immutable bytes; no second parse or unused audit
    hashes are needed by the pinned original-data callable.
    """
    _,descriptor,payload=_build_validated_frame(raw,node,maximum)
    return descriptor,payload
