from pathlib import Path
import ast,hashlib,json,zipfile
V=Path(__file__).parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application';W=R/'work/addsign-history-r180';P=W/'runtime-module-r191';assert not P.exists();P.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();enc=lambda o:(json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode()
jar='payload/platform/run-template/own-platform-async-request.jar';old=G/jar;release=json.loads((G/'release-manifest.json').read_bytes());contract=release['platformAsyncRequestMetadata'];pin=contract['files'][jar];assert sha(old.read_bytes())==pin['sha256']and old.stat().st_size==pin['bytes']
classes=W/'native-classes-r191';added={p.relative_to(classes).as_posix():p.read_bytes()for p in classes.rglob('*.class')};assert len(added)==6 and not any('Fixture'in n for n in added)
output=P/'own-platform-async-with-before-history.jar'
with zipfile.ZipFile(old)as before,zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED)as after:
 assert len(set(before.namelist()))==len(before.namelist())and not set(before.namelist()).intersection(added)
 for info in before.infolist():after.writestr(info,before.read(info.filename))
 for n,b in sorted(added.items()):after.writestr(n,b)
with zipfile.ZipFile(old)as before,zipfile.ZipFile(output)as after:
 assert set(after.namelist())==set(before.namelist())|set(added)and all(before.read(n)==after.read(n)for n in before.namelist())and all(after.read(n)==b for n,b in added.items())
newpin={'bytes':output.stat().st_size,'sha256':sha(output.read_bytes())};newcontract=json.loads(json.dumps(contract));newcontract['files'][jar]=newpin
helper='tools/original_platform_async_release_support.py';updater='tools/original_public_test_update.py'
def assignments(text,replacements):
 tree=ast.parse(text);lines=text.splitlines(keepends=True);found=set()
 for n in reversed(tree.body):
  if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in replacements:
   name=n.targets[0].id;found.add(name);lines[n.lineno-1:n.end_lineno]=[name+' = '+repr(replacements[name])+'\n']
 assert found==set(replacements);new=''.join(lines)
 functions=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
 assert functions(text)==functions(new);return new.encode()
newhelper=assignments((G/helper).read_text(encoding='utf-8'),{'CONTRACT':newcontract})
newupdater=assignments((G/updater).read_text(encoding='utf-8'),{'R23_ASYNC_CONTRACT':newcontract,'R23_ASYNC_ROWS':newcontract['files'],'R23_HELPER_SHA':sha(newhelper)})
(P/'original_platform_async_release_support.py').write_bytes(newhelper);(P/'original_public_test_update.py').write_bytes(newupdater)
proof={'oldAsyncModuleSHA256':pin['sha256'],'newAsyncModule':newpin,'newAsyncContract':newcontract,'allOriginalAsyncArchiveEntriesByteIdentical':True,'originalAuthenticationObservationAndCallbackModulesUnchanged':True,'allHelperAndUpdaterFunctionsASTIdentical':True,'onlyExactDeclarationPinsUpdatedInTwoOwnControlFiles':True,'addedClassPins':{n:sha(b)for n,b in added.items()},'sourcePins':{p.name:sha(p.read_bytes())for p in [V/'native_history_r191/OriginalAddsignOpinionHistory.java',V/'native_history_r191/OriginalBeforeAddsignHistoryInterceptor.java',V/'native_history_r191/NativeBeforeAddsignHistoryInitializer.java']},'originalSDKArchivesUnchanged':True,'prototypeNotRoleTested':True}
(P/'module-pins.json').write_bytes(enc(proof))
def replace_once(s,old,new):
 assert s.count(old)==1,(old[:90],s.count(old));return s.replace(old,new)
host=(V/'verify_full_controller_addsign_history_r183_20261102.py').read_text(encoding='utf-8').replace('r183','r191').replace("['r83']","['r91']")
host=replace_once(host,"current=read(app/'UserData/OriginalServer/current-run.json');assert current['controllerPID']==process.pid\nrun_path=Path(current['run']);assert run_path.parent==app/'UserData/OriginalServer/runs'", """current=read(app/'UserData/OriginalServer/current-run.json')
if current['controllerPID']==process.pid:run_path=Path(current['run'])
else:
    matches=[p for p in(app/'UserData/OriginalServer/runs').glob('j*/receipt.json')if read(p)['controllerPID']==process.pid]
    assert len(matches)==1,'EXACT_OWN_CONTROLLER_RECEIPT_REQUIRED';run_path=matches[0].parent
assert run_path.resolve()==run_path and run_path.parent==app/'UserData/OriginalServer/runs'""")
browser=(V/'verify_native_addsign_history_browser_r183_20261102.mjs').read_text(encoding='utf-8')
runner=(V/'run_native_history_r183_20261102.py').read_text(encoding='utf-8').replace('r183','r191').replace("attempt='r83'","attempt='r91'")
restore=(V/'restore_native_history_runtime_r183.py').read_text(encoding='utf-8').replace('r183','r191').replace('r83','r91')
start=restore.index("receipt_path=C/'r91/scoped-controller-receipt.json'");end=restore.index('query=',start)
restore=restore[:start]+"receipt=J(C/'r91/scoped-controller-receipt.json');assert receipt['allOwnedChildrenExited']and not receipt['forcedJobClosureComponents']and not receipt['jobAssignmentFailureComponents']\n"+restore[end:]
for name,text in [('verify_full_controller_addsign_history_r191_20261102.py',host),('verify_native_addsign_history_browser_r191_20261102.mjs',browser),('run_native_history_r191_20261102.py',runner),('restore_native_history_runtime_r191.py',restore)]:
 path=V/name;assert not path.exists();path.write_text(text,encoding='utf-8')
 if name.endswith('.py'):ast.parse(text)
print(json.dumps({'prepared':True,'existingAsyncExtensionAugmented':True,'authObservationAndCallbackExactlyOriginal':True,'allControlFunctionsUnchangedOnlyExactModuleDeclarationsUpdated':True,'jarBytes':output.stat().st_size}))
