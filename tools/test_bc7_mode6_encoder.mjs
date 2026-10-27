import test from 'node:test';
import assert from 'node:assert/strict';
import {encodeOpaqueBc7Mode6} from './bc7_mode6_encoder.mjs';
// Independent decoder uses whole-block integer extraction, not encoder helpers.
function decode(block){
 let value=0n;for(let i=15;i>=0;i--)value=(value<<8n)|BigInt(block[i]);
 let pos=0n;const read=n=>{const v=Number((value>>pos)&((1n<<BigInt(n))-1n));pos+=BigInt(n);return v;};
 assert.equal(read(7),64);const ends=[[],[]];for(let c=0;c<4;c++){ends[0][c]=read(7);ends[1][c]=read(7);}const parity=[read(1),read(1)];
 for(let e=0;e<2;e++)for(let c=0;c<4;c++)ends[e][c]=ends[e][c]*2+parity[e];
 const weights=[0,4,9,13,17,21,26,30,34,38,43,47,51,55,60,64],out=[];
 for(let p=0;p<16;p++){const index=read(p?4:3);for(let c=0;c<4;c++)out.push(Math.floor(((64-weights[index])*ends[0][c]+weights[index]*ends[1][c]+32)/64));}
 assert.equal(pos,128n);return out;
}
function image(w,h,fn){const a=new Uint8Array(w*h*4);for(let y=0;y<h;y++)for(let x=0;x<w;x++)a.set([...fn(x,y),255],(y*w+x)*4);return a;}
test('opaque constant images preserve channels within the one-bit endpoint precision',()=>{
 for(const rgb of [[0,0,0],[255,255,255],[255,0,0],[0,127,255],[64,128,192]]){const out=decode(encodeOpaqueBc7Mode6(image(4,4,()=>rgb),4,4));for(let p=0;p<16;p++){assert.equal(out[p*4+3],255);for(let c=0;c<3;c++)assert.ok(Math.abs(out[p*4+c]-rgb[c])<=1);}}
});
test('gradient endpoints, fix-up index and alpha survive independent decoding',()=>{
 const a=image(4,4,(x,y)=>{const t=(y*4+x)/15;return [Math.round(255*t),Math.round(127*t),Math.round(255*(1-t))];}),out=decode(encodeOpaqueBc7Mode6(a,4,4));let mse=0;
 for(let i=0;i<a.length;i++){if(i%4===3)assert.equal(out[i],255);else mse+=(out[i]-a[i])**2;}assert.ok(mse/48<20);
});
test('non-power-of-two edges and sub-block mip levels replicate the last source pixel',()=>{
 for(const [w,h] of [[1,1],[2,1],[3,5],[9,7]]){const a=image(w,h,()=>[17,93,201]),out=encodeOpaqueBc7Mode6(a,w,h);assert.equal(out.length,Math.ceil(w/4)*Math.ceil(h/4)*16);for(let i=0;i<out.length;i+=16){const b=decode(out.subarray(i,i+16));for(let p=0;p<16;p++)assert.deepEqual(b.slice(p*4,p*4+4),[17,93,201,255]);}}
});
test('determinism and source immutability hold for randomized opaque color blocks',()=>{
 let seed=231;const next=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed>>>24;};
 for(let n=0;n<100;n++){const a=image(4,4,()=>[next(),next(),next()]),before=a.slice(),one=encodeOpaqueBc7Mode6(a,4,4),two=encodeOpaqueBc7Mode6(a,4,4);assert.deepEqual(one,two);assert.deepEqual(a,before);const out=decode(one);for(let p=0;p<16;p++)assert.equal(out[p*4+3],255);}
});
test('transparency, bad dimensions and unbounded inputs fail before encoding',()=>{
 const a=image(4,4,()=>[1,2,3]);a[3]=254;assert.throws(()=>encodeOpaqueBc7Mode6(a,4,4),/transparency/);
 for(const [w,h] of [[0,1],[1,0],[2049,1],[1.5,1],[NaN,4]])assert.throws(()=>encodeOpaqueBc7Mode6(new Uint8Array(),w,h));
 assert.throws(()=>encodeOpaqueBc7Mode6(new Uint8Array(7),1,1));
});
