import json,unittest,tempfile
from pathlib import Path
from collections import Counter
from urllib.parse import urlencode
from services.reference_demo import DemoStore,DemoError,MODULES
from services.tests import test_reference_demo as fixture

class FilterTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'isolated.sqlite';self.store=DemoStore(self.path)
 def tearDown(self):self.tmp.cleanup()
 def test_same_scope_facets_ignore_only_selected_state_and_summary_reconciles(self):
  for entity,model in MODULES.items():
   all_rows=self.store.list(entity)['records']+self.store.list(entity,page=2)['records']
   expected=[r for r in all_rows if r['enterprise']=='模拟企业甲' and '2026-10-13'<=r['date']<='2026-10-16']
   args=dict(enterprise='模拟企业甲',date_from='2026-10-13',date_to='2026-10-16')
   listing=self.store.list(entity,**args);self.assertEqual({r['id'] for r in listing['records']},{r['id'] for r in expected});self.assertEqual(listing['total'],len(expected));self.assertEqual(listing['counts'],dict(Counter(r['state'] for r in expected)))
   for state in model['states']:
    selected=self.store.list(entity,state=state,**args);self.assertEqual(selected['total'],sum(r['state']==state for r in expected));self.assertEqual(selected['counts'],listing['counts'])
   summary=self.store.summary(entity,**args);self.assertEqual(summary['total'],listing['total']);self.assertEqual(sum(summary['states'].values()),listing['total']);self.assertEqual(sum(summary['dates'].values()),listing['total']);self.assertEqual(sum(summary['enterprises'].values()),listing['total'])
 def test_inclusive_single_day_open_ends_and_empty_ranges(self):
  rows=self.store.list('events')['records']+self.store.list('events',page=2)['records']
  for start,end in [('2026-10-13','2026-10-13'),('','2026-10-14'),('2026-10-16',''),('2099-01-01','2099-01-02')]:
   v=self.store.list('events',date_from=start,date_to=end);self.assertEqual(v['total'],sum((not start or r['date']>=start) and (not end or r['date']<=end) for r in rows))
 def test_literal_search_and_enterprise_are_applied_to_state_facets(self):
  self.assertEqual(sum(self.store.list('events',enterprise='模拟企业甲')['counts'].values()),4)
  for query in ['%','_',"' OR 1=1 --"]:self.assertEqual(self.store.list('events',q=query)['counts'],{})
  found=self.store.list('events',q='模拟样本01');self.assertEqual(sum(found['counts'].values()),1)
 def test_invalid_dates_range_and_filter_values_fail_without_mutation(self):
  before=self.path.read_bytes()
  for args in [dict(date_from='2026-02-30'),dict(date_to='2026-1-01'),dict(date_from='20261013'),dict(date_from='2026-10-17',date_to='2026-10-12'),dict(state='unknown'),dict(enterprise='other'),dict(q='x'*257),dict(page=True)]:
   with self.assertRaises(DemoError):self.store.list('events',**args)
  self.assertEqual(self.path.read_bytes(),before)

class FilterHTTPTests(unittest.TestCase):
 setUp=fixture.DemoHTTPTests.setUp
 tearDown=fixture.DemoHTTPTests.tearDown
 req=fixture.DemoHTTPTests.req
 def test_filtered_list_and_summary_have_identical_counts_on_real_http(self):
  params=urlencode(dict(entity='events',enterprise='模拟企业甲',dateFrom='2026-10-13',dateTo='2026-10-15'))
  code,raw=self.req('/api/demo/records?'+params);self.assertEqual(code,200);listing=json.loads(raw)
  code,raw=self.req('/api/demo/summary?'+params);self.assertEqual(code,200);summary=json.loads(raw)
  self.assertEqual(listing['total'],2);self.assertEqual(summary['total'],2);self.assertEqual(sum(listing['counts'].values()),2);self.assertEqual(listing['dateBasis'],'record_date_utc')
 def test_http_rejects_bad_dates_duplicates_and_mixed_detail_filters(self):
  for suffix in ['dateFrom=2026-02-30','dateFrom=2026-10-16&dateTo=2026-10-13','dateTo=20261013','dateFrom=2026-10-13&dateFrom=2026-10-14','id=DEMO-EVENTS-001&dateFrom=2026-10-13','q='+('x'*257)]:self.assertEqual(self.req('/api/demo/records?entity=events&'+suffix)[0],400,suffix)
  self.assertEqual(self.req('/api/demo/summary?entity=events&page=1')[0],400)
  self.assertEqual(self.req('/api/demo/records?entity=events&id=DEMO-EVENTS-001')[0],200)

if __name__=='__main__':unittest.main()
