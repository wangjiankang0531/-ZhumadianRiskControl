"""Explicit original-data RAM pages beside verified prepared-page previews."""
import json
import hashlib
from pathlib import Path
from readonly_landscape_store import owned
import re
from urllib.parse import parse_qs,urlsplit
from osgb_v80_source_reader import PinnedOSGBDataReader
from readonly_source_memory_store import PinnedCatalogs,MemorySourceStore,MemoryStoreBusy,MemoryStoreClosed


def parse_data_tiles(value):
    if value=='indexed-missing':return value
    if not isinstance(value,str) or not re.fullmatch(r'[1-9][0-9]{0,3}(?:,[1-9][0-9]{0,3})*',value):
        raise ValueError('Explicit canonical OSGB data tile list is required')
    values=[int(v) for v in value.split(',')]
    if len(values)>256 or len(set(values))!=len(values) or any(v>2346 for v in values):
        raise ValueError('OSGB data tile list exceeds bounds or repeats identities')
    return tuple(sorted(values))


class PreviewOSGBDataLOD:
    def __init__(self,prepared,resources,source_root,tiles,*,sampler_pages=False,index_identity=None):
        if type(sampler_pages) is not bool:raise ValueError('Sampler page selection must be boolean')
        self.sampler_pages=sampler_pages
        self.prepared=prepared;self.indexed_missing=tiles=='indexed-missing'
        catalogs=PinnedCatalogs(resources)
        self.index_identity=index_identity
        self.source_manifest_identity=catalogs.identity
        if self.indexed_missing:
            if (not isinstance(index_identity,str) or not re.fullmatch('[0-9a-f]{64}',index_identity)
                    or not re.fullmatch('[0-9a-f]{64}',catalogs.identity)
                    or set(catalogs.records)!=set(range(1,2347))
                    or not 1<=len(prepared.sources.stores)<=4 or not isinstance(prepared.owners,dict)):
                raise ValueError('Indexed missing sources require the sealed complete scene and prepared owners')
            self.tiles=frozenset(catalogs.records)
        else:
            self.tiles=frozenset(tiles)
            if not self.tiles or len(self.tiles)>256 or any(type(v) is not int or not 1<=v<=2346 for v in self.tiles):
                raise ValueError('Bounded explicit data tiles required')
            if not self.tiles.issubset(catalogs.records):raise ValueError('Data tiles are not in pinned source catalog')
        options={}
        if sampler_pages:
            from osgb_sampler_pages import build_bundle,builder_identity
            options=dict(builder=build_bundle,builder_identity=builder_identity())
        self.memory=MemorySourceStore(catalogs,PinnedOSGBDataReader(source_root),**options)

    def close(self):
        try:self.memory.close()
        finally:self.prepared.close()

    def health(self):
        value=self.prepared.health();audit=self.memory.audit()
        value.update(scope='verified_prepared_and_explicit_python_original_sources',
            pythonOriginalSources=dict(enabled=True,tiles=sorted(self.tiles),readerIdentity=self.memory.reader.identity,
                pagePolicy='source_sampler_full_image_v2' if self.sampler_pages else 'original_full_mip_chain_v1',
                **{k:audit[k] for k in ('builds','failures','encodedBytes','limit','buildReservation','bundles','activeLeases','queuedJobs','assetWritesEnabled','buildMilliseconds','planRequests','planWaitRequests','planWaitCompleted','planWaitTimeouts','planWaitMilliseconds')}))
        if self.indexed_missing:
            detail=value['pythonOriginalSources'];detail.pop('tiles')
            detail.update(tileSelection='sealed_index_missing_prepared_v1',tileCount=len(self.tiles),
                indexIdentity=self.index_identity,sourceManifestSHA256=self.source_manifest_identity,preparedFirst=True)
        return value

    def prepared_marker_present(self,tile,depth=None,parent=None):
        name=f'tile_{tile}_depth_{depth}' if parent is None else f'family_tile_{tile}_'+hashlib.sha256(parent.encode()).hexdigest()[:16]
        # Presence alone selects the prepared validator. Invalid or incomplete
        # present markers must fail there, never silently fall back to raw data.
        return any(owned(store.cache,Path(name)/'complete.json').exists() for store in self.prepared.sources.stores)

    def error(self,handler,error):
        status=503 if isinstance(error,MemoryStoreBusy) else 409 if isinstance(error,(OSError,TimeoutError,MemoryStoreClosed)) else 422
        handler.reply(status,b'{"error":"ORIGINAL_DATA_UNAVAILABLE_OR_INVALID","keepParent":true,"nativeReaderEnabled":false}')

    def handle(self,handler):
        parsed=urlsplit(handler.path);route=parsed.path
        if route=='/api/health':
            handler.reply(200,json.dumps(self.health()).encode());return True
        release=re.fullmatch(r'/api/lod-lease/([0-9a-f]{32})/release',route)
        if release:
            if handler.command!='POST' or parsed.query or parsed.fragment:
                handler.reply(405,b'{"error":"POST_REQUIRED"}');return True
            if self.memory.release(release[1]):handler.reply(204,b'');return True
            return self.prepared.handle(handler)
        root=re.fullmatch(r'/api/lod(-plan)?/([1-9][0-9]{0,3})/([1-9][0-9]?)',route)
        family=re.fullmatch(r'/api/lod-family(-plan)?/([1-9][0-9]{0,3})/(Tile_[1-9][0-9]{0,3}_L[0-9]+_0[0-9u]+\.osgb)',route)
        payload=re.fullmatch(r'/native/((?:tile_([1-9][0-9]{0,3})_depth_[1-9][0-9]?|family_tile_([1-9][0-9]{0,3})_[0-9a-f]{16}))/(part_[0-9]{3})/([^/]+)',route)
        tile=int((root or family)[2]) if root or family else int(payload[2] or payload[3]) if payload else None
        if tile not in self.tiles:return self.prepared.handle(handler)
        if handler.command not in ('GET','HEAD'):
            handler.reply(405,b'{"error":"READ_ONLY_ORIGINAL_DATA"}');return True
        if parsed.fragment:
            handler.reply(400,b'{"error":"INVALID_ORIGINAL_DATA_ROUTE"}');return True
        token=None
        try:
            if payload:
                folder,_,_,part,name=payload.groups()
                query=parse_qs(parsed.query,strict_parsing=True,max_num_fields=1,keep_blank_values=True)
                values=query.get('lease',[])
                if set(query)!={'lease'} or len(values)!=1 or not re.fullmatch('[0-9a-f]{32}',values[0]):
                    handler.reply(400,b'{"error":"MATCHING_MEMORY_LEASE_REQUIRED"}');return True
                if self.indexed_missing and values[0] in self.prepared.owners:
                    return self.prepared.handle(handler)
                if name not in ('geometry.gltf','geometry.bin','texture.png'):
                    handler.reply(400,b'{"error":"MATCHING_MEMORY_LEASE_REQUIRED"}');return True
                raw,media=self.memory.payload(values[0],folder,part,name)
                handler.reply(200,raw,media);return True
            plan,_,value=(root or family).groups()
            if root and not 1<=int(value)<=12 or family and not value.startswith(f'Tile_{tile}_L'):
                handler.reply(400,b'{"error":"INVALID_ORIGINAL_SOURCE"}');return True
            if parsed.query and not (plan and parsed.query=='wait_ms=200'):
                handler.reply(400,b'{"error":"INVALID_ORIGINAL_SOURCE_QUERY"}');return True
            args={'depth':int(value)} if root else {'parent':value}
            if self.indexed_missing and self.prepared_marker_present(tile,**args):
                return self.prepared.handle(handler)
            if plan:
                result=self.memory.plan(tile,**args,wait_ms=200 if parsed.query else 0)
            else:
                granted=self.memory.grant(tile,**args)
                result=None if granted is None else granted[0]
                if result is not None:
                    token=result['cache_lease'];handler.source_marker_sha256=granted[1]
            wait_headers={'X-XNBY-Source-Plan-Wait-Ms':'200'} if plan and parsed.query=='wait_ms=200' else None
            handler.reply(202 if result is None else 200,json.dumps(result if result is not None else {'status':'preparing_original_data_memory'},allow_nan=False).encode(),headers=wait_headers)
        except (ValueError,RuntimeError,KeyError,TypeError,OSError) as error:
            if token:self.memory.release(token)
            self.error(handler,error)
        return True
