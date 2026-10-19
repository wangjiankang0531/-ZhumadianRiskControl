"""Read existing glTF triangles and attach estimated enterprise points to their local surface.
Never prepares, repairs or overwrites landscape assets. Z is a visual surface sample, not a surveyed elevation.
"""
from pathlib import Path
import hashlib,json
import numpy as np


def heights_on_triangles(vertices, indices, points, batch=65536):
    output=[None for _ in points]
    if len(indices)%3:raise ValueError('Triangle index count differs')
    for start in range(0,len(indices),batch*3):
        tri=np.asarray(vertices[indices[start:start+batch*3].reshape(-1,3)],dtype=np.float64)
        if not np.isfinite(tri).all():raise ValueError('Nonfinite landscape coordinates')
        low=tri[:,:,:2].min(axis=1);high=tri[:,:,:2].max(axis=1)
        for k,(x,y) in enumerate(points):
            selected=(low[:,0]<=x)&(high[:,0]>=x)&(low[:,1]<=y)&(high[:,1]>=y)
            t=tri[selected]
            if not len(t):continue
            a,b,c=t[:,0],t[:,1],t[:,2]
            den=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1])
            keep=np.abs(den)>1e-10;a,b,c,den=a[keep],b[keep],c[keep],den[keep]
            if not len(den):continue
            u=((b[:,1]-c[:,1])*(x-c[:,0])+(c[:,0]-b[:,0])*(y-c[:,1]))/den
            v=((c[:,1]-a[:,1])*(x-c[:,0])+(a[:,0]-c[:,0])*(y-c[:,1]))/den
            w=1-u-v;inside=(u>=-1e-9)&(v>=-1e-9)&(w>=-1e-9)
            z=u*a[:,2]+v*b[:,2]+w*c[:,2]
            if inside.any():
                value=float(z[inside].max())
                output[k]=value if output[k] is None else max(output[k],value)
    return output


def sample_gltf(path, points):
    path=Path(path);doc=json.loads(path.read_text(encoding='utf-8'))
    if len(doc['buffers'])!=1 or len(doc['meshes'])!=1 or len(doc['nodes'])!=1:raise ValueError('Unsupported surface mesh layout')
    node=doc['nodes'][0]
    if any(k in node for k in ['matrix','translation','rotation','scale']):raise ValueError('Surface frame must be explicitly untransformed')
    primitive=doc['meshes'][0]['primitives'][0]
    if len(doc['meshes'][0]['primitives'])!=1 or primitive.get('mode',4)!=4:raise ValueError('Triangle surface required')
    binary=(path.parent/doc['buffers'][0]['uri']).resolve()
    if binary.parent!=path.parent.resolve() or binary.stat().st_size!=doc['buffers'][0]['byteLength']:raise ValueError('Surface buffer ownership/size differs')
    def array(index,component,kind,width):
        acc=doc['accessors'][index];view=doc['bufferViews'][acc['bufferView']]
        if acc['componentType']!=component or acc['type']!=kind or acc.get('sparse') or view.get('byteStride') or view.get('buffer',0)!=0:raise ValueError('Unsupported surface accessor')
        count=acc['count'];offset=view.get('byteOffset',0)+acc.get('byteOffset',0)
        if type(count) is not int or count<=0 or offset<0 or offset+count*width*4>binary.stat().st_size:raise ValueError('Surface accessor bounds differ')
        return np.memmap(binary,mode='r',dtype='<f4' if component==5126 else '<u4',offset=offset,shape=(count,width) if width>1 else (count,))
    vertices=array(primitive['attributes']['POSITION'],5126,'VEC3',3);indices=array(primitive['indices'],5125,'SCALAR',1)
    if int(indices.max())>=len(vertices):raise ValueError('Surface index out of range')
    return heights_on_triangles(vertices,indices,points)
