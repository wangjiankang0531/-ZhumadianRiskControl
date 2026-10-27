"""Prepare the exact PNG2 preview source tree from fixed Git objects and own overlays.

Source preparation only; no SDK restore, build, graphics, file dialog or reader starts.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--application-repository',type=Path,required=True)
    parser.add_argument('--engine-repository',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();tools=Path(__file__).resolve().parent;root=args.output.resolve()
    if root.exists():raise ValueError('Fresh output directory required; do not repeat on an existing export')
    subprocess.run([sys.executable,'-I','-B',str(tools/'prepare_native_manual_preview_source.py'),
        '--application-repository',str(args.application_repository),'--engine-repository',str(args.engine_repository),'--output',str(root)],check=True)
    subprocess.run([sys.executable,'-I','-B',str(tools/'native_png_icon_patch.py'),'--source',str(root)],check=True)
    inputs=json.loads((root/'png-source-receipt.json').read_text(encoding='utf-8'))
    for name,pin in inputs['sourceSHA256'].items():
        if digest(root/name)!=pin:raise ValueError('Prepared PNG source changed: '+name)
    sys.path.insert(0,str(tools))
    from native_png_dialog_probe_patch import patched_probe
    name='Application/native/landscape_editor_annotation_probe.inl';path=root/name
    path.write_bytes(patched_probe(path.read_bytes()))
    pins=dict(inputs['sourceSHA256']);pins[name]=digest(path)
    receipt={'schema':'xnby.native.png-dialog-source.v1','sourceFiles':len(pins),'sourceSHA256':pins,
       'sourcePreparationSHA256':digest(Path(__file__)),'dialogProbePatchSHA256':digest(tools/'native_png_dialog_probe_patch.py'),
       'sourceOnly':True,'graphicsOrDialogsStarted':False,'GISCopied':False}
    (root/'png-dialog-source-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'prepared':True,'sourceFiles':len(pins),'sourceOnly':True,'graphicsOrDialogsStarted':False}))
if __name__=='__main__':main()
