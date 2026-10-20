import {referenceApiURL} from './reference-deployment.js';
export function materialLink(el,identity,version,material,reviewRevision=null){
 const query=new URLSearchParams({id:identity,version:String(version),materialId:material.material_id});if(reviewRevision!==null)query.set('reviewRevision',String(reviewRevision));
 const a=el('a','plan-material-download',material.name+' · '+Math.ceil(material.bytes/1024)+' KB');a.href=referenceApiURL('plan-material?'+query,location.href);return a;
}
export function renderPlanMaterials(ctx,body,dialog){
 const {el,button,api,afterSave,closeDialog,record,plan,version,schema}=ctx;
 const section=el('section','plan-materials');section.append(el('h3','','预案附件'));const editable=version.version===plan.currentVersion&&version.status==='draft';
 if(!version.materials.length)section.append(el('p','muted','此版本暂无附件。'));
 for(const material of version.materials){const row=el('div','plan-material-row'),copy=el('div');copy.append(materialLink(el,record.id,version.version,material),el('small','muted',material.description));row.append(copy);
  if(editable){const remove=button('从草稿移除',async()=>{remove.disabled=true;try{await api('plan-material-remove',{identity:record.id,revision:record.revision,materialId:material.material_id});closeDialog(dialog);await afterSave(record.id);}catch(error){row.append(el('p','error',error.message));remove.disabled=false;}},'text-button');row.append(remove);}section.append(row);}
 if(editable){const form=el('form','plan-material-upload'),file=el('input'),label=el('label','','选择附件'),descriptionLabel=el('label','','附件说明（模拟）'),description=el('input');file.type='file';file.accept='.pdf,.png,.jpg,.jpeg';file.required=true;file.setAttribute('aria-label','选择预案附件');label.append(file);description.required=true;description.maxLength=2000;description.setAttribute('aria-label','附件说明（模拟）');descriptionLabel.append(description);const submit=el('button','button secondary','上传到当前草稿');submit.type='submit';const errors=el('div');form.append(el('p','muted','支持 PDF、PNG、JPEG，每份不超过2MiB，每版本最多8份。移除只解除草稿关联，已留存的评审与历史附件继续可查。'),label,descriptionLabel,submit,errors);
  form.onsubmit=async event=>{event.preventDefault();errors.replaceChildren();submit.disabled=true;try{const value=file.files[0];if(!value||value.size>schema.materialPolicy.maxBytes||!value.size)throw Error('请选择1字节至2MiB的附件');const ext=value.name.split('.').pop().toLowerCase(),mediaType={pdf:'application/pdf',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg'}[ext];if(!mediaType)throw Error('仅支持PDF、PNG、JPEG');const bytes=new Uint8Array(await value.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=32768)binary+=String.fromCharCode(...bytes.subarray(i,i+32768));await api('plan-material',{identity:record.id,revision:record.revision,name:value.name,mediaType,base64Data:btoa(binary),description:description.value});closeDialog(dialog);await afterSave(record.id);}catch(error){const p=el('p','error',error.message);p.setAttribute('role','alert');errors.append(p);submit.disabled=false;}};
  section.append(form);
 }else section.append(el('p','muted','附件随此版本留存；如需调整，请先进入编制或修订草稿。'));
 body.append(section);
}
