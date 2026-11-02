// The caller supplies current visible-base evidence, distinct from detail gain.
// This request restores complete coverage; it never retires another root.
export function coverageRecoveryRequest({enabled,verified,id,parent,gain,weight,residents,cameraMatched,cutMatched}){
 if(![enabled,verified,cameraMatched,cutMatched].every(v=>typeof v==='boolean')||!(residents instanceof Map)||!Number.isInteger(id)||id<1||id>2346)throw Error('Invalid coverage recovery evidence');
 if(!enabled||!verified||!cameraMatched||!cutMatched||parent!==null||residents.has(id)||!Number.isFinite(gain)||gain<=0||!Number.isFinite(weight)||weight<=0||weight>1)return null;
 return {id,parent:null,score:gain,coverageWeight:weight};
}
