import {encodeOpaqueBc7PartitionProbe} from './bc7_opaque_encoder.mjs';
import {BC7_PARTITION2} from './bc7_partitions.mjs';
const rows=[];
for(let p=0;p<64;p++){
 const rgba=new Uint8Array(64);
 for(let i=0;i<16;i++){const s=(BC7_PARTITION2[p]>>>i)&1;rgba.set(s?[13+i*2,190+i*3,55+i]:[190+i*3,15+i,65+i*2],i*4);rgba[i*4+3]=255;}
 rows.push({partition:p,source:Buffer.from(rgba).toString('hex'),encoded:Buffer.from(encodeOpaqueBc7PartitionProbe(rgba,p)).toString('hex')});
}
process.stdout.write(JSON.stringify(rows));
