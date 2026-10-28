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
from urllib.request import build_opener,ProxyHandler,Request
sys.path.insert(0,str(Path(__file__).resolve().parent))
import preview_osgb_data_lod as module
from test_osgb_v80_data_reader import fixture
import test_readonly_level_index as level_fixture

sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda v:json.dumps(v,separators=(',',':')).encode()


class Prepared:
    def __init__(self):self.calls=[];self.closed=False
    def health(self):return dict(nativeReaderEnabled=False,conversionEnabled=False,preparedSourceCount=1)
    def handle(self,h):self.calls.append(h.path);h.reply(418,b'prepared');return True
    def close(self):self.closed=True


class Handler:
    command='GET'
    path='/'
    def reply(self,*args,**kwargs):self.result=args;self.headers=kwargs.get('headers') or {}


class SourceFixture:
    def __init__(self,root):
        self.identity='fixture-catalog';self.records={1:{}};self.root=root/'Data';(self.root/'Tile_1').mkdir(parents=True)
        self.raw,_=fixture();self.names=('Tile_1_L16_0u.osgb','Tile_1_L17_0uu.osgb')
        for name in self.names:(self.root/'Tile_1'/name).write_bytes(self.raw)
    def __call__(self,tile):
        if tile!=1:raise KeyError(tile)
        return dict(tile_id=1,source_directory='assets/驻马店园区/Data/Tile_1',root=self.names[0],nodes=[dict(name=name,children=[self.names[1]] if i==0 else [],level=16+i,bytes=len(self.raw),sha256=sha(self.raw)) for i,name in enumerate(self.names)])


class DataPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.catalogs=SourceFixture(self.root);self.prepared=Prepared()
        with patch.object(module,'PinnedCatalogs',return_value=self.catalogs):self.lod=module.PreviewOSGBDataLOD(self.prepared,self.root,self.catalogs.root,[1])
        self.addCleanup(self.lod.close)
    def request(self,path,method='GET'):
        h=Handler();h.path=path;h.command=method;self.assertTrue(self.lod.handle(h));return h
    def ready(self,path='/api/lod-plan/1/1?wait_ms=200'):
        deadline=time.monotonic()+4
        while True:
            h=self.request(path)
            if h.result[0]!=202:self.assertEqual(h.result[0],200);return json.loads(h.result[1])
            if time.monotonic()>deadline:self.fail('data job did not finish')
    def test_explicit_tile_ids_are_bounded_unique_and_canonical(self):
        self.assertEqual(module.parse_data_tiles('66,1'),(1,66))
        for v in ('','0','01','1,1','2347','1, 2','1/2',','.join(str(i) for i in range(1,258))):
            with self.subTest(v=v),self.assertRaises(ValueError):module.parse_data_tiles(v)
    def test_plan_grant_three_payloads_matching_lease_and_release(self):
        source=self.catalogs.root/'Tile_1'/self.catalogs.names[1];before=source.read_bytes();plan=self.ready()
        self.assertEqual(plan['verification'],'metadata_only');self.assertFalse(plan['availabilityVerified'])
        granted=self.request('/api/lod/1/1');marker=json.loads(granted.result[1]);token=marker['cache_lease'];self.assertEqual(granted.source_marker_sha256,plan['markerSHA256'])
        self.assertEqual(marker['source_format'],'osgb_memory_png_v1');self.assertTrue(marker['complete_frontier'])
        for file in marker['parts'][0]['files']:
            h=self.request(f"/native/tile_1_depth_1/part_000/{file['name']}?lease={token}")
            self.assertEqual(h.result[0],200);self.assertEqual(sha(h.result[1]),file['sha256'])
        self.assertEqual(self.request('/api/lod-lease/'+token+'/release','POST').result[0],204)
        self.assertEqual(self.request('/native/tile_1_depth_1/part_000/texture.png?lease='+token).result[0],409)
        self.assertEqual(before,source.read_bytes())
    def test_family_is_complete_and_lease_cannot_read_a_different_folder(self):
        self.ready('/api/lod-family-plan/1/'+self.catalogs.names[0]+'?wait_ms=200')
        marker=json.loads(self.request('/api/lod-family/1/'+self.catalogs.names[0]).result[1]);token=marker['cache_lease'];self.assertTrue(marker['complete_sibling_family'])
        self.assertEqual(self.request('/native/tile_1_depth_1/part_000/texture.png?lease='+token).result[0],409)
    def test_unknown_tiles_and_nonowned_tokens_use_only_original_prepared_handler(self):
        for path in ('/api/lod-plan/2/1','/native/tile_2_depth_1/part_000/atlas.jpg?lease='+'a'*32,'/api/lod-lease/'+'b'*32+'/release'):
            h=self.request(path,'POST' if 'release' in path else 'GET');self.assertEqual(h.result[0],418)
        self.assertEqual(self.lod.memory.audit()['builds'],0)
    def test_malformed_queries_paths_and_writes_never_start_data_work(self):
        for path in ('/api/lod-plan/1/1?wait_ms=201','/api/lod-plan/1/1?wait_ms=200&wait_ms=200','/api/lod/1/1?wait_ms=200','/api/lod-family/1/Tile_2_L16_0u.osgb','/native/tile_1_depth_1/part_000/atlas.jpg?lease='+'a'*32,'/api/lod/1/13'):
            with self.subTest(path=path):self.assertEqual(self.request(path).result[0],400)
        self.assertEqual(self.request('/api/lod-plan/1/1','POST').result[0],405)
        self.assertEqual(self.lod.memory.audit()['builds'],0)
    def test_building_busy_and_validation_errors_do_not_fall_back_to_file_cache(self):
        with patch.object(self.lod.memory,'plan',return_value=None):self.assertEqual(self.request('/api/lod-plan/1/1').result[0],202)
        for error,status in ((module.MemoryStoreBusy('busy'),503),(ValueError('secret path'),422),(PermissionError('secret path'),409)):
            with patch.object(self.lod.memory,'plan',side_effect=error):
                h=self.request('/api/lod-plan/1/1');self.assertEqual(h.result[0],status);self.assertNotIn(b'secret',h.result[1])
        self.assertEqual(self.prepared.calls,[])
    def test_bounded_wait_acknowledgement_covers_pending_and_ready_without_changing_plan(self):
        with patch.object(self.lod.memory,'plan',return_value=None) as plan:
            h=self.request('/api/lod-plan/1/1?wait_ms=200')
            self.assertEqual(h.result[0],202);self.assertEqual(h.headers,{'X-XNBY-Source-Plan-Wait-Ms':'200'})
            self.assertEqual(plan.call_args.kwargs['wait_ms'],200)
        self.ready()
        h=self.request('/api/lod-plan/1/1?wait_ms=200');self.assertEqual(h.result[0],200)
        self.assertEqual(h.headers,{'X-XNBY-Source-Plan-Wait-Ms':'200'})
        self.assertEqual(self.request('/api/lod-plan/1/1').headers,{})
        self.assertEqual(self.request('/api/lod/1/1').headers,{})

    def test_optional_full_image_sampler_pages_keep_lease_contract_and_report_actual_policy(self):
        self.lod.close()
        with patch.object(module,'PinnedCatalogs',return_value=self.catalogs):self.lod=module.PreviewOSGBDataLOD(self.prepared,self.root,self.catalogs.root,[1],sampler_pages=True)
        self.addCleanup(self.lod.close)
        plan=self.ready();image=plan['marker']['parts'][0]['source_image']
        self.assertEqual(plan['marker']['source_format'],'osgb_memory_png_crop_v2');self.assertEqual(image['mip_levels'],1)
        self.assertEqual(image['source_rect'],[0,0,image['width'],image['height']]);self.assertEqual(image['uv_transform'],[1,1,0,0])
        self.assertEqual(self.lod.health()['pythonOriginalSources']['pagePolicy'],'source_sampler_full_image_v2')
        granted=self.request('/api/lod/1/1');marker=json.loads(granted.result[1]);self.assertEqual(granted.source_marker_sha256,plan['markerSHA256'])
        token=marker['cache_lease']
        for file in marker['parts'][0]['files']:
            self.assertEqual(sha(self.request('/native/tile_1_depth_1/part_000/'+file['name']+'?lease='+token).result[1]),file['sha256'])
        self.assertEqual(self.request('/api/lod-lease/'+token+'/release','POST').result[0],204)

    def test_health_exposes_only_bounded_counts_and_no_source_paths(self):
        h=self.request('/api/health');value=json.loads(h.result[1]);self.assertFalse(value['nativeReaderEnabled']);self.assertFalse(value['conversionEnabled'])
        self.assertEqual(value['pythonOriginalSources']['tiles'],[1]);self.assertNotIn(str(self.root),h.result[1].decode());self.assertEqual(value['pythonOriginalSources']['limit'],256*1048576)


class DataPreviewCLITests(unittest.TestCase):
    def test_actual_isolated_preview_and_configuration_reuse(self):self.exercise_mode('1')
    def test_actual_indexed_missing_preview_and_corrupt_prepared_refusal(self):self.exercise_mode('indexed-missing')
    def exercise_mode(self,mode):
        fixture_index=level_fixture.LevelIndexTests('runTest');fixture_index.setUp();self.addCleanup(fixture_index.doCleanups)
        root=fixture_index.root;source=SourceFixture(root);resources=fixture_index.resources;index=fixture_index.index
        catalog=source(1);catalog_raw=encode(catalog);fixture_index.write(resources/'assets/showcase/runtime/zhumadian/native_hierarchy/tile_1.json',catalog_raw)
        fixture_index.master['root_records'][0]['sha256']=sha(catalog_raw);master=encode(fixture_index.master);fixture_index.write(resources/'data/showcase/zhumadian_native_hierarchy.json',master)
        fixture_index.root_index.update(sourceManifestSHA256=sha(master));fixture_index.root_index['roots'][0]['catalogSHA256']=sha(catalog_raw);root_raw=encode(fixture_index.root_index);fixture_index.write(index/'root_index.json',root_raw)
        tile=fixture_index.tile;tile.update(sourceManifestSHA256=sha(master),catalogSHA256=sha(catalog_raw))
        for n in tile['nodes']:n.update(sourceSHA256=sha(source.raw),sourceBytes=len(source.raw))
        tile_raw=encode(tile);fixture_index.write(index/'tile_1.json',tile_raw)
        fixture_index.manifest.update(sourceManifestSHA256=sha(master),rootIndexSHA256=sha(root_raw));fixture_index.manifest['tiles'][0].update(bytes=len(tile_raw),sha256=sha(tile_raw));fixture_index.write(index/'index_manifest.json',encode(fixture_index.manifest))
        bundle=root/'bundle';project=root/'project.json';project.write_bytes(b'{"user":"unchanged"}');state=root/'service.json'
        for name in ('index.html','viewer.js','source-gain-worker.js'):fixture_index.write(bundle/'web'/name,b'fixture')
        for rel in ('assets/landscape/icons.png','assets/showcase/runtime/zhumadian/context/context_fused.gltf','assets/showcase/runtime/zhumadian/context/context_fused.bin','assets/showcase/runtime/zhumadian/context/context_colormatched.jpg','assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf','assets/showcase/runtime/zhumadian/full/zhumadian_full.bin','assets/showcase/runtime/zhumadian/full/zhumadian_full_atlas.jpg','assets/showcase/runtime/zhumadian/full/base_lod_quality.json'):fixture_index.write(resources/rel,b'fixture')
        (resources/'work/zhumadian_native_chunk_cache').mkdir(parents=True)
        before={str(p):(p.stat().st_size,p.stat().st_mtime_ns,sha(p.read_bytes())) for base in (resources,index,source.root) for p in base.rglob('*') if p.is_file()}
        args=[sys.executable,'-I','-B',str(Path(__file__).with_name('serve_native_preview.py')),'--bundle',str(bundle),'--resources',str(resources),'--layers',str(project),'--state',str(state),'--prepared-lod','--level-index',str(index),'--osgb-data-root',str(source.root),'--osgb-data-tiles',mode,'--osgb-data-sampler-pages','--no-browser']
        proc=subprocess.Popen(args,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0);http=build_opener(ProxyHandler({}));url=None
        def request(path,method='GET',headers=None):
            try:r=http.open(Request(url+path,method=method,headers=headers or {}),timeout=5)
            except HTTPError as error:r=error
            with r:return r.status,r.read(),dict(r.headers)
        try:
            deadline=time.monotonic()+8
            while not state.exists():
                if proc.poll() is not None:self.fail(proc.stderr.read().decode(errors='replace'))
                if time.monotonic()>deadline:self.fail('data preview startup deadline')
                time.sleep(.02)
            saved=json.loads(state.read_bytes());url='http://127.0.0.1:'+str(saved['port'])
            self.assertEqual(saved['osgbDataTiles'],'indexed-missing' if mode=='indexed-missing' else [1]);self.assertEqual(request('/api/health')[0],200);self.assertTrue(saved['osgbDataSamplerPages'])
            if mode=='indexed-missing':
                detail=json.loads(request('/api/health')[1])['pythonOriginalSources'];self.assertEqual(detail['tileCount'],2346);self.assertNotIn('tiles',detail)
                bad=resources/'work/zhumadian_native_chunk_cache/tile_1_depth_1';bad.mkdir();(bad/'complete.json').write_bytes(b'{}')
                self.assertEqual(request('/api/lod-plan/1/1?wait_ms=200')[0],422)
                self.assertEqual(json.loads(request('/api/health')[1])['pythonOriginalSources']['builds'],0)
                (bad/'complete.json').unlink();bad.rmdir()
            deadline=time.monotonic()+5
            while True:
                status,raw,headers=request('/api/lod-plan/1/1?wait_ms=200')
                self.assertEqual(headers.get('X-XNBY-Source-Plan-Wait-Ms'),'200')
                if status!=202:self.assertEqual(status,200,raw);break
                self.assertLess(time.monotonic(),deadline)
            marker=json.loads(request('/api/lod/1/1')[1]);token=marker['cache_lease']
            for name in ('geometry.gltf','geometry.bin','texture.png'):
                path='/native/tile_1_depth_1/part_000/'+name+'?lease='+token;self.assertEqual(request(path)[0],200);self.assertEqual(request(path,'HEAD')[:2],(200,b''))
            self.assertEqual(request('/api/lod-lease/'+token+'/release','POST')[0],204)
            self.assertEqual(request('/native/tile_1_depth_1/part_000/texture.png?lease='+token)[0],409)
            self.assertEqual(request('/api/health',headers={'Host':'unrelated.invalid'})[0],403)
            for changed in ('tiles','disabled','sampler'):
                wrong=list(args)
                if changed=='tiles':wrong[wrong.index('--osgb-data-tiles')+1]='1,2'
                elif changed=='sampler':wrong.remove('--osgb-data-sampler-pages')
                else:
                    wrong.remove('--osgb-data-sampler-pages')
                    for flag in ('--osgb-data-tiles','--osgb-data-root'):at=wrong.index(flag);del wrong[at:at+2]
                result=subprocess.run(wrong,capture_output=True,timeout=5);self.assertNotEqual(result.returncode,0);self.assertIn(b'different OSGB data source',result.stderr)
            self.assertEqual(before,{str(p):(p.stat().st_size,p.stat().st_mtime_ns,sha(p.read_bytes())) for base in (resources,index,source.root) for p in base.rglob('*') if p.is_file()})
            self.assertEqual(project.read_bytes(),b'{"user":"unchanged"}')
        finally:
            if proc.poll() is None and state.exists():
                saved=json.loads(state.read_bytes());url='http://127.0.0.1:'+str(saved['port']);request('/__preview__/stop','POST',{'X-Preview-Key':saved['controlKey']});proc.wait(timeout=5)
            if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
            stderr=proc.stderr.read();proc.stderr.close()
        self.assertEqual(proc.returncode,0,stderr.decode(errors='replace'))



class IndexedMissingRoutingTests(DataPreviewTests):
    # Reuse the actual source fixture and exercise both routing contracts.
    def setUp(self):
        super().setUp();self.lod.close()
        from types import SimpleNamespace
        self.catalogs.identity='a'*64;self.catalogs.records={i:{} for i in range(1,2347)}
        self.caches=[self.root/'prepared-a',self.root/'prepared-b']
        for p in self.caches:p.mkdir()
        self.prepared.sources=SimpleNamespace(stores=[SimpleNamespace(cache=p) for p in self.caches]);self.prepared.owners={}
        with patch.object(module,'PinnedCatalogs',return_value=self.catalogs):self.lod=module.PreviewOSGBDataLOD(self.prepared,self.root,self.catalogs.root,'indexed-missing',index_identity='b'*64)
        self.addCleanup(self.lod.close)
    # These explicit-list-specific assertions have their own indexed equivalents.
    def test_unknown_tiles_and_nonowned_tokens_use_only_original_prepared_handler(self):
        self.assertEqual(self.request('/api/lod-lease/'+'b'*32+'/release','POST').result[0],418)
        self.assertEqual(self.request('/api/lod-plan/2347/1').result[0],418)
    def test_health_exposes_only_bounded_counts_and_no_source_paths(self):
        h=self.request('/api/health');v=json.loads(h.result[1])['pythonOriginalSources']
        self.assertNotIn('tiles',v);self.assertEqual(v['tileCount'],2346);self.assertEqual(v['indexIdentity'],'b'*64)
        self.assertEqual(v['sourceManifestSHA256'],'a'*64);self.assertTrue(v['preparedFirst']);self.assertNotIn(str(self.root),h.result[1].decode())
    def test_present_markers_on_either_store_delegate_even_when_invalid(self):
        for i,path in enumerate(('/api/lod-plan/1/1?wait_ms=200','/api/lod-family-plan/1/'+self.catalogs.names[0]+'?wait_ms=200')):
            name='tile_1_depth_1' if i==0 else 'family_tile_1_'+sha(self.catalogs.names[0].encode())[:16]
            target=self.caches[i]/name/'complete.json';target.parent.mkdir();target.write_bytes(b'not a valid marker')
            for endpoint in (path,path.replace('-plan','').split('?')[0]):
                self.assertEqual(self.request(endpoint).result[0],418)
        self.assertEqual(self.lod.memory.audit()['builds'],0)
    def test_prepared_lease_payload_uses_its_validator_without_memory_access(self):
        token='d'*32;self.prepared.owners[token]=object()
        with patch.object(self.lod.memory,'payload',side_effect=AssertionError('must use prepared validator')):
            for name in ('geometry.gltf','geometry.bin','atlas.jpg'):
                self.assertEqual(self.request('/native/tile_1_depth_1/part_000/'+name+'?lease='+token).result[0],418)
        self.assertEqual(self.request('/native/tile_1_depth_1/part_000/atlas.jpg?lease='+'e'*32).result[0],400)
        self.assertEqual(self.request('/native/tile_1_depth_1/part_000/geometry.bin?lease='+'e'*32).result[0],409)
    def test_indexed_scope_requires_complete_catalog_and_valid_index_identity(self):
        for key,value in (('index_identity',None),('index_identity','bad'),('records',{1:{}}),('identity','bad')):
            previous=getattr(self.catalogs,key,None)
            if key!='index_identity':setattr(self.catalogs,key,value)
            try:
                with patch.object(module,'PinnedCatalogs',return_value=self.catalogs),self.assertRaises(ValueError):
                    module.PreviewOSGBDataLOD(self.prepared,self.root,self.catalogs.root,'indexed-missing',index_identity=value if key=='index_identity' else 'b'*64)
            finally:
                if key!='index_identity':setattr(self.catalogs,key,previous)

if __name__=='__main__':unittest.main()
