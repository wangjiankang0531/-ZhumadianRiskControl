from pathlib import Path
V=Path(__file__).resolve().parent
s=(V/'hazard_attachment_observer_r1207.jsfrag').read_text('utf8').replace('hazard-attachment-probe-r1207','hazard-transaction-probe-r1212').replace('hazard_attachment_r1207','hazard_transaction_r1212')
def one(a,b):
 global s
 assert s.count(a)==1,a[:120]
 s=s.replace(a,b)
one('let ownId=null,','let ownId=w.ownId,')
one('mutations={upload:0,create:0,failedEdit:0}', 'mutations={upload:0,repair:0,failedKeep:0,retry:0,failedRemove:0}')
s=s.replace('xnby.own-hazard-attachment-ui-flight.v1','xnby.own-hazard-transaction-ui-flight.v1')
one("need(/^[0-9a-f]{32}$/.test(w.nonce)&&['mainflow','reopen'].includes(w.mode)","need(/^[0-9a-f]{32}$/.test(w.nonce)&&/^[0-9a-f]{32}$/.test(ownId)&&['mainflow','reopen'].includes(w.mode)")
one('ownId:null,uploadUrl:null','ownId,uploadUrl:null')
one('JSON.stringify({upload:1,create:1,failedEdit:1})','JSON.stringify({upload:1,repair:1,failedKeep:1,retry:1,failedRemove:1})')
a=s.index(" if(q.method!=='POST'||!");b=s.index('\n}\nfunction observe',a)
s=s[:a]+''' if(q.method!=='POST'||u.pathname!=='/zhumadian/api/serv/hazardSource/updateById')return false;
 need(typeof q.postData==='string'&&q.postData.length<16384,'BOUNDED_OWN_EDIT');const b=JSON.parse(q.postData),h=b.hazardSource;
 need(h&&h.id===ownId&&h.createdBy===w.expectedUserId&&h.sourceCode===ownCode&&h.sourceName===ownName&&h.location==='Own isolated zone'&&h.riskLevel==='四级'&&Number(h.criticalAmount)===1&&Number(h.currentAmount)===.25&&h.materialType==='Own material v2'&&Array.isArray(b.baseFileList),'EXACT_PREVIOUS_OWN_ROW_ONLY');
 need(['repair','failedKeep','retry','failedRemove'].includes(armed)&&mutations[armed]===0,'EXACT_SINGLE_ATTEMPT_PER_PHASE');
 if(armed==='failedRemove')need(h.status==='12345'&&b.baseFileList.length===0,'ONE_FINAL_FAILED_REMOVAL_DRAFT');
 else{need(b.baseFileList.length===1&&uploadUrl&&b.baseFileList[0].fileUrl===uploadUrl&&b.baseFileList[0].fileName==='own-attachment.png'&&b.baseFileList[0].fileType==='国家安全生产监督管理总局令第40号','OWN_UPLOADED_SINGLE_LINK');need(h.status===(armed==='failedKeep'?'12345':armed==='retry'?'2':'1'),'EXACT_EXPECTED_STATUS');}
 mutations[armed]++;await storeFlight(armed+'-issued-do-not-repeat');return true;
'''+s[b:]
one("if(row.path.endsWith('/updateById')){need(mututionsExpected()&&(row.status>=400||body.code!==0||body.data!==true),'ORIGINAL_EDIT_MUST_FAIL_FOR_OVERLENGTH_STATUS');failedEditReturned=true;writeResponses.push({path:row.path,status:row.status,businessCode:body.code,failed:true});return;}","if(row.path.endsWith('/updateById')){need(['repair','failedKeep','retry','failedRemove'].includes(armed)&&mutations[armed]===1,'EXACT_RESPONSE_PHASE');if(armed.startsWith('failed')){need(row.status>=400||body.code!==0||body.data!==true,'ORIGINAL_SQL_FAILURE_REQUIRED');failedEditReturned=true;writeResponses.push({kind:armed,status:row.status,businessCode:body.code,failed:true});}else{need(row.status===200&&body.code===0&&body.data===true,'NORMAL_ORIGINAL_EDIT_TRUE');saveReturned=true;writeResponses.push({kind:armed,result:true});}return;}")
a=s.index('function mututionsExpected()');b=s.index('async function filteredOwnList',a);s=s[:a]+s[b:]
old=(V/'hazard_crud_r1202/hazard_crud_browser_r1202.mjs').read_text('utf8');a=old.index('async function popupFromNormalOpener()');b=old.index('\nasync function clickPoint',a)
helper=old[a:b].replace('ownHazardDeleteR1202','ownHazardAtomicCheckR1212').replace('return opener;','return {opener,popupTarget:target.targetId};')
s+='\n'+helper
out=V/'hazard_transaction_observer_r1212.jsfrag';assert not out.exists();out.write_text(s,encoding='utf8');print('TRANSACTION_OBSERVER_DERIVED_NO_RUNTIME_STARTED')
