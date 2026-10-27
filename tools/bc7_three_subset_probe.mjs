import {BC7_PARTITION2} from './bc7_partitions.mjs';
import {BC7_PARTITION3} from './bc7_three_subset_partitions.mjs';
import {encodeOpaqueBc7ThreeSubsetProbe,decodeOpaqueBc7Block} from './bc7_three_subset_encoder.mjs';
const rows=[];
for(const mode of [0,2,3])for(let partition=0;partition<(mode===0?16:64);partition++){
 const rgba=new Uint8Array(64);
 for(let i=0;i<16;i++){const s=mode===3?(BC7_PARTITION2[partition]>>>i)&1:(BC7_PARTITION3[partition]>>>(i*2))&3;rgba.set([[190+i*2,23+i,51+i*3],[15+i*3,170+i*2,59+i],[35+i,71+i*2,185+i*3]][s],i*4);rgba[i*4+3]=255;}
 const encoded=encodeOpaqueBc7ThreeSubsetProbe(rgba,partition,mode);
 rows.push({mode,partition,source:Buffer.from(rgba).toString('hex'),encoded:Buffer.from(encoded).toString('hex'),reference:Buffer.from(decodeOpaqueBc7Block(encoded)).toString('hex')});
}
process.stdout.write(JSON.stringify(rows));
