"""Reject invalid selected-runtime flags before a real provider can start."""
import hashlib,json,pathlib,subprocess,sys
import argparse
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=pathlib.Path,required=True);p.add_argument('--selection',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);args=p.parse_args()
W=args.workspace.resolve(strict=True);A=W.parents[1];out=args.output.resolve();assert A.name=='Application' and out.is_relative_to(W) and not out.exists();out.mkdir();provider=W/'own-minio-source-build-r1/receipt.json';selection=args.selection.resolve(strict=True);sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();target=out/'must-not-start-provider'
base=[sys.executable,'-B',str(pathlib.Path(__file__).parent/'verify_original_file_roundtrip.py'),'--workspace',str(W),'--provider-receipt',str(provider),'--provider-receipt-sha256',sha(provider),'--output',str(target)]
checks=0
for name,extra,expected in [('missing-pin',['--reference-business-runtime',str(selection)],b'RUNTIME_RECEIPT_AND_PIN_PAIR_REQUIRED'),('bad-pin',['--reference-business-runtime',str(selection),'--reference-business-runtime-sha256','0'*64],b'EXPLICIT_OWN_SOURCE_RUNTIME_SELECTION_PIN_REQUIRED')]:
 r=subprocess.run(base+extra,capture_output=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW);(out/(name+'.private.log')).write_bytes(r.stdout+r.stderr);assert r.returncode!=0 and expected in r.stderr and not target.exists();checks+=1
r=subprocess.run([sys.executable,'-B',str(pathlib.Path(__file__).parent/'verify_original_file_roundtrip.py'),'--help'],capture_output=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0 and b'--reference-business-runtime' in r.stdout;checks+=1
(out/'receipt.json').write_text(json.dumps({'checks':checks,'invalidRuntimeFlagsRejectedBeforeProviderOrOutputCreation':True,'newProviderStarted':False},indent=2)+'\n',encoding='utf-8');print(json.dumps({'checks':checks,'newProviderStarted':False}))
