"""Inventory the current R22 source dependency closure against the existing public branch."""
from pathlib import Path
import ast,json,hashlib
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools';D=R/'Document/Deployment/public_test_risk_r22_20261101';S=R/'work/user_feedback_20261031/r22-risk-candidate-r3';base=json.loads((D/'public-git-base-app.json').read_bytes());known={x['path']:x['sha']for x in base['files']};blob=lambda b:hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
alias={'tools/original_server_release_parameters.py':S/'public-control/tools/original_server_release_parameters.py','tools/serve_original_server_release.py':S/'public-control/tools/serve_original_server_release.py','tools/original_public_test_update.py':T/'original_public_test_update_r22_20261101.py'}
roots=['build_risk_frontend_r22_r2_20261101.py','verify_risk_r22_r2_compiled_graph_20261101.py','verify_risk_r22_login_contract_20261101.py','prepare_risk_r22_r3_candidate_stage_20261101.py','build_native_business_session_r2_20261101.py','verify_public_risk_session_portal_r22_20261101.py','bootstrap_public_risk_session_portal_r22_20261101.py','original_public_risk_portal_chain_r22_20261101.py','original_public_test_update_r22_20261101.py','verify_r22_update_guard_20261101.py','build_public_risk_r22_20261101.py','verify_public_risk_r22_package_20261101.py','verify_published_font_chain_r22_20261101.py','verify_actual_empty_template_compatibility_20261101.py']
selected={};edges={};queue=['tools/'+n for n in roots]+list(alias)
while queue:
 rel=queue.pop()
 if rel in selected:continue
 p=alias.get(rel,A/rel);assert p.is_file(),p;selected[rel]=p
 if p.suffix!='.py':continue
 tree=ast.parse(p.read_text(encoding='utf-8-sig'));dependencies=set()
 for node in ast.walk(tree):
  names=[x.name.split('.')[0]for x in node.names]if isinstance(node,ast.Import)else[node.module.split('.')[0]]if isinstance(node,ast.ImportFrom)and node.module else[]
  for n in names:
   target='tools/'+n+'.py'
   if (T/(n+'.py')).is_file()or target in alias:dependencies.add(target)
 edges[rel]=sorted(dependencies);queue.extend(dependencies)
extra=[T/'verify_compiled_public_risk_portal_r22_20261101.mjs',T/'cleanup_public_risk_session_portal_r22_20261101.ps1',T/'risk_r22_transport.py.in']
pins=json.loads((R/'work/event_delivery_consistency_20261030/full-business-main-r101/source-pins.json').read_bytes())
for path in pins:
 p=Path(path)
 if p.is_relative_to(A):extra.append(p)
 else:assert p==alias['tools/original_server_release_parameters.py']
for folder in ['risk_unit_candidate_r3','risk_import_controller_candidate_r2','native_business_session_r2','native_business_session_fixture_r2','public_published_font_fixture_r1','empty_template_download_r1']:extra.extend((T/'java'/folder).glob('*.java'))
for p in extra:selected[p.relative_to(A).as_posix()]=p
for name in ['ECharts.vue','Chart3.vue','event-report-layout.ts','TaskList.vue','Statistics.vue']:selected['tools/frontend/workplace/'+name]=T/'frontend/workplace'/name
rows=[]
for rel,p in sorted(selected.items()):
 raw=p.read_bytes();current=blob(raw)
 if known.get(rel)!=current:rows.append({'path':rel,'source':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'gitBlobSHA1':current,'publicBaseBlobSHA1':known.get(rel)})
result={'schema':'xnby.r22.public-source-closure-draft.v1','base':{k:base[k]for k in ['repo','branch','commit','treeSHA']},'selectedRoots':roots,'selectedSourceFiles':len(selected),'pythonImportEdges':edges,'differentFromPublicFiles':rows,'differentSourceBytes':sum(x['bytes']for x in rows),'aliasesExplicitlySelectActualPublishedControlsAndR22Updater':{n:str(p)for n,p in alias.items()},'fixedOrApproved':False};(D/'public-source-closure-draft.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'selectedSourceFiles':len(selected),'differentFromPublicFiles':len(rows),'differentSourceBytes':result['differentSourceBytes']}));print(json.dumps([x['path']for x in rows]))
