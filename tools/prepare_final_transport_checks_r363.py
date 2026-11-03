from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;D=R/'Document/Deployment/public_test_unified_plan_r39_20261103'
wrapper=D/'delivery/deploy_unified_plan_r39.py';builder=V/'build_unified_plan_delivery_r351.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda x:(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
assert sha(wrapper)=='a1c9ef7b7428bab943c6bad74d2baa16d5bcfd2d48ce0665dd3bd3a39e38c781'
for p in [wrapper,builder]:
    text=p.read_text(encoding='utf-8');a="    m.apply_update(APP,stage,base['manifestSHA256'])";assert text.count(a)==1
    text=text.replace(a,"    write_scoped_result(root,'deploy-started',base,old,candidate_pool)\n"+a,1)
    a="        m.rollback_latest(APP)\n        raise";assert text.count(a)==1
    text=text.replace(a,"        m.rollback_latest(APP)\n        write_scoped_result(root,'postcheck-failed-rolled-back',base,old,candidate_pool)\n        raise",1);ast.parse(text)
    if p==wrapper:p.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode())
    else:p.write_text(text,encoding='utf-8')
manifest=json.loads((D/'delivery-manifest.json').read_bytes());manifest['files'][wrapper.name]={'bytes':wrapper.stat().st_size,'sha256':sha(wrapper)}
(D/'delivery-manifest.json').write_bytes(enc(manifest));(D/'delivery/delivery-manifest.json').write_bytes(enc(manifest))
fixed={'manifestSHA256':sha(D/'delivery-manifest.json'),'wrapperSHA256':sha(wrapper),'builderSHA256':sha(builder),
       'transportFiles':8,'transportBytes':sum(p.stat().st_size for p in(D/'delivery').iterdir()),'phaseClearedBeforeApplyAndOwnPostcheckRollbackReported':True,'uploadedOrDeployed':False}
(D/'final-transport-input-r363.json').write_bytes(enc(fixed))
source=V/'verify_unified_plan_delivery_r355.py';text=source.read_text(encoding='utf-8')
text=text.replace("refined=J(D/'wrapper-refinement-r352.json')","refined=J(D/'final-transport-input-r363.json')")
text=text.replace('verified-fixed-transport-r355.json','verified-fixed-transport-r364.json')
a="real_validate=ns['validate_archive']";assert text.count(a)==1
b="""transport_root=O/'transport-fixture';transport_root.mkdir()
for file in(D/'delivery').iterdir():os.link(file,transport_root/file.name)
ns['__file__']=str(transport_root/S.name)
"""+a
text=text.replace(a,b,1)
text=text.replace("assert Path(path)==D/'delivery/r39_update_runtime.py'", "assert Path(path)==transport_root/'r39_update_runtime.py'")
a="        orders.append({'variant':base['label'],'invalidLayout':bad"
b="""        if not bad:
            summary=J(transport_root/'r39-scoped-result.json');assert summary['phase']=='preflight-passed'and summary['selectedBase']==base['label']and summary['mysqlMaxConnections']==24 and summary['datasourceCount']==3
            assert not summary['credentialsSessionsBusinessRowsRuntimeUUIDOrRawLogsIncluded']
"""+a
assert text.count(a)==1;text=text.replace(a,b,1)
a="        assert 'FORBIDDEN_REAL_SERVICE'not in events"
b=a+"\n        summary=J(transport_root/'r39-scoped-result.json');assert summary['phase']=={'success':'deploy-complete','failure':'postcheck-failed-rolled-back','drift':'deploy-started'}[postcheck]\n        assert summary['serverLocalGatewayAndIISTLSStaticPassed']==(postcheck=='success')and not summary['externalHTTPSAndLoggedInTimingAccepted']"
assert text.count(a)==1;text=text.replace(a,b,1)
a="assert len(orders)==10";b=a+"""
helper_root=O/'limited-result-helper';helper_root.mkdir();base=next(iter(bases.values()));old=next(iter(bases))
ns['write_scoped_result'](helper_root,'preflight-passed',base,old)
summary_file=helper_root/'r39-scoped-result.json';good=summary_file.read_bytes()
for label,bad in [('foreign-schema',enc({'schema':'foreign','newReleaseSHA256':ns['NEW']})),('foreign-release',enc({'schema':'xnby.r39.scoped-deployment-result.v1','newReleaseSHA256':'0'*64})),('oversized',b'X'*(64*1024+1))]:
    summary_file.write_bytes(bad)
    try:ns['write_scoped_result'](helper_root,'deploy-complete',base,old)
    except ValueError:pass
    else:raise AssertionError('FOREIGN_SUMMARY_OVERWRITTEN:'+label)
    assert summary_file.read_bytes()==bad
summary_file.write_bytes(good)
ns['write_scoped_result'](helper_root,'deploy-started',base,old)
assert J(summary_file)['phase']=='deploy-started'and summary_file.stat().st_size<4096
"""
assert text.count(a)==1;text=text.replace(a,b,1)
a="'cleanTransportBuilderReproducedAll8FilesByteForByte':True"
b="'scopedResultPhaseAndThreeForeignOrOversizeRefusalsPassed':True,"+a
assert text.count(a)==1;text=text.replace(a,b,1);ast.parse(text)
out=V/'verify_unified_plan_delivery_r364.py';assert not out.exists();out.write_text(text,encoding='utf-8')
print(json.dumps({**fixed,'finalVerifierSHA256':sha(out)}))
