"""Run one SHA-pinned original operation and retain its actual child handles.

The caller must create this wrapper using normal Windows background execution,
outside the transient SSH command's process lifetime. No service registration,
security settings, implicit stop, restart or termination is performed here.
"""
from pathlib import Path
import contextlib,hashlib,json,os,runpy,subprocess,sys,time,traceback


def need(value,code):
    if not value:raise ValueError(code)


def regular(path):
    path=Path(path).absolute()
    need('..'not in path.parts,'CANONICAL_ABSOLUTE_PATH_REQUIRED')
    for parent in [path,*path.parents]:
        if parent.exists():
            need(not parent.is_symlink() and not(parent.lstat().st_file_attributes&1024),'REPARSE_REFUSED')
    return path


def read_scope(path,pin):
    path=regular(path);raw=path.read_bytes()
    need(len(raw)<=32768 and len(pin)==64 and hashlib.sha256(raw).hexdigest()==pin,'EXACT_OPERATION_SCOPE_REQUIRED')
    def pairs(rows):
        value={}
        for key,item in rows:
            need(key not in value,'DUPLICATE_SCOPE_KEY');value[key]=item
        return value
    value=json.loads(raw.decode('utf8'),object_pairs_hook=pairs)
    need(set(value)=={'schema','operation','operationSHA256','arguments','controllerScript','allowedReleaseSHA256','python'},'EXACT_SCOPE_FIELDS_REQUIRED')
    need(value['schema']=='xnby.durable-original-operation.v1','EXACT_SCOPE_SCHEMA_REQUIRED')
    for key in ['operation','controllerScript','python']:value[key]=regular(value[key])
    need(value['operation'].is_file() and hashlib.sha256(value['operation'].read_bytes()).hexdigest()==value['operationSHA256'],'EXACT_OPERATION_SOURCE_REQUIRED')
    need(value['controllerScript'].name=='serve_original_server_release.py' and value['controllerScript'].is_file(),'EXACT_ORIGINAL_CONTROLLER_PATH_REQUIRED')
    need(value['python'].samefile(sys.executable),'EXACT_INSTALLED_INTERPRETER_REQUIRED')
    need(isinstance(value['arguments'],list) and len(value['arguments'])<=16 and all(isinstance(v,str)and len(v)<=4096 and '\0'not in v for v in value['arguments']),'BOUNDED_ORIGINAL_ARGUMENTS_REQUIRED')
    need(isinstance(value['allowedReleaseSHA256'],list) and 1<=len(value['allowedReleaseSHA256'])<=2 and all(isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef'for c in v)for v in value['allowedReleaseSHA256']),'EXPLICIT_OLD_AND_NEW_RELEASES_REQUIRED')
    return path,value


def main(scope_path,pin):
    path,scope=read_scope(scope_path,pin);root=path.parent
    def put(name,value):
        with regular(root/name).open('x',encoding='utf8')as f:
            json.dump(value,f,separators=(',',':'));f.flush();os.fsync(f.fileno())
    need(not(root/'operation-result.json').exists() and not(root/'wrapper-terminal.json').exists(),'NO_REPEAT_OPERATION_REQUIRED')
    actual_popen=subprocess.Popen;children=[];operation_code=0;error_code=None
    def tracked(command,*args,**kwargs):
        relevant=isinstance(command,(list,tuple)) and any(isinstance(v,(str,os.PathLike)) and str(v).replace('\\','/').split('/')[-1]=='serve_original_server_release.py'for v in command)
        if relevant:
            argv=[os.fspath(v) for v in command]
            need(str(scope['controllerScript'])in argv,'ONLY_EXACT_CONTROLLER_SCRIPT_REQUIRED')
            need(regular(argv[0]).samefile(scope['python']),'ORIGINAL_CONTROLLER_INTERPRETER_REQUIRED')
            need(argv.count('--release-manifest-sha256')==1,'EXACT_CONTROLLER_RELEASE_ARGUMENT_REQUIRED')
            index=argv.index('--release-manifest-sha256')
            need(index+1<len(argv) and argv[index+1]in scope['allowedReleaseSHA256'],'CONTROLLER_RELEASE_OUTSIDE_SCOPE')
            need(not kwargs.get('shell',False),'NO_CONTROLLER_SHELL_REQUIRED')
        child=actual_popen(command,*args,**kwargs)
        if relevant:
            children.append(child)
            put('controller-created-'+str(len(children))+'.json',{'wrapperPID':os.getpid(),'controllerPID':child.pid,'realPopenHandleRetained':True})
        return child
    previous_argv=sys.argv;subprocess.Popen=tracked
    try:
        with (root/'operation.private.log').open('x',encoding='utf8')as log:
            with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
                sys.argv=[str(scope['operation']),*scope['arguments']]
                try:runpy.run_path(str(scope['operation']),run_name='__main__')
                except SystemExit as error:
                    operation_code=error.code if type(error.code)is int else 0 if error.code is None else 1
                except BaseException as error:
                    operation_code=1;error_code=type(error).__name__;traceback.print_exc()
    finally:
        subprocess.Popen=actual_popen;sys.argv=previous_argv
    report_failure=False
    try:
        put('operation-result.json',{'operationExitCode':operation_code,'safeErrorType':error_code,'createdControllers':len(children),'liveControllersWhenOperationReturned':sum(p.poll()is None for p in children),'actualChildHandlesRetained':True,'wrapperPID':os.getpid(),'forcedTermination':False})
    except OSError:
        # An observer/report disk failure must not abandon a running controller.
        report_failure=True
    # Failure does not abandon a newly started or restored original controller.
    # The release's own normal shutdown remains its only lifecycle authority.
    codes=[]
    for child in children:
        while child.poll()is None:
            try:child.wait(timeout=15)
            except subprocess.TimeoutExpired:pass
        codes.append({'controllerPID':child.pid,'actualExitCode':child.returncode})
    final=operation_code if operation_code else 0 if not report_failure and all(x['actualExitCode']==0 for x in codes)else 1
    try:
        put('wrapper-terminal.json',{'wrapperPID':os.getpid(),'operationExitCode':operation_code,'controllers':codes,'actualWrapperExitCode':final,'allCapturedControllersTerminal':True,'forcedTermination':False})
    except OSError:
        final=1
    return final


if __name__=='__main__':
    need(len(sys.argv)==3,'EXACT_SCOPE_FILE_AND_HASH_ARGUMENTS_REQUIRED')
    raise SystemExit(main(sys.argv[1],sys.argv[2]))
