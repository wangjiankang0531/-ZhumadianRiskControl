import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from original_frontend_deployment_assets import HOME_HANDLER,ORIGINAL_HOME_OPEN,ORIGINAL_COMMAND,COMMAND_URL,home_deployment_override,home_navigation_adapter

class AdminHomeDeploymentTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Existing Node required')
    def test_admin_target_is_same_origin_and_original_menu_remains_intact(self):
        source=HOME_HANDLER+b'\nif (!item.path) return;\nif (item.enCode == "mjyjzh") {\n'+ORIGINAL_COMMAND+b'\nreturn;\n}\n'+ORIGINAL_HOME_OPEN+b'\n};'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);reference=root/'reference';project=root/'project'
            for p in (reference,project):
                (p/'src/views/home').mkdir(parents=True);(p/'src/views/home/index.vue').write_bytes(source)
            with home_deployment_override(project,reference,True,'/zhumadian','/zhumadian/admin') as receipt:
                script=(project/'src/views/home/index.vue').read_text('utf-8')
                assertions='''
const item=Object.freeze({enCode:'syslink',path:'https://old.example/admin/?t=private-fixture&user=private-user'});
handleTo(item);let target=opened.pop();
if(target[0]!='/zhumadian/admin/'||target[1]!='_blank'||item.path.indexOf('private-fixture')<0)throw Error('Admin path or original object changed');
handleTo(Object.freeze({enCode:'other',path:'https://other.example/original?x=1'}));
if(opened.pop()[0]!='https://other.example/original?x=1')throw Error('Unrelated external link changed');
handleTo(Object.freeze({enCode:'normal',path:'/tianjinrisk/emergency?x=1#row'}));
if(opened.pop()[0]!='/zhumadian/emergency?x=1#row')throw Error('Internal route changed');
handleTo(Object.freeze({enCode:'mjyjzh',path:'http://old.example/command'}));
if(opened.pop()[0]!=='''+json.dumps(COMMAND_URL)+''')throw Error('Local command changed');
console.log('admin-home-deployment-passed');
'''
                run=subprocess.run([shutil.which('node'),'--input-type=module','-e','const opened=[];const window={open:(...args)=>opened.push(args)};\n'+script+assertions],capture_output=True,text=True,timeout=15)
                self.assertEqual(run.returncode,0,run.stderr);self.assertIn('admin-home-deployment-passed',run.stdout)
                self.assertEqual(receipt['adminHomeBase'],'/zhumadian/admin');self.assertFalse(receipt['menuRowsChanged']);self.assertFalse(receipt['adminLoginTokenOrUserForwarded'])
            self.assertTrue(receipt['sourceRestored']);self.assertEqual((reference/'src/views/home/index.vue').read_bytes(),source);self.assertEqual((project/'src/views/home/index.vue').read_bytes(),source)

    def test_admin_target_rejects_other_origins_routes_queries_and_missing_home_base(self):
        for value in ('https://other.example/admin','//other/admin','/other/admin','/zhumadian/admin/','/zhumadian/admin?t=x','/zhumadian/../admin'):
            with self.subTest(value=value),self.assertRaises(ValueError):home_navigation_adapter('/zhumadian',value)
        with self.assertRaises(ValueError):home_navigation_adapter(None,'/zhumadian/admin')

if __name__=='__main__':unittest.main()
