// QA ordering evidence only. Neither depth separation nor a ranking boost grants
// source admission, quality acceptance, retirement, GPU memory or coverage.
export const SOURCE_PRECISE_DEPTH_POLICY='gpu_log_depth_rgb24_observation_v1';
const require=(v,m)=>{if(!v)throw Error(m);};
export function preciseVisibleDepths(ids,depths,width,height,weights,registry){
 require(ids instanceof Uint8Array&&depths instanceof Uint8Array&&ids.length===width*height*4&&depths.length===ids.length&&weights.length===width*height,'Invalid precise depth raster');
 const result=new Map();for(let i=0;i<width*height;i++){const id=ids[i*4]|ids[i*4+1]<<8|ids[i*4+2]<<16;if(!id||!(weights[i]>0))continue;const key=registry.get(id),code=depths[i*4]|depths[i*4+1]<<8|depths[i*4+2]<<16,depth=.5*120000**(code/16777215),bin=ids[i*4+3];require(key&&depths[i*4+3]===255&&Math.abs(code/16777215*255-bin)<=1.01,'Precise depth does not match visible ID pass');if(!result.has(key))result.set(key,[]);result.get(key).push(depth);}return result;
}
export function observedDepthNovelty(parentDepth,childDepth,fov,height,weight){
 require([parentDepth,childDepth,fov,height,weight].every(Number.isFinite)&&parentDepth>0&&childDepth>0&&fov>0&&fov<179&&height>0&&weight>0&&weight<=1,'Invalid observed depth novelty');
 const separationScaled=Math.max(0,Math.abs(parentDepth-childDepth)-Math.max(1e-4,parentDepth*1e-5))*height/(2*Math.tan(fov*Math.PI/360)*Math.max(parentDepth,childDepth));
 return {separationScaled,score:Math.log2(1+separationScaled/6)*weight};
}
export function chooseSurfacePair(candidates,feasible){
 require(Array.isArray(candidates)&&candidates.length<=2&&typeof feasible==='function','Invalid surface pair');const keys=new Set();
 for(const c of candidates){require(typeof c.key==='string'&&!keys.has(c.key)&&Number.isFinite(c.score)&&c.score>=0&&Number.isFinite(c.depthNovelty)&&c.depthNovelty>=0&&(c.cost===null||Number.isSafeInteger(c.cost)&&c.cost>0),'Invalid surface pair candidate');keys.add(c.key);}
 const rank=c=>c.score+Math.min(c.score,c.depthNovelty),ordered=candidates.filter(c=>c.score>0).sort((a,b)=>{const au=a.cost===null,bu=b.cost===null;if(au!==bu)return au?-1:1;return (au?rank(b)-rank(a):rank(b)/b.cost-rank(a)/a.cost)||b.score-a.score||a.key.localeCompare(b.key);});
 for(const c of ordered){const ok=feasible(c);require(typeof ok==='boolean','Invalid pair feasibility');if(ok)return c;}return null;
}

export function validateObservedDepthResult(result,enabled){
 if(!enabled){require(result.surfaceDepthPolicy===undefined&&result.depthNovelty===undefined&&result.maxDepthSeparationScaled===undefined,'Unexpected observed depth result');return;}
 require(result.surfaceDepthPolicy===SOURCE_PRECISE_DEPTH_POLICY&&Number.isFinite(result.depthNovelty)&&result.depthNovelty>=0&&Number.isFinite(result.maxDepthSeparationScaled)&&result.maxDepthSeparationScaled>=0,'Invalid observed depth result');
}
