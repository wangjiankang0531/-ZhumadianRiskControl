from pathlib import Path
import hashlib,http.client,json,ssl
D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_personal_workflow_r35_20261103');J=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));assert J(D/'server-version-retention-apply-result.json')['passed']and J(D/'public-authenticated-personal-workflow-verification.json')['passed']
rows=[];c=http.client.HTTPSConnection('www.joinlinksmart.com',context=ssl.create_default_context(),timeout=20)
for path,status in [('/zhumadian',301),('/zhumadian/',200),('/zhumadian/emergency/',200),('/zhumadian/emergency/home/index',200),('/zhumadian/emergency/workflow/flowTodo',200),('/zhumadian/emergency/workflow/completedMatters',200),('/zhumadian/emergency/workflow/startWithMeTwo',200)]:
 c.request('GET',path,headers={'Accept-Encoding':'identity','Cache-Control':'no-cache'});r=c.getresponse();body=r.read(2*1024**2);assert r.status==status
 if status==301:assert r.getheader('Location')in ['/zhumadian/','https://www.joinlinksmart.com/zhumadian/']
 rows.append({'path':path,'status':r.status,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
 if r.will_close:c.close();c=http.client.HTTPSConnection('www.joinlinksmart.com',context=ssl.create_default_context(),timeout=20)
c.close();proof={'passed':True,'checks':rows,'defaultTLSVerified':True,'normalAuthenticatedBusinessDetailVerificationSeparateAndPassed':True,'businessRowsCredentialsOrCookiesRead':False};(D/'post-retention-https.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':True,'checks':len(rows),'defaultTLSVerified':True}))
