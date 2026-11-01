"""Restore the three original published resource result guards in the full source build."""
from pathlib import Path
import hashlib,importlib.util,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';B=R/'work/user_feedback_20261031';old=B/'emergency-workflow-source-r7';new=B/'emergency-workflow-source-r8';assert not new.exists()
J=lambda p:json.loads(p.read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
def module(name):
 spec=importlib.util.spec_from_file_location(name,T/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
resource=module('original_emergency_resource_result_compat');team=module('original_emergency_team_frontend_compat')
public=B/'published-emergency-frontend-r1';pins=J(public/'source-proof.json');legacy=[]
for name,kind in [('index-BE-bz4zQ.js','materials'),('index-DJ6x5aBw.js','emergencyExperts'),('index-fKZVveaT.js','firstAidTeams')]:
 rel='assets/js/'+name;body=(public/'frontend'/rel).read_bytes();assert sha(body)==pins['files'][rel]['sha256']
 assert '保存未完成，请保留当前内容'.encode()in body
 legacy.append({'kind':kind,'exactR21PublishedFile':rel,'sha256':sha(body),'saveResultGuardNoticePresent':True})
shutil.copytree(old/'source',new/'source',copy_function=os.link)
meta=J(old/'source-closure.json');rows=[]
for kind in ['materials','emergencyExperts','firstAidTeams']:
 rel=resource.relative(kind)if kind!='firstAidTeams'else team.RELATIVE;p=new/'source'/rel
 before=p.read_bytes();updated,proof=resource.transform(kind,before)if kind!='firstAidTeams'else team.transform(before)
 p.unlink();p.write_bytes(updated)
 stored=T/'frontend/emergency-resource-preserved-guards'/rel;stored.parent.mkdir(parents=True,exist_ok=True);stored.write_bytes(updated)
 key=rel.removeprefix('src/');meta['sourceFiles'][key]={'source':str(stored),'sha256':sha(updated),'bytes':len(updated),'overlay':True}
 rows.append({'path':rel,'originalSHA256':sha(before),'adaptedSHA256':sha(updated),'proof':proof})
for rel in ['package.json','vite.config.ts','index.html']:
 assert (new/'source'/rel).is_file()
meta['preservedResourceResultGuards']={'r21PublishedCompiledForms':legacy,'restoredSourceFiles':rows,'originalThreePublishedGuardsMissingFromWF7':True,'onlySuccessfulCodeZeroBooleanTrueNavigates':True}
(new/'source-closure.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
allowed={r['path']for r in rows};diff=[]
for p in (old/'source').rglob('*'):
 if p.is_file():
  rel=p.relative_to(old/'source').as_posix()
  if sha(p.read_bytes())!=sha((new/'source'/rel).read_bytes()):diff.append(rel)
assert set(diff)==allowed
(new/'preserved-resource-guard-source-proof.json').write_text(json.dumps({'exactOldR21CompiledPinsVerified':legacy,'onlyThreeFormSourcesChanged':True,'files':rows,'WF7MaterialImportAndWF6WorkflowSourcesPreserved':True,'actualUIStillPending':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
 p=T/name;s=p.read_text(encoding='utf-8');needle="'r5','r6','r7'";assert needle in s;s=s.replace(needle,"'r5','r6','r7','r8'");p.write_text(s,encoding='utf-8')
print(json.dumps({'sourceRevision':'r8','threePublishedResourceResultGuardsRestored':True,'onlyThreeFormsChanged':True,'sourceClosureFiles':len(meta['sourceFiles']),'wholeBrowserAcceptancePending':True}))
