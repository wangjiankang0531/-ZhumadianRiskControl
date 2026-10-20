import {Box3,Vector3,Matrix4} from 'three';

const boundsCache=new WeakMap(),epsilon=2**-23,gamma=16*epsilon/(1-16*epsilon);
const full=(width,height,reason)=>({x:0,y:0,width,height,pixels:width*height,fullPixels:width*height,reason});
// Include float32 uniform conversion and a conservative bound for both shader
// dot products. Ambiguous w/near-plane intersections always use the full view.
function dot(row,values){let center=0,radius=0,magnitude=0;for(let i=0;i<4;i++){const [lo,hi]=values[i],mid=(lo+hi)/2,r=(hi-lo)/2;center+=row[i]*mid;radius+=Math.abs(row[i])*r;magnitude+=Math.abs(row[i])*(Math.abs(mid)+r);}const error=radius+gamma*magnitude+1e-36;return [center-error,center+error];}
function rows(matrix){return [0,1,2,3].map(r=>[0,1,2,3].map(c=>Math.fround(matrix.elements[c*4+r])));}
function spanBounds(mesh,spans){
 const geometry=mesh.geometry,p=geometry?.attributes?.position,index=geometry?.index;
 if(!p||!index||p.itemSize!==3||p.normalized||!Array.isArray(spans)||!spans.length||mesh.isSkinnedMesh||mesh.isInstancedMesh||mesh.isBatchedMesh||geometry.morphAttributes?.position?.length)return null;
 const key=spans.map(s=>`${s.first}/${s.count}`).sort().join(','),version=p.version??p.data?.version??0,iv=index.version??index.data?.version??0;let cached=boundsCache.get(geometry);
 if(!cached||cached.p!==p||cached.index!==index||cached.version!==version||cached.iv!==iv){cached={p,index,version,iv,entries:new Map()};boundsCache.set(geometry,cached);}
 if(cached.entries.has(key)){const box=cached.entries.get(key);cached.entries.delete(key);cached.entries.set(key,box);return box;}
 const box=new Box3(),point=new Vector3();for(const s of spans){if(!Number.isSafeInteger(s.first)||!Number.isSafeInteger(s.count)||s.first<0||s.count<=0||s.first%3||s.count%3||s.first+s.count>index.count)return null;for(let i=s.first;i<s.first+s.count;i++){const at=index.getX(i);if(!Number.isInteger(at)||at<0||at>=p.count)return null;point.fromBufferAttribute(p,at);if(![point.x,point.y,point.z].every(Number.isFinite))return null;box.expandByPoint(point);}}
 cached.entries.set(key,box);while(cached.entries.size>64)cached.entries.delete(cached.entries.keys().next().value);return box;
}

export function coverageRegion({camera,parentSpans,width,height}){
 if(!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>4096||height>2160)throw Error('Invalid coverage region dimensions');
 if(!(parentSpans instanceof Map)||!parentSpans.size)return full(width,height,'no_projectable_parent');
 camera.updateMatrixWorld(true);const projection=rows(camera.projectionMatrix);let minX=Infinity,minY=Infinity,maxX=-Infinity,maxY=-Infinity;
 for(const [mesh,spans] of parentSpans){
  const box=spanBounds(mesh,spans);if(!box||box.isEmpty())return full(width,height,'unsupported_parent_geometry');mesh.updateWorldMatrix(true,false);const modelView=rows(new Matrix4().multiplyMatrices(camera.matrixWorldInverse,mesh.matrixWorld));
  for(let corner=0;corner<8;corner++){
   const xyz=[corner&1?box.max.x:box.min.x,corner&2?box.max.y:box.min.y,corner&4?box.max.z:box.min.z,1].map(v=>[v,v]);const mv=modelView.map(r=>dot(r,xyz)),clip=projection.map(r=>dot(r,mv)),w=clip[3];
   if(!clip.flat().every(Number.isFinite)||w[0]<=1e-6||clip[2][0]+w[0]<=0)return full(width,height,'near_plane_or_numerical');
   for(let axis=0;axis<2;axis++){const ratios=[clip[axis][0]/w[0],clip[axis][0]/w[1],clip[axis][1]/w[0],clip[axis][1]/w[1]],lo=Math.min(...ratios),hi=Math.max(...ratios);if(axis===0){minX=Math.min(minX,lo);maxX=Math.max(maxX,hi);}else{minY=Math.min(minY,lo);maxY=Math.max(maxY,hi);}}
  }
 }
 // Four pixels cover the unchanged two-pixel neighborhood plus raster/rounding
 // fringe. Only a true viewport edge may clip the parent's neighborhood.
 const x=Math.max(0,Math.floor((minX+1)*width/2)-4),y=Math.max(0,Math.floor((minY+1)*height/2)-4),right=Math.min(width,Math.ceil((maxX+1)*width/2)+4),top=Math.min(height,Math.ceil((maxY+1)*height/2)+4);
 if(right<=x||top<=y)return full(width,height,'parent_outside_viewport');
 return {x,y,width:right-x,height:top-y,pixels:(right-x)*(top-y),fullPixels:width*height,reason:'original_parent_span_bounds'};
}
