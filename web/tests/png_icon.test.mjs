import test from 'node:test';
import assert from 'node:assert/strict';
import {deflateSync} from 'node:zlib';
import {readFileSync} from 'node:fs';
import {createContext,runInContext} from 'node:vm';
import {validatePNGIconData,maximumPNGIconBytes} from '../src/png_icon.js';
import {CustomIconCache} from '../src/custom_icon_cache.js';
import {validateLandscapeDocument} from '../src/landscape_document.js';

const table=Uint32Array.from({length:256},(_,v)=>{for(let i=0;i<8;i++)v=v&1?0xedb88320^(v>>>1):v>>>1;return v>>>0;});
function chunk(name,data){const out=Buffer.alloc(data.length+12);out.writeUInt32BE(data.length);out.write(name,4,'ascii');data.copy(out,8);let crc=0xffffffff;for(const byte of out.subarray(4,-4))crc=table[(crc^byte)&255]^(crc>>>8);out.writeUInt32BE((crc^0xffffffff)>>>0,out.length-4);return out;}
const signature=Buffer.from([137,80,78,71,13,10,26,10]);
function png({width=1,height=1,color=6,depth=8,extra=[],data=Buffer.from([0,255,64,32,255])}={}){
  const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(width);ihdr.writeUInt32BE(height,4);ihdr[8]=depth;ihdr[9]=color;
  return Buffer.concat([signature,chunk('IHDR',ihdr),...extra,chunk('IDAT',deflateSync(data)),chunk('IEND',Buffer.alloc(0))]);
}
const uri=bytes=>'data:image/png;base64,'+bytes.toString('base64');
const valid=uri(png());
const doc=iconData=>({schema:'hongtu.landscape.layers.v1',scene:'zhumadian',coordinates:{srs:'EPSG:32650',unit:'metre',axes:'east,north,up',origin:[225319.5,3648440.1,30.9]},layers:[{id:'layer',name:'合成',visible:true,locked:false,features:[{id:'point',name:'PNG',type:'point',positions:[[0,0,0]],style:{icon:'custom',iconData,pattern:'solid',sizePx:32,widthPx:4,color:'#22D3EE',fillColor:'#00AABB',opacity:.5,fillOpacity:.25}}]}]});

test('valid PNG bytes, dimensions, embedded identity and point alpha survive document validation',()=>{
  const raw=png(),result=validatePNGIconData(uri(raw));assert.equal(result.width,1);assert.equal(result.height,1);assert.deepEqual(Buffer.from(result.bytes),raw);
  const d=doc(valid),before=JSON.stringify(d);assert.equal(validateLandscapeDocument(d),d);assert.equal(JSON.stringify(d),before);
});
test('reject empty, wrong MIME, malformed alphabet, padding, noncanonical bits and disguised non-PNG',()=>{
  for(const data of ['',null,'data:image/png;base64,','data:image/jpeg;base64,AA==','data:image/png;base64,!!!!','data:image/png;base64,SGVsbG8=','data:image/png;base64,A===','data:image/png;base64,AA=A','data:image/png;base64,AB==',valid+'\n',valid.slice(0,-1)])assert.throws(()=>validatePNGIconData(data));
});
test('reject corrupt CRC, truncated chunks, missing IDAT/IEND, duplicate IHDR and trailing bytes',()=>{
  const good=png(),corrupt=Buffer.from(good);corrupt[29]^=1;
  const duplicate=Buffer.concat([good.subarray(0,33),good.subarray(8,33),good.subarray(33)]);
  for(const bad of [corrupt,good.subarray(0,-1),good.subarray(0,-12),Buffer.concat([good.subarray(0,33),good.subarray(-12)]),duplicate,Buffer.concat([good,Buffer.from([0])])])assert.throws(()=>validatePNGIconData(uri(bad)));
});
test('dimension boundaries and PNG color/depth combinations are checked',()=>{
  validatePNGIconData(uri(png({width:2048,height:2048})));
  for(const options of [{width:0},{height:0},{width:2049},{height:2049},{color:1},{color:6,depth:4},{color:2,depth:1},{color:3}])assert.throws(()=>validatePNGIconData(uri(png(options))));
  validatePNGIconData(uri(png({color:0,depth:1,data:Buffer.from([0,0])})));
  validatePNGIconData(uri(png({color:3,depth:1,data:Buffer.from([0,0]),extra:[chunk('PLTE',Buffer.from([255,0,0]))]})));
});
test('4 MiB limit uses decoded bytes and accepts the exact limit',()=>{
  const base=png(),extra=maximumPNGIconBytes-base.length-12;
  const exact=Buffer.concat([base.subarray(0,33),chunk('tEXt',Buffer.alloc(extra,32)),base.subarray(33)]);
  assert.equal(exact.length,maximumPNGIconBytes);assert.equal(validatePNGIconData(uri(exact)).bytes.length,maximumPNGIconBytes);
  assert.throws(()=>validatePNGIconData(uri(Buffer.concat([exact,Buffer.from([0])]))));
});
test('invalid embedded image is rejected before preparing a replacement document',()=>{
  for(const bad of ['data:image/png;base64,','data:image/png;base64,SGVsbG8=',uri(png({width:2049}))])assert.throws(()=>validateLandscapeDocument(doc(bad)));
});

function harness(){const images=[],errors=[];const cache=new CustomIconCache({createImage:()=>{const image={naturalWidth:1,naturalHeight:1,complete:true};images.push(image);return image;},onError:error=>errors.push(error.message)});return {cache,images,errors};}
test('loading is not drawn; success is decoded once and preserves original image pixels',()=>{
  const {cache,images,errors}=harness();assert.equal(cache.get(valid),null);assert.equal(cache.get(valid),null);assert.equal(images.length,1);images[0].onload();assert.equal(cache.get(valid),images[0]);assert.equal(cache.get(valid).src,valid);assert.equal(errors.length,0);
});
test('oversized decoded image is reported once and never retried on later frames',()=>{
  const {cache,images,errors}=harness();cache.get(valid);images[0].naturalWidth=2049;images[0].onload();for(let i=0;i<100;i++)assert.equal(cache.get(valid),null);assert.equal(images.length,1);assert.equal(errors.length,1);
});
test('decoder failure is reported once and never returned as drawable',()=>{
  const {cache,images,errors}=harness();cache.get(valid);images[0].onerror();for(let i=0;i<100;i++)assert.equal(cache.get(valid),null);assert.equal(images.length,1);assert.equal(errors.length,1);
});
test('malformed PNG is not passed to the browser image decoder',()=>{
  const {cache,images,errors}=harness();for(let i=0;i<100;i++)assert.equal(cache.get('data:image/png;base64,SGVsbG8='),null);assert.equal(images.length,0);assert.equal(errors.length,1);
});
test('clear detaches callbacks, suppresses old async results and allows one fresh decode',()=>{
  const {cache,images,errors}=harness();cache.get(valid);const oldLoad=images[0].onload,oldError=images[0].onerror;cache.clear();assert.equal(images[0].onload,null);assert.equal(images[0].onerror,null);oldLoad();oldError();assert.equal(errors.length,0);assert.equal(cache.get(valid),null);assert.equal(images.length,2);images[1].onload();assert.equal(cache.get(valid),images[1]);
});
test('actual viewer uses the failure-aware cache and clears it when replacing documents',()=>{
  const source=readFileSync(new URL('../src/viewer.js',import.meta.url),'utf8');
  const start=source.indexOf('function iconImage(key){'),end=source.indexOf('\nconst tintedCache=',start);assert.ok(start>=0&&end>start);
  const {cache,images,errors}=harness();const context=createContext({imageCache:cache});runInContext(source.slice(start,end)+';this.load=iconImage;',context);
  context.load(valid);images[0].onerror();for(let i=0;i<20;i++)assert.equal(context.load(valid),null);assert.equal(images.length,1);assert.equal(errors.length,1);
  assert.match(source,/const imageCache=new CustomIconCache\(/);assert.match(source,/tintedCache\.clear\(\);imageCache\.clear\(\)/);
});
