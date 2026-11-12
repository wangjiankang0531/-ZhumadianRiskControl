"""Publisher-only pinned ingress prepare/apply/recover; no automatic deployment."""
import argparse,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.layer_sync_deployment import DeploymentDriver,capture_preflight
from tools.layer_sync_server_owner import plain,read,loads,sha
from tools.layer_sync_supervisor import write_new,encode


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    snapshot=sub.add_parser('snapshot');snapshot.add_argument('--application',type=Path,required=True);snapshot.add_argument('--release-manifest-sha256',required=True);snapshot.add_argument('--output',type=Path,required=True)
    prepare=sub.add_parser('prepare');prepare.add_argument('--application',type=Path,required=True);prepare.add_argument('--preflight',type=Path,required=True);prepare.add_argument('--preflight-sha256',required=True)
    prepare.add_argument('--proxy-sha256',required=True);prepare.add_argument('--nginx-sha256',required=True);prepare.add_argument('--service-binding',type=Path,required=True);prepare.add_argument('--service-binding-sha256',required=True)
    prepare.add_argument('--project-files',action='store_true',help='Require configured private project JSON library and add its pinned routes');prepare.add_argument('--origin',required=True);prepare.add_argument('--nonce',required=True);prepare.add_argument('--transaction-root',type=Path,required=True)
    for name in ['apply','recover']:
        command=sub.add_parser(name);command.add_argument('--transaction-root',type=Path,required=True);command.add_argument('--plan-sha256',required=True)
    args=p.parse_args()
    if args.action=='snapshot':
        output=plain(args.output);app=plain(args.application)
        if output.is_relative_to(app/'iis') or output.exists():raise ValueError('NEW_PRIVATE_PREFLIGHT_OUTPUT_REQUIRED')
        value=capture_preflight(app,args.release_manifest_sha256);output.parent.mkdir(parents=True,exist_ok=True);write_new(output,encode(value))
        print(json.dumps({'snapshotPassed':True,'preflightSHA256':sha(read(output,65536)),'publicFilesChanged':False}));return
    if args.action=='prepare':
        binding_raw=read(args.service_binding,65536)
        if sha(binding_raw)!=args.service_binding_sha256:raise ValueError('SERVICE_BINDING_PIN_CHANGED')
        driver=DeploymentDriver.prepare(args.transaction_root,args.application,read(args.preflight,65536),args.preflight_sha256,args.proxy_sha256,loads(binding_raw),
                                       args.nginx_sha256,args.origin,args.nonce,project_files=args.project_files)
        print(json.dumps({'prepared':True,'planSHA256':sha(read(plain(args.transaction_root)/'deployment.json',131072)),'phase':driver.bundle.status['phase'],'publicFilesChanged':False}));return
    driver=DeploymentDriver(args.transaction_root,args.plan_sha256)
    result=driver.apply() if args.action=='apply' else driver.recover()
    print(json.dumps({'phase':result['phase'],'action':args.action,'databaseAndUserLayersWritten':False}))


if __name__=='__main__':
    try:main()
    except Exception as error:
        value=str(error);code=value if re.fullmatch('[A-Z0-9_]+',value) else type(error).__name__
        print(json.dumps({'passed':False,'error':code,'preserveTransactionEvidence':True}));raise SystemExit(1)
