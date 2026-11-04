"""Observe completed picker responses before judging their contents; retain R884 failure."""
from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;S=V/'event_picker_r884';D=V/'event_picker_r885';R=Path('D:/Project/Zhumadian')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not D.exists();pins=json.loads((S/'event-picker-source-pins-r884.json').read_bytes())['files'];assert all(sha(Path(n))==pin for n,pin in pins.items())
 old=json.loads((R/'work/ep884/verified-event-picker-r884.json').read_bytes());ui=json.loads((R/'work/event-picker-browser-r884/result.json').read_bytes())
 assert not old['passed'] and old['codeRestored'] and old['privateConfigurationUnchanged'] and old['originalCurrentPointerRestored']
 assert ui['failure']=='EXPECTED_OWN_CONFIRMED_EVENT_NOT_IN_INITIAL_PICKER' and not any(r['endpoint'].endswith('/eventInfo/getPage')for r in ui['requests'])
 assert ui['taskSaveRequests']==ui['researchRequests']==0 and json.loads((R/'work/event-picker-browser-r884/browser-terminal.json').read_bytes())['normalBrowserClosed']
 D.mkdir();files=[]
 for name in ['event_picker_browser_r884.mjs','event_picker_probe_r884.py','run_event_picker_full_r884.py']:
  s=(S/name).read_text('utf8').replace('r884','r885')
  if name.endswith('.mjs'):
   a=" const initialOwnPresent=eventRows.some(r=>r.id===w.eventId);\n if(!initialOwnPresent)throw Error('EXPECTED_OWN_CONFIRMED_EVENT_NOT_IN_INITIAL_PICKER');"
   assert s.count(a)==1;s=s.replace(a," await until(()=>requests.some(r=>r.endpoint.endsWith('/eventInfo/getPage')&&r.httpStatus===200&&r.businessCode===0));\n const initialOwnPresent=eventRows.some(r=>r.id===w.eventId);")
   a="  await clickButton('搜索',true);await until(()=>eventPageCount>before);"
   assert s.count(a)==1;s=s.replace(a,"  const responseStart=requests.length;await clickButton('搜索',true);await until(()=>requests.slice(responseStart).some(r=>r.endpoint.endsWith('/eventInfo/getPage')));")
   a="  const value=await response.json();return{httpStatus:response.status,businessCode:value.code,ownEventPresent:Array.isArray(value.data?.records)&&value.data.records.some(r=>r.id===w.eventId),rows:Array.isArray(value.data?.records)?value.data.records.length:null};"
   assert s.count(a)==1;s=s.replace(a,"  let value;try{value=await response.json()}catch{return{httpStatus:response.status,nonJSON:true,ownEventPresent:null,rows:null}};return{httpStatus:response.status,businessCode:value.code,ownEventPresent:Array.isArray(value.data?.records)&&value.data.records.some(r=>r.id===w.eventId),rows:Array.isArray(value.data?.records)?value.data.records.length:null};")
  if name.startswith('run_'):
   s=s.replace("prior=J(R/'work/ep883/verified-event-picker-r883.json')","prior=J(R/'work/ep884/verified-event-picker-r884.json')").replace("Z=R/'work/ep884'","Z=R/'work/ep885'")
  q=D/name.replace('r884','r885');q.write_text(s,encoding='utf8');files.append(q)
  if q.suffix=='.py':ast.parse(s)
  else:assert subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(q)],capture_output=True).returncode==0
 (D/'event-picker-source-pins-r885.json').write_text(json.dumps({'files':{str(p):sha(p)for p in files}},indent=2)+'\n',encoding='utf8')
 (D/'r884-observation-refusal.json').write_text(json.dumps({'reason':'Probe examined default empty array before any picker response completed; source assertion was premature','priorBusinessMutations':0,'priorServicesAndCodeConfigPointerRestored':True,'newProbeAwaitsCompletedNativeResponseAndRecordsEmptyResultAsEvidenceRatherThanBusinessSuccess':True})+'\n',encoding='utf8')
 print('R885_OBSERVATION_CORRELATION_FIXED')
if __name__=='__main__':main()
