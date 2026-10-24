"""Check exact original-business object-store scope and private overlay without launching an application."""
import argparse,hashlib,json,os
from pathlib import Path
import subprocess


def verify(workspace, output):
    w, output = Path(workspace).resolve(), Path(output).resolve()
    if output.exists(): raise ValueError('FRESH_OUTPUT_REQUIRED')
    meta = json.loads((w/'own-pboot-r32/preparation.json').read_bytes())
    row = json.loads((w/'own-mysql-r13/fixture_compile.json').read_bytes())
    java, boundary, yaml = Path(meta['javaHome']), Path(row['boundaryJar']), Path(meta['yamlJar'])
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    if sha(boundary) != row['boundaryJarSHA256'] or sha(yaml) != '1467931448a0817696ae2805b7b8b20bfb082652bf9c4efaed528930dc49389b': raise ValueError('EXISTING_PINNED_GUARD_OR_YAML_CHANGED')
    here = Path(__file__).resolve().parent; canonical = w.parents[1]/'tools'
    def source(name):
        candidate=here/'java'/name
        return candidate if candidate.is_file() else canonical/'java'/name
    sources=[source(name) for name in ('OriginalBusinessLaunch.java','BusinessPortScopeFixture.java','BusinessObjectStoreScopeFixture.java','OriginalBusinessConfigInventory.java','OriginalBusinessObjectStoreOverlay.java','ObjectStoreOverlayFixture.java','OriginalObjectStoreObservation.java')]
    flat=w/'original-shared-runtime-r1_20261024/flat/application.jar'
    if sha(flat)!='c4637e950664ff2ee26746b80366ca12e8c1f36f69288d35e126871f9afe30ae':raise ValueError('ORIGINAL_FLAT_JAR_PIN_MISMATCH')
    output.mkdir(parents=True);classes=output/'classes';classes.mkdir()
    env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH') and not k.upper().startswith('LOADER_')}
    def run(command,name):
        value=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        (output/(name+'.private.log')).write_bytes(value.stdout+value.stderr)
        if value.returncode!=0:raise RuntimeError('OWN_STORE_SCOPE_'+name.upper()+'_FAILED')
        return value.stdout
    run([java/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-cp',os.pathsep.join(map(str,(boundary,yaml,flat))),'-d',classes,*sources],'compile')
    results={}
    for name,classname,prefix in [('three','BusinessPortScopeFixture',b'BUSINESS_PORT_SCOPE_FIXTURE_RESULT '),('four','BusinessObjectStoreScopeFixture',b'BUSINESS_OBJECT_STORE_SCOPE_RESULT ')]:
        folder=output/name;folder.mkdir();raw=run([java/'bin/java.exe','-Xmx128m','-cp',os.pathsep.join(map(str,(classes,boundary))),'xnby.replica.'+classname,folder],name)
        result=json.loads(next(line[len(prefix):] for line in raw.splitlines() if line.startswith(prefix)));results[name]=result
    assert results['three']['passedCases']==27 and results['four']['passedChecks']==27 and results['four']['actualTCPExchanges']==4 and results['four']['fourthPortHTTPExchanges']==1
    raw=run([java/'bin/java.exe','-Xmx64m','-cp',os.pathsep.join(map(str,(classes,yaml))),'xnby.replica.ObjectStoreOverlayFixture'],'overlay')
    assert b'OBJECT_STORE_OVERLAY_FIXTURE_CHECKS=18' in raw
    result={'threePortActualChecks':27,'fourPortActualChecks':27,'overlayChecks':18,'fourOwnedTCPExchanges':4,'fourthPortHTTPExchanges':1,'sourceSHA256':{p.name:sha(p) for p in sources},'existingBoundaryJarSHA256':sha(boundary),'originalApplicationOnFixtureClasspath':False,'originalApplicationStarted':False,'sourceDatabaseOrObjectStoreConnected':False,'springObserverCompiledOnly':True,'fullCloneReady':False}
    (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(verify(a.workspace,a.output)))


if __name__=='__main__':main()
