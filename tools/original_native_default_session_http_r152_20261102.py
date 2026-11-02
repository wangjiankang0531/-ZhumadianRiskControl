"""Normal unchanged login/default-current-user/business/logout against the exact own synthetic server."""
from pathlib import Path
import http.client,json,urllib.parse
R=Path('D:/Project/Zhumadian')

def run_cases(root,platform_port,business_port):
 root=Path(root);assert root.parent==R/'work/event_delivery_consistency_20261030/full-controller-r152'
 assert json.loads((R/'_g/own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly'] and not(R/'_g/user-manual-protected.json').exists()
 own=json.loads((R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json').read_bytes());assert own['credentialsSynthetic']
 cases=[];current=None
 def dump():
  (root/'default-native-session-http-cases.json').write_text(json.dumps({'cases':cases,'onlyOwnSyntheticUsers':True,'rawTokensPasswordsUserIdsOrBusinessRowsExported':False},indent=2)+'\n',encoding='utf-8')
 def request(port,method,path,authorization=None,form=None):
  assert port in [platform_port,business_port] and 1024<=port<=65535 and path.startswith('/') and '\r'not in path and '\n'not in path
  headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) XNBYOwnedDefaultSessionProbe/1.0','Accept':'application/json','Connection':'close'}
  body=None
  if authorization:headers['Authorization']=authorization
  if form is not None:body=urllib.parse.urlencode(form).encode('ascii');headers['Content-Type']='application/x-www-form-urlencoded;charset=UTF-8'
  c=http.client.HTTPConnection('127.0.0.1',port,timeout=15)
  try:
   c.request(method,path,body=body,headers=headers);r=c.getresponse();raw=r.read(1048577);assert len(raw)<=1048576;v=json.loads(raw);assert isinstance(v,dict);return r.status,v
  finally:c.close()
 def record(case,status,v,**extra):cases.append({'case':case,'httpStatus':status,'businessCode':v.get('code'),**extra});dump()
 try:
  for name in ['own_operator_a','own_reviewer_b']:
   status,v=request(platform_port,'POST','/api/oauth/Login?'+urllib.parse.urlencode({'grant_type':'password','account':name,'password':own['wirePassword']}));current=(v.get('data')or{}).get('token');record('normal-login-'+name,status,v,normalTokenReturned=isinstance(current,str)and len(current)>16);assert status==200 and v.get('code')==200 and isinstance(current,str)and len(current)>16
   status,v=request(platform_port,'GET','/api/oauth/CurrentUser?systemCode='+urllib.parse.quote(own['systemCode'],safe=''),current);info=(v.get('data')or{}).get('userInfo')or{};matched=info.get('userId')==own['accounts'][name]['id'];record('original-client-declared-system-'+name,status,v,expectedSyntheticUserMatched=matched);assert status==200 and v.get('code')==200 and matched and str(info.get('isAdministrator')).lower()in ['false','0']
   status,v=request(platform_port,'GET','/api/oauth/CurrentUser',current);info=(v.get('data')or{}).get('userInfo')or{};matched=info.get('userId')==own['accounts'][name]['id'];record('real-native-default-context-'+name,status,v,expectedSyntheticUserMatched=matched);assert status==200 and v.get('code')==200 and matched,'ORIGINAL_DEFAULT_CONTEXT_MUST_ACCEPT_NORMAL_OWN_USER'
   status,v=request(business_port,'GET','/riskLevel/getPage?current=1&size=1',current);record('default-guard-authenticated-original-risk-list-'+name,status,v);assert status==200 and v.get('code')==0
   status,v=request(platform_port,'POST','/api/oauth/Logout/password',current,{});record('original-native-logout-'+name,status,v);assert status==200 and v.get('code')==200
   status,v=request(platform_port,'GET','/api/oauth/CurrentUser',current);matched=(v.get('data')or{}).get('userInfo')is not None;record('default-provider-after-logout-'+name,status,v,userInfoStillPresent=matched);assert v.get('code')!=200 or not matched
   status,v=request(business_port,'GET','/riskLevel/getPage?current=1&size=1',current);record('same-original-token-refused-after-logout-'+name,status,v,noRows=v.get('data')is None);assert v.get('code')!=0 and v.get('data')is None and status!=503,'REVOKED_SESSION_MUST_NOT_BE_AN_UNAVAILABLE_OR_ALLOWED_SESSION';current=None
  for label,authorization in [('anonymous',None),('forged','OWN_INVALID_NON_SESSION')]:
   status,v=request(business_port,'GET','/riskLevel/getPage?current=1&size=1',authorization);record(label+'-refused-without-data',status,v,noRows=v.get('data')is None);assert v.get('code')!=0 and v.get('data')is None
  result={'passed':True,'actualOriginalProviderAndSDK':True,'normalNonAdministratorRoles':2,'actualHTTPCheckpoints':len(cases),'defaultContextIdentityAndBusinessAccessPassed':True,'logoutImmediatelyRefusesSameSignedTokenWithoutPositiveCache':True,'anonymousAndForgedRefused':True,'businessWritesRequested':False,'onlyOwnSyntheticData':True,'rawCredentialsTokensUserIdsOrBusinessRowsExported':False};(root/'default-native-session-http-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
 finally:current=None;own.clear()
