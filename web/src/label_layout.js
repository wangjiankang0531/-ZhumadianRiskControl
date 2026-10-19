// Screen pixels only: this module never edits a feature or its world coordinates.
export const overlaps=(a,b,gap=0)=>a[0]<b[2]+gap&&a[2]+gap>b[0]&&a[1]<b[3]+gap&&a[3]+gap>b[1];
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
export function layoutLabels(items,{width,height,obstacles=[],previous=new Map(),avoid=true,dragging=null,preferCompact=false}={}){
 const bounds=[8,8,width-8,height-8],gap=7,fixedObstacles=obstacles;
 const ordered=[...items].sort((a,b)=>Number(b.id===dragging)-Number(a.id===dragging)||Number(!!b.manual)-Number(!!a.manual)||Number(b.selected)-Number(a.selected)||String(a.id).localeCompare(String(b.id))).slice(0,32);
 // Keep the ground feet of displayed cards clear. Bound work for large user layers.
 obstacles=[...obstacles,...ordered.map(i=>[i.anchor[0]-6,i.anchor[1]-6,i.anchor[0]+6,i.anchor[1]+6])];
 function attempt(compact,packing=false){const result=new Map(),placed=[];let omitted=items.length-ordered.length;
  for(const item of ordered){const small=compact&&!item.selected,metric=small?item.compact:item.full,w=metric.width,h=metric.height;
   const desired=item.manual?[item.anchor[0]+item.manual[0],item.anchor[1]+item.manual[1]]:[item.anchor[0]+(item.offset?.[0]??18),item.anchor[1]-h-Math.max(38,-(item.offset?.[1]??-38))];
   const old=previous.get(item.id),prior=old?[old.box[0]+item.anchor[0]-old.anchor[0],old.box[1]+item.anchor[1]-old.anchor[1]]:null;
   let best=null,bestScore=Infinity;
   const candidates=[];
   if(!avoid||item.id===dragging)candidates.push([clamp(desired[0],bounds[0],Math.max(bounds[0],bounds[2]-w)),clamp(desired[1],bounds[1],Math.max(bounds[1],bounds[3]-h))]);
   else for(const area of [bounds]){if(area[2]-area[0]<w||area[3]-area[1]<h)continue;
    const xs=[desired[0],prior?.[0]??desired[0],area[0],area[2]-w],ys=[desired[1],prior?.[1]??desired[1],area[1],area[3]-h];
    for(const r of [...placed,...fixedObstacles]){xs.push(r[0]-w-gap,r[2]+gap);ys.push(r[1]-h-gap,r[3]+gap);}
    const axis=(values,min,max,wanted)=>[...new Set(values.map(v=>clamp(v,min,max)))].sort((a,b)=>packing?a-b:Math.abs(a-wanted)-Math.abs(b-wanted)).slice(0,32);
    const xx=axis(xs,area[0],area[2]-w,desired[0]),yy=axis(ys,area[1],area[3]-h,desired[1]);
    for(const x of xx)for(const y of yy)candidates.push([x,y]);
   }
   for(const [x,y] of candidates){const box=[x,y,x+w,y+h];if(avoid&&item.id!==dragging&&(placed.some(r=>overlaps(box,r,gap))||obstacles.some(r=>overlaps(box,r))))continue;
    const distance=(x-desired[0])**2+(y-desired[1])**2,stability=prior?(x-prior[0])**2+(y-prior[1])**2:0;
    const score=packing&&!item.manual?y*width+x+distance*.002:distance*(item.manual?8:1)+stability*2;
    if(score<bestScore){bestScore=score;best={box,anchor:item.anchor,compact:small,metric};}}
   if(best){result.set(item.id,best);placed.push(best.box);}else omitted++;
  }return {placements:result,omitted,compact};
 }
 let result=attempt(preferCompact);if(avoid&&result.omitted){const small=attempt(true);if(small.omitted<=result.omitted)result=small;const packed=attempt(true,true);if(packed.omitted<result.omitted)result=packed;}return result;
}
export function readLabelOffsets(raw){
 const result=new Map();try{const data=JSON.parse(raw);if(!Array.isArray(data)||data.length>1000)return result;
 for(const entry of data)if(Array.isArray(entry)&&typeof entry[0]==='string'&&entry[0].length<=200&&Array.isArray(entry[1])&&entry[1].length===2&&entry[1].every(v=>Number.isFinite(v)&&Math.abs(v)<=10000))result.set(entry[0],entry[1]);}catch{}return result;
}
