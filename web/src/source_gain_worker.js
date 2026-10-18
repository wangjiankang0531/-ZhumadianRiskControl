import {evaluateSourceGeometryGain} from './source_geometry_gain.js';
self.onmessage=async event=>{const {id,...job}=event.data;try{self.postMessage({id,ok:true,result:await evaluateSourceGeometryGain(job)});}catch(error){self.postMessage({id,ok:false,error:String(error.message||error)});}};
