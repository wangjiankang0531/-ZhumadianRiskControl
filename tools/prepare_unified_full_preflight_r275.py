from pathlib import Path
import ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;T=R/'Application/tools'
s=(T/'verify_static_performance_full_program_r236.py').read_text(encoding='utf-8')
s=s.replace('r37-static-performance-r1','r38-unified-original-mappers-r1').replace('r37-static-full-preflight-r236','r38-unified-full-preflight-r275').replace('public_test_static_performance_r37_20261103','public_test_unified_mappers_r38_20261103').replace('original_public_test_update_r37_static_20261103.py','original_public_test_update_r38_unified_20261103.py')
a="q['files'][private]={'bytes':len(fake),'sha256':digest(fake)};qraw=enc(q);old['payloadManifestSHA256']=digest(qraw);new['payloadManifestSHA256']=digest(qraw);oldraw=enc(old);newraw=enc(new)"
b="q['files'][private]={'bytes':len(fake),'sha256':digest(fake)};qraw=enc(q);old['payloadManifestSHA256']=digest(qraw)\nnewq=J(S/'bundle/payload/payload-manifest.json');newq['files'][private]={'bytes':len(fake),'sha256':digest(fake)};newqraw=enc(newq);new['payloadManifestSHA256']=digest(newqraw);oldraw=enc(old);newraw=enc(new)";assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('newPayloadManifestSHA256=digest(qraw)','newPayloadManifestSHA256=digest(newqraw)')
a="plan['files']['payload-manifest.json']={'bytes':len(qraw),'SHA256':digest(qraw)}";assert s.count(a)==1;s=s.replace(a,"plan['files']['payload-manifest.json']={'bytes':len(newqraw),'SHA256':digest(newqraw)}")
s=s.replace("mutable=set(plan['files']);","mutable=set(plan['files'])|set(plan['removedFrontendFiles']);")
s=s.replace("else qraw if n=='payload-manifest.json'","else newqraw if n=='payload-manifest.json'")
s=s.replace('len(changes)==6',"len(changes)==len(plan['files'])+len(plan['removedFrontendFiles'])")
s=s.replace('final-R37-six-path-load_bundle','final-R38-unified-path-load_bundle').replace('all-R36-programs-and-final-R37','all-R36-programs-and-final-R38')
s=s.replace("'candidateInstallPaths':6,","'candidateInstallPaths':len(plan['files']),'obsoleteEmergencyFrontendRemovals':len(plan['removedFrontendFiles']),'allChangePaths':len(changes),")
s=s.replace("'publicWrapperStillRequiresExactR36SHA':True","'publicDeliveryWrapperNotPreparedYet':True")
ast.parse(s);p=V/'verify_unified_full_program_r275.py';assert not p.exists();p.write_text(s,encoding='utf-8');print('R38_COMPLETE_PROGRAM_PRECHECK_PREPARED')
