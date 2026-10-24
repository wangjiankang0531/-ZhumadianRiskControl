"""Adapt deployment metadata in a pinned original admin archive, entirely in memory."""
import argparse,datetime,gzip,hashlib,json,os,pathlib,re,subprocess,threading,time


def adapt_admin_files(files,base,node,parser,script=None):
    if not isinstance(base,str) or not re.fullmatch(r'/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',base) or len(base)>128:raise ValueError('Explicit safe admin deployment base required')
    node,parser=pathlib.Path(node).resolve(),pathlib.Path(parser).resolve()
    script=pathlib.Path(script or pathlib.Path(__file__).with_name('adapt_original_admin_static.mjs')).resolve()
    for item in [node,parser,script]:
        if not item.is_file():raise ValueError('Explicit existing Node, parser, and own deployment recipe required')
    if hashlib.sha256(files['static/js/index-26528473.js']).hexdigest()!='35e93f07c7985577bdbe89123500ad1e3009e5d3e8ca36309808dd9913c91e7d':raise ValueError('Original admin main script differs')
    if hashlib.sha256(files['_app.config.js']).hexdigest()!='d66b519756a85b8d7e81382f832fb88d6cde5ff1813c4d820987424b9739e0bf':raise ValueError('Original admin configuration differs')
    selected=[]
    markers=[b'"/static',b"'/static",b'`/static',b'"/assets',b"'/assets",b'`/assets',b'"/fonts',b"'/fonts",b'`/fonts']
    for name,data in files.items():
        if name.endswith(('.html','.css')) or name in ['static/js/index-26528473.js','_app.config.js'] or (name.endswith('.js') and any(marker in data for marker in markers)):
            selected.append({'path':name,'text':data.decode('utf-8')})
    env={key:value for key,value in os.environ.items() if key.upper() not in ['NODE_OPTIONS','NODE_PATH','NODE_EXTRA_CA_CERTS']}
    payload=json.dumps({'base':base,'files':selected,'assetPaths':list(files)},ensure_ascii=False).encode('utf-8')
    run=subprocess.run([str(node),str(script),str(parser)],input=payload,capture_output=True,timeout=90,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if run.returncode!=0:raise RuntimeError('Own AST deployment recipe failed: '+run.stderr.decode('utf-8',errors='replace')[-600:])
    result=json.loads(run.stdout);adapted=dict(files);changes=[]
    for row in result['files']:
        name=row['path'];original=files[name];data=row['text'].encode('utf-8');adapted[name]=data
        changes.append({'path':name,'originalSHA256':hashlib.sha256(original).hexdigest(),'deployedSHA256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'patches':row['patches'],'offsetUnit':'JavaScript UTF-16 code units'})
        if name+'.gz' in files:
            packed=gzip.compress(data,mtime=0);assert gzip.decompress(packed)==data;adapted[name+'.gz']=packed
            changes.append({'path':name+'.gz','originalSHA256':hashlib.sha256(files[name+'.gz']).hexdigest(),'deployedSHA256':hashlib.sha256(packed).hexdigest(),'bytes':len(packed),'regeneratedForChangedOriginalResource':name})
    if len(adapted)!=len(files):raise ValueError('Unexpected original static file set change')
    for name,data in files.items():
        if name not in {row['path'] for row in changes} and adapted[name]!=data:raise ValueError('Unrelated original resource changed')
    receipt={'base':base,'originalFileCount':len(files),'deployedFileCount':len(adapted),'changedFiles':changes,'ASTChanges':result['counts'],'recipeSHA256':hashlib.sha256(script.read_bytes()).hexdigest(),
             'nodeSHA256':hashlib.sha256(node.read_bytes()).hexdigest(),'parserSHA256':hashlib.sha256(parser.read_bytes()).hexdigest(),'originalJavaScriptEvaluated':False,'originalResourcesExtracted':False,
             'businessLogicRedesigned':False,'authenticatedOperationsVerified':False}
    return adapted,receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['archive','node','parser','output']:parser.add_argument('--'+name,type=pathlib.Path,required=True)
    parser.add_argument('--sha256',required=True);parser.add_argument('--base',required=True)
    parser.add_argument('--serve-minutes',type=int);parser.add_argument('--platform-owner-root',type=pathlib.Path)
    args=parser.parse_args()
    if args.serve_minutes is not None and not 1<=args.serve_minutes<=20:raise ValueError('Bounded independent serve duration required')
    if args.platform_owner_root and args.serve_minutes is None:raise ValueError('Read-only platform inspection requires explicit serving')
    output=args.output.resolve();source=args.archive.resolve()
    if output.exists() or output.is_relative_to(source.parent) or output.is_relative_to(args.parser.resolve().parent):raise ValueError('Fresh evidence output outside original inputs required')
    from readonly_original_static_archive import load_archive,ArchiveServer,verified_platform_owner
    files,original=load_archive(source,args.sha256)
    adapted,recipe=adapt_admin_files(files,args.base,args.node,args.parser)
    output.mkdir(parents=True)
    receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'source':original,'deploymentRecipe':recipe,'resourcesCopiedOrExtracted':False,
             'originalPlatformAnonymousGETOnly':False,'authenticatedOperationsVerified':False,'publicDeployed':False,'fullCloneReady':False}
    if args.serve_minutes is not None:
        port=pid=None
        if args.platform_owner_root:port,pid=verified_platform_owner(args.platform_owner_root)
        server=ArchiveServer(adapted,port,mount_prefix=args.base);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        receipt.update(url='http://127.0.0.1:'+str(server.server_port)+args.base+'/',originalPlatformOwnerPID=pid,originalPlatformAnonymousGETOnly=pid is not None,loginPOSTPermitted=False)
        (output/'ready.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps({'state':'ready','url':receipt['url']}),flush=True)
        try:
            deadline=time.monotonic()+args.serve_minutes*60
            while not (output/'stop').exists() and time.monotonic()<deadline:
                if not worker.is_alive():raise RuntimeError('Owned original static inspection server stopped unexpectedly')
                time.sleep(.25)
        finally:
            server.shutdown();server.server_close();worker.join(timeout=3)
            receipt.update(ownedServerStopped=not worker.is_alive(),statusCounts=dict(server.counts),missingPaths=dict(server.missing_paths),unavailableAPIReads=dict(server.unavailable_reads),originalReadResponses=server.original_reads)
            if worker.is_alive():raise RuntimeError('Owned inspection server shutdown incomplete')
    receipt['finishedAt']=datetime.datetime.now().astimezone().isoformat()
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({'base':args.base,'files':len(adapted),'changedFiles':len(recipe['changedFiles']),'resourcesCopiedOrExtracted':False,'publicDeployed':False}),flush=True)


if __name__=='__main__':main()
