import {projectCloudLayerClient} from './cloud_layer_client.js';
import {CloudEditorSession} from './cloud_editor_session.js';
import {openCloudDraft,listCloudDrafts} from './cloud_draft_store.js';
import {createCloudDraftJournal} from './cloud_draft_journal.js';
const fault=code=>Object.assign(Error(code),{code});
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const equivalent=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const element=(tag,text,props={})=>{const n=document.createElement(tag);if(text!==null)n.textContent=text;Object.assign(n,props);return n;};
const labels={ready:'已与公网版本同步',saving:'正在提交修改',queued:'本地修改等待提交',waiting:'当前操作中，稍后同步',conflict:'存在编辑冲突，请选择保留哪一方',confirming:'提交结果待确认，正在读取服务器版本','read-only':'当前账号不能提交，修改仅留在本地',revoked:'登录或权限失效，已清除本次协同数据',error:'暂未完成同步，修改仍保留在本地'};
const messages={CLOUD_LOGIN_REQUIRED:'请通过项目重新登录',CLOUD_INITIAL_IMPORT_REQUIRED:'请先下载或处理当前本地修改，再连接公网工程',CLOUD_CONNECT_EDITOR_CHANGED:'连接期间本地工程发生变化，未替换当前数据',CLOUD_CONFLICT_STALE:'比较期间数据已更新，请重新读取后选择',CLOUD_SYNC_BUSY:'后台正在同步，请稍后再提交选择',CLOUD_NOT_INSTALLED:'服务器图层同步接口尚未安装',CLOUD_ACCOUNT_CHANGED:'登录账号已变化，请重新连接',CLOUD_SESSION_CHANGED:'登录会话正在更新，请稍后重试'};
Object.assign(messages,{CLOUD_DRAFT_STORAGE_UNAVAILABLE:'浏览器草稿存储不可用，请下载工程保留修改',CLOUD_DRAFT_STORAGE_BLOCKED:'草稿存储被其他页面阻塞，请稍后重试',CLOUD_DRAFT_WRITE_FAILED:'本机草稿保存失败，修改仍在当前页面，请下载工程',CLOUD_DRAFT_RECORD_INVALID:'本机草稿校验失败，原记录已保留，未覆盖当前工程',CLOUD_DRAFT_CHECKPOINT_INVALID:'本机草稿格式不完整，原记录已保留',CLOUD_DRAFT_CONTEXT_INVALID:'草稿所属图层已变化，未自动恢复',CLOUD_DRAFT_IN_USE:'此草稿仍在另一个页面编辑，请先关闭该页面',CLOUD_DRAFT_LOCK_FAILED:'未取得本机草稿编辑权，请稍后重试',CLOUD_REVISION_INVALID:'服务器版本与草稿基线不一致，原草稿已保留'});
const detail=code=>messages[code]??'同步暂未完成，请稍后重试';
function valueAt(doc,[kind,id]){
 if(kind==='document')return id==='layerOrder'?doc.layers.map(l=>l.id):Object.hasOwn(doc,id)?doc[id]:undefined;
 const layer=doc.layers.find(l=>l.id===id);
 if(kind==='layer')return layer?Object.fromEntries(Object.entries(layer).filter(([key])=>key!=='features')):undefined;
 if(kind==='featureOrder')return layer?.features.map(f=>f.id);
 return doc.layers.flatMap(l=>l.features).find(f=>f.id===id);
}
function describe(value){
 if(value===undefined)return '此版本中已删除或不存在';
 if(value&&typeof value==='object'&&['point','line','region'].includes(value.type)){
  const p=value.positions,style=value.style,label=value.label;
  return [`名称：${value.name}`,`类型：${{point:'点',line:'线',region:'区域'}[value.type]}`,`顶点：${p.length} 个`,...p.slice(0,4).map((v,i)=>`${i+1}: ${v.map(n=>n.toFixed(3)).join(' / ')} 米`),p.length>4?'其余顶点见完整数据':'',`颜色：${style.color} · 线宽：${style.widthPx} · 不透明度：${style.opacity}`,value.type==='region'?`填色：${style.fillColor} · 填充不透明度：${style.fillOpacity}`:'',`标牌：${label?.text??'未设置'} · 数据字段：${label?.dataBindings?.length??0} 项`].filter(Boolean).join('\n');
 }
 const raw=JSON.stringify(value,null,2);return raw.length>2000?raw.slice(0,2000)+'…（完整内容见下方）':raw;
}
// The trusted project host calls connect(options). No URL/storage credential
// discovery or credential input is exposed to the user of the editor.
export function mountCloudEditorPanel({parent,adapter,after}){
 const style=element('style',`#dlg-cloud{border:1px solid #42778b;padding:9px;margin:8px 0}#dlg-cloud p{margin:5px 0}#dlg-cloud-dialog{background:#eef5f9;color:#17364b;border:1px solid #3b8099;border-radius:8px;width:min(1120px,calc(100vw - 40px));max-height:85vh;padding:20px}#dlg-cloud-dialog::backdrop{background:#061622b3}#dlg-cloud-dialog .comparison{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}#dlg-cloud-dialog fieldset{margin:15px 0;border:1px solid #92afbc}#dlg-cloud-dialog pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.6 system-ui;max-height:240px;overflow:auto}#dlg-cloud-dialog .version{border:1px solid #a5bdca;padding:10px;background:white}#dlg-cloud-dialog button{padding:9px 12px;margin:6px}#dlg-cloud-dialog summary{cursor:pointer}#dlg-cloud-dialog label{display:block;font-weight:bold;margin:10px 0}@media(max-width:800px){#dlg-cloud-dialog .comparison{grid-template-columns:1fr}}`);
 document.head.append(style);
 const root=element('section',null,{id:'dlg-cloud'}),heading=element('strong','图层协同'),status=element('p','未连接公网 · 当前为本地编辑',{id:'dlg-cloud-status'}),buttons=element('div',null),refresh=element('button','立即同步',{type:'button',id:'dlg-cloud-refresh',disabled:true}),review=element('button','处理冲突',{type:'button',id:'dlg-cloud-review',hidden:true}),disconnect=element('button','断开协同',{type:'button',id:'dlg-cloud-disconnect',disabled:true});
 const backup=element('p','连接协同后启用本机草稿保护',{id:'dlg-backup-status'}),recoveryNote=element('p','',{id:'dlg-draft-note'}),recovery=element('div',null,{hidden:true,id:'dlg-draft-recovery'}),draftSelect=element('select',null,{id:'dlg-draft-select','aria-label':'选择本机草稿'}),restoreDraft=element('button','恢复所选草稿',{type:'button',id:'dlg-draft-restore'}),scan=element('button','检查本机草稿',{type:'button',id:'dlg-draft-scan',disabled:true}),retry=element('button','重试保存草稿',{type:'button',id:'dlg-backup-retry',hidden:true});backup.setAttribute('role','status');recoveryNote.setAttribute('role','status');recovery.append(draftSelect,restoreDraft);root.append(heading,status,backup,recoveryNote,recovery,buttons);buttons.append(refresh,review,disconnect,scan,retry);if(after)after.after(root);else parent.append(root);
 const dialog=element('dialog',null,{id:'dlg-cloud-dialog'}),title=element('h2','协同编辑冲突'),guide=element('p','比较共同基线、本地修改和公网版本，逐项选择保留哪一方。线和区域按完整对象选择，不拼接顶点。'),content=element('div',null),feedback=element('p','',{id:'dlg-cloud-feedback'}),submit=element('button','提交选择并继续同步',{type:'button',id:'dlg-cloud-submit',disabled:true}),close=element('button','暂不处理',{type:'button'});const pager=element('div',null),previous=element('button','上一组',{type:'button',id:'dlg-cloud-previous'}),pageNote=element('span',''),next=element('button','下一组',{type:'button',id:'dlg-cloud-next'});pager.append(previous,pageNote,next);dialog.append(title,guide,pager,content,feedback,submit,close);document.body.append(dialog);
 let session=null,transport=null,connecting=null,epoch=0,disposed=false,shown=null,choices=new Map(),resolving=false,lastState=null,page=0,localVerification=false,journal=null,lease=null,lastOptions=null,accountKey=null,pendingClose=Promise.resolve(),backupState={state:'idle'};
 const dismiss=()=>{if(dialog.open)dialog.close();};
 dialog.addEventListener('keydown',event=>event.stopPropagation());close.onclick=dismiss;
 const clearConflict=()=>{dismiss();content.replaceChildren();feedback.textContent='';shown=null;choices.clear();review.hidden=true;submit.disabled=true;};
 function state(value){lastState=value;status.textContent=`${labels[value.state]??'协同状态待确认'}${Number.isInteger(value.revision)?' · 版本 '+value.revision:''}${value.code&&value.state==='error'?' · '+detail(value.code):''}`;if(localVerification)status.textContent=status.textContent.replaceAll('公网','本机测试服务');refresh.disabled=!value.running||resolving;disconnect.disabled=!value.running;adapter.state?.(value);if(value.state!=='conflict'&&shown&&!resolving)clearConflict();}
 function renderConflict(){
  const conflict=shown;if(!conflict)return;content.replaceChildren();const start=page*10;pager.hidden=conflict.paths.length<=10;previous.disabled=page===0;next.disabled=start+10>=conflict.paths.length;pageNote.textContent=`第 ${start+1}—${Math.min(start+10,conflict.paths.length)} / ${conflict.paths.length} 项`;
  for(const [offset,path]of conflict.paths.slice(start,start+10).entries()){const i=start+offset;
   const fieldset=element('fieldset',null),legend=element('legend',`${{feature:'点线面对象',layer:'图层属性',featureOrder:'对象顺序',document:'工程属性'}[path[0]]??path[0]} · ${path[1]}`),row=element('div',null,{className:'comparison'});fieldset.append(legend,row);
   for(const [key,label]of [['base','共同基线'],['local','本地编辑'],['remote',localVerification?'本机测试服务最新版本':'公网最新版本']]){
    const card=element('section',null,{className:'version'}),value=valueAt(conflict[key],path),details=element('details',null);const raw=element('pre','展开后加载完整数据');details.append(element('summary','完整数据'),raw);let loaded=false;details.ontoggle=()=>{if(details.open&&!loaded){loaded=true;raw.textContent=value===undefined?'不存在':JSON.stringify(value,null,2);}};card.append(element('h3',label),element('pre',describe(value)),details);
    if(key!=='base'){const label=element('label',null),radio=element('input',null,{type:'radio',name:'cloud-choice-'+i,value:key});radio.dataset.conflictIndex=String(i);radio.checked=choices.get(i)===key;radio.onchange=()=>{choices.set(i,key);submit.disabled=choices.size!==conflict.paths.length||resolving;feedback.textContent=`已选择 ${choices.size} / ${conflict.paths.length} 项`;};label.append(radio,document.createTextNode(key==='local'?' 保留本地编辑':localVerification?' 保留本机测试版本':' 保留公网版本'));card.append(label);}
    row.append(card);
   }content.append(fieldset);
  }
  submit.disabled=choices.size!==conflict.paths.length||resolving;
 }
 previous.onclick=()=>{if(page>0){page--;renderConflict();}};next.onclick=()=>{if(shown&&(page+1)*10<shown.paths.length){page++;renderConflict();}};
 function show(conflict){shown=conflict;choices.clear();page=0;feedback.textContent='';review.hidden=false;title.textContent=localVerification?'本机协同验证 · 编辑冲突':'协同编辑冲突';guide.textContent=localVerification?'比较共同基线、本地修改和本机测试服务版本，逐项选择保留哪一方。此环境不连接公网。':'比较共同基线、本地修改和公网版本，逐项选择保留哪一方。线和区域按完整对象选择，不拼接顶点。';renderConflict();if(!dialog.open)dialog.showModal();}
 review.onclick=()=>{const conflict=session?.conflict;if(conflict){if(shown?.token!==conflict.token)show(conflict);else dialog.showModal();}};
 refresh.onclick=()=>void session?.refresh();
 submit.onclick=async()=>{
  if(!session||!shown||choices.size!==shown.paths.length||resolving)return;
  const token=shown.token,selection=shown.paths.map((path,i)=>({path,side:choices.get(i)}));resolving=true;submit.disabled=true;refresh.disabled=true;
  try{await session.refresh();const success=await session.resolve(token,selection);if(success){clearConflict();}else{clearConflict();feedback.textContent='版本已变化或暂未完成，请重新读取后选择';await session.refresh();}}
  catch(error){feedback.textContent=detail(error.code);}
  finally{resolving=false;submit.disabled=!shown||choices.size!==shown.paths.length;refresh.disabled=!session?.state.running;}
 };
 // Capture before stopping/clearing: delayed callbacks must never read the next
 // account's model. Account metadata is shown only after a fresh authorized GET.
 function capture(active=session){if(!active)return null;const checkpoint=active.captureCheckpoint();checkpoint.local=adapter.persistenceDocument();return checkpoint;}
 function backupStatus(value){backupState={...value};backup.dataset.state=value.state;if(value.state==='error')retry.hidden=false;else if(['saved','idle'].includes(value.state))retry.hidden=true;retry.disabled=value.state==='saving';backup.textContent=({pending:'本机草稿等待保存',saving:'正在保存本机草稿',saved:value.recordKept?'本机草稿已保存 · 刷新后连接可恢复':'已同步 · 本页无待恢复草稿',error:detail(value.code),idle:'本机草稿保护已启用'})[value.state]??'本机草稿状态待确认';}
 function hideRecovery(){recovery.hidden=true;draftSelect.replaceChildren();recoveryNote.textContent='';scan.disabled=true;}
 function renderDrafts(rows,currentId){draftSelect.replaceChildren();for(const row of rows.filter(row=>row.id!==currentId)){const option=element('option',`${row.invalid?'记录格式异常':new Date(row.updatedAt).toLocaleString()} · ${row.id.slice(0,8)}`,{value:row.id,disabled:!!row.invalid});draftSelect.append(option);}recovery.hidden=!draftSelect.options.length;restoreDraft.disabled=!draftSelect.value;scan.disabled=false;}
 function closeOwned(ownedJournal,ownedLease,options){const work=ownedJournal?ownedJournal.close(options):ownedLease?.close();pendingClose=Promise.allSettled([pendingClose,work]).then(()=>{});return pendingClose;}
 function stop({clear=true,discard=false,alreadySaved=false,revoked=false}={}){
  const owned=!!session||!!connecting,ownedJournal=journal,ownedLease=lease;let checkpoint;
  if(!discard&&!alreadySaved&&session)try{checkpoint=capture();}catch(error){backupStatus({state:'error',code:error.code});}
  epoch++;connecting?.abort();connecting=null;session?.stop();session=null;transport?.disconnect();transport=null;journal=lease=null;lastOptions=null;accountKey=null;clearConflict();hideRecovery();refresh.disabled=disconnect.disabled=true;
  const done=closeOwned(ownedJournal,ownedLease,checkpoint?{checkpoint}:{discardPending:true});
  if(clear&&owned)adapter.clear();status.textContent=revoked?labels.revoked:'已断开协同 · 已清除本次会话数据';lastState=revoked?{state:'revoked',running:false}:null;backupState={state:'idle'};backup.dataset.state='idle';backup.textContent=revoked?'已保存的草稿仅在原账号重新验证后可恢复':'已提交的本机草稿保留，重新连接时检查恢复';retry.hidden=true;return done;
 }
 async function manualDisconnect(){
  if(!session||!journal)return stop();const active=session,own=epoch;disconnect.disabled=true;
  try{const snapshot=capture();await journal.commit(snapshot);if(active!==session||own!==epoch)return;if(!equivalent(snapshot,capture())){recoveryNote.textContent='保存期间又有修改，请稍后再断开';return;}await stop({alreadySaved:true});}
  catch(error){if(active===session&&own===epoch)backupStatus({state:'error',code:error.code});}
  finally{disconnect.disabled=!session;}
 }
 disconnect.onclick=()=>void manualDisconnect();retry.onclick=()=>{void journal?.flush().catch(()=>{});};
 async function connect(options,{draftId,expectedAccount}={}){
  if(disposed||session||connecting)throw fault('CLOUD_SESSION_ACTIVE');
  const own=++epoch,abort=new AbortController();connecting=abort;let client,ownedLease,ownedJournal,active;
  const live=()=>!disposed&&own===epoch&&!abort.signal.aborted;
  try{
   await pendingClose;if(!live())return null;const stamp=adapter.captureConnection();client=projectCloudLayerClient(options);transport=client;localVerification=options.development===true&&options.origin?.startsWith('http://127.0.0.1');heading.textContent=localVerification?'图层协同（本机验证）':'图层协同';
   status.textContent='正在核对项目登录和图层版本';await client.read(abort.signal);if(!live()){client.disconnect();return null;}
   const verifiedAccount=client.accountKey;if(expectedAccount&&verifiedAccount!==expectedAccount)throw fault('CLOUD_ACCOUNT_CHANGED');
   ownedLease=await openCloudDraft({accountKey:verifiedAccount,...(draftId?{draftId}:{})});const checkpoint=await ownedLease.load(),rows=await listCloudDrafts({accountKey:verifiedAccount});
   // Storage can yield while credentials change. No cached geometry or even
   // draft metadata becomes visible until both current identity and project ACL
   // have been checked again, after the asynchronous storage operations.
   const initialSnapshot=await client.read(abort.signal);if(!live()){await ownedLease.close();client.disconnect();return null;}
   if(client.accountKey!==verifiedAccount)throw fault('CLOUD_ACCOUNT_CHANGED');adapter.checkConnection(stamp);
   if(checkpoint){if(initialSnapshot.revision<checkpoint.base.revision||initialSnapshot.revision===checkpoint.base.revision&&!equivalent(initialSnapshot.document,checkpoint.base.document))throw fault('CLOUD_REVISION_INVALID');adapter.validateRecovery(checkpoint);}
   adapter.initialize(checkpoint?.local??initialSnapshot.document,{savedDocument:checkpoint?.base.document});if(checkpoint)adapter.restoreContext(checkpoint.context);
   ownedJournal=createCloudDraftJournal({store:ownedLease,capture:()=>live()&&session===active?capture(active):null,onState:value=>{if(live()&&session===active)backupStatus(value);}});
   active=new CloudEditorSession({transport:client,initialSnapshot,...(checkpoint?{checkpoint}:{}),current:()=>adapter.current(),context:()=>adapter.draftContext(),persist:value=>{if(!live()||session!==active)throw fault('CLOUD_SESSION_CLOSED');value.local=adapter.persistenceDocument();return ownedJournal.commit(value);},busy:()=>adapter.busy(),adopt:(doc,context)=>adapter.adopt(doc,context),acknowledge:(doc,context)=>adapter.acknowledge(doc,context),onState:value=>{if(live()&&session===active)state(value);},onConflict:value=>{if(live()&&session===active)show(value);},onRevoke:()=>{if(live()&&session===active)void stop({discard:true,revoked:true});}});
   session=active;journal=ownedJournal;lease=ownedLease;connecting=null;lastOptions=options;accountKey=verifiedAccount;renderDrafts(rows,lease.id);recoveryNote.textContent=checkpoint?'已恢复本页草稿、各TAB点集与待应用字段；确认后继续编辑':'';backupStatus({state:'idle'});active.start();return ()=>session===active?stop():Promise.resolve();
  }catch(error){if(ownedJournal)await ownedJournal.close({discardPending:true}).catch(()=>{});else await ownedLease?.close().catch(()=>{});client?.disconnect();if(own===epoch){connecting=null;transport=null;hideRecovery();status.textContent=detail(error.code);if(expectedAccount)adapter.clear();}throw error;}
 }
 scan.onclick=async()=>{const active=session,own=epoch,client=transport,key=accountKey;if(!active)return;scan.disabled=true;try{await client.read();const rows=await listCloudDrafts({accountKey:key});await client.read();if(own!==epoch||active!==session)return;if(client.accountKey!==key)throw fault('CLOUD_ACCOUNT_CHANGED');renderDrafts(rows,lease.id);}catch(error){if(own===epoch&&active===session){if(['CLOUD_LOGIN_REQUIRED','CLOUD_ACCOUNT_CHANGED','CLOUD_ACCESS_DENIED'].includes(error.code))void stop({discard:true,revoked:true});else recoveryNote.textContent=detail(error.code);}}finally{if(own===epoch&&active===session)scan.disabled=false;}};
 restoreDraft.onclick=async()=>{if(!session||!draftSelect.value)return;const id=draftSelect.value,options=lastOptions,key=accountKey;try{adapter.captureConnection({strict:true});adapter.transition(true);await stop();await connect(options,{draftId:id,expectedAccount:key});}catch(error){recoveryNote.textContent=detail(error.code);}finally{adapter.transition(false);}};
 return {
  get connected(){return !!session;},get state(){return session?.state??lastState;},get backupPending(){return !!journal&&['pending','saving','error'].includes(backupState.state);},get backupState(){return {...backupState};},
  get identity(){return session?epoch:null;},
  async verifyOwner(identity){const own=epoch,active=session,client=transport;if(!active||identity!==own)throw fault('CLOUD_SESSION_CLOSED');try{await client.read();if(own!==epoch||session!==active)throw fault('CLOUD_SESSION_CLOSED');}catch(error){if(own===epoch&&session===active&&['CLOUD_LOGIN_REQUIRED','CLOUD_ACCOUNT_CHANGED','CLOUD_ACCESS_DENIED'].includes(error.code))void stop({discard:true,revoked:true});throw error;}},
  async projectFiles(action,identity,...values){
   const own=epoch,active=session,client=transport;if(!active||identity!==own)throw fault('CLOUD_SESSION_CLOSED');
   const methods={list:()=>client.listProjectFiles(),read:()=>client.readProjectFile(...values),save:()=>client.saveProjectFile(...values)};
   if(!Object.hasOwn(methods,action))throw fault('CLOUD_CONFIGURATION_INVALID');
   try{const result=await methods[action]();if(own!==epoch||session!==active||client.accountKey!==accountKey)throw fault('CLOUD_SESSION_CLOSED');return result;}
   catch(error){if(own===epoch&&session===active){if(['CLOUD_LOGIN_REQUIRED','CLOUD_ACCOUNT_CHANGED'].includes(error.code))void stop({discard:true,revoked:true});else if(error.code==='CLOUD_ACCESS_DENIED'){try{await client.read();}catch(check){if(['CLOUD_LOGIN_REQUIRED','CLOUD_ACCOUNT_CHANGED','CLOUD_ACCESS_DENIED'].includes(check.code))void stop({discard:true,revoked:true});}}}throw error;}
  },
  async sceneFiles(action,identity,...values){
   const own=epoch,active=session,client=transport;if(!active||identity!==own)throw fault('CLOUD_SESSION_CLOSED');
   const methods={list:()=>client.listSceneFiles(),read:()=>client.readSceneFile(...values),save:()=>client.saveSceneFile(...values)};
   if(!Object.hasOwn(methods,action))throw fault('CLOUD_CONFIGURATION_INVALID');
   try{const result=await methods[action]();if(own!==epoch||session!==active||client.accountKey!==accountKey)throw fault('CLOUD_SESSION_CLOSED');return result;}
   catch(error){if(own===epoch&&session===active){if(['CLOUD_LOGIN_REQUIRED','CLOUD_ACCOUNT_CHANGED'].includes(error.code))void stop({discard:true,revoked:true});else if(error.code==='CLOUD_ACCESS_DENIED'){try{await client.read();}catch(check){if(['CLOUD_LOGIN_REQUIRED','CLOUD_ACCOUNT_CHANGED','CLOUD_ACCESS_DENIED'].includes(check.code))void stop({discard:true,revoked:true});}}}throw error;}
  },
  get localVerification(){return localVerification;},
  changed(){session?.notifyEdit();},draftChanged(){journal?.schedule();},connect,disconnect:stop,
  dispose(){if(disposed)return;stop({clear:false});disposed=true;root.remove();dialog.remove();style.remove();}
 };
}
