import {encodeOpaqueBc7Separated} from './bc7_separated_encoder.mjs';
import {encodeOpaqueBc7ThreeSubset,encodeOpaqueBc7Extended} from './bc7_three_subset_encoder.mjs';
import {encodeOpaqueBc7Mode6} from './bc7_mode6_encoder.mjs';
import {encodeOpaqueBc7} from './bc7_opaque_encoder.mjs';
const profile=process.argv[2]??'--profile=mode6';if(process.argv.length>3||!['--profile=mode6','--profile=mode1-6','--profile=mode0-1-2-6','--profile=mode0-1-2-3-6','--profile=mode0-1-2-3-4-5-6'].includes(profile))throw Error('Unsupported BC7 encoder profile');
const encode=profile==='--profile=mode6'?encodeOpaqueBc7Mode6:profile==='--profile=mode1-6'?encodeOpaqueBc7:profile==='--profile=mode0-1-2-6'?encodeOpaqueBc7ThreeSubset:profile==='--profile=mode0-1-2-3-6'?encodeOpaqueBc7Extended:encodeOpaqueBc7Separated;
const maximum=24*1024*1024,chunks=[];let count=0;
for await(const chunk of process.stdin){count+=chunk.length;if(count>maximum)throw Error('BC7 input exceeds CPU image window');chunks.push(chunk);}
const input=Buffer.concat(chunks);if(input.length<8||input.toString('ascii',0,4)!=='MB7R')throw Error('Invalid BC7 batch');
const headerBytes=input.readUInt32LE(4);if(headerBytes>16384||8+headerBytes>input.length)throw Error('Invalid BC7 batch header');
const rows=JSON.parse(input.toString('utf8',8,8+headerBytes));if(!Array.isArray(rows)||!rows.length||rows.length>12)throw Error('Invalid BC7 mip batch');
let offset=8+headerBytes;const output=[];
for(const row of rows){const size=row.width*row.height*4;if(!Number.isSafeInteger(size)||size<=0||offset+size>input.length)throw Error('Truncated BC7 mip image');output.push(encode(input.subarray(offset,offset+size),row.width,row.height));offset+=size;}
if(offset!==input.length)throw Error('Trailing BC7 batch bytes');
process.stdout.write(Buffer.concat(output));
