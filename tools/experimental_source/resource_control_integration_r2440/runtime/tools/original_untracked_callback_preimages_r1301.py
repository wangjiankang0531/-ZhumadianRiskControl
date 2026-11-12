"""Read-only, exact old callback preimages for the unified attachment updater.

This is a candidate helper, not an installation entry point. The caller must
first validate the accepted release, then pass its pinned original overlay
loader. It never changes a file, stops a service, or accepts arbitrary paths.
"""
from pathlib import Path
import hashlib,json,re

OVERLAY_ROOT='payload/callback-overlay/20261026-password-identity'
MANIFEST=OVERLAY_ROOT+'/manifest.json'
LAUNCHER_MEMBER='business-classes/xnby/replica/OriginalBusinessLaunch.class'
LAUNCHER=OVERLAY_ROOT+'/'+LAUNCHER_MEMBER
ACCEPTED_OLD_MANIFEST_SHA256='91f0edfac284df68e467e20714c96b08aa7f08b24a0c7618a42f0ba595fdf1eb'
ACCEPTED_OLD_LAUNCHER={'bytes':11451,'sha256':'64d03e5bdbcf149dba8424bd0b6ea0467845feb371b87121319bf3d068871307'}

def require(value,code):
    if not value:raise ValueError(code)

def regular(root,relative):
    root=Path(root).absolute();path=root/relative
    require('..'not in path.parts and path.is_relative_to(root),'CALLBACK_PREIMAGE_PATH_SCOPE')
    for part in [*reversed(path.parents),path]:
        require(not part.is_symlink()and not(getattr(part.lstat(),'st_file_attributes',0)&0x400),'CALLBACK_PREIMAGE_REPARSE_REFUSED')
    require(root.resolve(strict=True)==root and path.resolve(strict=True)==path and path.is_file(),'CALLBACK_PREIMAGE_REGULAR_FILE_REQUIRED')
    return path

def digest(path):
    with path.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read_unique(path,limit):
    require(path.stat().st_size<=limit,'CALLBACK_PREIMAGE_JSON_SIZE_BOUND')
    def pairs(items):
        out={}
        for key,value in items:require(key not in out,'CALLBACK_PREIMAGE_DUPLICATE_JSON_KEY');out[key]=value
        return out
    def constant(_):raise ValueError('CALLBACK_PREIMAGE_NONFINITE_JSON')
    return json.loads(path.read_bytes(),object_pairs_hook=pairs,parse_constant=constant)

def checked_preimages(application,release,load_overlay):
    """Return exactly two legacy pins, after original full-overlay validation."""
    require(isinstance(release,dict)and release.get('missingAuthOverlayManifestSHA256')==ACCEPTED_OLD_MANIFEST_SHA256,'CALLBACK_PREIMAGE_EXACT_RELEASE_OVERLAY_REQUIRED')
    payload_sha=release.get('payloadManifestSHA256')
    require(isinstance(payload_sha,str)and re.fullmatch('[0-9a-f]{64}',payload_sha),'CALLBACK_PREIMAGE_PAYLOAD_PIN_REQUIRED')
    root=Path(application).absolute();payload_path=regular(root,'payload-manifest.json')
    require(digest(payload_path)==payload_sha,'CALLBACK_PREIMAGE_PAYLOAD_CHANGED')
    payload=read_unique(payload_path,8*1024**2)
    require(isinstance(payload,dict)and payload.get('releaseId')==release.get('releaseId')and isinstance(payload.get('files'),dict),'CALLBACK_PREIMAGE_PAYLOAD_IDENTITY_REQUIRED')
    require(MANIFEST not in payload['files']and LAUNCHER not in payload['files'],'CALLBACK_PREIMAGE_ONLY_UNTRACKED_TWO_PATHS')
    manifest_path=regular(root,MANIFEST)
    require(manifest_path.stat().st_size<=256*1024 and digest(manifest_path)==ACCEPTED_OLD_MANIFEST_SHA256,'CALLBACK_PREIMAGE_OLD_MANIFEST_CHANGED')
    manifest=read_unique(manifest_path,256*1024)
    row=manifest.get('files',{}).get(LAUNCHER_MEMBER)
    require(row=={'bytes':ACCEPTED_OLD_LAUNCHER['bytes'],'SHA256':ACCEPTED_OLD_LAUNCHER['sha256']},'CALLBACK_PREIMAGE_OLD_LAUNCHER_MANIFEST_PIN_REQUIRED')
    launcher_path=regular(root,LAUNCHER)
    require(launcher_path.stat().st_size==row['bytes']and digest(launcher_path)==row['SHA256'],'CALLBACK_PREIMAGE_OLD_LAUNCHER_CHANGED')
    # Preserve the original validator's six members, six baselines and seven
    # callback-route pins; a successful hash of just these two files is weaker.
    validated=load_overlay(root,manifest_path,ACCEPTED_OLD_MANIFEST_SHA256)
    require(isinstance(validated,dict)and validated.get('manifestSHA256')==ACCEPTED_OLD_MANIFEST_SHA256 and validated.get('application')==root,'CALLBACK_PREIMAGE_ORIGINAL_FULL_OVERLAY_VALIDATION_REQUIRED')
    require(validated.get('filePins')==manifest['files'],'CALLBACK_PREIMAGE_ALL_ORIGINAL_FILE_PINS_REQUIRED')
    for path,expected in [(payload_path,payload_sha),(manifest_path,ACCEPTED_OLD_MANIFEST_SHA256),(launcher_path,ACCEPTED_OLD_LAUNCHER['sha256'])]:
        regular(root,path.relative_to(root).as_posix());require(digest(path)==expected,'CALLBACK_PREIMAGE_CHANGED_DURING_VALIDATION')
    return {MANIFEST:[ACCEPTED_OLD_MANIFEST_SHA256],LAUNCHER:[ACCEPTED_OLD_LAUNCHER['sha256']]}
