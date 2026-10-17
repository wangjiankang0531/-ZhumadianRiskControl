import {readPortalConfiguration,OAuthLogin} from './oauth_login.js';
import {FocusClient} from './focus_client.js';
export const states={pending:'待关注',feedback:'企业已反馈',supplement:'需补充材料',onsite:'需现场核查',following:'继续关注',inspection:'纳入专项检查',archived:'已归档'};
const flags={major:'重大',spillover:'外溢',repeated:'重复','high-risk':'高风险','special-inspection':'专项检查',supervision:'上级督办',overdue:'超期'};
const methods={phone:'电话核实',online:'线上查看',onsite:'现场核查',communication:'企业沟通',supplement:'材料补充'};
const conclusions={rectified:'已整改',inadequate:'整改不到位',continue:'需继续关注','special-inspection':'建议专项检查',emergency:'建议转应急关注'};
const kinds={create:'登记重点问题',feedback:'企业反馈',track:'园区跟踪',review:'复查记录',archive:'园区归档',reopen:'重新关注'};
const messages={SIGNED_OUT:'请登录后查看本人企业范围内的重点问题',AUTH_EXPIRED:'登录已到期，业务内容已清空',FORBIDDEN:'当前账号没有此项权限，业务内容已清空',POLICY_CHANGED:'权限发生变化，请重新登录',REVISION_CONFLICT:'其他人员已经修改此记录，请刷新详情后再操作',SOURCE_ALREADY_REGISTERED:'该企业的来源问题编号已登记，请搜索已有记录',REVIEW_REQUIRED:'请先记录“已整改”的复查结论，再归档',ISSUE_ARCHIVED:'该问题已归档，请先重新关注',SPATIAL_REFERENCE_UNAVAILABLE:'关联点位不存在，或不属于当前企业',FOCUS_NOT_CONFIGURED:'服务尚未配置业务数据库',INVALID_BODY:'请检查必填内容、日期和重点关注理由',CONNECTION_FAILED:'连接失败，请稍后刷新；重试不会覆盖其他人的更新'};
let notify=()=>{},configuration=null,oauth=null,initialization=null,synthetic=false;
const client=new FocusClient({onClear:code=>notify(code)});
const e=(tag,cls='',text='')=>{const n=document.createElement(tag);n.className=cls;n.textContent=text;return n;};
const button=(label,action,cls='button')=>{const n=e('button',cls,label);n.type='button';n.onclick=action;return n;};
const anchor=(label,url,cls='button secondary')=>{const n=e('a',cls,label);n.href=url;return n;};
const errorText=error=>{const code=typeof error?.code==='string'&&/^[A-Z_]{1,64}$/.test(error.code)?error.code:'CONNECTION_FAILED';console.info('[XNBY focus] '+code);return messages[code]??({LOGIN_INVALID:'登录事务已失效，请重新登录',LOGIN_REJECTED:'登录交换未完成，请重新登录',LOGIN_UNAVAILABLE:'登录服务暂不可用',CONFIG_INVALID:'业务连接配置无效'}[code]??'服务暂不可用，请刷新重试');};
async function initialize(){
  const callback=new URL(location.href),hasCallback=['code','state','error'].some(k=>callback.searchParams.has(k));
  if(hasCallback)history.replaceState(null,'',location.pathname+'#hidden-danger');
  configuration=await readPortalConfiguration(fetch,location.origin);
  if(configuration.mode==='local')return;
  oauth=new OAuthLogin(configuration,{storage:sessionStorage,fetcher:fetch,redirectUri:location.origin+location.pathname});
  if(configuration.development)try{const r=await fetch('/qa/status',{cache:'no-store'});synthetic=r.ok&&(await r.json()).synthetic===true;}catch{}
  if(hasCallback)await client.connect(await oauth.complete(callback));
}
function selectField(label,values,selected=''){
  const wrap=e('label','focus-field'),input=e('select');wrap.append(e('span','',label));
  for(const [value,name] of Object.entries(values)){const option=e('option','',name);option.value=value;input.append(option);}
  input.value=selected||Object.keys(values)[0];wrap.append(input);return {wrap,input};
}
function inputField(label,value='',multiline=false){
  const wrap=e('label','focus-field'),input=e(multiline?'textarea':'input');input.value=value;input.required=true;if(multiline)input.rows=3;
  wrap.append(e('span','',label),input);return {wrap,input};
}
function kv(container,label,value){const row=e('div','focus-kv');row.append(e('dt','',label),e('dd','',value??'未提供'));container.append(row);}
export function mountFocus(main){
  let alive=true,view=0,selected=null,offset=0,filter={},list=null,busy=false,detailRequest=0;
  const mount=e('div','focus-app');main.append(mount);
  const live=(node,generation)=>alive&&node.isConnected&&generation===view;
  async function login(){client.disconnect();try{location.assign(await oauth.begin());}catch(error){render(errorText(error));}}
  function render(message=''){
    if(!alive)return;view++;const generation=view;selected=null;list=null;mount.replaceChildren();
    const title=e('div','page-heading'),copy=e('div');copy.append(e('h1','','重点问题跟踪'),e('p','','重大 / 超期 / 外溢等问题的园区辅助闭环'));title.append(copy);
    const controls=e('div','focus-actions');
    if(client.session){controls.append(button('刷新',()=>render()),button('切换账号',login,'button secondary'),button('退出',()=>client.disconnect(),'button secondary'));}
    else if(oauth)controls.append(button('登录业务平台',login));title.append(controls);mount.append(title);
    const note=e('div','notice');note.append(e('strong','',synthetic?'模拟验收数据 · 非正式监管记录':'重点问题跟踪辅助闭环'),e('p','',synthetic?'合成A/B企业、位置和问题记录可独立操作，数据库保留本次体验修改。':'不接管企业一般隐患台账；园区记录关注、企业反馈、跟踪及复查结论。'));mount.append(note);
    const status=e('p','focus-status',message);status.setAttribute('role','status');status.setAttribute('aria-live','polite');mount.append(status);
    if(!configuration){status.textContent=message||'正在读取业务连接配置';return;}
    if(configuration.mode==='local'){
      const p=e('section','panel focus-welcome');p.append(e('h2','','模拟业务体验已准备'),e('p','','使用独立模拟账号查看A/B企业的重点问题、反馈与复查历史，并体验跟踪、归档和重新关注。'),anchor('打开模拟数据体验','http://127.0.0.1:8790/portal.html#hidden-danger'),e('p','panel-note','若服务未启动，请运行“体验重点问题闭环.cmd”。正式业务源与统一身份暂未接入。'));mount.append(p);return;
    }
    if(!client.session){status.textContent=message||'请登录后查看获准企业的业务数据';return;}
    const session=client.session;mount.append(e('p','focus-scope','账号：'+session.subject+' · 企业范围：'+(session.allEnterprises?'全部获准企业':session.enterprises.join('、')||'无')+' · '+(session.permissions.includes('focus:track')?'园区跟踪人员':session.permissions.includes('focus:feedback')?'企业反馈人员':'只读人员')));
    const metrics=e('div','metric-row');for(const [key,label] of [['total','当前问题'],['overdue','本地期限超期'],['onsite','需现场核查'],['archived','园区已归档']]){const card=e('div','metric'),n=e('div');n.append(e('h3','',label),e('strong','','—'));card.append(n);metrics.append(card);card.dataset.metric=key;}mount.append(metrics);
    const area=e('section','panel'),toolbar=e('form','focus-toolbar');
    const search=inputField('搜索问题 / 来源编号',filter.search||'');search.input.required=false;search.input.type='search';
    const state=selectField('关注状态',{'':'全部状态',...states},filter.status||'');state.input.value=filter.status||'';
    const flag=selectField('重点类型',{'':'全部类型',...flags},filter.flag||'');flag.input.value=filter.flag||'';
    const submit=e('button','button','筛选');submit.type='submit';toolbar.append(search.wrap,state.wrap,flag.wrap,submit);
    toolbar.onsubmit=event=>{event.preventDefault();filter=Object.fromEntries([['search',search.input.value.trim()],['status',state.input.value],['flag',flag.input.value]].filter(([,v])=>v));offset=0;render();};
    if(session.permissions.includes('focus:track'))toolbar.append(button('登记重点问题',()=>editIssue(null,'create')));area.append(toolbar);
    const table=e('table','business-table focus-table'),head=e('thead'),hr=e('tr');for(const label of ['问题 / 来源','企业','重点类型','关注状态','整改期限','操作'])hr.append(e('th','',label));head.append(hr);const body=e('tbody');table.append(head,body);const wrap=e('div','table-wrap');wrap.append(table);area.append(wrap);const pager=e('div','focus-pager');area.append(pager);mount.append(area);
    const detail=e('section','panel focus-detail');detail.hidden=true;mount.append(detail);
    async function load(){
      try{const data=await client.list({...filter,offset:String(offset),limit:'10'});if(!live(mount,generation))return;list=data;body.replaceChildren();
        for(const card of metrics.children)card.querySelector('strong').textContent=data.counts[card.dataset.metric];
        if(!data.items.length){const row=e('tr'),cell=e('td','empty-cell','当前范围没有匹配的重点问题');cell.colSpan=6;row.append(cell);body.append(row);}
        for(const issue of data.items){const row=e('tr'),name=e('td'),copy=e('div','focus-issue-title',issue.title);name.append(copy,e('small','',issue.sourceSystem+' / '+issue.sourceId));row.append(name,e('td','',issue.enterpriseId));const tags=e('td');for(const f of issue.flags)tags.append(e('span','focus-tag',flags[f]??f));if(issue.overdue)tags.append(e('span','focus-tag danger','超期'));row.append(tags);const stateCell=e('td');stateCell.append(e('span','focus-state '+issue.status,states[issue.status]));row.append(stateCell,e('td','',issue.dueDate??'未设置'));const action=e('td');action.append(button('查看记录',()=>showDetail(issue.id),'focus-text-button'));row.append(action);body.append(row);}
        pager.replaceChildren();const previous=button('上一页',()=>{offset=Math.max(0,offset-10);render();},'button secondary');previous.disabled=offset===0;const next=button('下一页',()=>{offset+=10;render();},'button secondary');next.disabled=offset+10>=data.total;pager.append(e('span','','共 '+data.total+' 条 · 当前筛选范围'),previous,next);status.textContent=message||'数据已读取 · 期限超期为本地辅助口径，非源系统认定';
      }catch(error){if(live(mount,generation)){body.replaceChildren();detail.hidden=true;for(const c of metrics.children)c.querySelector('strong').textContent='—';status.textContent=errorText(error);}}
    }
    async function showDetail(id){
      const request=++detailRequest;
      try{const data=await client.detail(id),events=await client.events(id);if(!live(mount,generation)||request!==detailRequest)return;if(events.revision!==data.issue.revision)throw Object.assign(Error(),{code:'REVISION_CONFLICT'});selected=data.issue;drawDetail(selected,events);detail.scrollIntoView({behavior:'smooth',block:'start'});}
      catch(error){if(live(mount,generation)&&request===detailRequest){detail.hidden=true;status.textContent=errorText(error);}}
    }
    function drawDetail(issue,events){
      detail.hidden=false;detail.replaceChildren();detail.append(e('h2','',issue.title));const meta=e('dl','focus-description');for(const [label,value] of [['企业',issue.enterpriseId],['来源',issue.sourceSystem+' / '+issue.sourceId],['关注状态',states[issue.status]],['问题描述',issue.description],['整改期限',issue.dueDate],['更新时间',issue.updatedAt],['记录版本',String(issue.revision)]])kv(meta,label,value);detail.append(meta);
      const controls=e('div','focus-actions');controls.append(button('刷新详情',()=>showDetail(issue.id),'button secondary'));
      if(issue.spatialId)controls.append(anchor('查看关联图层','/?'+new URLSearchParams({topic:'portrait',category:'hidden-danger',spatial:issue.spatialId}),'button secondary'));
      if(issue.status!=='archived'){
        if(session.permissions.includes('focus:feedback'))controls.append(button('填写企业反馈',()=>editIssue(issue,'feedback')));
        if(session.permissions.includes('focus:track')){controls.append(button('添加跟踪',()=>editIssue(issue,'track')),button('记录复查',()=>editIssue(issue,'review')));const archive=button('园区归档',()=>editIssue(issue,'archive'),'button secondary');archive.disabled=issue.latestReview?.result!=='rectified';archive.title=archive.disabled?'先记录已整改的复查结论':'';controls.append(archive);}
      }else if(session.permissions.includes('focus:track'))controls.append(button('重新关注',()=>editIssue(issue,'reopen')));detail.append(controls);
      if(issue.latestFeedback){const box=e('div','focus-evidence');box.append(e('h3','','企业最新反馈'));const values=e('dl');for(const [key,label] of [['cause','原因说明'],['measures','整改措施'],['plan','整改计划'],['completion','完成情况'],['improvement','后续改进'],['materialVersion','材料版本'],['actor','反馈人员'],['at','反馈时间']])kv(values,label,issue.latestFeedback[key]);box.append(values);detail.append(box);}
      if(issue.latestReview)detail.append(e('p','notice','最新复查：'+conclusions[issue.latestReview.result]+' · '+issue.latestReview.note));
      const history=e('div','focus-history');history.append(e('h3','','跟踪与复查历史'));detail.append(history);let nextOffset=0;
      const appendEvents=page=>{for(const event of page.items){const card=e('article','focus-event');card.append(e('strong','',kinds[event.kind]??event.kind),e('small','',event.at+' · '+event.actor+' · 版本 '+event.revision));const note=event.data.note??event.data.completion??event.data.description;if(note)card.append(e('p','',note));if(event.data.result)card.append(e('span','focus-tag',conclusions[event.data.result]??event.data.result));history.append(card);}nextOffset+=page.items.length;};appendEvents(events);
      const more=button('加载更多历史',async()=>{more.disabled=true;try{const page=await client.events(issue.id,nextOffset);if(!live(mount,generation)||selected?.id!==issue.id)return;if(page.revision!==issue.revision)throw Object.assign(Error(),{code:'REVISION_CONFLICT'});appendEvents(page);more.hidden=nextOffset>=page.total;}catch(error){status.textContent=errorText(error);}finally{more.disabled=false;}},'button secondary');more.hidden=nextOffset>=events.total;detail.append(more);
    }
    function editIssue(issue,action){
      if(busy)return;const dialog=e('dialog','focus-dialog'),form=e('form'),fields={},labels={create:'登记重点问题',feedback:'填写企业反馈',track:'添加跟踪记录',review:'记录现场复查',archive:'园区跟踪归档',reopen:'重新关注'};
      form.append(e('h2','',labels[action]),e('p','panel-note','园区侧辅助记录；不代替企业一般隐患治理与验收。'));
      const add=(key,label,value='',multiline=false)=>{const item=inputField(label,value,multiline);fields[key]=item.input;form.append(item.wrap);return item.input;};
      const choose=(key,label,values,value)=>{const item=selectField(label,values,value);fields[key]=item.input;form.append(item.wrap);};
      if(action==='create'){
        choose('enterpriseId','所属企业',Object.fromEntries(session.enterprises.map(v=>[v,v])));
        add('sourceSystem','来源系统',synthetic?'XNBY-DEMO-MANUAL':'');add('sourceId','来源问题编号',synthetic?'DEMO-'+Date.now():'');add('title','问题名称');add('description','问题描述','',true);
        choose('level','源问题等级',{major:'重大',ordinary:'一般（须有重点关注理由）',unclassified:'未分类'},'major');
        choose('focusFlag','重点关注理由',Object.fromEntries(Object.entries(flags).filter(([key])=>key!=='overdue')),'major');
        const date=add('dueDate','整改期限');date.type='date';date.required=false;
        add('spatialId','关联空间编号（可选）',synthetic?'qa-focus-'+(session.enterprises[0]??'').toLowerCase():'').required=false;
        if(synthetic)form.append(button('填入模拟问题内容',()=>{fields.title.value='模拟新增 · 园区重点问题';fields.description.value='这是独立验收模拟记录，用于检查重点问题登记、跟踪、复查与归档。';},'button secondary'));
      }else if(action==='feedback'){
        for(const [key,label] of [['cause','原因说明'],['measures','整改措施'],['plan','整改计划'],['completion','完成情况'],['improvement','后续改进'],['materialVersion','材料版本说明']])add(key,label,'',true);
        if(synthetic)form.append(button('填入模拟反馈',()=>{for(const [key,input] of Object.entries(fields))input.value='模拟'+({cause:'原因',measures:'措施',plan:'计划',completion:'反馈情况',improvement:'改进',materialVersion:'材料版本v2（无附件）'}[key]);},'button secondary'));
      }else{
        if(action==='track'){choose('method','跟踪方式',methods,'phone');choose('status','关注状态',Object.fromEntries(Object.entries(states).filter(([key])=>!['feedback','archived'].includes(key))),'following');}
        if(action==='review')choose('result','复查结论',conclusions,'continue');
        add('note',action==='reopen'?'重新关注原因':'记录内容','',true);
      }
      const feedback=e('p','focus-status');feedback.setAttribute('role','alert');form.append(feedback);
      const actions=e('div','focus-actions'),save=e('button','button','保存记录');save.type='submit';actions.append(button('取消',()=>dialog.close(),'button secondary'),save);form.append(actions);dialog.append(form);mount.append(dialog);
      dialog.addEventListener('close',()=>dialog.remove());let pendingSignature='',pendingKey='';
      form.onsubmit=async event=>{event.preventDefault();save.disabled=true;busy=true;try{
        let payload=Object.fromEntries(Object.entries(fields).map(([key,input])=>[key,input.value.trim()]));
        if(action==='create'){payload.flags=[payload.focusFlag];delete payload.focusFlag;payload.dueDate||=null;if(!payload.spatialId)delete payload.spatialId;}else payload.revision=issue.revision;
        const signature=JSON.stringify(payload);if(signature!==pendingSignature){pendingSignature=signature;pendingKey=crypto.randomUUID().replaceAll('-','');}
        const result=await client.write(issue?.id??null,action,payload,pendingKey);if(!alive)return;dialog.close();render('保存成功，记录已持久化');
        // The authoritative list/detail are always reread after a write.
      }catch(error){feedback.textContent=errorText(error);}finally{busy=false;save.disabled=false;}};
      dialog.showModal();
    }
    load();
  }
  notify=code=>render(messages[code]??'业务内容已清空，请重新登录');render();
  initialization??=initialize();initialization.then(()=>{if(alive)render();}).catch(error=>{if(alive)render(errorText(error));});
  return ()=>{alive=false;view++;notify=()=>{};for(const dialog of mount.querySelectorAll('dialog'))dialog.close();};
}
