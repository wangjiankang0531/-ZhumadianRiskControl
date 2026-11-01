"""Exact reversible transport adaptation for supplied original JNPF workflow API modules."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
import re
from original_workflow_user_request import REPLACEMENTS as USER_REPLACEMENTS

SOURCE_PINS = {'src/api/workFlow/FlowBefore.ts': '08449afe36c9a03c3c50f4bea559d11f592690959792b6c716149c583b4afcb4', 'src/api/workFlow/FlowLaunch.ts': 'f9f4cbbb8b9aff434ba3499d2a11ecfbe47c0f944a4a1ec864cf06269728b6bf', 'src/api/workFlow/index.ts': '662a20530ff3d6d91a37cb26c4ec97f2bed978035e863e56a9c46728ebdb3633', 'src/api/workFlow/user.ts': 'ef958976ca444a9eecac89838e18ee6d5e5444baa8c7d2af91a0839a5b49e08e', 'src/api/workFlow/workFlow.ts': 'b7c7f466f6fadf3494fdda2f41916972797ae8fdb73a550ecfd804db12150313', 'src/api/workFlow/workFlowForm.ts': '23a5d3416a03ebc239efbc3640278b2ce23b210941d6368a0a62be8f5516418b'}
LEGACY_MODULES={'src/api/workFlow/'+name for name in ['FlowBefore.ts','FlowLaunch.ts','workFlow.ts','workFlowForm.ts']}


def once(source,old,new):
    if source.count(old)!=1:raise ValueError('EXACT_KNOWN_WORKFLOW_REQUEST_REQUIRED')
    return source.replace(old,new,1)


def export_change(source,name,old,new):
    pattern=rb'(^export\s+(?:const|function)\s+'+re.escape(name.encode('ascii'))+rb'\b[\s\S]*?)(?=^export\s+(?:const|function)\s+|\Z)'
    matches=list(re.finditer(pattern,source,re.MULTILINE))
    if len(matches)!=1:raise ValueError('EXACT_KNOWN_WORKFLOW_EXPORT_REQUIRED')
    match=matches[0];return source[:match.start()]+once(match.group(),old,new)+source[match.end():]


def transform(relative,raw):
    if relative not in SOURCE_PINS or sha256(raw).hexdigest()!=SOURCE_PINS[relative]:
        raise ValueError('ORIGINAL_WORKFLOW_SOURCE_DRIFT')
    updated=raw;prefixes=0
    if relative in LEGACY_MODULES:
        for old in [b'/jnpf/safety/api/api/',b'/jnpf/api/']:
            prefixes+=updated.count(old);updated=updated.replace(old,b'/jnpf/')
    if relative in USER_REPLACEMENTS:
        old,new=USER_REPLACEMENTS[relative];updated=once(updated,old,new)
    elif relative.endswith('/workFlow.ts'):
        old,new=USER_REPLACEMENTS['src/api/workFlow/index.ts'];updated=once(updated,old,new)
    if relative.endswith('/user.ts'):
        updated=once(updated,
            b'request.get("/jnpf/permission/Users/ImUser/Selector/" + organizeId, { params: data })',
            b'request.post("/jnpf/permission/Users/ImUser/Selector/" + organizeId, data)')
    # These exact pinned API modules use axios-style wrappers only for query parameters.
    updated,explicit=re.subn(rb'\{\s*params\s*:\s*data\s*\}',b'data',updated)
    updated,shorthand=re.subn(rb'\{\s*params\s*\}',b'params',updated)
    if relative.endswith('/FlowBefore.ts'):
        updated=export_change(updated,'Candidates',b'request.get(',b'request.post(')
    if relative.endswith('/FlowLaunch.ts'):
        updated=once(updated,b'`/jnpf/workflow/Engine/FlowLaunch/${id}/Actions/Press`',b'`/jnpf/workflow/Engine/FlowLaunch/Press/${id}`')
    if relative.endswith('/workFlowForm.ts'):
        updated=export_change(updated,'Update',b"return request.put('/jnpf/workflow/Engine/FlowTask', data);",
            b'if (!data || data.id === undefined || data.id === null || String(data.id) === "") return Promise.reject(new Error("WORKFLOW_TASK_ID_REQUIRED"));\n'
            b'\treturn request.put(`/jnpf/workflow/Engine/FlowTask/${encodeURIComponent(String(data.id))}`, data);')
    if updated==raw:raise ValueError('DECLARED_WORKFLOW_ADAPTER_DID_NOT_CHANGE_SOURCE')
    return updated,{'originalSHA256':sha256(raw).hexdigest(),'adaptedSHA256':sha256(updated).hexdigest(),
        'legacyPrefixesNormalized':prefixes,'queryWrappersUnpacked':explicit+shorthand}


def regular(path):
    return path.is_file() and not path.is_symlink() and not getattr(path.lstat(),'st_file_attributes',0)&0x400 and path.resolve(strict=True)==path


@contextmanager
def workflow_request_override(project,reference):
    project,reference=Path(project).resolve(strict=True),Path(reference).resolve(strict=True)
    if project==reference or project.is_relative_to(reference) or reference.is_relative_to(project):
        raise ValueError('DISTINCT_BUILD_COPY_AND_PRISTINE_SOURCE_REQUIRED')
    planned=[];files={}
    for relative in SOURCE_PINS:
        target,origin=project/relative,reference/relative
        if not regular(target) or not regular(origin) or target.samefile(origin):raise ValueError('DIRECT_DISTINCT_WORKFLOW_SOURCE_FILES_REQUIRED')
        raw=origin.read_bytes()
        if target.read_bytes()!=raw:raise ValueError('BUILD_WORKFLOW_SOURCE_DRIFT')
        updated,pins=transform(relative,raw);planned.append((target,raw,updated));files[relative]=pins
    receipt={'adapter':'original-jnpf-workflow-request-contract-v1','includesPriorUserSelectorCompatibility':True,
        'requestPathsMethodsAndParameterPackingOnly':True,'authenticationOrPermissionModified':False,'referenceModified':False,
        'sourceFilesRestored':False,'files':files,
        'unverifiedOriginalBranches':['SubFlowInfo legacy scalar does not provide declared SubFlowDTO','Resurgence reference handler is empty and its legacy route is absent']}
    written=[]
    try:
        for target,raw,updated in planned:target.write_bytes(updated);written.append((target,raw,updated))
        yield receipt
    finally:
        drifted=[]
        for target,raw,updated in reversed(written):
            try:current=target.read_bytes()
            except OSError:drifted.append(target);continue
            if current!=updated:drifted.append(target)
            else:target.write_bytes(raw)
        receipt['sourceFilesRestored']=not drifted
        if drifted:raise ValueError('BUILD_WORKFLOW_EXTERNALLY_CHANGED_STOP_RESTORE')
