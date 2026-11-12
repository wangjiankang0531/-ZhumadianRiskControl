"""Saved label anchors; same explicit placement contract as Web and native.

Never normalizes a document or changes an automatic legacy anchor. Coordinates are
local east/north/up metres. Region height follows deterministic ear triangles.
"""
import math

def _number(v):
    return type(v) in (int,float) and math.isfinite(v)

def _cross(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def _triangles(p):
    def on(a,b,c):
        return (abs(_cross(a,b,c))<.0001 and min(a[0],b[0])-.0001<=c[0]<=max(a[0],b[0])+.0001
                and min(a[1],b[1])-.0001<=c[1]<=max(a[1],b[1])+.0001)
    n=len(p);area=0
    for i,a in enumerate(p):
        b=p[(i+1)%n]
        if math.hypot(b[0]-a[0],b[1]-a[1])<.001: raise ValueError('region has repeated vertices')
        area+=a[0]*b[1]-b[0]*a[1]
        for j in range(i+1,n):
            if j==i+1 or (i==0 and j==n-1):continue
            c,d=p[j],p[(j+1)%n]
            if ((_cross(a,b,c)*_cross(a,b,d)<0 and _cross(c,d,a)*_cross(c,d,b)<0)
                    or on(a,b,c) or on(a,b,d) or on(c,d,a) or on(c,d,b)):
                raise ValueError('region intersects itself')
    if abs(area)<.001: raise ValueError('region has zero area')
    ring=list(range(n)) if area>0 else list(reversed(range(n)));out=[]
    while len(ring)>3:
        for j,b in enumerate(ring):
            a,c=ring[j-1],ring[(j+1)%len(ring)]
            if _cross(p[a],p[b],p[c])<=.00001:continue
            if any(k not in (a,b,c) and _cross(p[a],p[b],p[k])>=-.00001
                   and _cross(p[b],p[c],p[k])>=-.00001 and _cross(p[c],p[a],p[k])>=-.00001 for k in ring):continue
            out.append((a,b,c));ring.pop(j);break
        else:raise ValueError('region cannot be triangulated')
    out.append(tuple(ring));return out

def specified_label_anchor(feature):
    label=feature.get('label')
    if not isinstance(label,dict) or 'anchor' not in label:return None
    a=label['anchor'];p=feature.get('positions');kind=feature.get('type')
    if (not isinstance(a,dict) or kind not in ('point','line','region') or not isinstance(p,list)
            or not {'point':1,'line':2,'region':3}[kind]<=len(p)<=1000 or (kind=='point' and len(p)!=1)
            or any(not isinstance(v,list) or len(v)!=3 or any(not _number(x) or abs(x)>100000 for x in v) for v in p)):
        raise ValueError('invalid label anchor geometry')
    if a.get('kind')=='point' and kind=='point' and set(a)=={'kind'}:return list(p[0])
    if (a.get('kind')=='line-ratio' and kind=='line' and set(a)=={'kind','fraction'}
            and _number(a['fraction']) and 0<=a['fraction']<=1):
        lengths=[math.dist(p[i],p[i+1]) for i in range(len(p)-1)];total=sum(lengths)
        if total==0 or a['fraction']==0:return list(p[0])
        if a['fraction']==1:return list(p[-1])
        remaining=total*a['fraction']
        for i,length in enumerate(lengths):
            if length>0 and remaining<=length:return [x+(p[i+1][k]-x)*remaining/length for k,x in enumerate(p[i])]
            remaining-=length
        return list(p[-1])
    if (a.get('kind')=='region-point' and kind=='region' and set(a)=={'kind','position'}
            and isinstance(a['position'],list) and len(a['position'])==2
            and all(_number(x) and abs(x)<=100000 for x in a['position'])):
        q=a['position']
        for ia,ib,ic in _triangles(p):
            x,y,z=p[ia],p[ib],p[ic];den=_cross(x,y,z)
            u=_cross(y,z,q)/den;v=_cross(z,x,q)/den;w=1-u-v
            if min(u,v,w)>=-1e-10:return [q[0],q[1],u*x[2]+v*y[2]+w*z[2]]
        raise ValueError('label anchor outside region')
    raise ValueError('label anchor does not match feature type or has invalid fields')
