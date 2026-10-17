import {Vector3,Box3} from 'three';
// Tessellation in screen pixels, not a survey/geometric-deviation error bound.
export function selectDepth(rootPixels, basePixels, readyPixels, readyDepth, maxDepth, parentPixels = 0, baseTexelPixels = 0, readyTexelPixels = 0, parentTexelPixels = 0) {
  basePixels=Math.max(basePixels,baseTexelPixels*4);readyPixels=Math.max(readyPixels,readyTexelPixels*4);parentPixels=Math.max(parentPixels,parentTexelPixels*4);
  if (![rootPixels, basePixels, readyPixels].every(Number.isFinite) || maxDepth < 1 || basePixels <= 0) return 0;
  if (basePixels < (readyDepth > 0 ? 3 : 6) || rootPixels < (readyDepth > 0 ? 24 : 32)) return 0;
  if (readyDepth < 1) return Math.min(3, maxDepth);
  if (readyDepth > 3 && readyPixels < 2 && parentPixels > 0 && parentPixels <= 4) return readyDepth - 1;
  return readyPixels > 6 ? Math.min(readyDepth + 1, maxDepth) : readyDepth;
}

export function measureBaseEdges(catalog, positions, indices) {
  const edges = new Map();
  const length = (a, b) => Math.hypot(positions[a * 3] - positions[b * 3],
    positions[a * 3 + 1] - positions[b * 3 + 1], positions[a * 3 + 2] - positions[b * 3 + 2]);
  for (const root of catalog.root_records) {
    const samples = [];
    for (const [first, count] of root.base_spans) {
      for (let i = first; i < first + count; i += 3) {
        const a = indices[i], b = indices[i + 1], c = indices[i + 2];
        samples.push(Math.max(length(a, b), length(b, c), length(c, a)));
      }
    }
    samples.sort((a, b) => a - b);
    const edge = samples[Math.min(samples.length - 1, Math.floor(samples.length * .9))];
    if (!Number.isFinite(edge) || edge <= 0) throw Error('基础层细节尺度无效');
    edges.set(root.tile_id, edge);
  }
  return edges;
}

export function measureBaseTexels(catalog,positions,indices,uvs,textureWidth,textureHeight) {
  const output=new Map();
  for(const root of catalog.root_records){const samples=[];
    for(const [first,count] of root.base_spans)for(let i=first;i<first+count;i+=3){const ids=[indices[i],indices[i+1],indices[i+2]];
      for(const [a,b] of [[0,1],[1,2],[2,0]]){const x=ids[a],y=ids[b],pixels=Math.hypot((uvs[x*2]-uvs[y*2])*textureWidth,(uvs[x*2+1]-uvs[y*2+1])*textureHeight);
        if(pixels>1e-6)samples.push(Math.hypot(positions[x*3]-positions[y*3],positions[x*3+1]-positions[y*3+1],positions[x*3+2]-positions[y*3+2])/pixels);
      }
    }
    samples.sort((a,b)=>a-b);const value=samples[Math.min(samples.length-1,Math.floor(samples.length*.9))];if(Number.isFinite(value)&&value>0)output.set(root.tile_id,value);
  }return output;
}
export function prioritizeDetail(ranked,residents,focusId){
  const phase=r=>{const prior=residents.get(r.id);return prior&&r.depth<prior.depth?0:r.id===focusId?1:prior?3:2;};
  return [...ranked].sort((a,b)=>phase(a)-phase(b)||(phase(a)===3?b.edgePixels-a.edgePixels:0));
}

export function pickFocusRoot(candidates,catalog,positions,indices,ray){
  const a=new Vector3(),b=new Vector3(),c=new Vector3(),hit=new Vector3(),boxHit=new Vector3();let closest=Infinity,chosen=null;
  for(const item of candidates){const root=catalog.root_records[item.id-1];const box=new Box3(new Vector3(...root.bounds_min),new Vector3(...root.bounds_max));
    if(!ray.intersectBox(box,boxHit)||box.distanceToPoint(ray.origin)**2>closest)continue;
    for(const [first,count] of root.base_spans)for(let i=first;i<first+count;i+=3){a.fromArray(positions,indices[i]*3);b.fromArray(positions,indices[i+1]*3);c.fromArray(positions,indices[i+2]*3);
      if(ray.intersectTriangle(a,b,c,false,hit)){const distance=hit.distanceToSquared(ray.origin);if(distance<closest){closest=distance;chosen=item;}}
    }
  }return chosen;
}
