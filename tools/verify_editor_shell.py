"""Check adaptive editor layout against the live Vulkan target, without OS input injection."""
import argparse, json, subprocess
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',required=True)
    parser.add_argument('--layers',required=True,help='Use a test copy of your layer file')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=True)
    with (output/'shell_probe.log').open('wb') as log:
        subprocess.run([str(Path(args.exe).resolve()),'--editor-shell-probe',
                        '--layers='+str(Path(args.layers).resolve()),'--stats='+str(output/'shell_probe.json')],
                       cwd=output,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    report=json.loads((output/'shell_probe.json').read_text(encoding='utf-8'))
    assert report['passed'] and len(report['states'])==8
    assert report['states'][0]['maximized'] and not report['states'][1]['panel_visible']
    assert report['states'][3]['dock_right'] and report['states'][6]['scroll']>0
    assert report['document_unchanged'] and report['draft_unchanged']
    print('LIVE EDITOR WINDOW / DOCK / HIDE / RESIZE / SCROLL / DOCUMENT PASS')

if __name__=='__main__':main()
