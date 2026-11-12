"""Run an owned sync supervisor, inspect its identity, or request a normal stop.

Run is deliberately foreground: the existing application controller must retain
its original Popen handle. This command does not install a Windows service or
modify the original project's IIS/nginx configuration.
"""
import argparse
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.layer_sync_supervisor import supervise,controller_status,request_controller_stop


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    run=sub.add_parser('run');run.add_argument('--config',type=Path,required=True)
    run.add_argument('--config-sha256',required=True);run.add_argument('--manifest-sha256',required=True)
    run.add_argument('--data-root',type=Path,required=True);run.add_argument('--control-root',type=Path,required=True)
    run.add_argument('--max-restarts',type=int,default=1);run.add_argument('--start-timeout',type=float,default=15)
    run.add_argument('--stop-timeout',type=float,default=15)
    for action in ['status','stop']:sub.add_parser(action).add_argument('--control-root',type=Path,required=True)
    args=parser.parse_args()
    if args.action=='status':print(json.dumps(controller_status(args.control_root)));return 0
    if args.action=='stop':print(json.dumps(request_controller_stop(args.control_root)));return 0
    return supervise(Path(__file__).resolve().parents[1],args.config,args.config_sha256,args.manifest_sha256,
                     args.data_root,args.control_root,max_restarts=args.max_restarts,
                     start_timeout=args.start_timeout,stop_timeout=args.stop_timeout)


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError,RuntimeError) as error:
        code=str(error) if re.fullmatch('[A-Z0-9_]+',str(error)) else type(error).__name__
        print(json.dumps({'ready':False,'error':code}),flush=True);raise SystemExit(1)
