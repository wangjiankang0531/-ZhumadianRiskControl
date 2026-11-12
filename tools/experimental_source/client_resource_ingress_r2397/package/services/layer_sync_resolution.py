"""Bounded conflict comparison; values stay JSON and are never rendered as HTML.

The remote side means the coordinator for an editor conflict, and the fetched
cloud snapshot for a cloud conflict. Neither means a fresh network read.
"""
import copy
import hashlib
import json

from services.layer_sync_state import merge_snapshots, SyncConflict, _equal


def encode(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(',', ':')).encode('utf-8')


def conflict_paths(base, local, remote):
    try:
        merge_snapshots(base, local, remote)
        return []
    except SyncConflict as error:
        return [list(p) for p in error.paths]


def choices_map(value):
    if not isinstance(value, list) or len(value) > 20000:
        raise ValueError('INVALID_CONFLICT_CHOICES')
    result = {}
    for item in value:
        if (not isinstance(item, dict) or set(item) != {'path', 'side'}
                or not isinstance(item['path'], list) or len(item['path']) != 2
                or any(not isinstance(s, str) for s in item['path'])
                or item['side'] not in ('local', 'remote') or tuple(item['path']) in result):
            raise ValueError('INVALID_CONFLICT_CHOICES')
        result[tuple(item['path'])] = item['side']
    return result


def comparison_mode(conflict):
    if conflict.get('basisDocument') is None or 'comparisonDocument' not in conflict:
        return 'whole-project'
    docs = (conflict['basisDocument'], conflict['draftDocument'], conflict['comparisonDocument'])
    # The legacy path name for layer order could collide with an unknown root
    # extension of that name. Retain both drafts; never guess its meaning.
    if any('layerOrder' in d for d in docs):
        return 'whole-project'
    return 'items'


def paths_for(conflict):
    if comparison_mode(conflict) != 'items':
        return [['document', 'initialSelection']]
    return conflict_paths(conflict['basisDocument'], conflict['draftDocument'], conflict['comparisonDocument'])


def value_at(conflict, path, side):
    if side not in ('base', 'local', 'remote'):
        raise ValueError('INVALID_CONFLICT_SIDE')
    docs = {'base': conflict.get('basisDocument'), 'local': conflict['draftDocument'],
            'remote': conflict.get('comparisonDocument', conflict['remoteDocument'])}
    document = docs[side]
    if comparison_mode(conflict) == 'whole-project':
        return {'present': False} if document is None else {'present': True, 'value': copy.deepcopy(document)}
    kind, key = path
    if kind == 'feature':
        for layer in document['layers']:
            for feature in layer['features']:
                if feature['id'] == key:
                    return {'present': True, 'value': {'layerId': layer['id'], 'layerName': layer['name'], 'feature': copy.deepcopy(feature)}}
        return {'present': False}
    if kind == 'document':
        if key == 'layerOrder':
            return {'present': True, 'value': [layer['id'] for layer in document['layers']]}
        return {'present': True, 'value': copy.deepcopy(document[key])} if key in document else {'present': False}
    layer = next((layer for layer in document['layers'] if layer['id'] == key), None)
    if layer is None:
        return {'present': False}
    if kind == 'featureOrder':
        return {'present': True, 'value': [f['id'] for f in layer['features']]}
    if kind == 'layer':
        # All three contain it: this path selects the atomic header only.
        header_only = all(any(l['id'] == key for l in d['layers']) for d in docs.values())
        return {'present': True, 'value': copy.deepcopy(
            {k: v for k, v in layer.items() if k != 'features'} if header_only else layer)}
    raise ValueError('INVALID_CONFLICT_PATH')


def overview(value, path, basis):
    if not value['present']:
        return []
    v = value['value']; b = basis.get('value') if basis['present'] else None
    rows = []
    def row(key, label, text, current, previous):
        rows.append({'key': key, 'label': label, 'text': str(text)[:192],
                     'changed': not basis['present'] or not _equal(current, previous)})
    def pos(points):
        if not points: return '无顶点'
        point = lambda p: ' / '.join(format(n, '.3f') for n in p)
        return str(len(points))+' 个顶点；首点 '+point(points[0])+('；末点 '+point(points[-1]) if len(points)>1 else '')+' 米'
    if path[0] == 'feature':
        f=v['feature']; old=b['feature'] if isinstance(b,dict) and 'feature' in b else {}
        row('name','名称',f.get('name',''),f.get('name'),old.get('name'))
        row('identity','类型 / 图层',{'point':'点','line':'线','region':'区域'}.get(f['type'],f['type'])+' / '+v.get('layerName',v['layerId']),[f['type'],v['layerId']],[old.get('type'),b.get('layerId') if isinstance(b,dict) else None])
        row('positions','位置 / 顶点',pos(f['positions']),f['positions'],old.get('positions'))
        style=f['style'];old_style=old.get('style');style_text='颜色 '+str(style.get('color',''))+'；透明度 '+str(style.get('opacity',''))
        if f['type']=='point':style_text+='；图标 '+str(style.get('icon',''))+'；尺寸 '+str(style.get('sizePx',''))+' 像素'
        else:style_text+='；线型 '+str(style.get('pattern',''))+'；宽度 '+str(style.get('widthPx',''))+' 像素'
        if f['type']=='region':style_text+='；填色 '+str(style.get('fillColor',''))+' / '+str(style.get('fillOpacity',''))
        row('style','样式',style_text,style,old_style)
        label=f.get('label');text='未配置标牌' if label is None else ('显示' if label.get('visible') else '隐藏')+'；文字 '+label.get('text','')+'；高度 '+str(label.get('heightM',''))+' 米；绑定 '+str(len(label.get('dataBindings',[])))+' 项'
        row('label','标牌 / 数据',text,label,old.get('label'))
        excluded={'id','name','type','positions','style','label'};extra={k:x for k,x in f.items() if k not in excluded};old_extra={k:x for k,x in old.items() if k not in excluded}
        if extra or old_extra:row('other','其它属性',('、'.join(sorted(extra)) or '无'),extra,old_extra)
    elif path[0]=='layer' and isinstance(v,dict):
        old=b if isinstance(b,dict) else {}
        for k,label in [('name','图层名称'),('visible','显示'),('locked','锁定')]:row(k,label,v.get(k),v.get(k),old.get(k))
        if 'features'in v or 'features'in old:row('features','层内对象',str(len(v.get('features',[])))+' 个',v.get('features'),old.get('features'))
        excluded={'id','name','visible','locked','features'};extra={k:x for k,x in v.items() if k not in excluded};old_extra={k:x for k,x in old.items() if k not in excluded}
        if extra or old_extra:row('other','其它属性','、'.join(sorted(extra)) or '无',extra,old_extra)
    elif isinstance(v,dict) and v.get('schema')=='hongtu.landscape.layers.v1' and isinstance(v.get('layers'),list):
        old=b if isinstance(b,dict) else {}
        row('layers','图层',str(len(v['layers']))+' 层',v['layers'],old.get('layers'))
        row('features','点线面对象',str(sum(len(l['features'])for l in v['layers']))+' 个',v['layers'],old.get('layers'))
        extra={k:x for k,x in v.items()if k!='layers'};old_extra={k:x for k,x in old.items()if k!='layers'};row('metadata','工程属性','、'.join(sorted(extra)),extra,old_extra)
    else:
        raw=encode(v).decode('utf-8');row('value','值 / 顺序',raw,v,b)
    return rows


def brief(value, path=None, basis=None):
    if not value['present']:
        return {'present': False}
    raw = encode(value['value'])
    return {'present': True, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'preview': raw[:4096].decode('utf-8', errors='replace'), 'truncated': len(raw) > 4096,
            'overview': overview(value, path, basis) if path is not None and basis is not None else []}


def comparison_page(conflict, generation, offset, limit):
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 16:
        raise ValueError('INVALID_CONFLICT_PAGE')
    paths = paths_for(conflict)
    if offset > len(paths):
        raise ValueError('INVALID_CONFLICT_PAGE')
    return {'generation': generation, 'mode': comparison_mode(conflict), 'source': conflict['source'],
            'comparisonRole': 'coordinator' if conflict['source'] == 'editor' else 'cloud',
            'remoteRevisionAtConflict': conflict['remoteRevision'], 'offset': offset, 'total': len(paths),
            'nextOffset': offset + limit if offset + limit < len(paths) else None,
            'items': [{'path': p, 'sides': {s: brief(value_at(conflict, p, s), p, value_at(conflict, p, 'base'))
                                          for s in ('base', 'local', 'remote')}} for p in paths[offset:offset + limit]]}
