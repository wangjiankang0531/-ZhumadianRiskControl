"""Optional exact native before-addsign history module; old releases stay strict no-ops.

Configuration is adapted in memory. Never edit private settings or log arguments.
The original authentication and async support archives remain byte-identical.
"""
from pathlib import Path
import copy,hashlib,re

FIELD='nativeBeforeAddsignOpinionHistory'
CONTRACT=None  # Fixed by the artifact builder, together with the exact Java 8 code pins.
INITIALIZER='xnby.platform.history.NativeBeforeAddsignHistoryInitializer'
OLD_MAIN='xnby.platform.OriginalAsyncPersistentPlatformLaunch'
NEW_MAIN='xnby.platform.OriginalHistoryPersistentPlatformLaunch'

def need(value,message):
    if not value:raise ValueError(message)

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def regular(path):
    path=Path(path).absolute()
    need(path.resolve(strict=True)==path and path.is_file(),'EXACT_REGULAR_HISTORY_RUNTIME_CODE_REQUIRED')
    for p in [path,*path.parents]:need(not p.is_symlink()and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'HISTORY_CODE_REDIRECTION_REFUSED')
    return path

def descriptor(release):
    if FIELD not in release:return None
    value=release[FIELD]
    need(CONTRACT is not None and isinstance(value,dict)and value==CONTRACT,'EXACT_DECLARED_NATIVE_HISTORY_REQUIRED')
    return value

def configure_history(release,spec):
    value=descriptor(release)
    if value is None:return spec
    from original_platform_async_release_support import descriptor as async_descriptor
    need(async_descriptor(release)is not None,'ORIGINAL_DECLARED_ASYNC_SUPPORT_REQUIRED_FOR_HISTORY')
    need(isinstance(spec,dict)and isinstance(spec.get('configuration'),dict)and isinstance(spec['configuration'].get('platform'),dict),'HISTORY_PLATFORM_CONFIGURATION_REQUIRED')
    value=spec['configuration']['platform'].get('context.initializer.classes','')
    need(isinstance(value,str)and value.isascii()and len(value)<=8192,'HISTORY_INITIALIZER_LIST_REQUIRED')
    items=value.split(',')if value else []
    need(len(set(items))==len(items)and all(re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+',x)for x in items),'HISTORY_INITIALIZER_LIST_INVALID')
    need(INITIALIZER not in items,'HISTORY_INITIALIZER_ALREADY_PRESENT')
    args=spec.get('platformArguments')
    need(isinstance(args,list)and all(isinstance(x,str)for x in args)and not any(x.startswith('-Down.workflow.before-addsign.')for x in args),'UNDECLARED_HISTORY_ARGUMENT_REFUSED')
    result=copy.deepcopy(spec);result['configuration']['platform']['context.initializer.classes']=','.join([*items,INITIALIZER])
    return result

def adapt_history_launch(application,release,platform_run,prepared):
    value=descriptor(release)
    if value is None:return prepared
    from original_platform_async_release_support import descriptor as async_descriptor,NATIVE_SHA256,ADAPTER_SHA256
    original=async_descriptor(release);need(original is not None,'PINNED_ORIGINAL_ASYNC_REQUIRED')
    app,root=Path(application).absolute(),Path(platform_run).absolute()
    need(app.name=='Application'and root.parent==app/'UserData/TianjinOriginalPlatform/runs'and re.fullmatch(r'j[1-9][0-9]{0,3}',root.name),'OWN_HISTORY_RUNTIME_LAYOUT_REQUIRED')
    for rel,pin in {**original['files'],**value['files']}.items():
        need(rel.startswith('payload/platform/run-template/')and '..'not in Path(rel).parts,'HISTORY_RUNTIME_PATH_REQUIRED')
        p=regular(root/rel.split('/run-template/',1)[1]);need(p.stat().st_size==pin['bytes']and sha(p)==pin['sha256'],'DECLARED_HISTORY_OR_ORIGINAL_ASYNC_CODE_CHANGED')
    need(sha(regular(root/'own-platform-observation.jar'))==ADAPTER_SHA256,'ORIGINAL_AUTH_ARCHIVE_REQUIRED_FOR_HISTORY')
    need(isinstance(prepared,dict)and prepared.get('side')=='platform'and Path(prepared.get('runtime','')).absolute()==root,'EXACT_HISTORY_PREPARED_RUNTIME_REQUIRED')
    items=prepared.get('configuration',{}).get('context.initializer.classes','').split(',');need(items.count(INITIALIZER)==1,'DECLARED_HISTORY_INITIALIZER_REQUIRED')
    arguments=prepared.get('arguments');need(isinstance(arguments,list)and all(isinstance(x,str)for x in arguments)and arguments.count(OLD_MAIN)==1 and NEW_MAIN not in arguments,'EXACT_ASYNC_MAIN_REQUIRED_BEFORE_HISTORY')
    need(not any(x.startswith('-Down.workflow.before-addsign.')for x in arguments),'HISTORY_ARGUMENT_OVERRIDE_REFUSED')
    index=arguments.index(OLD_MAIN);need(index>=2 and index+3==len(arguments)and '-cp'in arguments[:index],'EXACT_HISTORY_MAIN_ARGUMENT_SHAPE_REQUIRED')
    native=regular(arguments[-2]);need(sha(native)==NATIVE_SHA256 and Path(arguments[-1]).absolute()==root,'EXACT_ORIGINAL_NATIVE_ARCHIVE_AND_RUNTIME_REQUIRED')
    for key,wanted in [('own.platform.root',root),('own.platform.source.path',native)]:
        selected=[x[len('-D'+key+'='):]for x in arguments[:index]if x.startswith('-D'+key+'=')];need(len(selected)==1 and Path(selected[0]).absolute()==wanted,'EXACT_ORIGINAL_HISTORY_PATH_PROPERTIES_REQUIRED')
    rewritten=list(arguments);rewritten[index]=NEW_MAIN
    jar=value['files']['payload/platform/run-template/own-before-addsign-history.jar']
    result=dict(prepared);result['arguments']=['-Down.workflow.before-addsign.history.enabled=true','-Down.workflow.before-addsign.module.sha256='+jar['sha256'],*rewritten]
    return result
