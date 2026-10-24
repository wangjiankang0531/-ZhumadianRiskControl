"""Verify exact three-component business launch scope using real loopback TCP/HTTP fixtures."""
import argparse,hashlib,json,os
from pathlib import Path
import subprocess

def verify_scope(workspace,output):
 w,output=map(Path,(workspace,output))
 if output.exists():raise ValueError('FRESH_OUTPUT_REQUIRED')
 meta=json.loads((w/'own-pboot-r32/preparation.json').read_bytes());row=json.loads((w/'own-mysql-r13/fixture_compile.json').read_bytes());java=Path(meta['javaHome']);boundary=Path(row['boundaryJar']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 if sha(boundary)!=row['boundaryJarSHA256']:raise ValueError('EXISTING_PROCESS_BOUNDARY_PIN_MISMATCH')
 output.mkdir();classes=output/'classes';classes.mkdir();sources=[Path(__file__).parent/'java'/n for n in ('OriginalBusinessLaunch.java','BusinessPortScopeFixture.java')];env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH') and not k.upper().startswith('LOADER_')}
 def run(command,name):
  r=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);(output/(name+'.private.log')).write_bytes(r.stdout+r.stderr)
  if r.returncode!=0:raise RuntimeError('BUSINESS_SCOPE_'+name.upper()+'_FAILED')
  return r.stdout
 run([java/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-cp',boundary,'-d',classes,*sources],'compile')
 cp=os.pathsep.join(map(str,(classes,boundary)));fixture=output/'fixture';fixture.mkdir();raw=run([java/'bin/java.exe','-Xmx128m','-cp',cp,'xnby.replica.BusinessPortScopeFixture',fixture],'fixture')
 prefix=b'BUSINESS_PORT_SCOPE_FIXTURE_RESULT ';line=next(line for line in raw.splitlines() if line.startswith(prefix));result=json.loads(line[len(prefix):])
 if result['passedCases']!=27 or result['exactOwnedPorts']!=3 or result['ownTCPExchanges']!=3 or result['thirdPortHTTPExchanges']!=1 or not result['outsideSentinelUnchanged']:raise RuntimeError('BUSINESS_SCOPE_FIXTURE_INCOMPLETE')
 result.update(sourceSHA256={p.name:sha(p) for p in sources},unchangedProcessBoundaryJarSHA256=sha(boundary),originalApplicationOnFixtureClasspath=False,fullCloneReady=False)
 (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(verify_scope(a.workspace,a.output)))
if __name__=='__main__':main()
