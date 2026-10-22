"""Real multipart and XLSX download bytes through authenticated candidate HTTP."""
from io import BytesIO
from copy import deepcopy
import json,unittest,uuid
from openpyxl import load_workbook
from tools import test_replica_candidate_http as base
from tools.test_replica_risk_excel import fixture
from services.replica_risk_excel import HEADERS,XLSX_MIME,FILE_LIMIT

class ExcelHTTPTests(base.HTTPTests):
 @classmethod
 def setUpClass(cls):
  cls.cfg=base.config();cls.cfg['identities']['tester']['permissions'].append('risk-unit:import')
  cls.cfg['directory']['departments'].append({'id':'d2','name':'合成范围外部门'});cls.cfg['directory']['users'].append({'id':'u2','name':'合成范围外责任人','departments':['d2']})
 def setUp(self):super().setUp();self.row=['合成测试部门','合成测试人员','HTTP导入对象','HTTP导入单元','red','114,33'];self.s.identities=deepcopy(self.s.identities)
 def upload(self,raw=None,name='risk.xlsx',key=None,parts=1,headers=None):
  boundary='----xnbyExcelBoundary';file=fixture([self.row]) if raw is None else raw;chunks=[]
  for _ in range(parts):chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {XLSX_MIME}\r\n\r\n'.encode()+file+b'\r\n')
  data=b''.join(chunks)+f'--{boundary}--\r\n'.encode();h={'Origin':self.s.origin,'X-XNBY-CSRF':self.csrf,'Content-Type':'multipart/form-data; boundary='+boundary,'Idempotency-Key':key or uuid.uuid4().hex};h.update(headers or {})
  return self.req('POST','/replica-api/serv/riskLevel/importExcel',data,h)
 def test_template_download_has_actual_six_columns_and_headers(self):
  self.assertEqual(self.req('GET','/replica-api/serv/riskLevel/getModel')[0],401);self.login();status,h,raw=self.req('GET','/replica-api/serv/riskLevel/getModel');self.assertEqual(status,200);self.assertEqual(h['Content-Type'],XLSX_MIME);self.assertIn('attachment;',h['Content-Disposition']);self.assertEqual(int(h['Content-Length']),len(raw));w=load_workbook(BytesIO(raw));self.assertEqual(w.sheetnames,['sheet']);self.assertEqual(tuple(c.value for c in w.active[1]),HEADERS);self.assertEqual(w.active.max_row,1);w.close()
 def test_both_upload_formats_and_exact_http_replay(self):
  self.login()
  for extension in ('xls','xlsx'):
   raw=fixture([self.row],extension);request=uuid.uuid4().hex;status,_,data=self.upload(raw,'risk.'+extension,request);self.assertEqual(status,200);first=json.loads(data)['data'];self.assertEqual(first['imported'],1);self.assertEqual(json.loads(self.upload(raw,'risk.'+extension,request)[2])['data'],first)
  self.assertEqual(self.s.store.query(self._principal(),self.s.directory)['total'],2)
 def test_changed_same_request_conflicts(self):
  self.login();request=uuid.uuid4().hex;self.assertEqual(self.upload(key=request)[0],200);self.assertEqual(self.upload(fixture([self.row,self.row]),key=request)[0],409);self.assertEqual(self.s.store.query(self._principal(),self.s.directory)['total'],1)
 def test_unicode_upload_filename_and_loopback_origin_allowlist(self):
  self.login();self.assertEqual(self.upload(name='风险单元合成测试.xlsx')[0],200)
  from tools.serve_replica_candidate import make_server
  with self.assertRaises(ValueError):make_server(self.cfg,self.s.static,self.s.store.path,origin_host='0.0.0.0')
 def test_bad_later_row_http_error_includes_line_and_no_partial_records(self):
  self.login();bad=list(self.row);bad[1]='未知责任人';status,_,raw=self.upload(fixture([self.row,bad]));self.assertEqual(status,400);self.assertIn('第3行',json.loads(raw)['msg']);self.assertEqual(self.s.store.query(self._principal(),self.s.directory)['total'],0)
 def test_import_origin_csrf_permissions_and_multipart_contract(self):
  self.login();self.assertEqual(self.upload(headers={'Origin':'http://other.invalid'})[0],403);self.assertEqual(self.upload(headers={'X-XNBY-CSRF':'wrong'})[0],403);self.assertEqual(self.upload(parts=2)[0],400);self.assertEqual(self.upload(headers={'Content-Type':'application/json'})[0],415);self.assertEqual(self.upload(headers={'Idempotency-Key':'invalid'})[0],400)
  self.s.identities['tester']['permissions'].remove('risk-unit:import');self.assertEqual(self.upload()[0],403)
 def test_bounded_import_slot_and_size(self):
  self.login();self.s.import_slots.acquire()
  try:self.assertEqual(self.upload()[0],429)
  finally:self.s.import_slots.release()
  self.assertEqual(self.upload(headers={'Content-Length':str(FILE_LIMIT+8193)})[0],413)
 def test_filtered_export_all_rows_ignores_pagination_and_deleted(self):
  self.login();first=json.loads(self.upload()[2])['data'];second=list(self.row);second[3]='第二个单元';self.assertEqual(self.upload(fixture([second]))[0],200)
  status,_,raw=self.req('GET','/replica-api/serv/riskLevel/export?current=2&size=1');self.assertEqual(status,200);w=load_workbook(BytesIO(raw));self.assertEqual(w.active.max_row,3);w.close()
  status,_,raw=self.req('GET','/replica-api/serv/riskLevel/export?analysisUnit='+__import__('urllib.parse',fromlist=['quote']).quote('第二个'));w=load_workbook(BytesIO(raw));self.assertEqual(w.active.max_row,2);self.assertEqual(w.active['D2'].value,'第二个单元');w.close()
  self.assertEqual(self.post('/serv/riskLevel/removeById',{'id':first['ids'][0],'revision':1})[0],200);status,_,raw=self.req('GET','/replica-api/serv/riskLevel/export');w=load_workbook(BytesIO(raw));self.assertEqual(w.active.max_row,2);w.close()
 def test_export_current_scope_and_permission(self):
  self.login();self.s.identities['tester']['departments'].append('d2');self.assertEqual(self.upload()[0],200);other=['合成范围外部门','合成范围外责任人','范围外对象','范围外单元','red','114,33'];self.assertEqual(self.upload(fixture([other]))[0],200);self.s.identities['tester']['departments'].remove('d2')
  status,_,raw=self.req('GET','/replica-api/serv/riskLevel/export');w=load_workbook(BytesIO(raw));self.assertEqual(w.active.max_row,2);self.assertEqual(w.active['A2'].value,'合成测试部门');w.close();self.s.identities['tester']['permissions'].remove('risk-unit:export');self.assertEqual(self.req('GET','/replica-api/serv/riskLevel/export')[0],403)

def load_tests(loader,tests,pattern):
 # Base HTTP tests are run by their own module; select only the eight new cases.
 return unittest.TestSuite(ExcelHTTPTests(name) for name in ExcelHTTPTests.__dict__ if name.startswith('test_'))

if __name__=='__main__':unittest.main(verbosity=2)
