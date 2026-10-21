/** Keep a synthetic-business deployment inside its current directory. */
export function referenceApiURL(path, href) {
  if (typeof path !== 'string' || !/^[a-z][a-z-]*(?:\?[^#]*)?$/.test(path)) throw Error('Invalid business API path');
  return new URL('api/demo/' + path, new URL('./', href)).href;
}

export function referenceNavigation(deployment) {
  if (deployment?.mode === 'public-business') return [];
  return [
    ['三维一张图', 'http://127.0.0.1:8767/?topic=emergency'],
    ['原业务门户', 'http://127.0.0.1:8767/portal.html'],
  ];
}

/** Local navigation is a user click; never sends the public session to the scene. */
export function referenceCommandURL(deployment) {
 const value=deployment?.commandURL??'http://127.0.0.1:8767/?topic=emergency&mode=command';
 const u=new URL(value);
 if(u.protocol!=='http:'||!['127.0.0.1','localhost'].includes(u.hostname)||u.username||u.password||u.pathname!=='/'||u.hash||!/^\d+$/.test(u.port)||+u.port<1024||+u.port>65535||![2,4].includes(u.searchParams.size)||[...u.searchParams.keys()].some(k=>!['topic','mode','levelIndex','levelCut'].includes(k))||(u.searchParams.size===4&&(u.searchParams.get('levelIndex')!=='1'||u.searchParams.get('levelCut')!=='1'))||u.searchParams.get('topic')!=='emergency'||u.searchParams.get('mode')!=='command')throw Error('本地应急场景入口配置无效');
 return u.href;
}

// A local installation may name its verified scene explicitly. Public pages
// must never adopt a local HTML override or forward account/session fields.
export function referenceLocalDeployment(deployment,{hostname,commandURL}={}) {
 if(deployment?.mode==='public-business'||!['127.0.0.1','localhost'].includes(hostname)||!commandURL)return deployment;
 const next={...deployment,commandURL};referenceCommandURL(next);return next;
}
export function referenceSceneURL(deployment) {
 const u=new URL(referenceCommandURL(deployment));u.searchParams.delete('topic');u.searchParams.delete('mode');return u.href;
}
