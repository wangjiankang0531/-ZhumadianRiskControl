"""Prepare the previously source-bounded material-only import dialog on WF6; no installation."""
from pathlib import Path
import ast, copy, hashlib, importlib.util, json, shutil, sys
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031'
B=W/'emergency-workflow-source-r6';N=W/'emergency-workflow-source-r7';assert not N.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
assert shutil.disk_usage(W).free>1024**3
for p in [B/'source',*(B/'source').rglob('*')]:assert not p.is_symlink()and not p.lstat().st_file_attributes&0x400
N.mkdir();shutil.copytree(B/'source',N/'source')
spec=importlib.util.spec_from_file_location('own_material_dialog_source',T/'original_material_import_dialog_compat.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sys.path.insert(0,str(T))
root='src/views/emergencyResources/materials/index.vue';dialog='src/components/ImportExcel/index.vue';new=m.ADAPTED
root_bytes,root_receipt=m.transform(m.ROOT,(B/'source'/root).read_bytes())
dialog_bytes,dialog_receipt=m.transform(m.DIALOG,(B/'source'/dialog).read_bytes())
assert isinstance(root_bytes,bytes)and isinstance(dialog_bytes,bytes)
outputs={root:root_bytes,new:dialog_bytes};own=T/'frontend/material-native-import'
for rel,raw in outputs.items():
 p=N/'source'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
 p=own/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(raw)
c=json.loads((B/'source-closure.json').read_bytes());pinned=R/'Application/work/tianjin_native_20261023/emergency_pc'
for rel in [root,dialog]:
 file=pinned/rel;assert sha(file)==m.PINS[rel]
 c['sourceFiles'][rel.removeprefix('src/')]={'source':str(file),'sha256':sha(file),'bytes':file.stat().st_size}
new_file=own/new
c['sourceFiles'][new.removeprefix('src/')]={'source':str(new_file),'sha256':sha(new_file),'bytes':new_file.stat().st_size}
c['runtimeSourceAdaptations'][root]={'baseSourceSHA256':sha(B/'source'/root),'adaptedSHA256':sha(N/'source'/root),
 'onlyMaterialDialogImportChanged':True,'allOtherPageTextPreserved':True}
c['overlayFiles']=sorted(set(c['overlayFiles'])|{new.removeprefix('src/')});c['selectedSourceFiles']=len(c['sourceFiles'])
c['materialImportAdaptations']={rel:{'adaptedSHA256':sha(N/'source'/rel),'source':str(own/rel)}for rel in outputs}
c['sourceRevision']='r7';c['buildPassed']=False;c['actualNormalUserWorkflowUIAccepted']=False
(N/'source-closure.json').write_bytes(enc(c))
before={p.relative_to(B/'source').as_posix():sha(p)for p in(B/'source').rglob('*')if p.is_file()}
after={p.relative_to(N/'source').as_posix():sha(p)for p in(N/'source').rglob('*')if p.is_file()}
assert set(after)-set(before)=={new}and not set(before)-set(after)
assert {n for n in before if before[n]!=after[n]}=={root}
proof={'schema':'xnby.wf7.material-import-source.v1','entireWF6SourceTreeCompared':True,'sourceFilesCompared':len(before),
 'changedFiles':[root],'addedFiles':[new],'globalImportDialogRequestWorkflowsAndOtherPagesUnchanged':True,
 'allWf6NativeApprovalSafeguardsRetained':True,'installed':False,'publicOrManualPreviewChanged':False}
proof['sourceReceipts']=[root_receipt,dialog_receipt]
(N/'material-import-source-proof.json').write_bytes(enc(proof))
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
 p=T/name;s=p.read_text(encoding='utf-8');needle="['r1','r2','r3','r4','r5','r6']";assert s.count(needle)==1
 s=s.replace(needle,"['r1','r2','r3','r4','r5','r6','r7']")
 if p.suffix=='.py':ast.parse(s)
 p.write_text(s,encoding='utf-8',newline='\n')
print(json.dumps(proof,ensure_ascii=False))
