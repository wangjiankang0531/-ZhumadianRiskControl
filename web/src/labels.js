import * as THREE from 'three';
export function labelAnchor(feature) {
  const p=feature.positions.map(v=>new THREE.Vector3(...v));
  if(feature.type==='point')return p[0];
  if(feature.type==='region') {
    const triangles=THREE.ShapeUtils.triangulateShape(p.map(v=>new THREE.Vector2(v.x,v.y)),[]);
    let largest=-1,anchor=p[0];
    for(const [ia,ib,ic] of triangles){const a=p[ia],b=p[ib],c=p[ic],area=Math.abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x));
      if(area>largest){largest=area;anchor=a.clone().add(b).add(c).divideScalar(3);}}
    return anchor;
  }
  let length=0;for(let k=1;k<p.length;k++)length+=p[k].distanceTo(p[k-1]);
  let remaining=length/2;
  for(let k=1;k<p.length;k++){const segment=p[k].distanceTo(p[k-1]);if(segment>.0001&&remaining<=segment)return p[k-1].clone().lerp(p[k],remaining/segment);remaining-=segment;}
  return p.at(-1);
}
export function drawLabel(ctx,feature,project) {
  const label=feature.label;if(!label?.visible||label.opacity<=0)return;
  const text=label.text||feature.name,p=project(labelAnchor(feature).toArray());if(!p||!text)return;
  const x=p[0]+label.offset[0],y=p[1]+label.offset[1];ctx.save();
  ctx.font=`${label.fontPx}px "Microsoft YaHei",sans-serif`;ctx.textBaseline='top';ctx.globalAlpha=label.opacity;
  ctx.fillStyle='rgba(9,18,26,.8)';ctx.fillRect(x-4,y-2,ctx.measureText(text).width+8,label.fontPx+8);
  ctx.fillStyle=label.color;ctx.fillText(text,x,y);const box=[x-4,y-2,x+ctx.measureText(text).width+4,y+label.fontPx+6];ctx.restore();return box;
}
