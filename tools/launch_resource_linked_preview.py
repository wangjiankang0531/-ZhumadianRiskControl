"""Short, sealed launcher for resource-linked local preview shortcuts."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys


def launch(configuration, *, open_browser=False, stop=False):
    if open_browser and stop:
        raise ValueError('Open and stop are exclusive')
    configuration=Path(configuration).resolve()
    raw=configuration.read_bytes()
    if not 0<len(raw)<=65536:
        raise ValueError('Preview launcher configuration exceeds limit')
    value=json.loads(raw)
    arguments=value.get('arguments')
    if (value.get('schema')!='xnby.resource_linked_preview.launcher.v1' or
        not isinstance(arguments,list) or not 1<=len(arguments)<=80 or
        not all(isinstance(v,str) and v and len(v)<=4096 and '\0' not in v for v in arguments) or
        any(v in arguments for v in ('--stop','--no-browser')) or arguments.count('--state')!=1):
        raise ValueError('Invalid sealed preview launcher arguments')
    state_index=arguments.index('--state')+1
    if state_index>=len(arguments) or arguments[state_index]!=value.get('state'):
        raise ValueError('Preview state differs from sealed configuration')
    controller=configuration.parent/'tools/serve_native_preview.py'
    if controller.is_symlink() or hashlib.sha256(controller.read_bytes()).hexdigest()!=value.get('controllerSHA256'):
        raise ValueError('Preview controller differs from sealed launcher')
    selected=['--state',value['state'],'--stop','--no-browser'] if stop else [*arguments,*([] if open_browser else ['--no-browser'])]
    sys.argv=[str(controller),*selected]
    sys.path.insert(0,str(controller.parent))
    runpy.run_path(str(controller),run_name='__main__')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--open',action='store_true')
    mode.add_argument('--stop',action='store_true')
    args=parser.parse_args()
    launch(args.config,open_browser=args.open,stop=args.stop)


if __name__=='__main__':
    main()
