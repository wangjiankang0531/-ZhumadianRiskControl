from pathlib import Path
import ast, hashlib, json, os, shutil, subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';A=R/'_f/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r128'
out=C/'native-workbook-writer-r1';assert not out.exists();out.mkdir();(out/'classes').mkdir()
source=T/'java/material_full_controller_r1/OwnMaterialWorkbookWriter.java';assert not source.exists()
raw=(Path(__file__).parent/'OwnMaterialWorkbookWriter.java').read_text(encoding='utf-8')
raw=raw.replace('if(root.getParent().getFileName().toString().equals("r5")){','if(Files.isRegularFile(Path.of("D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r128/r4/material-browser/own-valid.xlsx"))){')
raw=raw.replace('System.out.println(new String(json,java.nio.charset.StandardCharsets.UTF_8));','System.out.println("OWN_MATERIAL_WORKBOOK_JSON:"+new String(json,java.nio.charset.StandardCharsets.UTF_8));')
source.write_text(raw,encoding='utf-8',newline='\n')
meta=json.loads((R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json').read_bytes())
cp=[]
for file in meta['classpath'].split(';'):
 name=Path(file).name;p=A/'payload/business'/(name if name in ['application.jar','process-boundary.jar']else'lib/'+name);assert p.is_file();cp.append(str(p))
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
r=subprocess.run([str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx256m','--release','17','-encoding','UTF-8','-proc:none','-cp',';'.join(cp),'-d',str(out/'classes'),str(source)],capture_output=True,env=env,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
(out/'compile.private.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,'NATIVE_WORKBOOK_WRITER_COMPILE_FAILED'
metadata={'java':str(A/'runtime/jdk17/bin/java.exe'),'classpath':str(out/'classes')+';'+';'.join(cp),'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest()}
(out/'compiled.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
p=T/'prepare_owned_material_workbooks_r128_20261101.py';previous=p.read_bytes();(out/'previous-xml-writer.py').write_bytes(previous)
bridge='''"""Use original POI and EasyExcel/model to create verified synthetic workbook rows."""
from pathlib import Path
import json,os,re,subprocess,sys
R=Path('D:/Project/Zhumadian');C=R/'work/event_delivery_consistency_20261030/full-controller-r128'
root=Path(sys.argv[1]).resolve(strict=True);template=Path(sys.argv[2]).resolve(strict=True)
assert root.parent.parent==C and root.name=='material-browser'and re.fullmatch('r[1-9][0-9]*',root.parent.name)
assert template.parent==root/'downloads'and template.suffix=='.xlsx'
m=json.loads((C/'native-workbook-writer-r1/compiled.json').read_bytes())
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
r=subprocess.run([m['java'],'-Xmx256m','-XX:ActiveProcessorCount=2','--add-opens','java.base/java.lang=ALL-UNNAMED','-cp',m['classpath'],'OwnMaterialWorkbookWriter',str(root),str(template)],capture_output=True,env=env,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==0,'OWN_NATIVE_WORKBOOK_GENERATOR_FAILED'
text=r.stdout.decode('utf-8');marker='OWN_MATERIAL_WORKBOOK_JSON:';assert text.count(marker)==1
result=json.loads(text.split(marker,1)[1]);assert result['originalEasyExcelAndModelActuallyUsed']and result['validParserProof']=={'parsedRows':3,'ownNamedRows':3}
print(json.dumps(result,ensure_ascii=False))
'''
ast.parse(bridge);p.write_text(bridge,encoding='utf-8',newline='\n')
probe=C/'r90/material-browser';(probe/'downloads').mkdir(parents=True)
native=C/'r3/material-browser/downloads/应急物资模板.xlsx';assert native.is_file();shutil.copyfile(native,probe/'downloads/own-native-template.xlsx')
print('Original-library writer compiled; prior XML generator preserved; pure parser probe ready.')
