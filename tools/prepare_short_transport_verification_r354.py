from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent;D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_unified_plan_r39_20261103')
source=V/'verify_unified_plan_delivery_r353.py';raw=source.read_bytes();text=source.read_text(encoding='utf-8')
old="O=V/'r39-fixed-transport-validation-r353'";new="O=R/'work/r39-transport-validation-r354'"
assert text.count(old)==1;text=text.replace(old,new,1)
text=text.replace('verified-fixed-transport-r353.json','verified-fixed-transport-r354.json')
ast.parse(text);out=V/'verify_unified_plan_delivery_r354.py';assert not out.exists();out.write_text(text,encoding='utf-8')
proof={'preparedOnly':True,'initialVerifierSHA256':hashlib.sha256(raw).hexdigest(),'shortRootVerifierSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),
 'initialAttemptExitedOneBeforeServiceOrDataAccess':True,'initialFailure':'FileNotFoundError creating frontend file under long temporary test root; production extraction maximum remains 237.',
 'initialTemporaryRootRetainedForScopedCleanup':str(V/'r39-fixed-transport-validation-r353'),'shortTemporaryRoot':'D:/Project/Zhumadian/work/r39-transport-validation-r354',
 'fixedTransportOrUpdaterChanged':False,'manifestSHA256':hashlib.sha256((D/'delivery-manifest.json').read_bytes()).hexdigest()}
(V/'short-transport-verifier-prepared-r354.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
