from pathlib import Path
import hashlib
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from build_original_frontend import route, baseline_files, verify_inputs, deployment_environment, restore_mobile_generated_manifest
from prepare_original_frontend_gateway import checked_port, quoted, prepare

class DeploymentGuards(unittest.TestCase):
    def test_same_origin_routes(self):
        self.assertEqual(route('/tianjinrisk/api',False),'/tianjinrisk/api')
        self.assertEqual(route('/tianjinrisk/h5/',True),'/tianjinrisk/h5/')
        for value in ('https://remote/api','//remote/api','/api?token=x','/a/../b','/api;return','/'):
            with self.subTest(value=value),self.assertRaises(ValueError):route(value,False)

    def test_manifest_rejects_escape_and_duplicate(self):
        for path in ('../outside','/outside','x\\outside','C:/outside','a//b'):
            with self.subTest(path=path),self.assertRaises(ValueError):
                baseline_files({'projects':{'mobile':{'files':[{'path':path,'sha256':'a'*64}]}}},'mobile')
        with self.assertRaises(ValueError):baseline_files({'projects':{'mobile':{'files':[
            {'path':'src/x','sha256':'a'*64},{'path':'src/x','sha256':'b'*64}]}}},'mobile')

    def test_source_drift_and_unexpected_env_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'app.ts').write_text('original',encoding='utf-8')
            expected={'app.ts':hashlib.sha256(b'original').hexdigest()}
            verify_inputs(root,expected)
            (root/'.env.local').write_text('VITE_API_URL=https://wrong',encoding='utf-8')
            with self.assertRaises(ValueError):verify_inputs(root,expected)
            (root/'.env.local').unlink();(root/'app.ts').write_text('changed',encoding='utf-8')
            with self.assertRaises(ValueError):verify_inputs(root,expected)

    def test_build_environment_overrides_are_process_local(self):
        with patch.dict(os.environ,{'VITE_API_URL':'https://unexpected','NODE_OPTIONS':'--import=unexpected'},clear=False):
            env=deployment_environment('security_pc','/tianjinrisk/api','/tianjinrisk/')
            self.assertEqual(env['VITE_API_URL'],'/tianjinrisk/api')
            self.assertNotIn('NODE_OPTIONS',env)
            self.assertEqual(os.environ['VITE_API_URL'],'https://unexpected')
            mobile=deployment_environment('mobile','/tianjinrisk/api','/tianjinrisk/h5/')
            self.assertEqual(mobile['VITE_SERVER_BASEURL'],mobile['VITE_APP_PROXY_PREFIX'])
            self.assertEqual(mobile['VITE_APP_PROXY'],'true')

    def test_generated_mobile_manifest_only_known_base_change_restored(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source';copy=root/'copy';output=root/'output'
            (source/'src').mkdir(parents=True);(copy/'src').mkdir(parents=True);output.mkdir()
            original={'h5':{'router':{'base':'/h5/','mode':'history'}},'versionName':'fixture'}
            raw=json.dumps(original).encode();(source/'src/manifest.json').write_bytes(raw)
            expected={'src/manifest.json':hashlib.sha256(raw).hexdigest()}
            generated=json.loads(raw);generated['h5']['router']['base']='/tianjinrisk/h5/'
            (copy/'src/manifest.json').write_text(json.dumps(generated),encoding='utf-8')
            self.assertTrue(restore_mobile_generated_manifest(copy,expected,source,'/tianjinrisk/h5/',output))
            self.assertEqual((copy/'src/manifest.json').read_bytes(),raw)
            generated['versionName']='unexpected business configuration change'
            (copy/'src/manifest.json').write_text(json.dumps(generated),encoding='utf-8')
            with self.assertRaises(ValueError):restore_mobile_generated_manifest(copy,expected,source,'/tianjinrisk/h5/',output)
            self.assertEqual(json.loads((copy/'src/manifest.json').read_text())['versionName'],generated['versionName'])

    def test_gateway_configuration_requires_local_ports_and_safe_paths(self):
        for value in (True,80,0,65536,'30001'):
            with self.subTest(value=value),self.assertRaises(ValueError):checked_port(value)
        self.assertEqual(checked_port(30001),30001)
        for value in ('path;return','path$variable','path\nnext'):
            with self.subTest(value=value),self.assertRaises(ValueError):quoted(value)

    def test_gateway_fresh_output_and_incomplete_upstreams_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaises(ValueError):prepare(root,root,{},12000)
            with self.assertRaises(ValueError):prepare(root/'new',root,{},12000,20111,None)
            self.assertFalse((root/'new').exists())

if __name__=='__main__':unittest.main()
