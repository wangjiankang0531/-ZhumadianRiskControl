/* Temporary observer for the owned local replica. Does not alter original handlers. */
(() => {
  'use strict';
  const records = [];
  const clean = value => String(value).slice(0, 4096)
    .replace(/([?&](?:t|token|authorization|password|secret|key)=)[^&\s]*/gi, '$1[redacted]')
    .replace(/(Bearer\s+)[A-Za-z0-9._-]+/gi, '$1[redacted]');
  function describe(value) {
    if (value == null || ['number','boolean','string','undefined'].includes(typeof value)) return clean(value);
    const result = {type: typeof value};
    for (const key of ['name','message','stack','code','errorCode','status']) {
      try {
        let object = value, descriptor;
        for (let depth=0; object && depth<3; depth++,object=Object.getPrototypeOf(object)) {
          descriptor=Object.getOwnPropertyDescriptor(object,key);
          if(descriptor) break;
        }
        if (descriptor && 'value' in descriptor && ['string','number','boolean'].includes(typeof descriptor.value)) result[key]=clean(descriptor.value);
      } catch (_) { result[key]='[unavailable]'; }
    }
    return result;
  }
  function render() {
    let target=document.getElementById('owned-original-error-observation');
    if(!target && document.body) {
      target=document.createElement('pre');target.id='owned-original-error-observation';target.hidden=true;document.body.appendChild(target);
    }
    if(target) target.textContent=JSON.stringify(records);
  }
  function record(kind,args) {
    try {
      if(records.length>=40) return;
      records.push({at:new Date().toISOString(),kind,args:Array.from(args).slice(0,4).map(describe)});render();
    } catch (_) { /* Observation must not change original execution. */ }
  }
  const original=console.error;
  console.error=function(...args) { record('console.error',args);return Reflect.apply(original,this,args); };
  window.addEventListener('error',event=>record('window.error',[event.error,event.message]));
  window.addEventListener('unhandledrejection',event=>record('unhandledrejection',[event.reason]));
  document.addEventListener('DOMContentLoaded',render,{once:true});
})();
