"""Explicit additive DLG import, distinct from three-way synchronization.

Absence in a file never deletes current data. There is no invented common
basis: collisions compare the current object with the selected file object.
Only the final, generation-fenced selection becomes a durable client edit.
"""
import base64,copy,hashlib,re,secrets
from collections import OrderedDict
from services.common import loads
from services.layer_sync_state import _equal
from services.layer_sync_resolution import brief
from tools.landscape_layer_validation import validate_editor_layers

MAX_FILE=16*1048576

def encode(value):
    from services.layer_sync_client import _encode
    return _encode(value)

def read_file(file_data,sha256,name):
    if (not isinstance(name,str) or not name or len(name)>256 or len(name.encode('utf-8'))>1024
            or any(ord(c)<32 or c in '/\\:' for c in name)):
        raise ValueError('IMPORT_BASENAME_REQUIRED')
    if not isinstance(sha256,str) or not re.fullmatch('[0-9a-f]{64}',sha256):raise ValueError('IMPORT_FILE_HASH_REQUIRED')
    if not isinstance(file_data,str) or len(file_data)>((MAX_FILE+2)//3)*4:raise ValueError('IMPORT_FILE_TOO_LARGE')
    try:raw=base64.b64decode(file_data,validate=True)
    except (ValueError,TypeError):raise ValueError('INVALID_IMPORT_ENCODING') from None
    if not raw or len(raw)>MAX_FILE:raise ValueError('IMPORT_FILE_TOO_LARGE')
    if hashlib.sha256(raw).hexdigest()!=sha256:raise ValueError('IMPORT_FILE_CHANGED')
    try:document=loads(raw);validate_editor_layers(document);encode(document)
    except (ValueError,TypeError,RecursionError):raise ValueError('INVALID_IMPORT_DOCUMENT') from None
    return document,len(raw)

def header(layer):return {k:v for k,v in layer.items()if k!='features'}
def layers(document):return {l['id']:l for l in document['layers']}
def features(document):return {f['id']:{'layerId':l['id'],'feature':f}for l in document['layers']for f in l['features']}

def choices_map(value):
    if not isinstance(value,list)or len(value)>12000:raise ValueError('INVALID_IMPORT_CHOICES')
    choices={}
    for v in value:
        if (not isinstance(v,dict)or set(v)!={'path','side'}or not isinstance(v['path'],list)or len(v['path'])!=2
                or any(not isinstance(x,str)for x in v['path'])or v['side']not in('current','import')or tuple(v['path'])in choices):
            raise ValueError('INVALID_IMPORT_CHOICES')
        choices[tuple(v['path'])]=v['side']
    return choices

class ImportPlan:
    def __init__(self,current,incoming,generation,name,file_sha256,raw_size):
        validate_editor_layers(current);validate_editor_layers(incoming)
        self.current=copy.deepcopy(current);self.incoming=copy.deepcopy(incoming);self.generation=generation
        self.name,self.file_sha256=name,file_sha256;self.id=secrets.token_hex(16);self.applied=False
        self.layer_maps=[layers(d)for d in(self.current,self.incoming)];self.feature_maps=[features(d)for d in(self.current,self.incoming)]
        self.logical_bytes=len(encode(current))+raw_size
        cl,il=self.layer_maps;cf,inf=self.feature_maps
        if len(set(cl)|set(il))>1000 or len(set(cf)|set(inf))>10000:raise ValueError('IMPORT_RESULT_LIMIT_EXCEEDED')
        paths=[]
        for key in sorted(set(current)&set(incoming)-{'layers'}):
            if not _equal(current[key],incoming[key]):paths.append(('document',key))
        for key in sorted(set(cl)&set(il)):
            if not _equal(header(cl[key]),header(il[key])):paths.append(('layer',key))
        for key in sorted(set(cf)&set(inf)):
            if not _equal(cf[key],inf[key]):paths.append(('feature',key))
        self.paths=tuple(paths);self.path_set=set(paths)
        duplicate=sum(_equal(cf[k],inf[k])for k in set(cf)&set(inf))
        self.summary={'fileName':name,'currentLayers':len(cl),'currentObjects':len(cf),'fileLayers':len(il),'fileObjects':len(inf),
                      'newLayers':len(set(il)-set(cl)),'newObjects':len(set(inf)-set(cf)),
                      'identicalObjects':duplicate,'collisionCount':len(paths),'resultLayers':len(set(cl)|set(il)),
                      'resultObjects':len(set(cf)|set(inf)),
                      'newProperties':len(set(incoming)-set(current)-{'layers'}),
                      'sameNameDifferentIdLayers':sum(any(l['name']==old['name']and l['id']!=old['id']for old in current['layers'])for l in incoming['layers']if l['id']not in cl),
                      'addedLayers':[{'id':l['id'],'name':l['name'][:128],'objects':len(l['features']),'visible':l['visible']}for l in incoming['layers']if l['id']not in cl][:50]}
    def value(self,path,side):
        if not isinstance(path,list) or len(path)!=2 or any(not isinstance(x,str)for x in path):raise ValueError('INVALID_IMPORT_PATH')
        p=tuple(path)
        if p not in self.path_set or side not in('current','import'):raise ValueError('INVALID_IMPORT_PATH')
        n=0 if side=='current'else 1;document=self.current if n==0 else self.incoming;kind,key=p
        if kind=='document':value=document[key]
        elif kind=='layer':value=header(self.layer_maps[n][key])
        else:
            value=copy.deepcopy(self.feature_maps[n][key]);value['layerName']=self.layer_maps[n][value['layerId']]['name']
        return {'present':True,'value':copy.deepcopy(value)}
    def page(self,offset=0,limit=8):
        if type(offset)is not int or offset<0 or offset>len(self.paths)or type(limit)is not int or not 1<=limit<=16:raise ValueError('INVALID_IMPORT_PAGE')
        items=[]
        for p in self.paths[offset:offset+limit]:
            path=list(p);current=self.value(path,'current');incoming=self.value(path,'import')
            items.append({'path':path,'sides':{'current':brief(current,path,current),'import':brief(incoming,path,current)}})
        return {'planId':self.id,'generation':self.generation,'summary':copy.deepcopy(self.summary),'offset':offset,'total':len(self.paths),
                'nextOffset':offset+limit if offset+limit<len(self.paths)else None,'items':items}
    def merged(self,value):
        choices=choices_map(value)
        if set(choices)!=self.path_set:raise ValueError('EXACT_IMPORT_CHOICES_REQUIRED')
        result=copy.deepcopy(self.current)
        for key,v in self.incoming.items():
            if key=='layers':continue
            if key not in result or choices.get(('document',key))=='import':result[key]=copy.deepcopy(v)
        cl,il=self.layer_maps;cf,inf=self.feature_maps;selected={}
        for key in set(cf)|set(inf):
            branch=inf if key not in cf or choices.get(('feature',key))=='import'else cf
            selected[key]=branch[key]
        ordered=[l['id']for l in self.current['layers']]+[l['id']for l in self.incoming['layers']if l['id']not in cl]
        result['layers']=[]
        for key in ordered:
            h=il[key]if key not in cl or choices.get(('layer',key))=='import'else cl[key]
            layer=copy.deepcopy(header(h));ids=[];seen=set()
            for branch in(cl.get(key,{}).get('features',[]),il.get(key,{}).get('features',[])):
                for f in branch:
                    if f['id']not in seen and selected[f['id']]['layerId']==key:ids.append(f['id']);seen.add(f['id'])
            layer['features']=[copy.deepcopy(selected[k]['feature'])for k in ids];result['layers'].append(layer)
        validate_editor_layers(result)
        if len(encode(result))>MAX_FILE:raise ValueError('IMPORT_RESULT_TOO_LARGE')
        return result

class ImportPlans:
    """At most two immutable previews; budget is serialized bytes, not RSS/VRAM."""
    def __init__(self):self.plans=OrderedDict()
    def add(self,plan):
        if plan.logical_bytes>64*1048576:raise ValueError('IMPORT_PREVIEW_TOO_LARGE')
        while self.plans and(len(self.plans)>=2 or sum(p.logical_bytes for p in self.plans.values())+plan.logical_bytes>64*1048576):self.plans.popitem(last=False)
        self.plans[plan.id]=plan
        return plan
    def get(self,plan_id):
        if not isinstance(plan_id,str)or not re.fullmatch('[0-9a-f]{32}',plan_id)or plan_id not in self.plans:raise ValueError('IMPORT_PREVIEW_EXPIRED')
        return self.plans[plan_id]