"""Exercise actual native XLSX endpoints against only this fresh owned database."""
from pathlib import Path
import http.client,io,json,zipfile,hashlib,urllib.parse,xml.etree.ElementTree as ET
import verify_emergency_business_http_20261030 as c

HEAD=['部门名称','负责人','分析对象','分析单元','风险等级','坐标']
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def cells(raw):
 with zipfile.ZipFile(io.BytesIO(raw))as z:
  workbook=ET.fromstring(z.read('xl/workbook.xml'))
  assert len(workbook.findall('s:sheets/s:sheet',NS))==1,'ONE_NATIVE_EXCEL_SHEET_REQUIRED'
  texts=[]
  if 'xl/sharedStrings.xml'in z.namelist():
   texts=[''.join(x.itertext())for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)]
  sheet=ET.fromstring(z.read('xl/worksheets/sheet1.xml'));rows=[]
  for row in sheet.findall('s:sheetData/s:row',NS):
   vals={}
   for cell in row.findall('s:c',NS):
    assert cell.find('s:f',NS)is None,'NO_FORMULAS_EXPECTED_IN_NATIVE_RISK_EXPORT'
    v=cell.find('s:v',NS);value=''if v is None else(v.text or'')
    if cell.get('t')=='s':value=texts[int(value)]
    elif cell.get('t')=='inlineStr':value=''.join(cell.find('s:is',NS).itertext())
    key=''.join(ch for ch in cell.get('r','')if ch.isalpha());vals[key]=value
   rows.append([vals.get(k,'')for k in 'ABCDEF'])
  return rows

def run(root,request,headers,business_port):
 assert root.parent==c.W and root.name.startswith('full-business-main-r')
 assert c.read(root/'risk-portal-seed-result.json')['originalAccountOrBusinessRowsImported']is False
 folder=root/'risk-excel-http';folder.mkdir();cases=[]
 def binary(label,method,path,body=None,mime=None,auth=True):
  sent={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) OwnNormalLoginProbe/1.0','Connection':'close'}
  if auth:sent['Authorization']=headers['own_operator_a']
  if mime:sent['Content-Type']=mime
  conn=http.client.HTTPConnection('127.0.0.1',business_port,timeout=25)
  try:
   conn.request(method,path,body=body,headers=sent);res=conn.getresponse();raw=res.read(5242881)
   assert len(raw)<=5242880,'OWN_SMALL_EXCEL_RESPONSE_BOUND'
   row={'case':label,'httpStatus':res.status,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'contentType':res.getheader('Content-Type'),'cacheControl':res.getheader('Cache-Control'),'xlsxZip':raw.startswith(b'PK\x03\x04')}
   if not row['xlsxZip']:
    try:
     value=json.loads(raw);row.update(businessCode=value.get('code'),ownedSyntheticMessage=str(value.get('msg')or value.get('message')or'')[:160])
    except(ValueError,AttributeError):row['nonJSONResponse']=True
   cases.append(row);c.dump(folder/'cases.json',{'cases':cases,'onlyOwnedSyntheticRows':True,'authValuesRecorded':False})
   return row,raw
  finally:conn.close()
 def page(label,**filters):
  status,value=request(business_port,'GET','/serv/riskLevel/getPage?'+urllib.parse.urlencode({'current':1,'size':100,**filters}),authorization=headers['own_operator_a'])
  assert status==200 and value.get('code')==0,'NATIVE_RISK_EXCEL_READBACK_FAILED:'+label
  return value['data']
 before=page('before');assert int(before['total'])==33,'OWN_NATIVE_UI_CREATED_ROW_EXPECTED'
 anon,raw=binary('anonymous-export-observation','GET','/serv/riskLevel/export',auth=False)
 anon_blocked=anon['httpStatus']==200 and anon.get('businessCode')==600 and not anon['xlsxZip'] and 'no-store' in str(anon.get('cacheControl')or '').lower() and str(anon.get('contentType')or '').lower().startswith('application/json')
 assert anon_blocked,'ORIGINAL_NATIVE_RISK_ANONYMOUS_AUTH_CONTRACT_REQUIRED'
 row,template=binary('download-native-template','GET','/serv/riskLevel/getModel')
 assert row['httpStatus']==200 and row['xlsxZip'],'NATIVE_RISK_TEMPLATE_MUST_BE_XLSX'
 model=cells(template);assert model==[HEAD],'NATIVE_RISK_TEMPLATE_SIX_HEADERS_REQUIRED'
 (folder/'native-template.xlsx').write_bytes(template)
 row,exported=binary('export-all','GET','/serv/riskLevel/export')
 assert row['httpStatus']==200 and row['xlsxZip'],'NATIVE_RISK_EXPORT_MUST_BE_XLSX'
 all_rows=cells(exported);assert all_rows[0]==HEAD and len(all_rows)==34,'NATIVE_RISK_EXPORT_MUST_CONTAIN_ALL_33_ROWS'
 (folder/'native-export.xlsx').write_bytes(exported)
 row,filtered=binary('export-department-filter','GET','/serv/riskLevel/export?'+urllib.parse.urlencode({'department':'Own risk department A'}))
 assert row['httpStatus']==200 and row['xlsxZip'],'NATIVE_FILTERED_EXPORT_MUST_BE_XLSX'
 filtered_rows=cells(filtered);assert len(filtered_rows)==19 and all(x[0]=='Own risk department A'for x in filtered_rows[1:]),'NATIVE_FILTERED_EXPORT_MUST_MATCH_18_ROWS'
 fixture=c.T/'test-data/risk-unit-excel-r76/risk-unit-import.xlsx';payload=fixture.read_bytes()
 expected=json.loads((fixture.parent/'expected.json').read_bytes())['values']
 assert cells(payload)==expected,'EXACT_SYNTHETIC_IMPORT_FIXTURE_REQUIRED'
 boundary='OWN_RISK_MULTIPART_R76'
 body=('--'+boundary+'\r\nContent-Disposition: form-data; name="file"; filename="own-risk.xlsx"\r\nContent-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\r\n\r\n').encode()+payload+('\r\n--'+boundary+'--\r\n').encode()
 row,raw=binary('import-one-synthetic-row','POST','/serv/riskLevel/importExcel',body,'multipart/form-data; boundary='+boundary)
 assert row['httpStatus']==200 and row.get('businessCode',0)in(0,200,None),'NATIVE_RISK_IMPORT_HTTP_MUST_SUCCEED'
 loaded=page('import-readback',analysisObject=expected[1][2])
 assert int(loaded['total'])==1 and len(loaded['records'])==1,'NATIVE_RISK_IMPORT_MUST_PERSIST_EXACTLY_ONE_ROW'
 actual=loaded['records'][0]
 for field,value in zip(['department','person','analysisObject','analysisUnit','riskLevel','coordinate'],expected[1]):
  assert str(actual.get(field))==value,'NATIVE_IMPORT_FIELD_MUST_MATCH:'+field
 after=page('after-import');assert int(after['total'])==34,'NATIVE_IMPORT_TOTAL_INCREMENT_REQUIRED'
 result={'normalOriginalSDKAndBusinessHTTP':True,'actualNativeTemplateAndExportXLSX':True,
  'nativeSixColumnTemplateAccepted':True,'exportedAllRows':33,'departmentFilteredRows':18,
  'oneSyntheticXLSXRowPersistedExactly':True,'allSixImportedFieldsMatched':True,
  'importedCreateTimePresent':bool(actual.get('createTime')),'importedRowFirst':after['records'][0].get('id')==actual['id'],
  'anonymousExportBlocked':anon_blocked,'anonymousExportReturnedXLSX':anon['xlsxZip'],
  'allDataSynthetic':True,'browserDownloadOrUploadAccepted':False,'formalOrPublicChanged':False,'fullCloneReady':False,'cases':cases}
 c.dump(folder/'result.json',result)
