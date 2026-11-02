// Detail admission may trade geometric error, but this optional policy keeps a
// sampled visible texel deficit from getting worse to fund another detail load.
// Infinity excludes an action from both direct and multi-step recovery plans.
export function sourceTexelRetirementPriority({combinedLoss,texelLoss=0,protectTexels=false}){
 if(typeof protectTexels!=='boolean'||[combinedLoss,texelLoss].some(n=>typeof n!=='number'||Number.isNaN(n)||n<0))throw Error('Invalid source retirement loss');
 return protectTexels&&texelLoss>0?Infinity:Math.max(combinedLoss,texelLoss);
}
