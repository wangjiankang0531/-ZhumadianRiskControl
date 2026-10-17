"""Serve only the Zhumadian viewer/data and schedule one bounded native converter.

Local manual test server. Public deployments should serve dist + prepared data
behind their existing HTTPS/authentication gateway; no upload or write endpoint.
"""
import argparse
import hashlib
import concurrent.futures
import http.server
import json
import os
import re
import subprocess
import threading
import io
import sys
from pathlib import Path
from urllib.parse import unquote,urlsplit,parse_qs
if __package__:
    from . import native_cache_policy as cache_policy, native_atlas_recipe as recipes
    from .native_cache_leases import LeaseRegistry
else:
    import native_cache_policy as cache_policy
    import native_atlas_recipe as recipes
    from native_cache_leases import LeaseRegistry

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from services.layers import LayerRepository
from services.common import ApiError
POOL=concurrent.futures.ThreadPoolExecutor(max_workers=1)
JOBS={};LOCK=threading.Lock()
CACHE_LEASES=LeaseRegistry()
def convert(tile,depth,python):
    with cache_policy.tile_lock(ROOT/"work/zhumadian_native_chunk_cache",tile):
        command=[str(python),'-X','utf8',str(ROOT/'tools/convert_zhumadian_native_chunks.py'),f'--tile={tile}',f'--depth={depth}']
        result=subprocess.run(command,cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
        folder=ROOT/f'work/zhumadian_native_chunk_cache/tile_{tile}_depth_{depth}'
        if result.returncode:
            failure=folder/'failure.json'
            reason=json.loads(failure.read_text(encoding='utf-8')).get('reason','conversion failed') if failure.exists() else result.stdout.decode('utf-8',errors='replace')[-4000:]
            raise RuntimeError(reason)
        marker=json.loads((folder/'complete.json').read_text(encoding='utf-8'))
        if not marker.get('complete_frontier'):raise RuntimeError('frontier incomplete')
        return marker

def bundle_present(tile,depth,marker):
    folder=ROOT/f'work/zhumadian_native_chunk_cache/tile_{tile}_depth_{depth}'
    if not (folder/'complete.json').is_file():return False
    expected_layout=recipes.resolve_cache(ROOT,ROOT/'work/zhumadian_native_chunk_cache')[0]
    if marker.get('atlas_layout_policy',recipes.LEGACY)!=expected_layout:return False
    if marker.get('texture_policy')!='original_pixels_v1':return False
    for key,name in [('converter_sha256','convert_zhumadian_native_chunks.py'),('texture_helper_sha256','native_texture_parts.py'),('frontier_helper_sha256','native_source_frontier.py'),('atlas_recipe_sha256','native_atlas_recipe.py')]:
        if marker.get('stamp',{}).get(key)!=hashlib.sha256((ROOT/'tools'/name).read_bytes()).hexdigest():return False
    for part in marker.get('parts',[]):
        if not re.fullmatch(r'part_\d{3}',part['directory']):return False
        for file in part['files']:
            if file['name'] not in {'geometry.gltf','geometry.bin','atlas.jpg'}:return False
            path=folder/part['directory']/file['name']
            if not path.is_file() or path.stat().st_size!=file['bytes']:return False
    return bool(marker.get('parts'))


def convert_family(tile,parent,python):
    with cache_policy.tile_lock(ROOT/"work/zhumadian_native_chunk_cache",tile):
        command=[str(python),'-X','utf8',str(ROOT/'tools/convert_zhumadian_native_family.py'),f'--tile={tile}',f'--parent={parent}']
        result=subprocess.run(command,cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
        folder=ROOT/'work/zhumadian_native_chunk_cache'/f'family_tile_{tile}_{hashlib.sha256(parent.encode()).hexdigest()[:16]}'
        if result.returncode:
            failure=folder/'failure.json'
            reason=json.loads(failure.read_text(encoding='utf-8')).get('reason','conversion failed') if failure.exists() else result.stdout.decode('utf-8',errors='replace')[-4000:]
            raise RuntimeError(reason)
        marker=json.loads((folder/'complete.json').read_text(encoding='utf-8'))
        if marker.get('schema')!='xnby.osgb_native_family.v1' or marker.get('replacement_parent')!=parent or not marker.get('complete_sibling_family'):
            raise RuntimeError('source sibling family incomplete')
        return marker

def family_bundle_present(tile,parent,marker):
    folder=ROOT/'work/zhumadian_native_chunk_cache'/f'family_tile_{tile}_{hashlib.sha256(parent.encode()).hexdigest()[:16]}'
    if not (folder/'complete.json').is_file():return False
    expected_layout=recipes.resolve_cache(ROOT,ROOT/'work/zhumadian_native_chunk_cache')[0]
    if marker.get('atlas_layout_policy',recipes.LEGACY)!=expected_layout:return False
    for key,name in [('family_converter_sha256','convert_zhumadian_native_family.py'),('converter_sha256','convert_zhumadian_native_chunks.py'),('texture_helper_sha256','native_texture_parts.py'),('frontier_helper_sha256','native_source_frontier.py'),('atlas_recipe_sha256','native_atlas_recipe.py')]:
        if marker.get('stamp',{}).get(key)!=hashlib.sha256((ROOT/'tools'/name).read_bytes()).hexdigest():return False
    for part in marker.get('parts',[]):
        if not re.fullmatch(r'part_\d{3}',part['directory']):return False
        for file in part['files']:
            if file['name'] not in {'geometry.gltf','geometry.bin','atlas.jpg'}:return False
            path=folder/part['directory']/file['name']
            if not path.is_file() or path.stat().st_size!=file['bytes']:return False
    return bool(marker.get('parts'))

def publication_assets(root):
    projects=root/'projects'
    if projects.is_dir() and projects.resolve()!=projects.absolute():
        return projects.resolve().parent
    return root.parent/'Assets'

def layer_data_binding(layers,database):
    # Identity stays stable across file saves and database revisions.
    paths=[os.path.normcase(str(Path(p).resolve())) for p in (layers,database)]
    return hashlib.sha256(json.dumps(paths,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()

class Handler(http.server.SimpleHTTPRequestHandler):
    layer_repository=None
    data_binding=None
    allow_local_layer_database=True
    root=ROOT; python=None; layers=None; business=None; spatial=None
    def _native_response(self,head=False):
        route=unquote(urlsplit(self.path).path)
        match=re.fullmatch(r'/native/((?:tile_\d+_depth_\d+|family_tile_\d+_[0-9a-f]{16}))/part_\d{3}/(?:geometry\.(?:gltf|bin)|atlas\.jpg)',route)
        if not match: return False
        cache=self.root/'work/zhumadian_native_chunk_cache'; name=match.group(1)
        try:
            query=parse_qs(urlsplit(self.path).query,strict_parsing=True,max_num_fields=2)
            tokens=query.get('lease',[])
            if query and (set(query)!={'lease'} or len(tokens)!=1 or not re.fullmatch(r'[0-9a-f]{32}',tokens[0])):
                self.send_error(400); return True
            guard=CACHE_LEASES.use(tokens[0],cache,name) if tokens else cache_policy.bundle_lock(cache,name,timeout=0)
            with guard:
                if head: super().do_HEAD()
                else: super().do_GET()
        except (PermissionError,TimeoutError): self.send_error(409,'Cache lease unavailable; keep previous complete layer')
        except ValueError: self.send_error(400)
        return True

    def do_HEAD(self):
        if not self._native_response(True): super().do_HEAD()

    def do_POST(self):
        match=re.fullmatch(r'/api/lod-lease/([0-9a-f]{32})/release',urlsplit(self.path).path)
        if not match: return self.send_error(501)
        if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Length','0')!='0': return self.send_error(400)
        CACHE_LEASES.release(match.group(1)); self.send_response(204); self.send_header('Content-Length','0'); self.end_headers()

    def _database_layers(self):
        try:
            source=Path(self.layers)
            before=source.stat()
            with source.open('rb') as stream:raw=stream.read(16*1048576+1)
            after=source.stat()
            if (before.st_mtime_ns,before.st_size)!=(after.st_mtime_ns,after.st_size):raise ApiError(409,'LAYER_SOURCE_CHANGED')
            if len(raw)>16*1048576:raise ApiError(413,'LAYER_SOURCE_TOO_LARGE')
            try:current=self.layer_repository.get('zhumadian','default')
            except ApiError as error:
                if error.code!='LAYER_DOCUMENT_NOT_FOUND':raise
                current={'revision':0,'sha256':None}
            if current['sha256']!=hashlib.sha256(raw).hexdigest():
                self.layer_repository.import_bytes('zhumadian','default',raw,current['revision'])
            stored=self.layer_repository.get('zhumadian','default')
            data=stored['raw']
            self.send_response(200);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)))
            self.send_header('X-XNBY-Layer-Storage','sqlite');self.send_header('X-XNBY-Layer-Revision',str(stored['revision']));self.end_headers()
            return io.BytesIO(data)
        except ApiError as error:self.send_error(error.status,error.code)
        except ValueError:self.send_error(422,'LAYER_SOURCE_INVALID')
        except Exception:self.send_error(503,'LAYER_DATABASE_UNAVAILABLE')
        return None

    def send_head(self):
        if self.allow_local_layer_database and self.layer_repository is not None and unquote(urlsplit(self.path).path)=='/layers/default.json':return self._database_layers()
        if unquote(urlsplit(self.path).path)=='/assets/showcase/runtime/zhumadian/full/base_lod_quality.json':
            quality=Path(self.translate_path(self.path))
            if quality.is_file() and quality.stat().st_size>1048576:
                self.send_error(413,'Prepared quality exceeds size limit');return None
        if unquote(urlsplit(self.path).path) in ('/business/default.json','/spatial/default.json'):
            snapshot=Path(self.translate_path(self.path))
            limit=(4 if unquote(urlsplit(self.path).path)=='/spatial/default.json' else 8)*1048576
            if snapshot.is_file() and snapshot.stat().st_size>limit:
                self.send_error(413,'Published JSON exceeds size limit')
                return None
        return super().send_head()
    def do_GET(self):
        if self._native_response(): return
        route=urlsplit(self.path).path
        if route.startswith('/api/lod-family/'):
            match=re.fullmatch(r'/api/lod-family/(\d{1,4})/(Tile_\d+_L\d+_0[0-9u]+\.osgb)',route)
            if not match:return self.send_error(400)
            tile,parent=int(match.group(1)),match.group(2)
            if not 1<=tile<=2346 or not parent.startswith(f'Tile_{tile}_'):return self.send_error(400)
            key=(tile,parent)
            with LOCK:
                previous=JOBS.get(key)
                if previous and previous.done():
                    try:present=family_bundle_present(tile,parent,previous.result())
                    except Exception:present=True
                    if not present:JOBS.pop(key)
                if key not in JOBS:
                    if sum(not job.done() for job in JOBS.values())>=2:
                        self.send_response(202);self.end_headers();return
                    JOBS[key]=POOL.submit(convert_family,tile,parent,self.python)
                    if len(JOBS)>256:
                        for old in list(JOBS):
                            if len(JOBS)<=256:break
                            if old!=key and JOBS[old].done():JOBS.pop(old)
                job=JOBS[key]
            if not job.done():self.send_response(202);self.end_headers();return
            try:
                marker=job.result()
                directory=f'family_tile_{tile}_{hashlib.sha256(parent.encode()).hexdigest()[:16]}'
                token=CACHE_LEASES.grant(self.root/'work/zhumadian_native_chunk_cache',directory,lambda:family_bundle_present(tile,parent,marker))
                data=json.dumps({**marker,'cache_lease':token}).encode('utf-8')
            except (FileNotFoundError,TimeoutError):
                with LOCK:
                    if JOBS.get(key) is job:JOBS.pop(key)
                self.send_response(202);self.end_headers();return
            except Exception as error:data=str(error).encode('utf-8');self.send_response(422)
            else:self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data);return
        if route.startswith('/api/lod/'):
            match=re.fullmatch(r'/api/lod/(\d{1,4})/(\d{1,2})',route)
            if not match:return self.send_error(400)
            tile,depth=map(int,match.groups())
            if not 1<=tile<=2346 or not 1<=depth<=12:return self.send_error(400)
            key=(tile,depth)
            with LOCK:
                previous=JOBS.get(key)
                if previous and previous.done():
                    try:present=bundle_present(tile,depth,previous.result())
                    except Exception:present=True  # Surface the real conversion error.
                    if not present:JOBS.pop(key)
                # Keep the worker queue bounded. Browser requests are serial.
                if key not in JOBS:
                    if sum(not job.done() for job in JOBS.values())>=2:
                        self.send_response(202);self.end_headers();return
                    JOBS[key]=POOL.submit(convert,tile,depth,self.python)
                    if len(JOBS)>256:
                        for old in list(JOBS):
                            if len(JOBS)<=256:break
                            if old!=key and JOBS[old].done():JOBS.pop(old)
                job=JOBS[key]
            if not job.done():self.send_response(202);self.end_headers();return
            try:
                marker=job.result()
                token=CACHE_LEASES.grant(self.root/'work/zhumadian_native_chunk_cache',f'tile_{tile}_depth_{depth}',lambda:bundle_present(tile,depth,marker))
                data=json.dumps({**marker,'cache_lease':token}).encode('utf-8')
            except (FileNotFoundError,TimeoutError):
                with LOCK:
                    if JOBS.get(key) is job:JOBS.pop(key)
                self.send_response(202);self.end_headers();return
            except Exception as error:data=str(error).encode('utf-8');self.send_response(422)
            else:self.send_response(200)
            self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data);return
        if route=='/api/health':
            data=b'{"application":"xnby.landscape.web.v1","scene":"zhumadian"}'
            manifest=self.root/'package.json'
            if manifest.is_file():
                raw=manifest.read_bytes();release=json.loads(raw)
                payload=json.loads(data)
                payload['release']={key:release.get(key) for key in ('editorVersion','webVersion','apiVersion')}
                payload['release']['manifestSha256']=hashlib.sha256(raw).hexdigest()
                data=json.dumps(payload,separators=(',',':')).encode('utf-8')
            if self.data_binding:
                payload=json.loads(data);payload['dataBinding']=self.data_binding
                data=json.dumps(payload,separators=(',',':')).encode('utf-8')
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        return super().do_GET()
    def translate_path(self,path):
        route=unquote(urlsplit(path).path).lstrip('/')
        if '\\' in route or '..' in route.split('/') or '\x00' in route:return str(ROOT/'work/web_not_found')
        if route in ('','index.html','viewer.js','THREE-LICENSE.txt','portal.html','portal.js','portal.css'):
            return str(self.root/'apps/landscape_web/dist'/(route or 'index.html'))
        if route=='layers/default.json':return str(self.layers)
        if route=='spatial/default.json':return str(self.spatial or publication_assets(self.root)/'Spatial/spatial_catalog.json')
        if route=='business/default.json':return str(self.business or publication_assets(self.root)/'BusinessData/business_records.json')
        if route=='layers/sample.json':return str(self.root/'projects/驻马店图层示例.json')
        if route=='assets/showcase/runtime/zhumadian/full/base_lod_quality.json':return str(self.root/route)
        if route=='assets/landscape/icons.png' or route=='data/showcase/zhumadian_native_hierarchy.json':return str(self.root/route)
        if re.fullmatch(r'assets/showcase/runtime/zhumadian/(full|context)/[\w.-]+\.(gltf|bin|jpg)',route):return str(self.root/route)
        if re.fullmatch(r'native/tile_\d+_depth_\d+/part_\d{3}/(geometry\.(gltf|bin)|atlas\.jpg)',route):
            return str(self.root/'work/zhumadian_native_chunk_cache'/route.removeprefix('native/'))
        if re.fullmatch(r'native/family_tile_\d+_[0-9a-f]{16}/part_\d{3}/(geometry\.(gltf|bin)|atlas\.jpg)',route):
            return str(self.root/'work/zhumadian_native_chunk_cache'/route.removeprefix('native/'))
        return str(ROOT/'work/web_not_found')
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store' if (unquote(urlsplit(self.path).path) in ('/business/default.json','/spatial/default.json') or unquote(urlsplit(self.path).path).startswith(('/api/lod/','/api/lod-family/'))) else 'no-cache');super().end_headers()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--layer-database',type=Path);parser.add_argument('--layers',type=Path);parser.add_argument('--python',type=Path)
    parser.add_argument('--business',type=Path,help='Published business snapshot JSON, read-only')
    parser.add_argument('--spatial',type=Path,help='Published spatial directory JSON, read-only')
    args=parser.parse_args();Handler.layer_repository=LayerRepository(args.layer_database or publication_assets(ROOT)/'BusinessData/xnby_business.sqlite');Handler.spatial=args.spatial;Handler.layers=args.layers or ROOT/'projects/驻马店图层.json'
    Handler.data_binding=layer_data_binding(Handler.layers,Handler.layer_repository.path)
    Handler.business=args.business
    Handler.python=args.python or ROOT/'runtime/python/python.exe'
    if not Handler.python.exists():Handler.python=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    server=http.server.ThreadingHTTPServer((args.host,args.port),Handler)
    print(f'XNBY LANDSCAPE WEB http://{args.host}:{args.port}  (Ctrl+C to stop)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close();POOL.shutdown(wait=False,cancel_futures=True);CACHE_LEASES.close()
if __name__=='__main__':main()
