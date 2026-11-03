from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
source=V/'verify_unified_plan_delivery_r354.py';text=source.read_text(encoding='utf-8')
old="O=R/'work/r39-transport-validation-r354';assert not O.exists();assert shutil.disk_usage(V).free>512*1024**2;O.mkdir()"
new="""O=R/'work/v39';assert not O.exists();assert shutil.disk_usage(V).free>512*1024**2
temporary_path_budget=json.loads((D/'delivery-manifest.json').read_bytes())['maximumExtractionPathCharacters']+len(str(O/'Application'))-len(str(Path('C:/inetpub/wwwroot/Zhumadian/Application')))
assert temporary_path_budget<250,'TEST_FIXTURE_PATH_BUDGET_REQUIRED_BEFORE_ALLOCATION'
O.mkdir()"""
assert text.count(old)==1;text=text.replace(old,new,1).replace('verified-fixed-transport-r354.json','verified-fixed-transport-r355.json')
ast.parse(text);out=V/'verify_unified_plan_delivery_r355.py';assert not out.exists();out.write_text(text,encoding='utf-8')
print(json.dumps({'prepared':True,'sourceSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'earlierVerifierSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'productionPayloadUnchanged':True,'temporaryPathBudgetNowCheckedBeforeAllocation':True}))
