"""Exact, reversible original frontend request-method adaptation for the supplied JNPF user selector."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path

SOURCE_PINS={
    'src/api/workFlow/index.ts':'662a20530ff3d6d91a37cb26c4ec97f2bed978035e863e56a9c46728ebdb3633',
    'src/api/workFlow/user.ts':'ef958976ca444a9eecac89838e18ee6d5e5444baa8c7d2af91a0839a5b49e08e',
}
REPLACEMENTS={
    'src/api/workFlow/index.ts':(
        b'request.get(`/jnpf/permission/Users/getSubordinates`)',
        b'request.post(`/jnpf/permission/Users/getSubordinates`, {})'),
    'src/api/workFlow/user.ts':(
        b'request.get("/jnpf/permission/Users/getSubordinates", { params: data })',
        b'request.post("/jnpf/permission/Users/getSubordinates", { keyword: data?.keyword ?? "" })'),
}


@contextmanager
def workflow_user_request_override(project,reference):
    project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
    if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):
        raise ValueError('DISTINCT_BUILD_COPY_AND_PRISTINE_SOURCE_REQUIRED')
    planned=[]
    for relative,pin in SOURCE_PINS.items():
        target,origin=project/relative,reference/relative
        if target.is_symlink() or origin.is_symlink() or target.resolve(strict=True)!=target or origin.resolve(strict=True)!=origin:
            raise ValueError('DIRECT_SOURCE_FILES_REQUIRED')
        original=origin.read_bytes()
        if sha256(original).hexdigest()!=pin or target.read_bytes()!=original:
            raise ValueError('ORIGINAL_WORKFLOW_SOURCE_DRIFT')
        old,new=REPLACEMENTS[relative]
        if original.count(old)!=1:raise ValueError('ONE_KNOWN_REQUEST_REQUIRED')
        updated=original.replace(old,new,1)
        planned.append((relative,target,original,updated))
    written=[]
    receipt={'adapter':'original-jnpf-user-selector-post-v1','requestMethodAndKeywordBodyOnly':True,
             'referenceModified':False,'authenticationOrPermissionModified':False,
             'sourceFilesRestored':False,'files':{relative:{'originalSHA256':sha256(original).hexdigest(),
             'adaptedSHA256':sha256(updated).hexdigest()} for relative,_,original,updated in planned}}
    try:
        for relative,target,original,updated in planned:
            target.write_bytes(updated);written.append((target,original,updated))
        yield receipt
    finally:
        drifted=[]
        for target,original,updated in reversed(written):
            try:current=target.read_bytes()
            except OSError:drifted.append(target);continue
            if current!=updated:drifted.append(target)
            else:target.write_bytes(original)
        receipt['sourceFilesRestored']=not drifted
        if drifted:raise ValueError('BUILD_COPY_CHANGED_EXTERNALLY_STOP_RESTORE')
