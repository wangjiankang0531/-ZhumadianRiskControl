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
const font=(size,weight=400)=>`${weight} ${size}px "Microsoft YaHei",sans-serif`;
function wrap(ctx,text,maxWidth,maxLines=2){
 const lines=[];let line='';for(const ch of text){if(ctx.measureText(line+ch).width>maxWidth&&line){lines.push(line);line=ch;}else line+=ch;}
 if(line)lines.push(line);if(lines.length>maxLines){lines.length=maxLines;let last=lines[maxLines-1];while(last&&ctx.measureText(last+'…').width>maxWidth)last=last.slice(0,-1);lines[maxLines-1]=last+'…';}return lines.length?lines:[''];
}
export function measureSign(ctx,feature,compact=false){
 const lines=(feature.label.text||feature.name).split(/\r?\n/u),size=Math.max(12,Math.min(15,feature.label.fontPx)),width=compact?208:236;
 ctx.save();ctx.font=font(size,600);const title=wrap(ctx,lines[0],width-34,compact?1:2);ctx.font=font(12);
 const body=compact?[]:lines.slice(1).flatMap(line=>wrap(ctx,line,width-28,2));ctx.restore();
 return {width,height:20+title.length*20+(body.length?14+body.length*19:0)+12,title,body,size};
}
function rounded(ctx,x,y,w,h,r){ctx.beginPath();ctx.roundRect(x,y,w,h,r);}
export function drawSignLeader(ctx,feature,anchor,layout){
 const [x,y,right,bottom]=layout.box,color=feature.style.color;
 ctx.save();ctx.globalAlpha=feature.label.opacity;ctx.setLineDash([]);
 const elbow=[anchor[0],anchor[1]-30],edge=[Math.max(x+10,Math.min(right-10,elbow[0])),Math.max(y+8,Math.min(bottom-8,elbow[1]))];
 ctx.strokeStyle='rgba(2,17,29,.75)';ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(...anchor);ctx.lineTo(...elbow);ctx.lineTo(...edge);ctx.stroke();
 ctx.strokeStyle=color;ctx.lineWidth=1.6;ctx.stroke();ctx.fillStyle=color;ctx.beginPath();ctx.arc(...anchor,3,0,Math.PI*2);ctx.fill();ctx.restore();
}
export function drawSign(ctx,feature,anchor,layout,{selected=false,manual=false,leader=true}={}){
 const [x,y,right,bottom]=layout.box,w=right-x,h=bottom-y,m=layout.metric,color=feature.style.color;
 if(leader)drawSignLeader(ctx,feature,anchor,layout);
 ctx.save();ctx.globalAlpha=feature.label.opacity;ctx.setLineDash([]);
 ctx.shadowColor='rgba(0,10,24,.4)';ctx.shadowBlur=14;ctx.shadowOffsetY=5;
 const gradient=ctx.createLinearGradient(x,y,right,bottom);gradient.addColorStop(0,'rgba(17,45,65,.94)');gradient.addColorStop(1,'rgba(7,25,42,.91)');ctx.fillStyle=gradient;
 rounded(ctx,x,y,w,h,10);ctx.fill();ctx.shadowBlur=0;ctx.shadowOffsetY=0;
 ctx.strokeStyle=selected?'#a2f3ff':'rgba(139,203,224,.42)';ctx.lineWidth=selected?1.5:1;ctx.stroke();
 ctx.fillStyle=color;rounded(ctx,x+1,y+12,3,h-24,2);ctx.fill();
 ctx.textBaseline='top';ctx.font=font(m.size,600);ctx.fillStyle=feature.label.color;m.title.forEach((line,i)=>ctx.fillText(line,x+15,y+13+i*20));
 // Small grip dots communicate that this is a movable card, without a toolbar on every sign.
 ctx.fillStyle=manual?'#a2f3ff':'rgba(181,216,232,.6)';for(let i=0;i<3;i++){ctx.beginPath();ctx.arc(right-10,y+12+i*4,1,0,Math.PI*2);ctx.fill();}
 if(m.body.length){const top=y+20+m.title.length*20;ctx.strokeStyle='rgba(156,211,231,.17)';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x+14,top);ctx.lineTo(right-14,top);ctx.stroke();
 ctx.font=font(12);m.body.forEach((line,i)=>{ctx.fillStyle=line.includes('待核实')?'#e9c985':i===0?'#c6e3ef':'#a7c4d4';ctx.fillText(line,x+14,top+10+i*19);});}
 ctx.restore();return layout.box;
}
export function drawLabel(ctx,feature,project){
 const label=feature.label;if(!label?.visible||label.opacity<=0)return;
 const options=labelOptions(label),text=label.text||feature.name,p=project(labelWorldAnchor(feature).toArray());if(!p||!text)return;
 if(options.placement==='billboard'){const metric=measureSign(ctx,feature);return drawSign(ctx,feature,p,{metric,box:[p[0]+18,p[1]-metric.height-38,p[0]+18+metric.width,p[1]-38]});}
 ctx.save();ctx.font=font(label.fontPx);ctx.textBaseline='top';ctx.globalAlpha=label.opacity;const width=ctx.measureText(text).width,x=p[0]+label.offset[0],y=p[1]+label.offset[1],height=label.fontPx+4;
 ctx.fillStyle='rgba(9,18,26,.86)';ctx.fillRect(x-4,y-2,width+8,height+4);ctx.fillStyle=label.color;ctx.fillText(text,x,y);ctx.restore();return [x-6,y-4,x+width+6,y+height+4];
}

export function markerScreenPoint(point,style) { return point&&style.icon==='pin'?[point[0],point[1]-style.sizePx/2]:point; }

export function signFootFeature(feature){return feature.type==='point'&&feature.label?.placement==='billboard'?{...feature,style:{...feature.style,icon:'circle',sizePx:6}}:feature;}
