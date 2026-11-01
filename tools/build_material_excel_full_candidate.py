"""Compile the existing source-bounded material import repair; never install or start services."""
from pathlib import Path
import hashlib, importlib.util, json, os, subprocess, sys, zipfile
sys.dont_write_bytecode=True
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';A=R/'_f/Application'
out=R/'work/event_delivery_consistency_20261030/full-controller-r128/material-excel-candidate-r1'
assert not out.exists();out.mkdir();(out/'classes').mkdir();(out/'tmp').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('material_import_source',T/'original_material_excel_import_compat.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
origin=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java'/m.REL
raw,receipt=m.transform(origin.read_bytes());source=out/'src'/m.REL;source.parent.mkdir(parents=True);source.write_bytes(raw)
metadata=json.loads((R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json').read_bytes())
jars=[]
for path in metadata['classpath'].split(';'):
 name=Path(path).name;target=A/'payload/business'/(name if name in ['application.jar','process-boundary.jar']else'lib/'+name)
 assert target.is_file();jars.append(str(target))
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
env.update(TEMP=str(out/'tmp'),TMP=str(out/'tmp'))
java=A/'runtime/jdk17/bin';helper=T/'java/OriginalMaterialExcelImport.java'
result=subprocess.run([str(java/'javac.exe'),'-J-Xmx256m','--release','17','-parameters','-g','-encoding','UTF-8','-proc:none','-cp',';'.join(jars),'-d',str(out/'classes'),str(source),str(helper)],capture_output=True,env=env,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
(out/'compile.private.log').write_bytes(result.stdout+result.stderr)
assert result.returncode==0,'OWN_MATERIAL_IMPORT_COMPILE_FAILED'
rel='com/iemp/endanger/server/materials/controller/MaterialsController.class'
base=out/'original';p=base/rel;p.parent.mkdir(parents=True)
with zipfile.ZipFile(A/'payload/business/application.jar')as z:p.write_bytes(z.read(rel))
descriptors=[]
for root in [base,out/'classes']:
 r=subprocess.run([str(java/'javap.exe'),'-p','-s','-classpath',str(root),'com.iemp.endanger.server.materials.controller.MaterialsController'],capture_output=True,env=env,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
 assert r.returncode==0
 lines=r.stdout.decode('utf-8').splitlines();public=[]
 for i,line in enumerate(lines):
  if line.strip().startswith('public ')and '('in line:public.append([line.strip(),lines[i+1].strip()])
 descriptors.append(public)
assert descriptors[0]==descriptors[1],'ORIGINAL_PUBLIC_CONTROLLER_ABI_CHANGED'
classes={p.relative_to(out/'classes').as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted((out/'classes').rglob('*.class'))}
assert rel in classes and any(n.startswith('xnby/replica/OriginalMaterialExcelImport')for n in classes)
assert all(n==rel or n.startswith('xnby/replica/OriginalMaterialExcelImport')for n in classes)
proof={'schema':'xnby.material.excel.full-candidate.v1','sourceReceipt':receipt,'classFiles':classes,
 'sourceSHA256':sha(source),'helperSourceSHA256':sha(helper),'publicControllerABIUnchanged':True,
 'compiledWithOriginalParameterNamesAndDebugMetadata':True,'installed':False,'servicesStarted':False,'databaseReadOrChanged':False,
 'wholeControllerAndNormalRoleCandidatePassed':False,'fixedR24TransportChanged':False}
(out/'candidate.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'compiled':True,'classFiles':len(classes),'publicABIUnchanged':True,'installed':False}))
