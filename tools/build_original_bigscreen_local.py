"""Build original bigscreen UI using two pinned request overlays, without changing source or copying public assets."""
import argparse,datetime,hashlib,json,os,pathlib,re,shutil,subprocess

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--mount',required=True);p.add_argument('--mock-base',required=True);a=p.parse_args()
 W=a.workspace.resolve(strict=True);A=W.parents[1];assert A.name=='Application';root=a.output.resolve();assert root.is_relative_to(W) and not root.exists()
 assert re.fullmatch('/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*/',a.mount) and re.fullmatch('/[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',a.mock_base)
 project=json.loads((A.parent/'Document/Deployment/tianjin_native_replica_20261023/original_source_copies.json').read_bytes())['projects']['bigscreen'];src=pathlib.Path(project['copy']).resolve(strict=True);ref=pathlib.Path(project['reference']).resolve(strict=True);assert src!=ref and src.is_relative_to(W)
 sha=lambda f:hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
 def check_sources():
  for row in project['files']:assert sha(src/row['path'])==row['sha256'] and sha(ref/row['path'])==row['sha256'],'ORIGINAL_SOURCE_INPUT_CHANGED'
 check_sources();assert shutil.disk_usage(W).free>1024**3,'ONE_GIB_BUILD_RESERVE_REQUIRED';root.mkdir();(root/'tmp').mkdir();parser=W/'security_pc/node_modules/@babel/parser/lib/index.js';node=pathlib.Path('D:/Program Files/nodejs/node.exe');assert node.is_file()
 env={k:v for k,v in os.environ.items() if k not in ('NODE_OPTIONS','VUE_CLI_SERVICE_CONFIG_PATH')};env.update(TEMP=str(root/'tmp'),TMP=str(root/'tmp'),NODE_OPTIONS='--openssl-legacy-provider',VUE_CLI_SERVICE_CONFIG_PATH=str(root/'vue.own.config.cjs'))
 adapt=[str(node),str(A/'tools/adapt_original_bigscreen_requests.mjs'),'--service-source',str(src/'src/utils/service.js'),'--request-source',str(src/'src/utils/request.js'),'--mock-base',a.mock_base,'--parser',str(parser),'--parser-sha256','82d72e197e27bf909ae10ffc8d1a969aeb94fe96ec96c4e9cb685a0a8229e40c','--output',str(root/'overlays')]
 r=subprocess.run(adapt,env=env,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);(root/'adapter.private.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0,'REQUEST_OVERLAY_PREPARATION_FAILED'
 mapping={str(src/'src/utils'/name):{'inputSHA256':sha(src/'src/utils'/name),'overlay':str(root/'overlays'/name),'overlaySHA256':sha(root/'overlays'/name),'receipt':str(root/('compiled-'+name+'.json'))} for name in ('service.js','request.js')}
 loader='''const fs=require('fs'),crypto=require('crypto');
const mapping=MAP;
module.exports=function(source){this.cacheable(false);const row=mapping[this.resourcePath];if(!row)throw Error('EXACT_ORIGINAL_RESOURCE_REQUIRED');const sha=x=>crypto.createHash('sha256').update(x).digest('hex');if(sha(Buffer.from(source))!==row.inputSHA256)throw Error('ORIGINAL_SOURCE_PIN_MISMATCH');const overlay=fs.readFileSync(row.overlay);if(sha(overlay)!==row.overlaySHA256)throw Error('OWN_OVERLAY_PIN_MISMATCH');this.addDependency(row.overlay);fs.writeFileSync(row.receipt,JSON.stringify({inputSHA256:row.inputSHA256,compiledSHA256:sha(overlay),originalRelativeImportContextPreserved:true}));return overlay.toString('utf8');};
'''.replace('MAP',json.dumps(mapping))
 (root/'own-request-loader.cjs').write_text(loader,encoding='utf-8')
 config='''const cfg=require(ORIGINAL);const chain=cfg.chainWebpack;
cfg.publicPath=MOUNT;cfg.outputDir=OUTPUT;cfg.parallel=false;
cfg.chainWebpack=config=>{if(chain)chain(config);config.plugins.delete('copy');const rule=config.module.rule('own-original-bigscreen-requests').test(/\\.js$/).enforce('pre');for(const file of INPUTS)rule.include.add(file);rule.use('own-pinned-request-overlay').loader(LOADER);};
module.exports=cfg;
'''
 for key,value in [('ORIGINAL',str(src/'vue.config.js')),('MOUNT',a.mount),('OUTPUT',str(root/'dist')),('INPUTS',list(mapping)),('LOADER',str(root/'own-request-loader.cjs'))]:config=config.replace(key,json.dumps(value))
 (root/'vue.own.config.cjs').write_text(config,encoding='utf-8');command=[str(node),str(src/'node_modules/@vue/cli-service/bin/vue-cli-service.js'),'build','--dest',str(root/'dist')]
 receipt={'startedAt':datetime.datetime.now().astimezone().isoformat(),'sourceFilesVerified':len(project['files']),'originalSourceChanged':False,'publicAssetsCopied':False,'readOnlyPublicAssetRoot':str(src/'public'),'estimatedMaximumOutputBytes':1024**3,'mount':a.mount,'mockBase':a.mock_base,'buildCompleted':False,'gatewayChanged':False,'servedOrOpenedInBrowser':False,'publicDeployed':False,'fullCloneReady':False}
 try:
  with (root/'build.private.log').open('wb') as log:r=subprocess.run(command,cwd=src,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=300,creationflags=subprocess.CREATE_NO_WINDOW)
  receipt['buildExitCode']=r.returncode;assert r.returncode==0,'ORIGINAL_UI_OVERLAY_BUILD_FAILED'
  for name in ('service.js','request.js'):
   seen=json.loads((root/('compiled-'+name+'.json')).read_bytes());assert seen['compiledSHA256']==sha(root/'overlays'/name) and seen['originalRelativeImportContextPreserved']
  assert (root/'dist/index.html').is_file() and not (root/'dist/config.js').exists(),'PUBLIC_ASSETS_MUST_BE_REFERENCED_NOT_COPIED'
  bundles=list((root/'dist').rglob('*.js'));assert bundles and all(b'https://mock.apipost.net/mock/42471b1e0ce0000' not in f.read_bytes() for f in bundles),'EXTERNAL_MOCK_LITERAL_REMAINS'
  outputs=[f for f in (root/'dist').rglob('*') if f.is_file()];receipt.update(buildCompleted=True,bothPinnedOverlaysActuallyCompiled=True,externalMockLiteralAbsent=True,outputFiles=len(outputs),outputBytes=sum(f.stat().st_size for f in outputs),outputSHA256={f.relative_to(root/'dist').as_posix():sha(f) for f in outputs})
 finally:
  check_sources();receipt['completedAt']=datetime.datetime.now().astimezone().isoformat();(root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:v for k,v in receipt.items() if k!='outputSHA256'}))

if __name__=='__main__':main()
