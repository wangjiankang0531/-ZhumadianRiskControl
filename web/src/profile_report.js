// The automatic tick updates only a lightweight summary in manual mode. Full
// immutable reports are made on opening or explicit refresh, with capture time.
export class ProfileReportPublisher {
 constructor({mode='manual',summary,capture,publish,clock=()=>performance.now()}={}){
  if(!['manual','live'].includes(mode)||[summary,capture,publish,clock].some(f=>typeof f!=='function'))throw Error('Invalid profile report publisher');
  Object.assign(this,{mode,summary,capture,publish,clock});this.generation=0;this.lastCapture=null;
 }
 tick(){this.summary();if(this.mode==='live')return this.refresh();}
 opened(){if(this.mode==='manual'||!this.generation)return this.refresh();}
 refresh(){const capturedAtMs=this.clock();if(!Number.isFinite(capturedAtMs)||capturedAtMs<0)throw Error('Invalid profile capture clock');const meta=Object.freeze({mode:this.mode,generation:this.generation+1,capturedAtMs});const report=this.capture(meta);this.publish(report,meta);this.generation=meta.generation;this.lastCapture=meta;return report;}
 snapshot(){return {mode:this.mode,generation:this.generation,capturedAtMs:this.lastCapture?.capturedAtMs??null,automaticDetails:this.mode==='live'};}
}
