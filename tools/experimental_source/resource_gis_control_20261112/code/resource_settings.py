"""Reuse qualified client checks; recheck authorization at the atomic config commit."""
from pathlib import Path
import secrets
from client_settings import ClientSettings,workspace_document,PATHS
from client_control import atomic_json,ordinary,private_directory
from client_manifest import workspace_context,public_context
from client_workspace import parse_document,inspect_existing
from client_gis_runtime import current_owner
from client_job import StateLock
class ResourceSettings(ClientSettings):
    def configuration(self):
        saved=self.saved_document()
        return{'schema':'xnby.client-resources.configuration.v1','workspaceRoot':saved['workspaceRoot']if saved else self.suggested_root(),'paths':dict(PATHS),'saved':saved is not None}
    def save_authorized(self,root,commit):
        document=workspace_document(root);inspect_existing(document);base,_=parse_document(document)
        ordinary(Path(str(base)),directory=True);ordinary(Path(str(base))/'Assets/3DGIS/驻马店园区/Data',directory=True);ordinary(Path(str(base))/'Assets/Runtime',directory=True)
        self.folder.mkdir(parents=True,exist_ok=True);private_directory(self.folder);lock=StateLock(self.folder)
        try:
            existing=self.saved_document()
            if existing is not None:
                old=workspace_context(self.file,self.installation,verify_resources=False);owner=current_owner(old)
                if owner is not None and existing!=document:raise ValueError('STOP_GIS_BEFORE_CHANGING_WORKSPACE')
            candidate=self.folder/('candidate-'+secrets.token_hex(16)+'.json')
            try:
                atomic_json(candidate,document,replace=False);context=workspace_context(candidate,self.installation,verify_resources=True)
                # Do not permit an expired/retired HTTP session to commit after qualification.
                commit(lambda:atomic_json(self.file,document)if existing!=document else None)
                result=self.configuration();result.update(saved=True);return result
            finally:
                if candidate.exists():candidate.unlink()
        finally:lock.close()
