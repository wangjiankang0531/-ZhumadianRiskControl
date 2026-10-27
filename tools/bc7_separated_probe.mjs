import {encodeOpaqueBc7SeparatedProbe,decodeOpaqueBc7SeparatedBlock} from './bc7_separated_encoder.mjs';
const rows=[];
for(const mode of [4,5])for(let rotation=0;rotation<4;rotation++)for(let selection=0;selection<(mode===4?2:1);selection++)for(let seed=0;seed<4;seed++){
 const rgba=new Uint8Array(64);for(let i=0;i<16;i++)rgba.set([(i*51+seed*37)%256,(i*29+seed*43)%256,(i*73+seed*19)%256,255],i*4);
 const encoded=encodeOpaqueBc7SeparatedProbe(rgba,mode,rotation,selection);rows.push({mode,rotation,selection,seed,source:Buffer.from(rgba).toString('hex'),encoded:Buffer.from(encoded).toString('hex'),reference:Buffer.from(decodeOpaqueBc7SeparatedBlock(encoded)).toString('hex')});
}
process.stdout.write(JSON.stringify(rows));
