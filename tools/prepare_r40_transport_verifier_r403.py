from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).resolve().parent
text=(T/'verify_unified_plan_delivery_r364.py').read_text(encoding='utf-8')
text=text.replace('public_test_unified_plan_r39_20261103','public_test_plan_resources_r40_20261103')
text=text.replace('delivery/deploy_unified_plan_r39.py','delivery/deploy_plan_resources_r40.py')
text=text.replace("O=R/'work/v39'","O=R/'work/v40'")
text=text.replace('final-transport-input-r363.json','preparation-result-r402.json')
text=text.replace('r39_update_runtime.py','r40_update_runtime.py').replace('original_public_test_update_r39_plan_runtime_r337.py','original_public_test_update_r40_resource_cancel_r385.py')
text=text.replace("R/'work/r39-plan-runtime-unified-r1/shared/payload/release-manifest.json'","R/'work/r40-plan-resource-cancel-r385/r36/bundle/payload/release-manifest.json'")
text=text.replace('r39-scoped-result.json','r40-scoped-result.json').replace('xnby.r39.scoped-deployment-result.v1','xnby.r40.scoped-deployment-result.v1')
text=text.replace('build_unified_plan_delivery_r351.py','build_plan_resources_delivery_r402.py')
start=text.index('anchor="(D/\'delivery-manifest.json\').write_bytes(enc(manifest));')
end=text.index("repro=O/'reproduced-delivery'",start)
text=text[:start]+"builder_raw=builder.read_bytes();assert sha(builder)==refined['builderSHA256']\n"+text[end:]
anchor="assert sha(builder)==hashlib.sha256(build.replace('\\n',os.linesep).encode()).hexdigest()"
assert text.count(anchor)==1;text=text.replace(anchor,"assert builder.read_bytes()==builder_raw",1)
text=text.replace('verified-fixed-transport-r364.json','verified-fixed-transport-r403.json')
text=text.replace('archive-cases-r353.json','archive-cases-r403.json').replace('selection-and-recovery-cases-r353.json','selection-and-recovery-cases-r403.json')
text=text.replace('wrapper-order-cases-r353.json','wrapper-order-cases-r403.json').replace('response-cases-r353.json','response-cases-r403.json')
text=text.replace("'priorSameFinalUpdaterTwoActualSixComponentLifecyclesAnd21UIEvidenceRetained':True", "'priorThisR40R37ActualApplyRollbackAndFinal29UIEvidenceRetained':True,'r36ActualThisR40LifecycleNotRepeated':True")
ast.parse(text);out=V/'verify_plan_resources_delivery_r403.py';assert not out.exists();out.write_text(text,encoding='utf-8')
print(json.dumps({'preparedOnly':True,'sourceSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'noRealServicesWillStart':True,'wrapperIdentityLifecycleAndTLSExplicitSpies':True}))
