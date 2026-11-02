import {initialIndexedCoverageDepth} from './source_level_index.js';

// A first complete source cut, never a relaxation of geometry-gain, SHA,
// topology, atomic replacement or budget admission. The renderer continues
// refining complete child families using its existing measured-gain gates.
export class RootCoverageSeed {
 constructor({enabled=false,geometryGuard=false}={}){if(typeof enabled!=='boolean'||typeof geometryGuard!=='boolean')throw Error('Invalid coverage seed policy');this.enabled=enabled;this.geometryGuard=enabled&&geometryGuard;this.geometryTiers=new Map();this.view=null;this.rejected=new Map();this.selected=new Map();this.rejections=0;}
 context(view){if(typeof view!=='string'||view.length>16384)throw Error('Invalid coverage seed view');if(view!==this.view){this.view=view;this.rejected.clear();this.selected.clear();}}
 select({record,proposed,scale,depth,verified=false}){
  if(!this.enabled||!verified)return proposed;
  if(this.view===null||!Number.isSafeInteger(record?.tile)||record.tile<1||record.tile>2346)throw Error('Invalid coverage seed root');
  let initial=initialIndexedCoverageDepth(record,proposed,scale,depth);
  if(this.geometryGuard){const tiers=this.geometryTiers.get(record.tile);initial=proposed;for(let d=1;d<proposed;d++){const tier=tiers?.[d];if(tier&&tier.edge*scale/depth<=6&&tier.texel*scale/depth<=1.5){initial=d;break;}}}
  const chosen=Math.min(proposed,Math.max(initial,(this.rejected.get(record.tile)??0)+1));
  this.selected.set(record.tile,{initial,chosen,proposed});return chosen;
 }
 reject({id,depth,gain}){
  if(!this.enabled)return false;
  if(!Number.isSafeInteger(id)||!Number.isInteger(depth)||depth<1||depth>3||!Number.isFinite(gain)||gain<0)throw Error('Invalid coverage seed observation');
  const selected=this.selected.get(id);if(!selected||selected.chosen!==depth||gain>0||depth>=selected.proposed)return false;
  this.rejected.set(id,Math.max(depth,this.rejected.get(id)??0));this.rejections++;return true;
 }
 learnTopology(data){
  if(!this.enabled||!this.geometryGuard)return false;
  if(!data||data.complete!==true||!Number.isSafeInteger(data.tile)||data.tile<1||data.tile>2346||!Array.isArray(data.nodes)||!data.nodes.length||data.nodes.length>8192)throw Error('Invalid coverage seed topology');
  if(this.geometryTiers.has(data.tile))return false;
  const nodes=new Map(data.nodes.map(n=>[n.name,n])),tiers={};
  for(let depth=1;depth<=3;depth++){let edge=0,texel=0,visits=0,count=0;
   const visit=name=>{const n=nodes.get(name);if(!n||++visits>nodes.size||!Array.isArray(n.children))throw Error('Incomplete coverage seed metrics');if(n.depth>=depth||!n.children.length){if(![n.edgeP90,n.texelP90].every(Number.isFinite)||n.edgeP90<0||n.texelP90<=0){edge=Infinity;texel=Infinity;}else{edge=Math.max(edge,n.edgeP90);texel=Math.max(texel,n.texelP90);}count++;}else for(const child of n.children)visit(child);};visit(data.root);tiers[depth]={edge,texel,count};
  }
  // Called only after the browser's SHA-pinned LEVEL tile validator. This cache
  // affects priority; actual source validation and admission remain mandatory.
  this.geometryTiers.set(data.tile,tiers);return true;
 }
 snapshot(){const depths={};for(const row of this.selected.values())depths[row.chosen]=(depths[row.chosen]??0)+1;return {enabled:this.enabled,geometryGuard:this.geometryGuard,topologyRoots:this.geometryTiers.size,selectedRoots:this.selected.size,depths,rejectedRoots:this.rejected.size,rejections:this.rejections};}
}
