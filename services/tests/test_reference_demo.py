import json, tempfile, unittest, threading, http.client, sqlite3
from contextlib import closing
from pathlib import Path
from services.reference_demo import DemoStore,DemoError,MODULES
from tools.serve_reference_demo import make_server

class DemoTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'isolated.sqlite';self.store=DemoStore(self.path)
 def tearDown(self):self.tmp.cleanup()
 def test_all_modules_pagination_and_filters(self):
  self.assertGreaterEqual(len(MODULES),34)
  for entity,model in MODULES.items():
   first=self.store.list(entity);second=self.store.list(entity,page=2)
   self.assertEqual((first['total'],len(first['records']),len(second['records'])),(12,8,4))
   self.assertFalse({r['id'] for r in first['records']}&{r['id'] for r in second['records']})
   self.assertEqual(sum(first['counts'].values()),12)
   self.assertEqual(self.store.list(entity,enterprise='模拟企业甲')['total'],4)
   self.assertEqual(self.store.list(entity,state=model['states'][0])['total'],3)
 def test_new_transition_restart_and_audit(self):
  entity='events';fields={c:'模拟 '+c for c in MODULES[entity]['columns']}
  v=self.store.create(entity,fields,'模拟企业甲','合成演练');identity=v['record']['id'];self.assertEqual(v['record']['revision'],1)
  for revision in (1,2,3):self.store.change(entity,identity,revision,'模拟处理'+str(revision))
  reopened=DemoStore(self.path);v=reopened.detail(entity,identity)
  self.assertEqual(v['record']['state'],MODULES[entity]['states'][-1]);self.assertEqual(v['record']['revision'],4);self.assertEqual([e['revision'] for e in v['events']],[1,2,3,4])
  self.assertEqual(reopened.list(entity)['total'],13)
  with self.assertRaises(DemoError):reopened.change(entity,identity,4,'超出终态')
 def test_conflict_is_atomic(self):
  row=self.store.list('hidden-danger')['records'][0];self.store.change(row['entity'],row['id'],1,'第一次模拟')
  with self.assertRaises(DemoError) as conflict:self.store.change(row['entity'],row['id'],1,'过期重复提交')
  self.assertEqual(conflict.exception.status,409)
  self.assertEqual(len(self.store.detail(row['entity'],row['id'])['events']),2)
 def test_search_is_literal_and_input_does_not_form_sql(self):
  self.assertEqual(self.store.list('events',q='%')['total'],0)
  self.assertEqual(self.store.list('events',q='_')['total'],0)
  self.assertEqual(self.store.list('events',q="' OR 1=1 --")['total'],0)
  self.assertEqual(self.store.list('events',q='模拟样本01')['total'],1)
 def test_business_status_column_tracks_state_transition(self):
  row=self.store.list('hidden-danger')['records'][0]
  changed=self.store.change('hidden-danger',row['id'],row['revision'],'模拟状态一致性核对')['record']
  self.assertEqual(changed['fields']['隐患状态'],changed['state'])
 def test_invalid_fields_do_not_insert(self):
  for fields in ({},{'extra':'injected'},{c:'x'*257 for c in MODULES['events']['columns']}):
   with self.assertRaises(DemoError):self.store.create('events',fields,'模拟企业甲','')
  self.assertEqual(self.store.list('events')['total'],12)
 def test_summary_reconciles_all_records_and_new_entry(self):
  fields={c:'模拟字段' for c in MODULES['events']['columns']}
  self.store.create('events',fields,'模拟企业甲','合成样本')
  value=self.store.summary('events')
  self.assertEqual(value['total'],13);self.assertEqual(sum(value['states'].values()),13);self.assertEqual(sum(value['dates'].values()),13);self.assertEqual(sum(value['enterprises'].values()),13)
  for values in value['groups'].values():self.assertEqual(sum(values.values()),13)
 def test_fixture_field_extension_keeps_user_edits_and_audits(self):
  entity='events';record=self.store.list(entity)['records'][0]
  with sqlite3.connect(self.path) as db:
   payload=json.loads(db.execute('SELECT payload FROM demo_records WHERE entity=? AND id=?',(entity,record['id'])).fetchone()[0]);key=MODULES[entity]['columns'][-1];del payload['fields'][key];payload['note']='保留模拟备注';db.execute('UPDATE demo_records SET payload=? WHERE entity=? AND id=?',(json.dumps(payload),entity,record['id']))
  db.close();reopened=DemoStore(self.path);v=reopened.detail(entity,record['id']);self.assertEqual(v['record']['note'],'保留模拟备注');self.assertIn(key,v['record']['fields']);self.assertEqual(v['events'][-1]['kind'],'fixture_field_extension');self.assertEqual(v['record']['revision'],2)
 def test_sqlite_backup_restore(self):
  target=Path(self.tmp.name)/'restored.sqlite'
  with closing(sqlite3.connect(self.path)) as source,closing(sqlite3.connect(target)) as dest:source.backup(dest)
  self.assertEqual(DemoStore(target).list('events'),self.store.list('events'))

class DemoHTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();folder=Path(self.tmp.name);(folder/'reference-demo.html').write_text('<html>synthetic</html>');self.server=make_server(0,folder,folder/'demo.sqlite');self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
 def req(self,path,body=None,headers=None):
  connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=5)
  connection.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,headers or {});r=connection.getresponse();raw=r.read();connection.close();return r.status,raw
 def test_static_whitelist_and_rebinding_rejected(self):
  self.assertEqual(self.req('/')[0],200)
  self.assertEqual(self.req('/../demo.sqlite')[0],404)
  self.assertEqual(self.req('/api/demo/catalog',headers={'Host':'untrusted.invalid'})[0],403)
 def test_write_origin_token_conflict_and_method_contract(self):
  code,raw=self.req('/api/demo/catalog');token=json.loads(raw)['token'];port=self.server.server_port
  row=self.server.store.list('events')['records'][0];payload=dict(entity='events',id=row['id'],revision=1,note='模拟研判')
  self.assertEqual(self.req('/api/demo/transition',payload)[0],403)
  headers={'Origin':f'http://127.0.0.1:{port}','Content-Type':'application/json','X-XNBY-Demo':token}
  self.assertEqual(self.req('/api/demo/transition',payload,headers)[0],200)
  self.assertEqual(self.req('/api/demo/transition',payload,headers)[0],409)
  self.assertEqual(self.req('/api/demo/records?entity=events&page=invalid')[0],400)
  self.assertEqual(self.req('/api/demo/records?entity=events&entity=closed')[0],400)
  headers['Origin']='https://untrusted.invalid';self.assertEqual(self.req('/api/demo/transition',payload,headers)[0],403)

if __name__=='__main__':unittest.main()
