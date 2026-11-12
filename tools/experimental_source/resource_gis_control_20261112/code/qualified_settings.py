"""Original registered GIS ownership plus independently pinned full raw auditor."""
from pathlib import Path
from client_control import check,ordinary
from client_manifest import load_installation,verify_files,workspace_context
from client_settings import workspace_document
from client_workspace import inspect_existing,parse_document
from resource_settings import ResourceSettings

class QualifiedResourceSettings(ResourceSettings):
    def __init__(self,installation,configuration,*,gis=None):
        configuration=ordinary(configuration)
        # Keep this exact originally registered path. Never copy/normalize to
        # another profile and thereby change a live GIS owner's binding.
        super().__init__(installation,profile_folder=configuration.parent)
        self.file=configuration;self.gis=gis
    def save_authorized(self,root,commit):
        if self.gis is None:return super().save_authorized(root,commit)
        from client_control import atomic_json,private_directory
        from client_job import StateLock
        from client_gis_runtime import current_owner
        import secrets
        document=workspace_document(root);inspect_existing(document);base,_=parse_document(document)
        ordinary(Path(str(base)),directory=True);ordinary(Path(str(base))/'Assets/3DGIS/驻马店园区/Data',directory=True);ordinary(Path(str(base))/'Assets/Runtime',directory=True)
        self.folder.mkdir(parents=True,exist_ok=True);private_directory(self.folder);lock=StateLock(self.folder);guard=None
        try:
            existing=self.saved_document()
            if existing is not None and existing!=document:guard=self.gis.begin_root_change()
            if existing is not None and not(guard is not None and guard.permits_missing_root):
                old=workspace_context(self.file,self.installation,verify_resources=False);owner=current_owner(old)
                check(owner is None or existing==document,'STOP_GIS_BEFORE_CHANGING_WORKSPACE')
            candidate=self.folder/('candidate-'+secrets.token_hex(16)+'.json')
            try:
                atomic_json(candidate,document,replace=False);workspace_context(candidate,self.installation,verify_resources=True)
                operation=lambda:atomic_json(self.file,document)if existing!=document else None
                commit(lambda:guard.commit(operation)if guard is not None else operation())
                result=self.configuration();result.update(saved=True);return result
            finally:
                if candidate.exists():candidate.unlink()
        finally:
            if guard is not None:guard.close()
            lock.close()
    def audit(self,root,*,progress=None,cancel_event=None):
        from verify_offline_gis import verify_workspace
        document=workspace_document(root);inspect_existing(document);_,paths=parse_document(document)
        if progress:progress({'phase':'checking_program','completedFiles':0,'readBytes':0})
        install=load_installation(self.installation)
        verify_files(Path(str(paths['renderData'])),install['offlineResources'])
        result=verify_workspace(document,workers=2,progress=progress,cancel_event=cancel_event)
        result.update(programFilesVerified=len(install['files']),offlineSupportFilesVerified=len(install['offlineResources']))
        # ResourceManager persists this only in the authenticated actor/project
        # report store. No unowned duplicate beside the source assets.
        return {'integrityAudit':True,'result':result}
