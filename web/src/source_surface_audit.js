import {Vector3,Ray} from 'three';
import {buildGeometryBvh,intersectGeometryBvh,geometryPacketLimit} from './source_geometry_gain.js';

const verified=new WeakSet(),require=(ok,message)=>{if(!ok)throw Error(message);};
// Observation only. The caller must validate source bytes/layout/ownership first.
// A sampled separation is neither a geometric-error bound nor admission proof.
export function prepareSurfaceAudit(pages){
 require(Array.isArray(pages)&&pages.length>0&&pages.length<=128,'Invalid surface page count');
 let bytes=0;const keys=new Set(),parts=[],buffers=new Set();
 for(const p of pages){
  require(typeof p.key==='string'&&p.key.length>0&&p.key.length<=512&&!keys.has(p.key)&&typeof p.group==='string'&&p.group.length>0&&p.group.length<=512,'Invalid surface page identity');keys.add(p.key);
  require(p.positions instanceof Float32Array&&p.positions.length>0&&p.positions.length%3===0&&p.indices instanceof Uint32Array&&p.indices.length>0&&p.indices.length%3===0&&p.owners instanceof Int32Array&&p.owners.length===p.indices.length/3,'Invalid surface arrays');
  for(const array of [p.positions,p.indices,p.owners])if(!buffers.has(array.buffer)){buffers.add(array.buffer);bytes+=array.buffer.byteLength;}bytes+=p.indices.length/3*8;require(bytes<=geometryPacketLimit,'Surface CPU bound exceeded');
  require(p.positions.every(Number.isFinite)&&p.indices.every(i=>i<p.positions.length/3)&&Array.isArray(p.metrics)&&p.metrics.length>0&&p.metrics.length<=8192&&p.owners.every(i=>i>=0&&i<p.metrics.length),'Invalid surface geometry or ownership');
  require(p.metrics.every(m=>typeof m.name==='string'&&Number.isFinite(m.longest_edge_p90_m)&&m.longest_edge_p90_m>=0&&Number.isFinite(m.texel_world_p90_m)&&m.texel_world_p90_m>=0),'Invalid surface metrics');
  const count=p.indices.length/3;parts.push({...buildGeometryBvh({positions:p.positions,indices:p.indices,owners:Uint32Array.from({length:count},(_,i)=>i)}),key:p.key,group:p.group,sources:p.owners,metrics:p.metrics});
 }
 const result={parts,CPUArrayBytes:bytes};verified.add(result);return result;
}

export function traceSurfaceAudit(model,ray,minimum,maximum){
 require(verified.has(model)&&ray instanceof Ray&&[...ray.origin.toArray(),...ray.direction.toArray()].every(Number.isFinite)&&Math.abs(ray.direction.length()-1)<1e-8&&Number.isFinite(minimum)&&minimum>=0&&Number.isFinite(maximum)&&maximum>minimum,'Invalid surface ray');
 let best=null;
 for(const p of model.parts){const h=intersectGeometryBvh(p,ray,best?.distance??maximum,minimum);if(h)best={...h,page:p};}
 if(!best)return null;
 const {positions,indices}=best.page,j=best.node*3,a=new Vector3().fromArray(positions,indices[j]*3),b=new Vector3().fromArray(positions,indices[j+1]*3),c=new Vector3().fromArray(positions,indices[j+2]*3),normal=new Vector3().crossVectors(b.sub(a),c.sub(a));
 require(normal.lengthSq()>0,'Degenerate surface hit');normal.normalize();
 return {point:best.point,distance:best.distance,normal,metric:best.page.metrics[best.page.sources[best.node]],group:best.page.group,page:best.page.key,triangle:best.node};
}

function quantiles(values){if(!values.length)return {p50:null,p90:null,p99:null,max:null};values.sort((a,b)=>a-b);const at=q=>values[Math.min(values.length-1,Math.floor(values.length*q))];return {p50:at(.5),p90:at(.9),p99:at(.99),max:values.at(-1)};}
const fields=['edgePixels','raySeparationScaled','normalSeparationScaled','normalAngleDegrees','parentTexelPixels','childTexelPixels'];
function cell(){return {beforeOnly:0,afterOnly:0,outsideFocus:0,changedGroup:0,matched:0,edgeOver6:0,edgeOver6AndNormalUnder1:0,...Object.fromEntries(fields.map(k=>[k,[]]))};}
function finish(c){return {...c,...Object.fromEntries(fields.map(k=>[k,quantiles(c[k])]))};}

export function sampleSurfaceSeparation({before,after,camera,width,height,rasterWidth=96,focusGroup=null}){
 require(verified.has(before)&&verified.has(after)&&camera?.isPerspectiveCamera&&Number.isInteger(width)&&width>0&&width<=16384&&Number.isInteger(height)&&height>0&&height<=16384&&Number.isInteger(rasterWidth)&&rasterWidth>=8&&rasterWidth<=512&&(focusGroup===null||typeof focusGroup==='string'),'Invalid surface sampling view');
 require(Number.isFinite(camera.near)&&camera.near>0&&Number.isFinite(camera.far)&&camera.far>camera.near&&Number.isFinite(camera.fov)&&camera.fov>0&&camera.fov<179&&Math.abs(camera.aspect-width/height)<1e-9,'Surface projection differs');
 camera.updateMatrixWorld();const rasterHeight=Math.max(1,Math.round(rasterWidth*height/width));require(rasterWidth*rasterHeight<=65536&&[...camera.matrixWorld.elements,...camera.projectionMatrixInverse.elements].every(Number.isFinite),'Surface sampling bound exceeded');
 const focal=height/(2*Math.tan(camera.fov*Math.PI/360)),origin=new Vector3().setFromMatrixPosition(camera.matrixWorld),cells=Array.from({length:9},cell),total=cell(),largestNormalSeparations=[],largestNormalAngles=[];let empty=0;
 const keep=(list,row,key)=>{if(list.length===16&&row[key]<=list.at(-1)[key])return;list.push(row);list.sort((a,b)=>b[key]-a[key]||a.y-b.y||a.x-b.x);if(list.length>16)list.pop();};
 for(let y=0;y<rasterHeight;y++)for(let x=0;x<rasterWidth;x++){
  const dir=new Vector3((x+.5)/rasterWidth*2-1,1-(y+.5)/rasterHeight*2,.5).unproject(camera).sub(origin).normalize(),forward=-dir.clone().transformDirection(camera.matrixWorldInverse).z;require(forward>0,'Invalid surface sample direction');
  const ray=new Ray(origin,dir),p=traceSurfaceAudit(before,ray,camera.near/forward,camera.far/forward),q=traceSurfaceAudit(after,ray,camera.near/forward,camera.far/forward),c=cells[Math.min(2,Math.floor(y*3/rasterHeight))*3+Math.min(2,Math.floor(x*3/rasterWidth))];
  if(!p&&!q){empty++;continue;}let reason=null;if(!p)reason='afterOnly';else if(!q)reason='beforeOnly';else if(p.group!==q.group)reason='changedGroup';else if(focusGroup!==null&&p.group!==focusGroup)reason='outsideFocus';
  if(reason){c[reason]++;total[reason]++;continue;}
  const delta=q.point.clone().sub(p.point),depth=-p.point.clone().applyMatrix4(camera.matrixWorldInverse).z,scale=focal/depth,e=p.metric.longest_edge_p90_m*scale,n=Math.abs(delta.dot(p.normal))*scale;
  const row=[e,delta.length()*scale,n,Math.acos(Math.max(-1,Math.min(1,Math.abs(p.normal.dot(q.normal)))))*180/Math.PI,p.metric.texel_world_p90_m*scale,q.metric.texel_world_p90_m*scale];require(row.every(Number.isFinite),'Invalid surface separation');
  for(const out of [c,total]){out.matched++;if(e>6){out.edgeOver6++;if(n<1)out.edgeOver6AndNormalUnder1++;}fields.forEach((key,i)=>out[key].push(row[i]));}
  const sample={x:(x+.5)*width/rasterWidth,y:(y+.5)*height/rasterHeight,normalSeparationScaled:n,raySeparationScaled:row[1],normalAngleDegrees:row[3],parentSource:p.metric.name,childSource:q.metric.name,parentPage:p.page,childPage:q.page,parentTriangle:p.triangle,childTriangle:q.triangle};keep(largestNormalSeparations,sample,'normalSeparationScaled');keep(largestNormalAngles,sample,'normalAngleDegrees');
 }
 return {schema:'xnby.source_surface_separation_audit.v1',scope:'sampled_two_surface_ray_and_parent_normal_separation_not_geometric_error_bound_silhouette_color_or_admission_proof',width,height,rasterWidth,rasterHeight,focusGroup,emptySamples:empty,total:finish(total),largestNormalSeparations,largestNormalAngles,cells:cells.map((c,i)=>({row:Math.floor(i/3),column:i%3,...finish(c)}))};
}
