from pathlib import Path
import copy,hashlib,importlib.util,json,os,sys
R=Path('D:/Project/Zhumadian');G=R/'_g/Application';W=R/'work/addsign-history-r180/production-module-r199-r2';J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.dont_write_bytecode=True;sys.path.insert(0,str(G/'tools'));spec=importlib.util.spec_from_file_location('own_history_support_test',W/'original_native_history_release_support.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert not(W/'support-test-result.json').exists();model=J(W/'module-pins.json');old=J(G/'release-manifest.json');release=copy.deepcopy(old);release[m.FIELD]=model['contract'];release['controllerFiles']['tools/serve_original_server_release.py']=model['controllerSHA256'];release['controllerFiles']['tools/original_native_history_release_support.py']=model['helperSHA256']
app=W/'support-fixture-r2/Application';root=app/'UserData/TianjinOriginalPlatform/runs/j1';root.mkdir(parents=True);native=app/'payload/platform/original-platform.jar';native.parent.mkdir(parents=True);os.link(G/'payload/platform/original-platform.jar',native)
for n,pin in {**old['platformAsyncRequestMetadata']['files'],**model['contract']['files']}.items():
 sub=n.split('/run-template/',1)[1];source=W/'own-before-addsign-history.jar'if sub=='own-before-addsign-history.jar'else W/'launcher-classes'/sub.split('persistent-launcher-classes/',1)[1]if n in model['contract']['files']else G/n
 target=root/sub;target.parent.mkdir(parents=True,exist_ok=True);os.link(source,target);assert sha(target)==pin['sha256']
os.link(G/'payload/callback-overlay/20261026-password-identity/own-platform-observation.jar',root/'own-platform-observation.jar')
specimen={'configuration':{'platform':{'context.initializer.classes':'xnby.platform.OriginalAsyncRequestSnapshotRegistration'}},'platformArguments':['-cp','own-original-classpath',m.OLD_MAIN,str(native),str(root)]}
cases=[]
assert m.configure_history(old,specimen)is specimen and m.adapt_history_launch(app,old,root,specimen)is specimen;cases.append('old-release-strict-object-identity-no-op')
configured=m.configure_history(release,specimen);assert m.INITIALIZER not in specimen['configuration']['platform']['context.initializer.classes']and configured['platformArguments']==specimen['platformArguments'];cases.append('initializer-in-memory-copy-private-specimen-unchanged')
prepared={'side':'platform','runtime':str(root),'configuration':configured['configuration'],'arguments':['-Down.platform.root='+str(root),'-Down.platform.source.path='+str(native),'-Down.async.request.snapshot.enabled=true',*specimen['platformArguments']]}
actual=m.adapt_history_launch(app,release,root,prepared);assert actual['arguments'].count(m.NEW_MAIN)==1 and m.OLD_MAIN in prepared['arguments']and len([x for x in actual['arguments']if x.startswith('-Down.workflow.before-addsign.history.enabled=')])==1;cases.append('exact-original-auth-async-source-and-separate-history-launch-pins')
def rejects(label,call):
 try:call()
 except(ValueError,FileNotFoundError):cases.append(label);return
 raise AssertionError('HISTORY_SUPPORT_ACCEPTED_INVALID:'+label)
bad=copy.deepcopy(release);bad[m.FIELD]['revision']='other';rejects('wrong-history-contract',lambda:m.configure_history(bad,specimen))
bad=copy.deepcopy(release);bad.pop('platformAsyncRequestMetadata');rejects('missing-original-async-contract',lambda:m.configure_history(bad,specimen))
bad=copy.deepcopy(specimen);bad['configuration']['platform']['context.initializer.classes']+=','+m.INITIALIZER;rejects('existing-history-initializer-refused',lambda:m.configure_history(release,bad))
bad=copy.deepcopy(specimen);bad['platformArguments'].insert(0,'-Down.workflow.before-addsign.history.enabled=false');rejects('private-history-override-refused',lambda:m.configure_history(release,bad))
bad=copy.deepcopy(prepared);bad['arguments'].insert(0,'-Down.workflow.before-addsign.module.sha256='+'0'*64);rejects('launch-history-override-refused',lambda:m.adapt_history_launch(app,release,root,bad))
bad=copy.deepcopy(prepared);bad['arguments'].insert(0,'-Down.platform.root='+str(root));rejects('duplicate-original-path-property-refused',lambda:m.adapt_history_launch(app,release,root,bad))
bad=copy.deepcopy(prepared);bad['configuration']['platform']['context.initializer.classes']='xnby.platform.OriginalAsyncRequestSnapshotRegistration';rejects('missing-declared-history-initializer-refused',lambda:m.adapt_history_launch(app,release,root,bad))
rejects('outside-owned-platform-run-refused',lambda:m.adapt_history_launch(app,release,app/'j1',prepared))
target=root/'own-before-addsign-history.jar';original=target.read_bytes();target.unlink();target.write_bytes(original+b'own-drift');rejects('tampered-history-archive-refused',lambda:m.adapt_history_launch(app,release,root,prepared));target.unlink();os.link(W/'own-before-addsign-history.jar',target)
up=importlib.util.spec_from_file_location('own_optional_history_updater',W/'original_public_test_update.py');u=importlib.util.module_from_spec(up);up.loader.exec_module(u)
assert u.runtime_pool_declared(old)and u.runtime_pool_declared(release)and u.controller_pin_for(old)==old['controllerFiles']['tools/serve_original_server_release.py']and u.controller_pin_for(release)==model['controllerSHA256'];cases.append('old-and-new-controller-declarations-exact-and-no-global-R23-pin-change')
for n,pin in old['platformAsyncRequestMetadata']['files'].items():assert sha(G/n)==pin['sha256']
proof={'passed':True,'cases':len(cases),'caseNames':cases,'oldAsyncHelperAndArchivesUnchanged':True,'noPrivateConfigurationOrDatabaseRead':True,'codePinsAndNoOpAndOverridesVerified':True,'servicesStartedOrPublicOperated':False}
(W/'support-test-result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
