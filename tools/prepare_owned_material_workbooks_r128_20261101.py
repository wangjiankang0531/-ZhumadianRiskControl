"""Use original POI and EasyExcel/model to create verified synthetic workbook rows."""
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
