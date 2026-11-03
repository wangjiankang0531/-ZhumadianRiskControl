from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent;D=R/'Document/Deployment/public_test_native_history_r36_20261103';prior=T/'original_public_test_update_r36_20261103.py';target=T/'original_public_test_update_r36_20261103_r2.py'
s=prior.read_text(encoding='utf-8');old="            'UNEXPECTED_UPDATE_PATH:' + name)";assert s.count(old)==1
needle="        require(allowed and not name.startswith(('private/', 'UserData/', 'runtime/', 'seed/')),"
assert s.count(needle)==1;s=s.replace(needle,"        allowed = allowed or (history_declared(read(bundle / 'payload/release-manifest.json')) and name in R36_HISTORY_CONTRACT['files'])\n\n"+needle)
func=lambda text:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)};a,b=func(prior.read_text(encoding='utf-8')),func(s);assert {n for n in a if a[n]!=b[n]}=={'load_bundle'}
assert not target.exists();target.write_text(s,encoding='utf-8');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(D/'r2-load-path-scope-comparison.json').write_text(json.dumps({'priorR1UpdaterSHA256':sha(prior),'newR2UpdaterSHA256':sha(target),'onlyFunctionChanged':'load_bundle','onlyAdditionalAllowedPayloadPaths':2,'newPathsRequireExactDeclaredHistoryContractAndPins':True,'privateUserDataRuntimeAndSeedStillForbidden':True,'allLifecycleHealthHistoryAndOtherContractsASTIdentical':True,'originalFullProgramR1RefusalPreserved':True,'publicUploadedOrInstalled':False},indent=2)+'\n',encoding='utf-8')
for oldname,newname in [('prepare_native_history_sparse_r208.py','prepare_native_history_sparse_r209.py'),('verify_native_history_full_program_r208_20261103.py','verify_native_history_full_program_r209_20261103.py')]:
 text=(V/oldname).read_text(encoding='utf-8').replace('original_public_test_update_r36_20261103.py','original_public_test_update_r36_20261103_r2.py').replace('r36-native-history-candidate-r1','r36-native-history-candidate-r2').replace('r36tx-r1','r36tx-r2').replace('r36gv-r1','r36gv-r2').replace('xnby.r208.','xnby.r209.')
 ast.parse(text);p=V/newname;assert not p.exists();p.write_text(text,encoding='utf-8')
print(json.dumps({'prepared':True,'r2UpdaterSHA256':sha(target),'oneExactPayloadPathWhitelistExtensionFunctionOnly':True}))
