// Schema is served by the same backend that validates and persists the payload.
export function chinaInput(value) {
 if(!value)return '';
 if(/^\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d)?$/.test(value))return value.slice(0,16);
 const date=new Date(value);if(Number.isNaN(date.getTime()))return value;
 return new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(date).replace(' ','T');
}
export function workSummary(form) {
 const rows=[['作业类型',form.jobType],...Object.entries(form.values).filter(([,v])=>v).map(([k,v])=>[k,k.endsWith('时间')?chinaInput(v).replace('T',' ')+'（北京时间）':v])];
 for(const [role,people] of Object.entries(form.people))rows.push([role,people.length?people.map(p=>Object.values(p).join(' / ')).join('\n'):'未添加']);
 return rows;
}
export function openWorkForm({schema,record=null,el,button,select,dialogBase,closeDialog,api,afterSave}) {
 const d=dialogBase(record?'继续编辑作业草稿':'模拟作业票预约');d.classList.add('work-dialog');
 const form=el('form','work-form'),intro=el('p','muted',schema.policy+' 时间按北京时间填写。');form.append(intro);
 const top=el('div','work-grid'),typeLabel=el('label','','作业类型 *'),type=select('选择作业类型',schema.types.map(t=>t.name),record?.workForm?.jobType||schema.types[0].name),enterpriseLabel=el('label','','所属模拟企业'),enterprise=select('模拟企业',['模拟企业甲','模拟企业乙','模拟企业丙'],record?.enterprise||'模拟企业甲');type.required=true;typeLabel.append(type);enterpriseLabel.append(enterprise);top.append(typeLabel,enterpriseLabel);form.append(top);
 const fieldsRoot=el('section','work-grid'),peopleRoot=el('section','work-people');form.append(el('h3','','基础信息'),fieldsRoot,el('h3','','人员信息'),peopleRoot);
 let inputs={},people={},cached={...record?.workForm?.values},selected=type.value;
 function remember(){for(const [key,n] of Object.entries(inputs))cached[key]=n.value;}
 function renderFields(){
  const model=schema.types.find(t=>t.name===selected);fieldsRoot.replaceChildren();inputs={};
  for(const f of model.fields){const label=el('label',f.kind==='textarea'?'wide':'',f.key+(f.required?' *':''));let n;
   if(f.kind==='select')n=select('请选择',f.options,cached[f.key]||(f.key==='是否为承包商'?'否':''));
   else {n=el(f.kind==='textarea'?'textarea':'input');n.maxLength=f.maxLength;if(f.kind==='datetime'){n.type='datetime-local';n.value=chinaInput(cached[f.key]);}else {if(n.tagName==='INPUT')n.type=f.kind==='positive'?'number':'text';if(f.kind==='positive'){n.min='0';n.step='any';}n.value=cached[f.key]||'';}}
   n.setAttribute('aria-label',f.key);n.required=f.required;label.append(n);inputs[f.key]=n;fieldsRoot.append(label);
  }
 }
 function renderPeople(){peopleRoot.replaceChildren();const required=schema.requiredRoles[selected]||schema.defaultRequiredRoles;
  for(const role of schema.roles){const section=el('section','people-section'),head=el('div','people-heading');head.append(el('b','',role+(required.includes(role)?' *':'')),button('＋ 添加模拟人员',()=>{if(people[role].length>=schema.maxPeoplePerRole)return;people[role].push(Object.fromEntries(schema.personColumns.map(k=>[k,k==='是否承包商'?'否':''])));renderPeople();},'button secondary'));section.append(head);const wrap=el('div','table-wrap'),table=el('table'),tr=el('tr');for(const k of [...schema.personColumns,'操作'])tr.append(el('th','',k));const thead=el('thead');thead.append(tr);table.append(thead);const body=el('tbody');people[role].forEach((person,index)=>{const row=el('tr');for(const k of schema.personColumns){const td=el('td'),input=k==='是否承包商'?select('请选择',['否','是'],person[k]):el('input');input.value=person[k];input.maxLength=128;input.setAttribute('aria-label',`${role} ${index+1} ${k}`);input.required=true;input.addEventListener('input',()=>person[k]=input.value);input.addEventListener('change',()=>person[k]=input.value);td.append(input);row.append(td);}const action=el('td');action.append(button('移除',()=>{people[role].splice(index,1);renderPeople();},'text-button'));row.append(action);body.append(row);});table.append(body);wrap.append(table);section.append(wrap);peopleRoot.append(section);}
 }
 for(const role of schema.roles)people[role]=(record?.workForm?.people[role]||[]).map(p=>({...p}));
 type.onchange=()=>{if(!type.value){type.value=selected;return;}remember();selected=type.value;renderFields();renderPeople();};renderFields();renderPeople();
 const noteLabel=el('label','','备注（合成测试内容）'),note=el('textarea');note.maxLength=2000;note.value=record?.note||'';noteLabel.append(note);form.append(noteLabel);
 const error=el('p','error');error.setAttribute('role','alert');form.append(error);const actions=el('div','work-actions');
 const draft=button('暂存草稿',()=>save('draft'),'button secondary'),submit=el('button','button','模拟提交'),cancel=button('取消',()=>closeDialog(d),'button secondary');submit.type='submit';actions.append(draft,submit,cancel);form.append(actions);
 async function save(action){error.textContent='';if(!type.value){error.textContent='请选择作业类型';return;}if(action==='submit'&&!form.reportValidity())return;
  draft.disabled=true;submit.disabled=true;type.disabled=true;
  try{const values=Object.fromEntries(Object.entries(inputs).map(([key,n])=>[key,n.type==='datetime-local'&&n.value?n.value+':00+08:00':n.value]));const value=await api('work-reservation',{form:{schema:schema.schema,jobType:selected,values,people},enterprise:enterprise.value,note:note.value,action,identity:record?.id||null,revision:record?.revision??null});closeDialog(d);await afterSave(value.record.id);}catch(e){error.textContent=e.message;draft.disabled=false;submit.disabled=false;type.disabled=false;}}
 form.onsubmit=e=>{e.preventDefault();save('submit');};d.append(form);d.showModal();
}
