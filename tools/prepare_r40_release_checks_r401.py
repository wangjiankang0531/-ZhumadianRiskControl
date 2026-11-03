from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103/release-verification'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not D.exists()and J(D.parent/'verified-stage-r399.json')['actualNormalRoleCases']==29
D.mkdir();sources=[]
for label in ['r36','r37']:
 (D/label).mkdir()
 old='verify_plan_unified_full_r36_r339.py'if label=='r36'else'verify_plan_unified_full_r37_r341.py'
 text=(T/old).read_text(encoding='utf-8')
 text=text.replace("S=R/'work/r39-plan-runtime-unified-r1/"+label+"'", "S=R/'work/r40-plan-resource-cancel-r385/"+label+"'")
 text=text.replace('r39-full-preflight-'+label+('-r339'if label=='r36'else'-r341'),'r40-full-preflight-'+label+'-r401')
 text=text.replace('native_plan_unified_candidate_r39_20261103/'+label,'native_plan_resource_cancel_r385_20261103/release-verification/'+label)
 text=text.replace('original_public_test_update_r39_plan_runtime_r337.py','original_public_test_update_r40_resource_cancel_r385.py')
 text=text.replace("assert str(e)=='UNKNOWN_OLD_ENTRY_SCRIPT'","assert str(e)==('FILE_PIN_MISMATCH:'+live if live in old['controllerFiles']else'UNKNOWN_OLD_ENTRY_SCRIPT')")
 text=text.replace('final-R39','final-R40')
 ast.parse(text);out=V/('verify_r40_full_'+label+'_r401.py');assert not out.exists();out.write_text(text,encoding='utf-8')
 sources.append({'kind':'full','variant':label,'file':out.name,'sha256':sha(out)})
 text=(T/('verify_plan_unified_transactions_'+label+'_r342.py')).read_text(encoding='utf-8')
 text=text.replace("O=R/'work/r39-plan-runtime-unified-r1/"+label+"'", "O=R/'work/r40-plan-resource-cancel-r385/"+label+"'")
 text=text.replace('native_plan_unified_candidate_r39_20261103/'+label,'native_plan_resource_cancel_r385_20261103/release-verification/'+label)
 text=text.replace('original_public_test_update_r39_plan_runtime_r337.py','original_public_test_update_r40_resource_cancel_r385.py')
 anchor="put(D/'composition-negative-cases.json',enc(cases))"
 extra="""negative('resource-cancel-actions-changed',lambda p,o,n,q:n[m.R38_FRONTEND_FIELD]['resourceDeleteCancellation'].__setitem__('actions',['foreign']))
negative('resource-cancel-unknown-error-swallowed',lambda p,o,n,q:n[m.R38_FRONTEND_FIELD]['resourceDeleteCancellation'].__setitem__('unknownRejectionsPropagated',False))
negative('resource-cancel-relative-input-metadata-changed',lambda p,o,n,q:n[m.R38_FRONTEND_FIELD]['resourceDeleteCancellation'].__setitem__('relativeToR224OnlyThreeComponentsChanged',False))
negative('resource-cancel-component-source-pin-changed',lambda p,o,n,q:n[m.R38_FRONTEND_FIELD]['resourceDeleteCancellation']['components'].__setitem__(next(iter(n[m.R38_FRONTEND_FIELD]['resourceDeleteCancellation']['components'])),'0'*64))
negative('resource-cancel-frontend-inventory-pin-changed',lambda p,o,n,q:n[m.R38_FRONTEND_FIELD].__setitem__('actualCompiledSourceInventorySHA256','0'*64))
negative('resource-cancel-frontend-manifest-pin-changed',lambda p,o,n,q:n[m.R38_FRONTEND_FIELD]['frontends']['emergency_pc'].__setitem__('manifestSHA256','0'*64))

"""
 assert text.count(anchor)==1;text=text.replace(anchor,extra+anchor,1)
 anchor="def resolve(n,pin):\n candidates="
 extra="resolution=J(R/'work/r40-full-preflight-"+label+"-r401/resolution.json');resolved={**resolution['programs'],**resolution['controls']}\ndef resolve(n,pin):\n known=resolved.get(n)\n if known is not None and known['sha256']==pin:\n  p=Path(known['source']);assert p.is_file()and sha(p.read_bytes())==pin;return p.read_bytes()\n candidates="
 assert text.count(anchor)==1;text=text.replace(anchor,extra,1)
 ast.parse(text);out=V/('verify_r40_transactions_'+label+'_r401.py');assert not out.exists();out.write_text(text,encoding='utf-8')
 sources.append({'kind':'transactions','variant':label,'file':out.name,'sha256':sha(out)})
(D/'prepared-sources-r401.json').write_text(json.dumps({'prepared':True,'sources':sources,'servicesWillNotStart':True,'dataAndAssetsNeverCopied':True},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':True,'drivers':len(sources),'fullProgramsAndFaultRecoveryPending':True}))
