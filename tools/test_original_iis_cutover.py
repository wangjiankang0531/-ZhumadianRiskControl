from pathlib import Path
import tempfile,unittest
from original_iis_cutover import apply,rollback

class Cutover(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='iis-transaction-');self.base=Path(self.tmp.name);self.root=self.base/'iis';(self.root/'App_Code').mkdir(parents=True);self.backup=self.base/'backup'
        self.old={'web.config':b'old private config fixture','App_Code/XnbyReferenceProxy.cs':b'old adapter fixture'};self.new={'web.config':b'new private config fixture','App_Code/XnbyReferenceProxy.cs':b'new adapter fixture'}
        for k,v in self.old.items():(self.root/k).write_bytes(v)
    def tearDown(self):self.tmp.cleanup()
    def test_success_and_explicit_rollback_exact(self):
        r=apply(self.root,self.backup,self.new,lambda:True);self.assertTrue(r['applied']);self.assertFalse((self.root/'App_offline.htm').exists());rollback(self.backup)
        for k,v in self.old.items():self.assertEqual((self.root/k).read_bytes(),v)
    def test_failed_probe_restores_original_bytes(self):
        with self.assertRaisesRegex(RuntimeError,'POST_SWITCH'):apply(self.root,self.backup,self.new,lambda:False)
        for k,v in self.old.items():self.assertEqual((self.root/k).read_bytes(),v)
        self.assertFalse((self.root/'App_offline.htm').exists())
    def test_user_maintenance_file_untouched(self):
        (self.root/'App_offline.htm').write_bytes(b'not ours')
        with self.assertRaisesRegex(ValueError,'NOT_OWNED'):apply(self.root,self.backup,self.new,lambda:True)
        self.assertEqual((self.root/'App_offline.htm').read_bytes(),b'not ours')
    def test_concurrent_edit_never_overwritten(self):
        def changed():(self.root/'web.config').write_bytes(b'unrelated operator edit');return False
        with self.assertRaises(Exception):apply(self.root,self.backup,self.new,changed)
        self.assertEqual((self.root/'web.config').read_bytes(),b'unrelated operator edit')
    def test_changed_backup_refuses_rollback(self):
        apply(self.root,self.backup,self.new,lambda:True);(self.backup/'web.config').write_bytes(b'changed backup')
        with self.assertRaisesRegex(ValueError,'BACKUP_CHANGED'):rollback(self.backup)
        self.assertEqual((self.root/'web.config').read_bytes(),self.new['web.config'])
    def test_duplicate_transaction_refused(self):
        apply(self.root,self.backup,self.new,lambda:True)
        with self.assertRaisesRegex(ValueError,'FRESH'):apply(self.root,self.backup,self.new,lambda:True)

if __name__=='__main__':unittest.main()
