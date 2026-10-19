"""Lossless in-memory glTF delivery for already verified source-node frames.

No atlas packing, geometry simplification, JPEG re-encoding or asset-file writes.
"""
from __future__ import annotations
import io
import json
from types import MappingProxyType
from PIL import Image


class MemoryGltf:
    def __init__(self, name, max_bytes=128*1024*1024):
        if not name.isascii() or not name.replace('_','').isalnum():
            raise ValueError("invalid memory asset name")
        self.name=name; self.max_bytes=max_bytes; self.binary=bytearray(); self.resources={}
        self.gltf={"asset":{"version":"2.0","generator":"Zhumadian read-only memory source"},
                   "extensionsUsed":["KHR_materials_unlit"],"scene":0,"scenes":[{"nodes":[0]}],"nodes":[{"mesh":0}],
                   "meshes":[{"primitives":[]}],"buffers":[],"bufferViews":[],"accessors":[],"images":[],"textures":[],"samplers":[],"materials":[]}
        self.sealed=False; self.source_nodes=[];self.triangles=0;self.rgba_bytes=0

    def array(self,payload,segment,components,component_type,minimum=None,maximum=None):
        if self.sealed:raise ValueError("memory frontier already sealed")
        while len(self.binary)%4:self.binary.append(0)
        offset=len(self.binary);data=payload[segment["offset"]:segment["offset"]+segment["bytes"]]
        if len(self.binary)+len(data)+sum(len(value[0]) for value in self.resources.values())>self.max_bytes:raise ValueError("memory geometry exceeds budget")
        self.binary.extend(data);view=len(self.gltf['bufferViews']);self.gltf['bufferViews'].append({"buffer":0,"byteOffset":offset,"byteLength":len(data)})
        accessor={"bufferView":view,"componentType":component_type,"count":segment['count']//components,"type":{1:"SCALAR",2:"VEC2",3:"VEC3"}[components]}
        if minimum is not None:accessor['min']=minimum;accessor['max']=maximum
        index=len(self.gltf['accessors']);self.gltf['accessors'].append(accessor);return index

    @staticmethod
    def sampler(source):
        # Match OSG's GL3/GLES adaptation: legacy GL_CLAMP -> GL_CLAMP_TO_EDGE.
        result={}
        for key in ['wrapS','wrapT']:
            value=source[key];value=33071 if value==10496 else value
            if value not in [10497,33071,33648]:raise ValueError("unsupported source texture wrap")
            result[key]=value
        if source['minFilter'] not in [9728,9729,9984,9985,9986,9987] or source['magFilter'] not in [9728,9729]:
            raise ValueError("unsupported source texture filter")
        result.update(minFilter=source['minFilter'],magFilter=source['magFilter']);return result

    def add(self,descriptor,payload):
        if self.sealed:raise ValueError("memory frontier already sealed")
        if descriptor['node'] in self.source_nodes:raise ValueError("duplicate source node")
        image_ids=[]
        for image in descriptor['images']:
            data=bytes(payload[image['offset']:image['offset']+image['bytes']])
            # Preserve source storage row order and UV values together. glTF textures use flipY=false.
            raster=Image.frombytes('RGBA',(image['width'],image['height']),data);output=io.BytesIO();raster.save(output,format='PNG',compress_level=1)
            encoded=output.getvalue();index=len(self.gltf['images']);name=f"{self.name}_texture_{index}.png"
            if sum(len(value[0]) for value in self.resources.values())+len(encoded)+len(self.binary)>self.max_bytes:raise ValueError("memory delivery exceeds budget")
            self.resources[name]=(encoded,'image/png');self.gltf['images'].append({'uri':name});image_ids.append(index);self.rgba_bytes+=len(data)
        for mesh in descriptor['meshes']:
            if mesh['vertexColorsWhite'] is not True:raise ValueError("source color material adapter missing")
            sampler=self.sampler(mesh['sampler']);sampler_index=len(self.gltf['samplers']);self.gltf['samplers'].append(sampler)
            texture=len(self.gltf['textures']);self.gltf['textures'].append({'source':image_ids[mesh['image']],'sampler':sampler_index})
            material=len(self.gltf['materials']);self.gltf['materials'].append({'doubleSided':True,'extensions':{'KHR_materials_unlit':{}},'pbrMetallicRoughness':{'baseColorTexture':{'index':texture},'metallicFactor':0,'roughnessFactor':1}})
            positions=self.array(payload,mesh['positions'],3,5126,mesh['boundsMin'],mesh['boundsMax']);uv=self.array(payload,mesh['uv'],2,5126);indices=self.array(payload,mesh['indices'],1,5125)
            self.gltf['meshes'][0]['primitives'].append({'attributes':{'POSITION':positions,'TEXCOORD_0':uv},'indices':indices,'material':material,'mode':4,'extras':{'sourceNode':descriptor['node']}})
        self.source_nodes.append(descriptor['node']);self.triangles+=descriptor['triangles']

    def finish(self):
        if self.sealed:raise ValueError("memory frontier already sealed")
        if not self.source_nodes:raise ValueError("empty source frontier")
        binary_name=self.name+'.bin';self.gltf['buffers']=[{'uri':binary_name,'byteLength':len(self.binary)}]
        gltf=json.dumps(self.gltf,separators=(',',':')).encode('utf-8');self.resources[binary_name]=(bytes(self.binary),'application/octet-stream');self.resources[self.name+'.gltf']=(gltf,'model/gltf+json')
        total=sum(len(value[0]) for value in self.resources.values())
        if total>self.max_bytes:raise ValueError("complete memory delivery exceeds budget")
        self.sealed=True
        return MappingProxyType(dict(self.resources)),{'sourceNodes':len(self.source_nodes),'triangles':self.triangles,'images':len(self.gltf['images']),'rgbaBytes':self.rgba_bytes,'geometryBytes':len(self.binary),'deliveryBytes':total,'sourceNodeNames':list(self.source_nodes)}
