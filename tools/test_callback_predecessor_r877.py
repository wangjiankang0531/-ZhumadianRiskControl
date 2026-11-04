"""Synthetic metadata tests; no service, real identity, SQL or native code."""
import copy, json, unittest
import owned_callback_predecessor_r877 as m

def rows():
    result=[]
    for n in (1,2):
        value=[None]*17;value[0]='a546'+format(n,'028x');value[1]='OWN_MANAGER_CALLBACK_'+value[0]
        value[2]='合成回调'+str(n);value[3]=value[4]='3';value[5]='{"url":"http://127.0.0.1:50123/synthetic"}';value[8]='1';result.append(value)
    return result

def fixture():
    app='D:\\OwnedFixture\\Application';stage='D:\\OwnedFixture\\stages\\prior';data=app+'\\data'
    p={'schema':'xnby.owned-original-callback-plan.r662.v1','onlyOwnedRuntimeFixture':True,'application':app,'attempt':stage,'stage':'normal-restart',
       'attemptId':'1'*32,'databaseUUID':'00000000-0000-0000-0000-000000000001','releaseSHA256':'2'*64,'controllerPID':12345,
       'beforeRows':rows(),'afterRows':rows(),'businessPort':50123,'previousBusinessPort':50122,'databasePort':50124,'gatewayPort':50125}
    raw=lambda x:(json.dumps(x,ensure_ascii=False)+'\n').encode('utf8')
    pr=raw(p);j={'schema':'xnby.owned-callback-provisioning.r658.v1','attemptId':p['attemptId'],'databaseUUID':p['databaseUUID'],'dataDirectory':data,
       'releaseSHA256':p['releaseSHA256'],'controllerPID':str(p['controllerPID']),'planSHA256':m.sha(pr),'beforeRowsSHA256':m.rows_sha256(p['beforeRows']),
       'afterRowsSHA256':m.rows_sha256(p['afterRows']),'stage':'normal-restart','journalPath':stage+'\\callback-normal-restart-journal.private.properties','phase':'readback-verified'}
    def journal(values):return ''.join(k+'='+v.replace('\\','\\\\').replace(':','\\:')+'\n' for k,v in values.items()).encode('ascii')
    jr=journal(j);r={'passed':True,'actualJobDescendantsZero':True,'mutationRetried':False,'journalSHA256':m.sha(jr)}
    kwargs=dict(expected_journal_sha256=m.sha(jr),expected_release_sha256=p['releaseSHA256'],expected_application=app,expected_stage_root=stage,expected_data_directory=data)
    return p,j,r,kwargs,raw,journal

class PredecessorTests(unittest.TestCase):
    def setUp(self):self.p,self.j,self.r,self.k,self.raw,self.journal=fixture()
    def run_case(self,p=None,j=None,r=None,k=None):
        return m.verify_predecessor(self.raw(self.p if p is None else p),self.journal(self.j if j is None else j),self.raw(self.r if r is None else r),**(self.k if k is None else k))
    def test_valid_escaped_java_properties_and_utf8_rows(self):
        proof=self.run_case();self.assertTrue(proof['verified']);self.assertFalse(proof['authorizesSQL']);self.assertFalse(proof['provesLiveRuntime'])
    def test_immutable_journal_change_rejected(self):
        for key,value in [('phase','commit-confirmed'),('controllerPID','999'),('afterRowsSHA256','f'*64)]:
            j=copy.deepcopy(self.j);j[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_case(j=j)
    def test_modified_plan_rejected(self):
        for key,value in [('databaseUUID','00000000-0000-0000-0000-000000000002'),('attemptId','3'*32),('businessPort',50126),('application','D:\\Elsewhere')]:
            p=copy.deepcopy(self.p);p[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_case(p=p)
    def test_failed_incomplete_or_retried_predecessor_rejected(self):
        for key,value in [('passed',False),('actualJobDescendantsZero',False),('mutationRetried',True),('journalSHA256','f'*64)]:
            r=copy.deepcopy(self.r);r[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_case(r=r)
    def test_wrong_expected_scope_or_release_rejected(self):
        for key in ['expected_release_sha256','expected_application','expected_stage_root','expected_data_directory']:
            k=dict(self.k);k[key]='f'*64 if key.endswith('sha256')else'D:\\Wrong'
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_case(k=k)
    def test_duplicate_json_or_properties_not_accepted(self):
        with self.assertRaises(ValueError):m.object_json(b'{"stage":1,"stage":2}')
        with self.assertRaises(ValueError):m.properties(b'phase=a\nphase=b\n')
    def test_row_shape_identity_duplicates_and_unicode_are_checked(self):
        original=rows();self.assertEqual(m.rows_sha256(original),m.rows_sha256(copy.deepcopy(original)))
        bad=copy.deepcopy(original);bad[0][0]='foreign'
        with self.assertRaises(ValueError):m.rows_sha256(bad)
        with self.assertRaises(ValueError):m.rows_sha256([original[0],original[0]])
        with self.assertRaises(ValueError):m.rows_sha256([original[0][:-1],original[1]])
        bad=copy.deepcopy(original);bad[0][2]='changed';self.assertNotEqual(m.rows_sha256(bad),m.rows_sha256(original))
    def test_nonfinite_oversize_and_journal_controls_refused(self):
        with self.assertRaises(ValueError):m.object_json(b'{"x":NaN}')
        with self.assertRaises(ValueError):m.object_json(b' '*1048577)
        with self.assertRaises(ValueError):m.properties(b'phase=a\\nb\n')
    def test_wrong_phase_still_rejected_when_caller_updates_hash(self):
        j=dict(self.j);j['phase']='commit-confirmed';k=dict(self.k);k['expected_journal_sha256']=m.sha(self.journal(j));r=dict(self.r);r['journalSHA256']=k['expected_journal_sha256']
        with self.assertRaises(ValueError):self.run_case(j=j,r=r,k=k)

if __name__=='__main__':unittest.main(verbosity=2)
