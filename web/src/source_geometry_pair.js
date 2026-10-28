// At most two reads for one physical page, never concurrent page packets.
// Drain both reads before returning/rejecting so the owner may release its lease.
export async function readSourceGeometryPair({part,loadFile,wanted,concurrency=1}){
 if(![1,2].includes(concurrency)||typeof loadFile!=='function'||typeof wanted!=='function')throw Error('Invalid geometry read concurrency');
 wanted();if(concurrency===1){const json=await loadFile(part,'geometry.gltf');wanted();const binary=await loadFile(part,'geometry.bin');wanted();return {json,binary};}
 const result=await Promise.allSettled(['geometry.gltf','geometry.bin'].map(name=>Promise.resolve().then(()=>{wanted();return loadFile(part,name);})));wanted();
 for(const row of result)if(row.status==='rejected')throw row.reason;
 return {json:result[0].value,binary:result[1].value};
}
