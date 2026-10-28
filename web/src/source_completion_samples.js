export const COMPLETION_SAMPLE_LIMIT=16384;
const metricOK=n=>Number.isFinite(n?.longest_edge_p90_m)&&n.longest_edge_p90_m>=0&&Number.isFinite(n?.texel_world_p90_m)&&n.texel_world_p90_m>0;
export function collectCompletionPixels({pixels,width,height,cssWidth,cssHeight,registry,metrics,roots,obscured=[],remaining}){
 if(!(pixels instanceof Uint8Array)||![width,height,cssWidth,cssHeight].every(n=>Number.isSafeInteger(n)&&n>0)||width*height>2097152||pixels.length!==width*height*4||!(registry instanceof Map)||!(metrics instanceof Map)||!Array.isArray(roots)||roots.length>64||new Set(roots).size!==roots.length||!roots.every(id=>Number.isInteger(id)&&id>=1&&id<=2346)||!Number.isSafeInteger(remaining)||remaining<0||remaining>COMPLETION_SAMPLE_LIMIT||!obscured.every(r=>['left','right','top','bottom'].every(k=>Number.isFinite(r[k]))))throw Error('Invalid completion raster');
 const wanted=new Set(roots.map(id=>'root/'+id)),rows=new Map(),selected=new Map();let count=0,unknown=0;
 for(let i=0;i<width*height;i++){
  const off=i*4,id=pixels[off]|pixels[off+1]<<8|pixels[off+2]<<16;if(!id)continue;const key=registry.get(id);if(!key)throw Error('Unknown completion source ID');if(!wanted.has(key))continue;
  const x=i%width,y=Math.floor(i/width),px=(x+.5)*cssWidth/width,py=(height-y-.5)*cssHeight/height;
  if(obscured.some(r=>px>=r.left&&px<r.right&&py>=r.top&&py<r.bottom))continue;
  const metric=metrics.get(key);if(!metricOK(metric)){unknown++;continue;}
  if(++count>remaining)return {status:'refused',reason:'worker_sample_capacity',pixels:count,unknown};
  if(!rows.has(key)){rows.set(key,[]);selected.set(key,metric);}rows.get(key).push((x+.5)/width*2-1,(y+.5)/height*2-1,pixels[off+3],1/(width*height));
 }
 return {status:'ready',rows,metrics:selected,pixels:count,unknown};
}
export function mergeCompletionSamples(snapshot,completion){
 if(!snapshot||snapshot.surfaceDepths||!(snapshot.samples instanceof Map)||!(snapshot.metrics instanceof Map)||completion?.status!=='ready'||!(completion.rows instanceof Map)||!(completion.metrics instanceof Map))throw Error('Invalid completion snapshot');
 let before=0,added=0,addedMass=0;
 const validRows=rows=>Array.isArray(rows)&&rows.length%4===0&&rows.every((v,i)=>Number.isFinite(v)&&(i%4<2?Math.abs(v)<1:i%4===2?Number.isInteger(v)&&v>=0&&v<=255:v>0));
 for(const rows of snapshot.samples.values()){if(!validRows(rows))throw Error('Invalid primary completion samples');before+=rows.length/4;}
 for(const [key,rows] of completion.rows){
  const beforeMetric=snapshot.metrics.get(key),afterMetric=completion.metrics.get(key);
  if(!/^root\/[1-9][0-9]*$/.test(key)||snapshot.samples.has(key)||!metricOK(afterMetric)||!beforeMetric||beforeMetric.longest_edge_p90_m!==afterMetric.longest_edge_p90_m||beforeMetric.texel_world_p90_m!==afterMetric.texel_world_p90_m||!validRows(rows))throw Error('Completion identity differs from primary snapshot');
  added+=rows.length/4;for(let i=3;i<rows.length;i+=4)addedMass+=rows[i];
 }
 if(before+added>COMPLETION_SAMPLE_LIMIT||addedMass>1+1e-6)throw Error('Completion sample capacity exceeded');
 const normalizer=1+addedMass,samples=new Map();let mass=0;
 for(const [key,rows] of [...snapshot.samples,...completion.rows]){const copy=rows.map((v,i)=>i%4===3?v/normalizer:v);samples.set(key,copy);for(let i=3;i<copy.length;i+=4)mass+=copy[i];}
 if(mass>1+1e-6)throw Error('Completion weights exceed viewport');
 return {snapshot:{...snapshot,samples},addedSamples:added,addedSources:completion.rows.size,normalizer};
}
