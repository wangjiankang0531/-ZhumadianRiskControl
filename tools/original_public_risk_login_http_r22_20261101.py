"""Normal published SDK login/current-user/risk/logout against synthetic data; no task-identity prototype."""
import http.client,json,urllib.parse,uuid
import verify_emergency_business_http_20261030 as c

def run_cases(root,platform_port,business_port,snapshot,workflow):
 own=c.read(root/'own-normal-login.private.json');assert own['credentialsSynthetic'];accounts=own['accounts'];cases=[];headers={};system=own['systemCode']
 def request(port,method,path,form=None,authorization=None,json_body=None,extra_headers=None):
  assert isinstance(port,int) and 1024<=port<=65535 and path.startswith('/') and not any(x in path for x in ['\r','\n','://'])
  body=urllib.parse.urlencode(form).encode('ascii') if form is not None else None;sent={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) OwnNormalLoginProbe/1.0','Accept':'application/json','Connection':'close'}
  if body is not None:sent['Content-Type']='application/x-www-form-urlencoded;charset=UTF-8'
  if json_body is not None:body=json.dumps(json_body,ensure_ascii=False).encode('utf8');sent['Content-Type']='application/json;charset=UTF-8'
  if extra_headers:sent.update(extra_headers)
  if authorization:sent['Authorization']=authorization
  conn=http.client.HTTPConnection('127.0.0.1',port,timeout=15)
  try:
   conn.request(method,path,body=body,headers=sent);response=conn.getresponse();raw=response.read(1048577);assert len(raw)<=1048576;value=json.loads(raw);assert isinstance(value,dict);return response.status,value
  finally:conn.close()
 def record(name,status,value,**details):
  cases.append({'case':name,'httpStatus':status,'businessCode':value.get('code'),'diagnosticMessage':str(value.get('msg',value.get('message','')))[:160],**details});c.dump(root/'public-normal-login-http-cases.json',{'cases':cases,'originalLoginHTTPUsed':True,'originalClientQueryPostAndUnchangedAuthorizationValue':True,'tokensOrPasswordsRecorded':False,'realAccountsUsed':False})
 def login(name,password):return request(platform_port,'POST','/api/oauth/Login?'+urllib.parse.urlencode({'grant_type':'password','account':name,'password':password}))
 def token(value):
  data=value.get('data');return data.get('token') if isinstance(data,dict) else None
 def reject(name,status,value):
  record(name,status,value,tokenReturned=bool(token(value)));assert value.get('code')==400 and not token(value),'EXPECTED_ORIGINAL_LOGIN_REJECTION:'+name;expected={'wrong-password':'账号或密码错误','no-permission':'该用户未分配权限','disabled-account':'账号已被禁用'};assert value.get('msg')==expected[name],'ORIGINAL_SPECIFIC_LOGIN_REJECTION_REQUIRED:'+name
 def ids(value):
  found=set()
  if isinstance(value,dict):
   if isinstance(value.get('id'),str):found.add(value['id'])
   for nested in value.values():found.update(ids(nested))
  elif isinstance(value,list):
   for nested in value:found.update(ids(nested))
  return found
 try:
  status,value=login('own_operator_a',own['wrongWirePassword']);reject('wrong-password',status,value)
  status,value=login('own_no_permission_c',own['wirePassword']);reject('no-permission',status,value)
  status,value=login('own_disabled_d',own['wirePassword']);reject('disabled-account',status,value)
  snapshot('negative');negative=c.read(root/'normal-login-snapshot-negative.json');assert negative['own_operator_a']['errorCount']==1,'ORIGINAL_PASSWORD_FAILURE_COUNTER_NOT_OBSERVED';assert all(not row['isAdministrator'] for row in negative.values())
  for name in ['own_operator_a','own_reviewer_b']:
   status,value=login(name,own['wirePassword']);value_token=token(value);record('normal-login-'+name,status,value,tokenReturned=bool(value_token));assert status==200 and value.get('code')==200 and isinstance(value_token,str) and len(value_token)>16,'ORIGINAL_NORMAL_LOGIN_FAILED:'+name
   authorization=value_token;headers[name]=authorization
   status,value=request(platform_port,'GET','/api/oauth/CurrentUser?systemCode='+urllib.parse.quote(system,safe=''),authorization=authorization);data=value.get('data') or {};info=data.get('userInfo') or {};menu_ids=ids(data.get('menuList'));expected=accounts[name];other=accounts['own_reviewer_b' if name=='own_operator_a' else 'own_operator_a'];record('original-current-user-'+name,status,value,expectedIdentityMatched=info.get('userId')==expected['id'],expectedRolePresent=expected['roleId'] in (info.get('roleIds') or []),expectedModulePresent=expected['moduleId'] in menu_ids,otherModuleExposed=other['moduleId'] in menu_ids)
   assert status==200 and value.get('code')==200 and info.get('userId')==expected['id'] and str(info.get('isAdministrator')).lower() in ['false','0'],'ORIGINAL_CURRENT_USER_IDENTITY_FAILED:'+name
   assert expected['roleId'] in (info.get('roleIds') or []) and expected['moduleId'] in menu_ids and other['moduleId'] not in menu_ids,'ORIGINAL_ROLE_MENU_ISOLATION_FAILED:'+name
   status,value=request(business_port,'GET','/serv/riskLevel/getPage?current=1&size=5',authorization=authorization);record('authenticated-native-risk-list-'+name,status,value);assert status==200 and value.get('code')==0,'ORIGINAL_BUSINESS_LOGIN_BINDING_FAILED:'+name
  workflow(request,headers)
  snapshot('positive')
  status,value=request(business_port,'GET','/serv/riskLevel/getPage?current=1&size=5',authorization='OWN_INVALID_TOKEN');record('invalid-native-risk-session',status,value);assert status in (200,401,403,500) and value.get('code')!=0 and value.get('data') is None,'ORIGINAL_NATIVE_AUTH_MUST_REJECT_WITHOUT_RECORDS'
  for name,authorization in list(headers.items()):
   status,value=request(platform_port,'POST','/api/oauth/Logout/password',{},authorization);record('original-logout-'+name,status,value);assert status==200 and value.get('code')==200,'ORIGINAL_LOGOUT_FAILED:'+name
   native_status,native_value=request(platform_port,'GET','/api/oauth/CurrentUser?systemCode='+urllib.parse.quote(system,safe=''),authorization=authorization);native_info=(native_value.get('data')or{}).get('userInfo')or{};record('platform-current-user-after-logout-'+name,native_status,native_value,ownUserInfoStillReturned=bool(native_info),ownUserIdentityStillMatched=native_info.get('userId')==accounts[name]['id'])
   status,value=request(business_port,'GET','/serv/riskLevel/getPage?current=1&size=5',authorization=authorization);record('revoked-native-risk-session',status,value);assert status in (200,401,403,500) and value.get('code')!=0 and value.get('data') is None,'ORIGINAL_NATIVE_AUTH_MUST_REJECT_WITHOUT_RECORDS'
  snapshot('final');result={'schema':'xnby.original-normal-login.http-result.v1','actualOriginalLoginAndCurrentUserHTTP':True,'nonAdministratorUsersAuthenticated':2,'wrongPasswordNoPermissionAndDisabledRejected':True,'distinctRoleMenusIsolated':True,'actualOriginalSDKRiskBusinessUsed':True,'invalidAndLoggedOutTokensRejectedByOriginalNativeBoundary':True,'sessionsCreatedOnlyByOriginalLogin':True,'tokensPasswordsOrRealAccountDataRecorded':False,'captchaBranchTested':False,'realWorkflowOrBrowserAccepted':False,'runtimeInstalled':False,'publicChanged':False,'fullCloneReady':False,'cases':cases};c.dump(root/'public-normal-login-http-result.json',result);return result
 finally:
  headers.clear();own.clear()
