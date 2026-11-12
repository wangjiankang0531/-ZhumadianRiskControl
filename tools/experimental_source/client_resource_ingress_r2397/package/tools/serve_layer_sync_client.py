"""Start the editor's owned, loopback-only background sync helper.

Credentials must arrive through the protected local RPC. There is deliberately
no command-line or on-disk public Authorization option.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import threading

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.common import loads
from services.layer_sync_client import LayerSyncClient
from services.layer_sync_transport import CloudTransport
from services.layer_sync_identity import ProjectAccountIdentity, checked_account_key
from services.layer_sync_bridge import CredentialVault, LayerSyncBridge, write_binding, remove_binding


def regular(path):
    path = Path(path).absolute()
    for item in (*reversed(path.parents), path):
        if item.exists() and (item.is_symlink() or getattr(item.lstat(),'st_file_attributes',0)&0x400):
            raise ValueError('LOCAL_WORKSPACE_REDIRECTION_REJECTED')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.local/share')))/'XNBY/LayerSync/Zhumadian'
    parser.add_argument('--workspace', type=Path, default=default)
    parser.add_argument('--account-key', type=checked_account_key, required=True)
    parser.add_argument('--initial-document', type=Path)
    parser.add_argument('--publish-if-empty', action='store_true')
    parser.add_argument('--allowed-origin', action='append', default=[])
    args = parser.parse_args()
    workspace = regular(regular(args.workspace)/"accounts"/args.account_key)
    app = Path(__file__).resolve().parents[1]
    if workspace.is_relative_to(app): raise ValueError('PRIVATE_WORKSPACE_OUTSIDE_CODE_PACKAGE_REQUIRED')
    workspace.mkdir(parents=True, exist_ok=True)
    checkpoint = regular(workspace/'client-state.private.json')
    binding = regular(workspace/'connection.private.json')
    initial = None
    if args.initial_document:
        with regular(args.initial_document).open('rb') as stream:raw=stream.read(16*1048576+1)
        if len(raw)>16*1048576:raise ValueError('INITIAL_DOCUMENT_TOO_LARGE')
        initial = loads(raw)
    vault = CredentialVault()
    identity = ProjectAccountIdentity(args.account_key)
    client = LayerSyncClient(CloudTransport(vault.get,credential_guard=identity.verify,account_key=args.account_key),
                             checkpoint, initial_document=initial,publish_if_empty=args.publish_if_empty,account_key=args.account_key)
    client.pause(login_required=True)
    bridge = None; binding_raw = None; observer = None; closing = threading.Event()
    try:
        bridge = LayerSyncBridge(client, vault, allowed_origins=args.allowed_origin,credential_verifier=identity.verify)
        runs = regular(workspace/'runs'); runs.mkdir(exist_ok=True)
        run = regular(runs/bridge.instance_id); run.mkdir()
        stop = run/'stop.json'
        binding_raw = write_binding(binding, bridge)
        def observe_stop():
            while not closing.wait(.2):
                if not stop.exists(): continue
                try:
                    with stop.open('rb') as stream:raw=stream.read(8193)
                    value=loads(raw) if len(raw)<=8192 else None
                    if value=={'schema':'xnby.layer-sync.stop.v1','instanceId':bridge.instance_id}:
                        bridge.shutdown();return
                except (OSError,ValueError,TypeError):
                    continue
        client.start()
        observer = threading.Thread(target=observe_stop, name='xnby-layer-stop', daemon=True);observer.start()
        print(json.dumps({'ready':True,'binding':str(binding),'instanceId':bridge.instance_id,
                          'pid':os.getpid(),'publicAuthorizationRecorded':False}),flush=True)
        bridge.serve_forever(poll_interval=.2)
    finally:
        closing.set()
        if bridge is not None:bridge.server_close()
        client.stop()
        vault.clear()
        if binding_raw is not None:remove_binding(binding,binding_raw)
        if observer is not None:observer.join(timeout=2)


if __name__=='__main__':main()
