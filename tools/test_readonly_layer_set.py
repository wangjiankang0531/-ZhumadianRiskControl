"""Read-only multi-file editor publication and real HTTP replacement safety."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from readonly_layer_set import ReadOnlyLayerSet, ReadOnlyBusinessRecords


def document(suffix):
    point=dict(id='point-'+suffix,name='Point '+suffix,type='point',positions=[[1,2,3]],
               style=dict(color='#112233',fillColor='#223344',pattern='dash',icon='warning',opacity=.4,fillOpacity=.3,widthPx=3.5,sizePx=24),
               label=dict(visible=True,text='Pending location verification',color='#FFFFFF',fontPx=16,opacity=.7,offset=[12,-16]),
               business=dict(objectType='enterprise',businessId='business-'+suffix,enterpriseId='enterprise-'+suffix,sourceSystem='fixture'))
    return dict(schema='hongtu.landscape.layers.v1',scene='zhumadian',coordinates=dict(srs='EPSG:32650',unit='metre',axes='east,north,up',origin=[225319.5,3648440.1,30.9]),
                metadata=dict(verification='pending',source='fixture-'+suffix),layers=[dict(id='layer-'+suffix,name='Layer '+suffix,visible=True,locked=True,features=[point])])


def records():
    return dict(schema='xnby.business.records.v1',scene='zhumadian',exportedAt='2026-10-19T12:28:29.546Z',ttlHours=24,
                records=[dict(sourceSystem='fixture',objectType='enterprise',businessId='business-enterprise',
                    enterpriseId='enterprise-enterprise',name='Enterprise fixture',updatedAt='2026-10-19T12:28:29.546Z',
                    attributes=[dict(label='Location verification',value='pending')])])


class LayerSetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='readonly-layers-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.primary=self.root/'editor.json';self.overlay=self.root/'enterprise.json'
        self.editor=document('editor');self.enterprises=document('enterprise')
        self.write(self.primary,self.editor);self.write(self.overlay,self.enterprises)

    @staticmethod
    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False),'utf-8')

    def pins(self):
        return [(p.stat().st_size,p.stat().st_mtime_ns,hashlib.sha256(p.read_bytes()).hexdigest()) for p in (self.primary,self.overlay)]

    def test_all_geometry_styles_business_ids_and_metadata_survive_without_source_writes(self):
        before=self.pins();source=ReadOnlyLayerSet(self.primary,[self.overlay]);combined=json.loads(source.read())
        self.assertEqual(combined['layers'],self.editor['layers']+self.enterprises['layers'])
        self.assertEqual(combined['metadata'],self.editor['metadata'])
        self.assertEqual(combined['viewerSourceDocuments']['sources'][1]['metadata']['metadata'],self.enterprises['metadata'])
        self.assertTrue(combined['viewerSourceDocuments']['readOnly']);self.assertEqual(before,self.pins())

    def test_new_valid_editor_save_is_seen_on_next_read_without_rewriting_overlay(self):
        source=ReadOnlyLayerSet(self.primary,[self.overlay]);old_overlay=self.pins()[1]
        edited=copy.deepcopy(self.editor);edited['layers'][0]['features'][0]['style']['widthPx']=7.5
        self.write(self.primary,edited);combined=json.loads(source.read())
        self.assertEqual(combined['layers'][0],edited['layers'][0]);self.assertEqual(old_overlay,self.pins()[1])

    def test_conflicting_ids_invalid_coordinates_and_invalid_style_are_rejected(self):
        for mutate in (lambda d:d['layers'][0].update(id='layer-editor'),
                       lambda d:d['layers'][0]['features'][0].update(id='point-editor'),
                       lambda d:d['coordinates'].update(origin=[0,0,0]),
                       lambda d:d['layers'][0]['features'][0]['style'].update(opacity=2)):
            other=copy.deepcopy(self.enterprises);mutate(other);self.write(self.overlay,other)
            with self.subTest(mutation=mutate):
                with self.assertRaises(ValueError):ReadOnlyLayerSet(self.primary,[self.overlay])
        self.write(self.overlay,self.enterprises)

    def test_size_bounds_duplicate_json_nonfinite_and_duplicate_paths_are_rejected(self):
        with self.assertRaises(ValueError):ReadOnlyLayerSet(self.primary,[self.primary])
        with self.assertRaises(ValueError):ReadOnlyLayerSet(self.primary,[self.overlay]*4)
        raw=self.overlay.read_bytes()
        for invalid in (raw[:-1]+b',"scene":"zhumadian"}',raw[:-1]+b',"extra":NaN}'):
            self.overlay.write_bytes(invalid)
            with self.assertRaises(ValueError):ReadOnlyLayerSet(self.primary,[self.overlay])
        self.overlay.write_bytes(raw)
        with patch('readonly_layer_set.LIMIT',len(raw)):
            with self.assertRaisesRegex(ValueError,'16 MiB'):ReadOnlyLayerSet(self.primary,[self.overlay])

    def test_cross_file_mutation_during_read_is_rejected_as_one_transaction(self):
        import readonly_layer_set as module
        original=module.snapshot;calls=0
        def changing(path):
            nonlocal calls
            calls+=1
            if calls==3:
                edited=copy.deepcopy(self.editor);edited['metadata']['source']='changed'
                self.write(self.primary,edited)
            return original(path)
        source=ReadOnlyLayerSet(self.primary,[self.overlay])
        with patch.object(module,'snapshot',side_effect=changing):
            with self.assertRaisesRegex(ValueError,'changed'):source.read()

    def test_business_snapshot_retains_exact_bytes_original_time_ttl_and_source_file(self):
        path=self.root/'records.json';self.write(path,records());before=path.read_bytes();mtime=path.stat().st_mtime_ns
        source=ReadOnlyBusinessRecords(path)
        self.assertEqual(source.read(),before);self.assertEqual(path.stat().st_mtime_ns,mtime)
        self.assertEqual(json.loads(source.read())['ttlHours'],24)
        self.assertEqual(json.loads(source.read())['exportedAt'],'2026-10-19T12:28:29.546Z')
        broken=records();broken['records'].append(copy.deepcopy(broken['records'][0]));self.write(path,broken)
        with self.assertRaises(ValueError):source.read()

    def test_real_preview_live_reload_rejection_and_configuration_ownership(self):
        resources=self.root/'resources';bundle=self.root/'bundle';state=self.root/'state.json'
        for name in ('index.html','viewer.js','source-gain-worker.js'):
            p=bundle/'web'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
        for rel in ('data/showcase/zhumadian_native_hierarchy.json','assets/landscape/icons.png',
                    'assets/showcase/runtime/zhumadian/context/context_fused.gltf','assets/showcase/runtime/zhumadian/context/context_fused.bin',
                    'assets/showcase/runtime/zhumadian/context/context_colormatched.jpg','assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf',
                    'assets/showcase/runtime/zhumadian/full/zhumadian_full.bin','assets/showcase/runtime/zhumadian/full/zhumadian_full_atlas.jpg',
                    'assets/showcase/runtime/zhumadian/full/base_lod_quality.json'):
            p=resources/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'fixture')
        before=self.pins();business=self.root/'records.json';self.write(business,records());business_before=business.read_bytes()
        args=[sys.executable,'-I','-B',str(Path(__file__).with_name('serve_native_preview.py')),
              '--bundle',str(bundle),'--resources',str(resources),'--layers',str(self.primary),
              '--layer-overlay',str(self.overlay),'--business-records',str(business),'--state',str(state),'--no-browser']
        flags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0
        proc=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=flags)
        http=build_opener(ProxyHandler({}))
        def request(path,method='GET',headers=None):
            try:response=http.open(Request(url+path,method=method,headers=headers or {}),timeout=5)
            except HTTPError as error:response=error
            with response:return response.status,response.read(),dict(response.headers)
        try:
            deadline=time.monotonic()+8
            while not state.exists():
                if proc.poll() is not None:self.fail(proc.stderr.read().decode(errors='replace'))
                if time.monotonic()>deadline:self.fail('layer preview readiness timeout')
                time.sleep(.02)
            saved=json.loads(state.read_bytes());url='http://127.0.0.1:'+str(saved['port'])
            status,raw,headers=request('/layers/default.json');self.assertEqual(status,200)
            self.assertEqual(json.loads(raw)['layers'],self.editor['layers']+self.enterprises['layers'])
            self.assertEqual(headers['X-XNBY-Layer-Source-Count'],'2')
            self.assertEqual(request('/layers/default.json','HEAD')[:2],(200,b''))
            self.assertEqual(request('/layers/default.json?file=C:/Windows/win.ini')[0],400)
            self.assertEqual(before,self.pins())
            self.assertEqual(request('/application/config.json')[:2],(200,b'{"schema":"xnby.portal.config.v1","mode":"local"}'))
            self.assertEqual(request('/business/default.json')[:2],(200,business_before))
            self.assertEqual(request('/business/default.json','HEAD')[:2],(200,b''))
            self.assertEqual(request('/business/default.json?file=other')[0],400)
            business.write_bytes(b'{invalid')
            self.assertEqual(request('/business/default.json')[0],422)
            self.assertEqual(request('/layers/default.json')[0],200)
            business.write_bytes(business_before)
            edited=copy.deepcopy(self.editor);edited['layers'][0]['features'][0]['name']='New editor save'
            self.write(self.primary,edited)
            self.assertEqual(json.loads(request('/layers/default.json')[1])['layers'][0],edited['layers'][0])
            good_raw=self.overlay.read_bytes();self.overlay.write_bytes(b'{invalid')
            self.assertEqual(request('/layers/default.json')[0],422)
            self.overlay.write_bytes(good_raw)
            self.assertEqual(request('/layers/default.json')[0],200)
            wrong=list(args);wrong[wrong.index('--layer-overlay')+1]=str(self.root/'another.json')
            refused=subprocess.run(wrong,capture_output=True,timeout=5)
            self.assertNotEqual(refused.returncode,0);self.assertIn(b'different layer sources',refused.stderr)
            self.assertEqual(saved['PID'],json.loads(state.read_bytes())['PID'])
        finally:
            if proc.poll() is None and state.exists():
                saved=json.loads(state.read_bytes());url='http://127.0.0.1:'+str(saved['port'])
                request('/__preview__/stop','POST',{'X-Preview-Key':saved['controlKey']});proc.wait(timeout=5)
            if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
            errors=proc.stderr.read().decode(errors='replace');proc.stderr.close()
        self.assertEqual(proc.returncode,0,errors)


if __name__=='__main__':unittest.main()
