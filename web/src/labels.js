import {labelOptions} from './label_options.js';
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
export function labelWorldAnchor(feature) {
  // A sign stays attached to its saved surface point. Legacy heightM does not lift the world anchor.
  return labelAnchor(feature);
}
export function labelFramingPositions(feature) { return feature.positions; }
export function drawLabel(ctx,feature,project) {
  const label=feature.label;if(!label?.visible||label.opacity<=0)return;
  const options=labelOptions(label),text=label.text||feature.name,p=project(labelWorldAnchor(feature).toArray());if(!p||!text)return;
  ctx.save();
  ctx.font=`${label.fontPx}px "Microsoft YaHei",sans-serif`;ctx.textBaseline='top';ctx.globalAlpha=label.opacity;
  const lines=options.placement==='billboard'?text.split(/\r?\n/u):[text];
  const width=Math.max(...lines.map(line=>ctx.measureText(line).width)),lineHeight=Math.ceil(label.fontPx*1.4),height=options.placement==='billboard'?lines.length*lineHeight:label.fontPx+4;
  const x=p[0]+label.offset[0],y=p[1]+label.offset[1]-(options.placement==='billboard'?height:0);
  if(options.placement==='billboard') {
    const ground=project(labelAnchor(feature).toArray());
    ctx.strokeStyle=feature.style.color;ctx.lineWidth=2;
    ctx.beginPath();if(ground){ctx.moveTo(...ground);ctx.lineTo(...p);}ctx.moveTo(...p);ctx.lineTo(x,y+height);ctx.stroke();
    ctx.fillStyle='rgba(3,23,40,.9)';ctx.fillRect(x+1,y+3,width+12,height+8);
    ctx.strokeStyle=feature.style.color;ctx.lineWidth=1;ctx.strokeRect(x-6,y-4,width+12,height+8);
  }
  ctx.fillStyle='rgba(9,18,26,.86)';ctx.fillRect(x-4,y-2,width+8,height+4);
  ctx.fillStyle=label.color;lines.forEach((line,i)=>ctx.fillText(line,x,y+i*lineHeight));
  const box=[x-6,y-4,x+width+6,y+height+4];ctx.restore();return box;
}

export function markerScreenPoint(point,style) { return point&&style.icon==='pin'?[point[0],point[1]-style.sizePx/2]:point; }
