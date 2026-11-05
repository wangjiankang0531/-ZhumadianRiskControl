from pathlib import Path
import ast,hashlib,json,subprocess
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
W=R/'work/event-result-full-r996';D=R/'Document/Deployment/event_result_full_r996_20261105'
assert not W.exists()and not D.exists()
old=(T/'run_canonical_compatible_build_r841.py').read_text('utf8')
s=old.replace('canonical_bootstrap_compatible_r841_20261104','event_result_full_r996_20261105').replace('work/canonical-bootstrap-compatible-r841','work/event-result-full-r996')
s=s.replace('build_canonical_compatible_bootstrap_r841.mjs','build_event_result_bootstrap_r996.mjs')
s=s.replace('from original_authenticated_installer_r817 import authenticated_installer_override,GLOBAL,GUARD,EXTRA','from original_authenticated_installer_r817 import authenticated_installer_override,GLOBAL,GUARD,EXTRA\nfrom original_event_form_result_overlay_r996 import event_form_result_override,EVENT_REL')
s=s.replace('authenticated_installer_override(P)as lazy):','authenticated_installer_override(P)as lazy,event_form_result_override(P)as eventguard):')
s=s.replace("expected=set(J(D/'prepared-candidate-r481.json')['candidatePins'])|{GLOBAL,GUARD,EXTRA};assert changed==expected and len(changed)==7", "expected=set(J(D/'prepared-candidate-r481.json')['candidatePins'])|{GLOBAL,GUARD,EXTRA,EVENT_REL};assert changed==expected and len(changed)==8\n                actualR841=J(R/'work/canonical-bootstrap-compatible-r841/actual-compiled-source-files.json')\n                assert {n for n in set(actualR841)|set(actual)if actualR841.get(n)!=actual.get(n)}=={EVENT_REL},'ONLY_EVENT_FORM_DIFF_FROM_ACTUAL_R841_COMPILER_INPUTS'")
anchor="assert (hashlib.sha256(raw).hexdigest()==lazy['files'][n]['after'] if n in [GLOBAL,GUARD,EXTRA] else {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}==J(D/'prepared-candidate-r481.json')['candidatePins'][n])"
replacement="assert (hashlib.sha256(raw).hexdigest()==eventguard['adaptedSHA256'] if n==EVENT_REL else hashlib.sha256(raw).hexdigest()==lazy['files'][n]['after'] if n in [GLOBAL,GUARD,EXTRA] else {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}==J(D/'prepared-candidate-r481.json')['candidatePins'][n])"
assert s.count(anchor)==1;s=s.replace(anchor,replacement)
s=s.replace('lazy[\'sourceRestored\']])','lazy[\'sourceRestored\'],eventguard[\'sourceRestored\']])')
# The original runner uses originalSourcesRestored for lazy; extend that exact check.
s=s.replace("lazy['originalSourcesRestored']])","lazy['originalSourcesRestored'],eventguard['sourceRestored']])")
s=s.replace('len(changed)==7','len(changed)==8')
s=s.replace("'tenOverrideLayersRestored':restored","'elevenOverrideLayersRestored':restored,'oneEventGuardDifferenceFromActualR841Inputs':True")
s=s.replace('verified-full-build-r841.json','verified-full-build-r996.json')
assert 'eventguard[' in s and 'ONLY_EVENT_FORM_DIFF_FROM_ACTUAL_R841_COMPILER_INPUTS'in s
ast.parse(s);p=V/'run_event_result_full_build_r996.py';assert not p.exists();p.write_text(s,encoding='utf8')
node=(T/'build_canonical_compatible_full_r841.mjs').read_text('utf8').replace('work/canonical-bootstrap-compatible-r841','work/event-result-full-r996')
p=V/'build_event_result_full_r996.mjs';assert not p.exists();p.write_text(node,encoding='utf8')
boot=(T/'build_canonical_compatible_bootstrap_r841.mjs').read_text('utf8').replace('build_canonical_compatible_full_r841.mjs','build_event_result_full_r996.mjs')
p=V/'build_event_result_bootstrap_r996.mjs';assert not p.exists();p.write_text(boot,encoding='utf8')
for p in [V/'build_event_result_full_r996.mjs',V/'build_event_result_bootstrap_r996.mjs']:
 r=subprocess.run(['node','--check',str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0
assert 'eventguard' in [line for line in s.splitlines()if 'assert all(['in line][0],'EVENT_OVERLAY_RESTORATION_MUST_BE_REQUIRED'
D.mkdir();files=[V/'run_event_result_full_build_r996.py',V/'build_event_result_full_r996.mjs',V/'build_event_result_bootstrap_r996.mjs',V/'original_event_form_result_overlay_r996.py',T/'original_event_creation_frontend_compat.py']
(D/'prepared-build-source-r996.json').write_text(json.dumps({'preparedOnly':True,'actualBuildOrProductAcceptance':False,'onlyOneActualCompilerInputMayDifferFromR841':True,'files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}},indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':True,'existingTenLayersRetainedPlusEventGuard':True,'oneActualCompilerInputDifferenceRequired':True,'actualBuildAccepted':False}))
