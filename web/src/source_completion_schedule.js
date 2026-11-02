// Observe sparse-missed root coverage before spending the same budget on
// already-covered family detail. No source, budget or quality gate is skipped.
export function completionBeforeRefinement(candidates,hasRoot){
 if(!Array.isArray(candidates)||candidates.length>16384||typeof hasRoot!=='function')throw Error('Invalid completion scheduling inputs');
 let refine=false,uncovered=false;
 for(const c of candidates){
  if(!c||!['root','family'].includes(c.kind)||!Number.isInteger(c.id)||c.id<1||c.id>2346||!Number.isFinite(c.score)||c.score<0)throw Error('Invalid completion scheduling candidate');
  if(c.score===0)continue;
  if(c.kind==='family')refine=true;
  else{const present=hasRoot(c.id);if(typeof present!=='boolean')throw Error('Invalid completion root presence');if(!present)uncovered=true;}
 }
 return refine&&!uncovered;
}
