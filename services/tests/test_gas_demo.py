import tempfile,unittest
from pathlib import Path
from services.tests import test_api as fixture
from tools.serve_gas_portal_qa import configure_gas_fixture
from services.gas_demo import seed,PERMS
from services.auth import Principal
from services.database_transfer import validate_database
class GasDemoTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):fixture.ApiTests.setUpClass()
 def test_explicit_scenarios_persist_and_seed_never_overwrites_user_edits(self):
  p=fixture.ApiTests();p.setUp()
  try:
   path=p.root/'isolated.sqlite';points=configure_gas_fixture(p,path);store=p.service.gas
   with store.transaction() as db:
    self.assertEqual(db.execute('SELECT count(*) FROM gas_alerts').fetchone()[0],6);self.assertEqual(db.execute('SELECT count(*) FROM gas_outbox').fetchone()[0],0);before=[tuple(r) for r in db.execute('SELECT * FROM gas_alerts ORDER BY id')];validate_database(db)
   actor=Principal('QA-A','QA',PERMS,frozenset({'A'}),False,True,'qa-manual-edit')
   event=store.list(actor,points)['items'][0]
   store.mutate(actor,points,event['id'],'classify',{'revision':event['revision'],'classification':'persistent','note':'User edit must survive seeding'},'f'*32)
   with store.transaction() as db:before=[tuple(r) for r in db.execute('SELECT * FROM gas_alerts ORDER BY id')]
   seed(store,points)
   with store.transaction() as db:self.assertEqual([tuple(r) for r in db.execute('SELECT * FROM gas_alerts ORDER BY id')],before)
   b=next(person for person in p.policy['principals'] if person['subject']=='QA-B');self.assertNotIn('gas:verify',b['permissions']);self.assertIn('gas:cooperate',b['permissions'])
   self.assertEqual(set(points),{'qa-gas-1','qa-gas-2','qa-gas-3'});snapshot=p.service.store.snapshot();self.assertEqual(len([f for f,owner,*_ in snapshot['objects'] if f['id'] in points and owner is None]),3)
  finally:p.tearDown()
if __name__=='__main__':unittest.main()
