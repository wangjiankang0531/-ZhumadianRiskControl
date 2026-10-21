import {performance} from 'node:perf_hooks';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {writeFileSync} from 'node:fs';
import {coverageDimensions,coverageInteriorLoss} from '../src/source_coverage.js';
// Frozen pre-scanline integral reference. It is an oracle/benchmark only.
export function legacyCoverageInteriorLoss(parent,child,width,height){
 coverageDimensions(width,height);if(!(parent instanceof Uint8Array)||!(child instanceof Uint8Array)||parent.length!==width*height*4||child.length!==parent.length)throw Error('Invalid geometric coverage masks');
 const stride=width+1,p=new Uint32Array(stride*(height+1)),c=new Uint32Array(p.length);
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){const at=(y+1)*stride+x+1,pixel=(y*width+x)*4;p[at]=(parent[pixel]!==0)+p[at-1]+p[at-stride]-p[at-stride-1];c[at]=(child[pixel]!==0)+c[at-1]+c[at-stride]-c[at-stride-1];}
 const sum=(a,x0,y0,x1,y1)=>a[y1*stride+x1]-a[y0*stride+x1]-a[y1*stride+x0]+a[y0*stride+x0];let loss=0,parentPixels=0;
 for(let y=0;y<height;y++)for(let x=0;x<width;x++){parentPixels+=parent[(y*width+x)*4]!==0;const x0=Math.max(0,x-2),y0=Math.max(0,y-2),x1=Math.min(width,x+3),y1=Math.min(height,y+3);if(sum(p,x0,y0,x1,y1)===(x1-x0)*(y1-y0)&&sum(c,x0,y0,x1,y1)===0)loss++;}
 return {loss,parentPixels};
}


function fixture(width,height){const parent=new Uint8Array(width*height*4),child=parent.slice();for(let y=0;y<height;y++)for(let x=0;x<width;x++){const p=(y*width+x)*4;parent[p]=x>width*.1&&y>height*.1?255:0;child[p]=parent[p]&&(x>width*.4||y>height*.4)?255:0;}return [parent,child,width,height];}
function benchmark(){const results=[];for(const [width,height] of [[320,180],[1280,573],[1920,1080],[4096,2160]]){const args=fixture(width,height),a=legacyCoverageInteriorLoss(...args),b=coverageInteriorLoss(...args);if(JSON.stringify(a)!==JSON.stringify(b))throw Error('Coverage benchmark oracle differs');const row={width,height,pixels:width*height,result:a,scratchBytes:{legacyIntegral:2*(width+1)*(height+1)*4,scanline:7*width},measurements:{}};
 for(const [name,fn] of [['legacyIntegral',legacyCoverageInteriorLoss],['scanline',coverageInteriorLoss]]){for(let i=0;i<3;i++)fn(...args);const times=[];for(let i=0;i<12;i++){const start=performance.now();fn(...args);times.push(performance.now()-start);}times.sort((a,b)=>a-b);row.measurements[name]={samples:times.length,medianMs:(times[5]+times[6])/2,minMs:times[0],maxMs:times.at(-1)};}results.push(row);}
 const report={schema:'zhumadian.coverage.mask_benchmark.v1',node:process.version,scope:'Node CPU synthetic fixed masks, not browser GPU or loading SLA',results};const output=process.argv.indexOf('--out');if(output!==-1)writeFileSync(process.argv[output+1],JSON.stringify(report,null,2));console.log(JSON.stringify(report));}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url))benchmark();
