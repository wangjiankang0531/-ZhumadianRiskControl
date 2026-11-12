"""Start an explicitly configured, loopback-only layer service; no auto-install."""
import argparse
import hashlib
import re
from contextlib import closing
import json
import os
import msvcrt
from pathlib import Path
import sqlite3
import sys
import threading
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.layer_sync_server import OriginalPlatformAccess, LayerSyncServer, checked_project_origin
from services.common import loads
from services.database import SCHEMA_SQLITE, SCHEMA_VERSION
from services.layers import LayerRepository


def regular(path, directory=False):
    path = Path(path).absolute()
    if '..' in path.parts:raise ValueError('CANONICAL_SYNC_PATH_REQUIRED')
    for item in (*reversed(path.parents), path):
        if item.exists() and (item.is_symlink() or getattr(item.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('SYNC_PATH_REDIRECTION_REJECTED')
    if path.exists() and (path.is_dir() != directory):
        raise ValueError('INVALID_SYNC_PATH_KIND')
    return path


def read_server_config(path,expected_sha=None):
    config_path = regular(path)
    with config_path.open("rb") as stream: raw=stream.read(32769)
    if expected_sha is not None and hashlib.sha256(raw).hexdigest()!=expected_sha:
        raise ValueError("SYNC_CONFIG_PIN_CHANGED")
    if len(raw) > 32768: raise ValueError('SYNC_CONFIG_TOO_LARGE')
    config = loads(raw)
    if not isinstance(config,dict) or not {'schema','listenPort','platformPort','access'}<=set(config) or set(config)-{'schema','listenPort','platformPort','access','projectFilesRoot','gatewayOrigin','sceneProjectsRoot','sceneModelCatalog','sceneModelCatalogSHA256','sceneModelsRoot','sceneModelsCatalog','sceneModelsCatalogSHA256','localGIS','clientResources'} or config['schema'] != 'xnby.layer-sync.server.v1':
        raise ValueError('INVALID_SYNC_SERVER_CONFIG')
    checked_project_origin(config.get('gatewayOrigin'))
    if type(config['listenPort']) is not int or not 1024 <= config['listenPort'] <= 65535:
        raise ValueError('EXPLICIT_SYNC_PORT_REQUIRED')
    acl = config['access']
    if not isinstance(acl, dict) or set(acl) != {'readers', 'writers', 'read_roles', 'write_roles', 'administrators'}:
        raise ValueError('INVALID_SYNC_PROJECT_ACCESS')
    for name in ('readers', 'writers', 'read_roles', 'write_roles'):
        if not isinstance(acl[name], list): raise ValueError('INVALID_SYNC_PROJECT_ACCESS')
    if 'projectFilesRoot'in config:
        if not isinstance(config['projectFilesRoot'],str)or not Path(config['projectFilesRoot']).is_absolute():raise ValueError('INVALID_PROJECT_FILES_ROOT')
        regular(config['projectFilesRoot'],directory=True)
    from services.scene_projects import validate_scene_settings
    validate_scene_settings(config)
    from services.scene_model_configuration import validate_model_settings
    validate_model_settings(config)
    access = OriginalPlatformAccess(config['platformPort'], **acl)
    if 'localGIS' in config:
        value = config['localGIS']
        if not isinstance(value, dict) or set(value) != {'schema', 'allowedSources'} or value['schema'] != 'xnby.local-gis.server-settings.v1':
            raise ValueError('EXACT_LOCAL_GIS_SETTINGS_REQUIRED')
        # Validate before touching data roots or binding a listener. Descriptor
        # validation is shared with the actual authority, never browser supplied.
        from services.local_gis_grants import LocalGISGrantAuthority
        probe = LocalGISGrantAuthority(access, value['allowedSources'])
        probe.close()
    from services.client_resource_configuration import validate_client_resource_settings
    validate_client_resource_settings(config,access)
    return config,access,hashlib.sha256(raw).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--run-root',type=Path)
    parser.add_argument('--instance-id')
    parser.add_argument('--config-sha256')
    parser.add_argument('--manifest-sha256')
    args = parser.parse_args()
    managed_values=[args.run_root,args.instance_id,args.config_sha256,args.manifest_sha256]
    managed=any(value is not None for value in managed_values)
    if managed and not all(value is not None for value in managed_values):raise ValueError('COMPLETE_MANAGED_IDENTITY_REQUIRED')
    if managed:
        if not re.fullmatch('[0-9a-f]{32}',args.instance_id) or not re.fullmatch('[0-9a-f]{64}',args.config_sha256) or not re.fullmatch('[0-9a-f]{64}',args.manifest_sha256):
            raise ValueError('INVALID_MANAGED_IDENTITY')
        from tools.layer_sync_supervisor import verify_package
        verify_package(Path(__file__).resolve().parents[1],args.manifest_sha256)
    config,access,config_sha=read_server_config(args.config,args.config_sha256)
    root = regular(args.data_root, directory=True)
    file_root=None
    if 'projectFilesRoot'in config:
        file_root=regular(config['projectFilesRoot'],directory=True)
        if file_root==root or root.is_relative_to(file_root):raise ValueError('PROJECT_FILES_MUST_NOT_CONTAIN_SERVICE_STATE')
    root.mkdir(parents=True, exist_ok=True)
    run=regular(args.run_root,directory=True) if managed else root
    if managed and (not run.is_dir() or run.name!=args.instance_id or run.is_relative_to(root) or root.is_relative_to(run) or (root/'ready.json').exists()):
        raise ValueError('SEPARATE_MANAGED_RUN_REQUIRED')
    if managed and file_root is not None and(file_root.is_relative_to(run)or run.is_relative_to(file_root)):raise ValueError('PROJECT_FILES_MUST_NOT_OVERLAP_RUN_STATE')
    stop = regular(run / ('stop.json' if managed else 'stop-requested.txt'))
    ready = regular(run / 'ready.json')
    if stop.exists():
        if managed:
            with stop.open('rb') as stream: stop_raw=stream.read(8193)
            if len(stop_raw)<=8192 and loads(stop_raw)=={'schema':'xnby.layer-sync.worker-stop.v1','instanceId':args.instance_id,'configSHA256':config_sha}:return
        raise ValueError('STALE_SYNC_STOP_REQUEST')
    if ready.exists(): raise ValueError('SYNC_READY_ALREADY_EXISTS')
    lease_path = regular(root / 'owner.lock')
    lease = lease_path.open('a+b')
    if not lease_path.stat().st_size:
        lease.write(b'0'); lease.flush()
    lease.seek(0)
    msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
    database = regular(root / 'layers.sqlite')
    for suffix in ('-wal', '-shm', '-journal'): regular(Path(str(database) + suffix))
    if database.exists():
        # Existing data is checked, never silently upgraded/repaired by startup.
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as db:
            if db.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
                raise ValueError('EXPLICIT_SYNC_DATA_MIGRATION_REQUIRED')
            schema = lambda c: c.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
            with closing(sqlite3.connect(':memory:')) as expected:
                expected.executescript(SCHEMA_SQLITE)
                if schema(db) != schema(expected): raise ValueError('SYNC_DATABASE_SCHEMA_CHANGED')
            if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchall():
                raise ValueError('SYNC_DATABASE_INVALID')
    repo = LayerRepository(database)
    project_files=None
    if file_root is not None:
        from services.project_files import ProjectFileRepository
        project_files=ProjectFileRepository(file_root)
    from services.scene_projects import configured_scene_repository
    scenes=configured_scene_repository(config,root,run)
    from services.scene_model_configuration import configured_scene_models
    models=configured_scene_models(config,root,run)
    server_type = LayerSyncServer
    resource_options = {}
    if 'clientResources' in config:
        from services.client_resource_server import with_client_resource_server
        server_type = with_client_resource_server(LayerSyncServer)
        resource_options['client_resource_installations'] = config['clientResources']['allowedInstallations']
    server = server_type(config['listenPort'], repo, access, project_files=project_files, origin=config.get('gatewayOrigin'),scene_projects=scenes,scene_models=models,local_gis_sources=config['localGIS']['allowedSources'] if 'localGIS' in config else None,**resource_options)
    # A supervising deployment controller owns this process and its data directory.
    # Service stop is a local file marker, never a remotely callable HTTP action.
    identity={'schema': 'xnby.layer-sync.ready.v1', 'listen': '127.0.0.1', 'pid': os.getpid(),
              'port': server.server_port, 'nativePlatformPort': config['platformPort']}
    if managed:
        from services.layer_sync_bridge import process_creation
        identity.update(schema='xnby.layer-sync.ready.v2',instanceId=args.instance_id,creation=process_creation(os.getpid()),
                        configSHA256=config_sha,manifestSHA256=args.manifest_sha256)
    ready_raw = json.dumps(identity).encode()
    with ready.open('xb') as output: output.write(ready_raw)
    closing_event=threading.Event()
    def observe_stop():
        while not closing_event.wait(.2):
            if not stop.exists():continue
            if managed:
                try:
                    with regular(stop).open('rb') as stream:raw=stream.read(8193)
                    value=loads(raw) if len(raw)<=8192 else None
                    if value!={'schema':'xnby.layer-sync.worker-stop.v1','instanceId':args.instance_id,'configSHA256':config_sha}:continue
                except (OSError,ValueError,TypeError):continue
            server.shutdown();return
    thread = threading.Thread(target=observe_stop, daemon=True); thread.start()
    try: server.serve_forever(poll_interval=.2)
    finally:
        closing_event.set();server.server_close()
        if ready.exists():
            try:
                if regular(ready).read_bytes()==ready_raw:ready.unlink()
            except (OSError,ValueError):pass
        thread.join(timeout=1);lease.close()


if __name__ == '__main__': main()
