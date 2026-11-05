"""Resume only the completed fixed archive after R1025 selector assertion."""
from pathlib import Path
import ast,json,hashlib
V=Path(__file__).resolve().parent
source=V/'prepare_event_result_transport_r1025.py';target=V/'prepare_event_result_transport_r1026.py'
assert not target.exists()
s=source.read_text('utf8')
s=s.replace('assert not D.exists()',"assert D.is_dir() and DEL.is_dir()\nassert {p.name for p in DEL.iterdir()}=={'Zhumadian_Event_Write_Results_20261105_R48.zip'}\nassert sha(DEL/'Zhumadian_Event_Write_Results_20261105_R48.zip')=='33ffbac4e5ded03570f38340a415cd372727d260a69fb7aad596a2c974e2465d'")
s=s.replace('D.mkdir();DEL.mkdir()','# Reuse only the prior exact, terminal R1025 archive; no rerun or replacement.')
start=s.index("with zipfile.ZipFile(DEL/archive_name,'x')as z:")
end=s.index("text=(OLD/'deploy_home_supervision_r47.py')",start)
body="""with zipfile.ZipFile(DEL/archive_name) as z:
 expected={'web.config'}|{'variants/'+label+'/update-manifest.json'for label in plans}|{'payload/'+n for n in union}
 assert set(z.namelist())==expected and len(z.namelist())==len(expected)
 assert z.read('web.config')==(OLD/'web.config').read_bytes()
 for label in plans:assert z.read('variants/'+label+'/update-manifest.json')==(R2/('update-from-'+label+'.json')).read_bytes()
 for name,pin in union.items():
  raw=z.read('payload/'+name);assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['SHA256']
"""
s=s[:start]+body+s[end:]
old="event=[n for n in J(R2/'candidate/payload-manifest.json')['files']if n.startswith('frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-')]"
new="event=[n for n in J(R2/'candidate/payload-manifest.json')['files']if n.startswith('frontend/emergency_pc/assets/js/wf-addOrEdit.vue_vue_type_script_setup_true_lang-')and all(marker in (dist/n.removeprefix('frontend/emergency_pc/')).read_text('utf8')for marker in ['事件名称','保存未完成','详情未取得'])]"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('prepared-transport-r1025.json','prepared-transport-r1026.json')
ast.parse(s);target.write_text(s,encoding='utf8')
print(json.dumps({'source':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'priorAttemptTerminalExit1':True,'archiveRebuiltOrChanged':False}))
