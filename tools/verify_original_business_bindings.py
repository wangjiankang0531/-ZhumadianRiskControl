"""Verify prepared values using original configuration beans and Spring Binder, without app startup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.parse
import zipfile
from reference_flat_runtime import verify

PINS={'com/iemp/endanger/base/entity/SystemParams.class':'2d81f9622423dd349119b3584ce13efedaeab4ec5ee17177917cc14d345fd432','com/iemp/endanger/util/flow/FlowConfig.class':'e81328ed9e1908902b9478c1b6eecc77752602ea0e98863097628c3034fa6296'}
def check(value,code):
 if not value:raise ValueError(code)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_bindings(workspace,candidate,pin,output):
 w,candidate,output=map(Path,(workspace,candidate,output));check(not output.exists(),'FRESH_OUTPUT_REQUIRED');check(re.fullmatch('[0-9a-f]{64}',pin),'EXPLICIT_PRIVATE_CONFIG_PIN_REQUIRED');check(candidate.is_file() and candidate.stat().st_size<=256*1024 and sha(candidate)==pin,'PRIVATE_CONFIG_PIN_MISMATCH');flat=w/'original-shared-runtime-r1_20261024/flat';verify(flat)
 meta=json.loads((w/'own-pboot-r32/preparation.json').read_bytes());java=Path(meta['javaHome']);sources=[Path(__file__).parent/'java'/n for n in ('OriginalInternalPlatformObservation.java','OriginalBusinessBeanBindingFixture.java')]
 with zipfile.ZipFile(flat/'application.jar') as z:
  pins={n:hashlib.sha256(z.read(n)).hexdigest() for n in PINS};check(pins==PINS,'ORIGINAL_CONFIG_CLASS_PIN_MISMATCH');manifest=z.read('META-INF/MANIFEST.MF').decode().replace('\r\n ','').replace('\n ','');uris=next(l[len('Class-Path: '):] for l in manifest.splitlines() if l.startswith('Class-Path: ')).split()
 deps=[]
 for uri in uris:
  path=urllib.parse.unquote(urllib.parse.urlsplit(uri).path)
  if re.match(r'^/[A-Za-z]:',path):path=path[1:]
  deps.append(Path(path) if uri.startswith('file:') else flat/path)
 check(len(deps)==219,'ORIGINAL_DEPENDENCY_ORDER_SCOPE');output.mkdir();classes=output/'classes';classes.mkdir();cp=os.pathsep.join(map(str,[classes,flat/'application.jar',*deps]));env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
 def run(command,name):
  result=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);(output/(name+'.private.log')).write_bytes(result.stdout+result.stderr);check(result.returncode==0,'BINDING_'+name.upper()+'_FAILED');return result.stdout
 run([java/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-cp',cp,'-d',classes,*sources],'compile')
 raw=run([java/'bin/java.exe','-Xmx128m','-cp',cp,'xnby.replica.OriginalBusinessBeanBindingFixture',candidate,pin,output/'binding-summary.properties'],'fixture');check(b'REAL_ORIGINAL_BEAN_BINDINGS_MATCHED=16' in raw,'ORIGINAL_BINDING_COUNT');check(sha(candidate)==pin,'PRIVATE_INPUT_CHANGED')
 summary={line.split('=',1)[0]:line.split('=',1)[1] for line in (output/'binding-summary.properties').read_text('ascii').splitlines() if line and not line.startswith(('#','!'))};check(summary.get('atomicReceiptPublicationVerified')=='true' and summary.get('duplicateReceiptRejected')=='true','ATOMIC_RECEIPT_FIXTURE_NOT_VERIFIED')
 result={'sourceSHA256':{s.name:sha(s) for s in sources},'originalConfigClassSHA256':pins,'inputCandidateSHA256':pin,'realOriginalBeanPropertyBindingsMatched':16,'realSpringBinderUsed':True,'atomicReceiptPublicationVerified':True,'duplicateReceiptRejected':True,'springApplicationStarted':False,'httpOrDatabaseRequested':False,'runningCandidateChanged':False,'fullCloneReady':False};(output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--candidate-properties',type=Path,required=True);p.add_argument('--candidate-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(verify_bindings(a.workspace,a.candidate_properties,a.candidate_sha256,a.output)))
if __name__=='__main__':main()
