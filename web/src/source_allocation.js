// Lazy benefit-per-byte selection. Unknown costs need metadata only; measured
// gains replace upper bounds before a candidate may reserve GPU memory.
export function chooseRefinementCandidate(candidates){
 const seen=new Set();let best=null;
 for(const c of candidates){
  if(typeof c.key!=='string'||!c.key||seen.has(c.key)||!Number.isFinite(c.score)||c.score<0||c.cost!==null&&(!Number.isSafeInteger(c.cost)||c.cost<=0))throw Error('Invalid refinement candidate');
  seen.add(c.key);if(!c.score)continue;
  if(!best){best=c;continue;}
  const unknown=c.cost===null,priorUnknown=best.cost===null;
  if(unknown!==priorUnknown){if(unknown)best=c;continue;}
  const density=unknown?0:c.score/c.cost,prior=priorUnknown?0:best.score/best.cost;
  if(density>prior||density===prior&&(c.score>best.score||c.score===best.score&&c.key<best.key))best=c;
 }
 return best;
}
