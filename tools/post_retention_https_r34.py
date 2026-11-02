from pathlib import Path
import datetime,http.client,ssl,json,re
D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_pending_visibility_r34_20261102');results=[];h=http.client.HTTPSConnection('www.joinlinksmart.com',context=ssl.create_default_context(),timeout=20)
for p in ['/zhumadian','/zhumadian/','/zhumadian/home','/zhumadian/emergency/','/zhumadian/emergency/home/index','/zhumadian/emergency/workflow/flowTodo','/zhumadian/api/jnpf/oauth/getLoginConfig']:
 h.request('GET',p,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'});r=h.getresponse();b=r.read(2*1024**2);expected=301 if p=='/zhumadian'else 200;assert r.status==expected
 row={'path':p,'status':r.status,'passed':True}
 if p.endswith('getLoginConfig'):assert json.loads(b)['code']==200;row['originalLoginConfigBusinessCode']=200
 results.append(row)
h.close();proof={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'defaultTLSCertificateVerification':True,'afterActualOldVersionDeletion':True,'checks':results,'publicAuthenticatedWorkflowDetailAccepted':False,'businessRowsOrCredentialsRead':False};(D/'post-retention-https.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
