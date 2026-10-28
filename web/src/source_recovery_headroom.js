// Unallocated capacity for complete parent-page coexistence, not a GPU pin or
// permission to exceed the physical ledger. Final detail admissions keep it free.
export const SOURCE_RECOVERY_HEADROOM=64*1048576;
export function sourceRecoveryAdmissionCost(cost,headroom){
 if(![cost,headroom].every(Number.isSafeInteger)||cost<1||headroom<0||!Number.isSafeInteger(cost+headroom))throw Error('Invalid recovery admission cost');
 return cost+headroom;
}
export function sourceRecoveryHeadroom({requested,verified}){
 if(typeof requested!=='boolean'||typeof verified!=='boolean')throw Error('Invalid recovery headroom capability');
 return requested&&verified?SOURCE_RECOVERY_HEADROOM:0;
}
