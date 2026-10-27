"""Immutable metadata and real preview HTTP tests; no native/GIS fixtures."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler, Request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from readonly_level_index import ReadOnlyLevelIndex


def encoded(value):
    return json.dumps(value, separators=(',', ':')).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class LevelIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='readonly-level-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.resources, self.index = self.root/'resources', self.root/'index'
        self.index.mkdir()
        names = ['Tile_1_L16_0u.osgb', 'Tile_1_L17_0uu.osgb']
        self.catalog = dict(tile_id=1, root=names[0], nodes=[
            dict(name=names[0], children=[names[1]], level=16, bytes=1, sha256=sha(b'a')),
            dict(name=names[1], children=[], level=17, bytes=1, sha256=sha(b'b'))])
        self.catalog_bytes = encoded(self.catalog)
        self.write(self.resources/'assets/showcase/runtime/zhumadian/native_hierarchy/tile_1.json', self.catalog_bytes)
        self.master = dict(root_records=[dict(tile_id=i, sha256=sha(self.catalog_bytes),
            catalog=f'assets/showcase/runtime/zhumadian/native_hierarchy/tile_{i}.json',
            bounds_min=[0, 0, 0], bounds_max=[1, 1, 1]) for i in range(1, 2347)])
        master_raw = encoded(self.master)
        self.write(self.resources/'data/showcase/zhumadian_native_hierarchy.json', master_raw)
        nodes = [dict(name=n['name'], children=n['children'], level=n['level'], depth=d,
                      sourceSHA256=n['sha256'], sourceBytes=1, edgeP90=1/(d+1), texelP90=1/(d+1),
                      boundsMin=[0, 0, 0], boundsMax=[1, 1, 1], subtreeMin=[0, 0, 0], subtreeMax=[1, 1, 1])
                 for d, n in enumerate(self.catalog['nodes'])]
        self.tile = dict(schema='zhumadian.level_bounds.tile.v1', tile=1, complete=True, root=names[0],
                         roots=[names[0]], sourceManifestSHA256=sha(master_raw), catalogSHA256=sha(self.catalog_bytes),
                         boundsMin=[0, 0, 0], boundsMax=[1, 1, 1], nodes=nodes)
        raw = encoded(self.tile)
        self.write(self.index/'tile_1.json', raw)
        self.root_index = dict(schema='zhumadian.level_bounds.roots.v1', sourceManifestSHA256=sha(master_raw),
            coordinateSystem='source_local_metres', boundsSource='union_of_original_subtree_geometry',
            roots=[dict(id=i, tile=i, boundsMin=[0, 0, 0], boundsMax=[1, 1, 1], catalogSHA256=sha(self.catalog_bytes),
                   coverageTiers=[dict(depth=d, sourceCount=1, maxTexel=.5) for d in range(1, 4)]) for i in range(1, 2347)])
        root_raw = encoded(self.root_index)
        self.write(self.index/'root_index.json', root_raw)
        self.manifest = dict(schema='zhumadian.level_bounds.manifest.v1', sourceManifestSHA256=sha(master_raw),
            boundsSource='exact_original_geometry', sourceWrites=0, sourceNodes=4692, rootIndexSHA256=sha(root_raw),
            tiles=[dict(tile=i, path=f'tile_{i}.json', bytes=len(raw), sha256=sha(raw), sourceNodes=2) for i in range(1, 2347)])
        self.write(self.index/'index_manifest.json', encoded(self.manifest))

    @staticmethod
    def write(path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def provider(self):
        return ReadOnlyLevelIndex(self.index, self.resources)

    def reseal_tile(self, value):
        raw = encoded(value)
        self.write(self.index/'tile_1.json', raw)
        self.manifest['tiles'][0].update(bytes=len(raw), sha256=sha(raw))
        self.write(self.index/'index_manifest.json', encoded(self.manifest))

    def snapshot(self):
        return {str(p.relative_to(self.root)):(p.stat().st_size, p.stat().st_mtime_ns, sha(p.read_bytes()))
                for base in (self.resources, self.index) for p in base.rglob('*') if p.is_file()}

    def test_lazy_delivery_revalidates_and_does_not_write_or_read_native_sources(self):
        before = self.snapshot()
        provider = self.provider()
        self.assertEqual(provider.file('tile_1.json'), encoded(self.tile))
        self.assertEqual(provider.file('root_index.json'), encoded(self.root_index))
        self.assertEqual(provider.file('index_manifest.json'), encoded(self.manifest))
        self.assertEqual(before, self.snapshot())
        self.assertFalse(any('reader' in p.name for p in self.root.rglob('*')))

    def test_manifest_and_root_mutations_are_rejected_after_initialization(self):
        for name in ('index_manifest.json', 'root_index.json'):
            with self.subTest(name=name):
                provider = self.provider()
                path = self.index/name
                before = path.read_bytes()
                path.write_bytes(before+b' ')
                with self.assertRaisesRegex(ValueError, 'changed|SHA differs'):
                    provider.file(name)
                path.write_bytes(before)

    def test_same_length_tile_and_source_catalog_mutations_are_rejected(self):
        provider = self.provider()
        for path in (self.index/'tile_1.json', self.resources/'assets/showcase/runtime/zhumadian/native_hierarchy/tile_1.json'):
            with self.subTest(path=path):
                before = path.read_bytes()
                changed = bytearray(before);changed[-2] ^= 1
                path.write_bytes(changed)
                with self.assertRaisesRegex(ValueError, 'SHA differs'):
                    provider.file('tile_1.json')
                path.write_bytes(before)

    def test_hash_valid_but_wrong_topology_identity_bounds_and_tiers_are_rejected(self):
        mutations = [lambda d:d.update(sourceManifestSHA256='a'*64),
                     lambda d:d['nodes'][1].update(sourceSHA256='b'*64),
                     lambda d:d['nodes'][1].update(depth=3),
                     lambda d:d['nodes'][0].update(subtreeMax=[.5, .5, .5]),
                     lambda d:d['nodes'][1].update(texelP90=.6),
                     lambda d:d['nodes'][1].update(edgeP90=-1)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                value = copy.deepcopy(self.tile);mutate(value);self.reseal_tile(value)
                with self.assertRaises(ValueError):self.provider().file('tile_1.json')
        self.reseal_tile(self.tile)

    def test_unlisted_paths_partial_forests_and_duplicate_json_are_rejected(self):
        provider = self.provider()
        for name in ('../index_manifest.json', 'tile_0.json', 'tile_2347.json', 'tile_01.json', 'C:/Windows/win.ini'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):provider.file(name)
        before = encoded(self.manifest)
        self.manifest['tiles'].pop()
        self.write(self.index/'index_manifest.json', encoded(self.manifest))
        with self.assertRaisesRegex(ValueError, 'Incomplete'):self.provider()
        self.write(self.index/'index_manifest.json', before[:-1]+b',"sourceWrites":0}')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):self.provider()

    def test_preview_cli_delivers_index_with_native_disabled_and_existing_leases_unchanged(self):
        bundle, state, project = self.root/'bundle', self.root/'state.json', self.root/'layers.json'
        self.write(project, b'{"user":"unchanged"}')
        for name in ('index.html', 'viewer.js', 'source-gain-worker.js'):
            self.write(bundle/'web'/name, b'fixture')
        for rel in ('assets/landscape/icons.png', 'assets/showcase/runtime/zhumadian/context/context_fused.gltf',
                    'assets/showcase/runtime/zhumadian/context/context_fused.bin', 'assets/showcase/runtime/zhumadian/context/context_colormatched.jpg',
                    'assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf', 'assets/showcase/runtime/zhumadian/full/zhumadian_full.bin',
                    'assets/showcase/runtime/zhumadian/full/zhumadian_full_atlas.jpg', 'assets/showcase/runtime/zhumadian/full/base_lod_quality.json'):
            self.write(self.resources/rel, b'fixture')
        (self.resources/'work/zhumadian_native_chunk_cache').mkdir(parents=True)
        before = self.snapshot()
        args = [sys.executable, '-I', '-B', str(Path(__file__).with_name('serve_native_preview.py')),
                '--bundle', str(bundle), '--resources', str(self.resources), '--layers', str(project),
                '--state', str(state), '--prepared-lod', '--level-index', str(self.index), '--no-browser']
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=flags)
        http = build_opener(ProxyHandler({}))
        def request(path, method='GET', headers=None):
            try:r=http.open(Request(url+path, method=method, headers=headers or {}), timeout=5)
            except HTTPError as error:r=error
            with r:return r.status,r.read(),dict(r.headers)
        try:
            deadline = time.monotonic()+8
            while not state.exists():
                if proc.poll() is not None:self.fail(proc.stderr.read().decode(errors='replace'))
                if time.monotonic()>deadline:self.fail('preview readiness timeout')
                time.sleep(.02)
            saved = json.loads(state.read_bytes());url = 'http://127.0.0.1:'+str(saved['port'])
            self.assertEqual(saved['levelIndexDirectory'],str(self.index.resolve()))
            self.assertEqual(saved['levelIndexIdentity'],sha(encoded(self.manifest)))
            self.assertIn(b'?levelIndex=1',request('/__preview__/status')[1])
            reopened=subprocess.run(args,capture_output=True,timeout=5)
            self.assertEqual(reopened.returncode,0,reopened.stderr.decode(errors='replace'))
            other_args=list(args);other_args[other_args.index('--level-index')+1]=str(self.root/'other-index')
            refused=subprocess.run(other_args,capture_output=True,timeout=5)
            self.assertNotEqual(refused.returncode,0)
            self.assertIn(b'different LEVEL index',refused.stderr)
            self.assertEqual(json.loads(state.read_bytes())['PID'],saved['PID'])
            status, raw, headers = request('/api/level-index/status')
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(raw)['roots'], 2346)
            self.assertEqual(headers['X-XNBY-Level-Index-SHA256'], sha(encoded(self.manifest)))
            for name in ('index_manifest.json', 'root_index.json', 'tile_1.json'):
                path = '/api/level-index/files/'+name
                self.assertEqual(request(path)[:2], (200, (self.index/name).read_bytes()))
                self.assertEqual(request(path, 'HEAD')[:2], (200, b''))
            for path in ('/api/level-index/status?convert=1','/api/level-index/files/../secret',
                         '/api/level-index/files/tile_01.json','/api/level-index/files/%2e%2e/secret'):
                with self.subTest(path=path):self.assertEqual(request(path)[0],400)
            self.assertEqual(request('/api/level-index/status',headers={'Host':'unrelated.invalid'})[0],403)
            health=json.loads(request('/api/health')[1])
            self.assertFalse(health['conversionEnabled']);self.assertFalse(health['nativeReaderEnabled'])
            self.assertEqual(health['loaded'],0)
            self.assertEqual(request('/application/config.json')[:2],(200,b'{"schema":"xnby.portal.config.v1","mode":"local"}'))
            self.assertEqual(before,self.snapshot())
            (self.index/'tile_1.json').write_bytes(encoded(self.tile)+b' ')
            self.assertEqual(request('/api/level-index/files/tile_1.json')[0],422)
            self.assertEqual(json.loads(request('/api/health')[1])['loaded'],0)
        finally:
            if proc.poll() is None and state.exists():
                saved=json.loads(state.read_bytes());url='http://127.0.0.1:'+str(saved['port'])
                request('/__preview__/stop','POST',{'X-Preview-Key':saved['controlKey']})
                proc.wait(timeout=5)
            if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
            errors=proc.stderr.read().decode(errors='replace');proc.stderr.close()
        self.assertEqual(proc.returncode,0,errors)
        self.assertEqual(project.read_bytes(),b'{"user":"unchanged"}')


if __name__ == '__main__':
    unittest.main()
