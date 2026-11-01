"""Exercise the new full compiled safety portal, using only actual normal original SDK services."""
from pathlib import Path
import json
import verify_emergency_business_http_20261030 as c
from original_public_risk_portal_host_r22_20261101 import host
from original_risk_unit_portal_session_handoff_20261031 import handoff

def browser(root,request,headers,platform_port,business_port,password,phase,account):
 own=c.read(root/'own-normal-login.private.json');assert own['credentialsSynthetic']
 with host(root,business_port,platform_port,phase)as base:
  with handoff(root,request,headers,platform_port,business_port,phase,account)as(descriptor,record):
   wire={'base':base,'phase':phase,'account':account,'password':password,'expectedWirePassword':own['wirePassword'],
    'expectedUserId':own['accounts'][account]['id'],'newObject':'Own UI risk '+__import__('uuid').uuid4().hex[:8],'syntheticNormalUser':True,'ownCaptchaPolicyDisabled':True,'syntheticSessionHandoff':descriptor,'excelFixture':(c.T/'test-data/risk-unit-excel-r76/risk-unit-import.xlsx').as_posix()}
   encoded=json.dumps(wire).encode()
   try:c.run(root,'compiled-security-browser-'+phase,[Path('D:/Program Files/nodejs/node.exe'),c.T/'verify_compiled_public_risk_portal_r22_20261101.mjs',root.as_posix()],150,encoded)
   finally:wire.clear();del encoded
   assert record['accepted']and record['wrongNonceRejected']==1 and record['replayRejected']==1,'NORMAL_SECURITY_UI_SESSION_HANDOFF_REQUIRED'
  assert c.read(root/('compiled-security-browser-'+phase)/'browser-terminal.json')['normalBrowserClosed']
 report=c.read(root/('compiled-security-browser-'+phase)/'result.json');assert len(report['cases'])==18 and report['actualNativeExcelBrowserDownloadsAndUpload']
 downloads=c.read(root/('compiled-security-browser-'+phase)/'excel-downloads.json');assert downloads['oneNativeUpload'] and len(downloads['downloads'])==3
 from original_risk_unit_excel_http_20261101 import cells,HEAD
 expected=[1,34,19];checks=[]
 for index,row in enumerate(downloads['downloads']):
  assert __import__('re').fullmatch('[a-f0-9-]{36}',row['guid'])
  path=root/('compiled-security-browser-'+phase)/'downloads'/row['guid'];raw=path.read_bytes();rows=cells(raw)
  assert rows[0]==HEAD and len(rows)==expected[index]
  if index==2:assert all(x[0]=='Own risk department A'for x in rows[1:])
  checks.append({'case':row['case'],'sha256':c.sha(path),'bytes':len(raw),'dataRows':len(rows)-1,'sixHeadersMatched':True,'actualBrowserDownload':True})
 c.dump(root/'compiled-risk-excel-browser-result.json',{'cases':18,'actualOriginalCompiledPortal':True,'normalOriginalSDKLogin':True,'nativeBrowserDownloads':checks,'nativeUploadExactlyOnceAndSuccessUIAndCount34':True,'onlySyntheticFixtureUsed':True,'formalOrPublicInstalled':False})
 own.clear()

def run(root,request,headers,platform_port,business_port,snapshot,password):
 from original_public_risk_newest_http_r22_20261101 import run as retained
 retained(root,request,headers,platform_port,business_port,snapshot,password)
 status,reply=request(platform_port,'GET','/api/oauth/CurrentUser?systemCode=safety',authorization=headers['own_operator_a'])
 c.dump(root/'risk-safety-menu-preflight.json',{'httpStatus':status,'businessCode':reply.get('code'),'ownedSyntheticMessage':str(reply.get('msg')or reply.get('message')or'')[:200],'ownUserPresent':bool((reply.get('data')or{}).get('userInfo'))})
 assert status==200 and reply.get('code')==200,'OWN_SAFETY_CURRENT_USER_PREFLIGHT_REQUIRED'
 browser(root,request,headers,platform_port,business_port,password,'risk-unit','own_operator_a')
 c.dump(root/'compiled-risk-portal-chain-result.json',{'actualCompiledRiskPortalAndNativeDirectory':True,'originalHTTPRegressionPreserved':True,'formalOrPublicChanged':False,'fullCloneReady':False})
