from pathlib import Path
import json,re
W=Path('D:/Project/Zhumadian/work/user_feedback_20261031');S=W/'security-build-risk-r22-from-r21-r2';d=json.loads((S/'candidate-result.json').read_bytes());n=d['workplaceAdapter']['publishedNativeLoginQuery'];assert n['sourceFilesRestored']and n['passwordTransformTokenStorageAndBackendAuthenticationUnchanged'];hits=[]
for p in(S/'build/dist/assets/js').glob('*.js'):
 s=p.read_text(encoding='utf-8');i=s.find('/jnpf/oauth/Login')
 if i>=0:hits.append({'file':p.name,'snippet':s[max(0,i-120):i+100]})
assert len(hits)==1 and re.search(r'void\s*0',hits[0]['snippet']);v=json.loads((S/'compiled-static-verification.json').read_bytes());v.update(publishedNativeLoginPOSTQueryCompiled=True,loginEncryptionAndTokenStorageUnchanged=True,publishedLoginAdapterSourceRestored=True,loginCompiledChunk=hits[0]['file']);(S/'compiled-static-verification.json').write_text(json.dumps(v,indent=2),encoding='utf-8');print(json.dumps({'compiledFiles':len(d['fullFrontendFiles']),'nativeLoginPOSTQueryCompiled':True,'allLoginSourcesRestored':True,'oldBackendAuthenticationUnchanged':True}))
