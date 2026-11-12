import {checkedSceneFileName,checkedSceneFileList,checkedSceneFile,checkedSceneFileReceipt} from './scene_file_contract.js';
import {checkedSceneProject} from './scene_project.js';
import {checkedProjectFileName,checkedProjectFileList,checkedProjectFile,checkedProjectFileReceipt} from './project_file_contract.js';
import {readJSON} from './http_json.js';
import {checkedProjectSubject, projectAccountKey, projectSubjectFromCurrentUser} from './project_account_identity.js';
import {cloudSnapshot} from './cloud_layer_adoption.js';
import {prepareLandscapeDocument} from './landscape_document.js';

const fail = (code, mayHaveCommitted = false) => Object.assign(Error(code), {code, mayHaveCommitted});
const credential = value => typeof value === 'string' && /^[\x21-\x7e][\x20-\x7e]{0,16383}$/.test(value) && value.trim() === value;
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const revision = value => Number.isInteger(value) && value >= 0 && value <= 2147483647;

// Browser editor V2 transport. The original project login supplies credentials
// in memory; no storage, URL tokens, V1 fallback, automatic POST retry or seed.
// A failed POST may already be committed: callers must GET and reconcile their
// retained base/draft before another write, rather than repeat the submission.
export function projectCloudLayerClient({authorizationProvider, expectedSubject,
  fetcher = fetch, origin = location.origin, development = false}) {
  if (typeof authorizationProvider !== 'function' || typeof fetcher !== 'function') throw fail('CLOUD_CONFIGURATION_INVALID');
  let url;
  try { url = new URL(origin); } catch { throw fail('CLOUD_CONFIGURATION_INVALID'); }
  if (url.origin !== origin || !(origin === 'https://www.joinlinksmart.com' ||
      development === true && url.protocol === 'http:' && url.hostname === '127.0.0.1')) throw fail('CLOUD_CONFIGURATION_INVALID');
  if (expectedSubject !== undefined) {
    try { checkedProjectSubject(expectedSubject); } catch { throw fail('CLOUD_CONFIGURATION_INVALID'); }
  }
  const identityEndpoint = origin + '/zhumadian/api/jnpf/oauth/CurrentUser';
  const endpoint = origin + '/zhumadian/api/spatial-sync/v2/project/layers';
  const filesEndpoint=origin+'/zhumadian/api/spatial-sync/v2/project/files';
  const scenesEndpoint=origin+'/zhumadian/api/spatial-sync/v2/project/scenes';
  const active = new Set();
  let boundAccount = null, closed = false, writing = false, fileWriting=false,sceneFileWriting=false;
  async function authorization() {
    let value;
    try { value = await authorizationProvider(); } catch { throw fail('CLOUD_LOGIN_REQUIRED'); }
    if (!credential(value)) throw fail('CLOUD_LOGIN_REQUIRED');
    return value;
  }
  function serializeDocument(document,metadata,prepare=prepareLandscapeDocument){
        const captured = prepare(document);
        const stack = [captured], seen = new WeakSet();
        while (stack.length) {
          const item = stack.pop();
          if (item === null || typeof item !== 'object') continue;
          if (seen.has(item) || !Array.isArray(item) && ![Object.prototype, null].includes(Object.getPrototypeOf(item))) throw Error();
          seen.add(item);
          stack.push(...Object.values(item));
        }
        return JSON.stringify({...metadata, document: captured}, (key, value) => {
          if (value === undefined || typeof value === 'function' || typeof value === 'symbol' ||
              typeof value === 'bigint' || typeof value === 'number' && !Number.isFinite(value)) throw Error();
          return value;
        });
  }
  async function operation(externalSignal, payload, files=null) {
    if (closed) throw fail('CLOUD_LOGIN_REQUIRED');
    if (externalSignal !== undefined && !(externalSignal instanceof AbortSignal)) throw fail('CLOUD_CONFIGURATION_INVALID');
    const controller = new AbortController();
    const signal = AbortSignal.any([controller.signal, AbortSignal.timeout(10000), ...(externalSignal ? [externalSignal] : [])]);
    active.add(controller);
    let dispatched = false;
    try {
      const token = await authorization();
      async function current() {
        if (closed) throw fail('CLOUD_SESSION_CHANGED', dispatched);
        let latest;
        try { latest = await authorization(); } catch (error) { throw fail(error.code, dispatched); }
        if (latest !== token) throw fail('CLOUD_SESSION_CHANGED', dispatched);
        if (signal.aborted) throw fail(dispatched ? 'CLOUD_COMMIT_UNKNOWN' : 'CLOUD_UNAVAILABLE', dispatched);
      }
      async function request(target, {body, headers = {}, maximum = 17 * 1048576} = {}) {
        await current();
        const post = body !== undefined;
        let response;
        try {
          if (post) dispatched = true;
          response = await fetcher(target, {method: post ? 'POST' : 'GET',
            headers: {Authorization: token, Accept: 'application/json', ...headers,
              ...(post ? {'Content-Type': 'application/json'} : {})}, ...(post ? {body} : {}),
            credentials: 'omit', cache: 'no-store', redirect: 'error', referrerPolicy: 'no-referrer', signal});
        } catch {
          await current();
          throw fail(post ? 'CLOUD_COMMIT_UNKNOWN' : 'CLOUD_UNAVAILABLE', post);
        }
        await current();
        if (!response.ok) {
          try { await response.body?.cancel(); } catch {}
          const code = response.status === 401 ? 'CLOUD_LOGIN_REQUIRED' : response.status === 403 ? 'CLOUD_ACCESS_DENIED' :
            response.status === 404 ? (files?(files.kind==='read'?'CLOUD_FILE_NOT_FOUND':'CLOUD_FILE_LIBRARY_NOT_INSTALLED'):'CLOUD_NOT_INSTALLED') : files&&response.status===501?'CLOUD_FILE_LIBRARY_NOT_INSTALLED': post && response.status === 409 ? (files?'CLOUD_FILE_REVISION_CONFLICT':'CLOUD_REVISION_CONFLICT') :
            post && [400, 413, 415, 422].includes(response.status) ? 'CLOUD_DOCUMENT_REJECTED' :
            post ? 'CLOUD_COMMIT_UNKNOWN' : 'CLOUD_UNAVAILABLE';
          throw fail(code, code === 'CLOUD_COMMIT_UNKNOWN');
        }
        let value;
        try { value = (await readJSON(response, maximum)).document; }
        catch {
          await current();
          throw fail(post ? 'CLOUD_COMMIT_UNKNOWN' : 'CLOUD_RESPONSE_INVALID', post);
        }
        await current();
        return value;
      }
      const subject = projectSubjectFromCurrentUser(await request(identityEndpoint, {maximum: 1048576}));
      const account = await projectAccountKey(subject);
      await current();
      if (expectedSubject !== undefined && subject !== expectedSubject || boundAccount !== null && account !== boundAccount) {
        throw fail('CLOUD_ACCOUNT_CHANGED');
      }
      boundAccount = account;
      const value = await request(files?.endpoint??endpoint, {body: payload?.body, headers: {'X-XNBY-Sync-Account': account},maximum:files?.kind==='list'?1048576:17*1048576});
      if(files){try{return files.check(value);}catch{throw fail(payload?'CLOUD_COMMIT_UNKNOWN':'CLOUD_RESPONSE_INVALID',!!payload);}}
      if (!payload) {
        cloudSnapshot(value);
        return structuredClone(value);
      }
      // Product receipts include optional counts for changed documents. An
      // unchanged write retains its version; a changed one advances exactly one.
      if (!value || typeof value !== 'object' || Array.isArray(value) || !revision(value.revision) ||
          !hash(value.sha256) || typeof value.changed !== 'boolean' ||
          value.revision !== payload.expectedRevision + (value.changed ? 1 : 0) ||
          Object.keys(value).some(k => !['revision', 'sha256', 'changed', 'layerCount', 'featureCount'].includes(k)) ||
          ['layerCount', 'featureCount'].some(k => Object.hasOwn(value, k) &&
            (!Number.isInteger(value[k]) || value[k] < 0 || value[k] > (k === 'layerCount' ? 1000 : 10000)))) {
        throw fail('CLOUD_COMMIT_UNKNOWN', true);
      }
      return structuredClone(value);
    } catch (error) {
      if (dispatched && !Object.hasOwn(error, 'mayHaveCommitted')) throw fail('CLOUD_COMMIT_UNKNOWN', true);
      throw error;
    } finally {
      active.delete(controller);
      controller.abort();
    }
  }
  return Object.freeze({
    // Verified identity metadata only; callers must complete a fresh read and
    // recheck after asynchronous draft loading. This is not an access grant.
    get accountKey() { return closed ? null : boundAccount; },
    read: signal => operation(signal),
    async write(document, expectedRevision, signal) {
      if (writing) throw fail('CLOUD_WRITE_IN_PROGRESS');
      if (!revision(expectedRevision) || expectedRevision === 2147483647) throw fail('CLOUD_REVISION_INVALID');
      let body;
      try {
        // Serialize before awaiting identity so subsequent UI mutations cannot
        // change the captured submission. Reject non-JSON extension values.
        body=serializeDocument(document,{expectedRevision});
      } catch { throw fail('CLOUD_DOCUMENT_INVALID'); }
      if (new TextEncoder().encode(body).byteLength > 16 * 1048576) throw fail('CLOUD_DOCUMENT_TOO_LARGE');
      writing = true;
      try { return await operation(signal, {body, expectedRevision}); }
      finally { writing = false; }
    },
    listProjectFiles:signal=>operation(signal,undefined,{kind:'list',endpoint:filesEndpoint,check:checkedProjectFileList}),
    readProjectFile(name,signal){try{checkedProjectFileName(name);}catch{throw fail('CLOUD_FILE_NAME_INVALID');}return operation(signal,undefined,{kind:'read',endpoint:filesEndpoint+'/'+encodeURIComponent(name),check:value=>checkedProjectFile(value,name)});},
    async saveProjectFile(name,document,expectedSHA256,signal){
      if(fileWriting)throw fail('CLOUD_WRITE_IN_PROGRESS');
      try{checkedProjectFileName(name);}catch{throw fail('CLOUD_FILE_NAME_INVALID');}
      if(expectedSHA256!==null&&!hash(expectedSHA256))throw fail('CLOUD_FILE_REVISION_INVALID');
      let body;try{body=serializeDocument(document,{name,expectedSHA256});}catch{throw fail('CLOUD_DOCUMENT_INVALID');}
      if(new TextEncoder().encode(body).byteLength>16*1048576)throw fail('CLOUD_DOCUMENT_TOO_LARGE');
      fileWriting=true;
      try{return await operation(signal,{body},{kind:'save',endpoint:filesEndpoint,check:value=>checkedProjectFileReceipt(value,name)});}finally{fileWriting=false;}
    },
    listSceneFiles:signal=>operation(signal,undefined,{kind:'list',endpoint:scenesEndpoint,check:checkedSceneFileList}),
    readSceneFile(name,signal){try{checkedSceneFileName(name);}catch{throw fail('CLOUD_FILE_NAME_INVALID');}return operation(signal,undefined,{kind:'read',endpoint:scenesEndpoint+'/'+encodeURIComponent(name),check:value=>checkedSceneFile(value,name)});},
    async saveSceneFile(name,document,expectedSHA256,signal){
      if(sceneFileWriting)throw fail('CLOUD_WRITE_IN_PROGRESS');
      try{checkedSceneFileName(name);}catch{throw fail('CLOUD_FILE_NAME_INVALID');}
      if(expectedSHA256!==null&&!hash(expectedSHA256))throw fail('CLOUD_FILE_REVISION_INVALID');
      let body;try{body=serializeDocument(document,{name,expectedSHA256},checkedSceneProject);}catch{throw fail('CLOUD_DOCUMENT_INVALID');}
      if(new TextEncoder().encode(body).byteLength>16*1048576)throw fail('CLOUD_DOCUMENT_TOO_LARGE');
      sceneFileWriting=true;
      try{return await operation(signal,{body},{kind:'save',endpoint:scenesEndpoint,check:value=>checkedSceneFileReceipt(value,name)});}finally{sceneFileWriting=false;}
    },
    disconnect() { closed = true; for (const controller of active) controller.abort(); }
  });
}