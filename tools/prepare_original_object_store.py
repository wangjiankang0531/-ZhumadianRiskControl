"""Prepare an owned MinIO overlay retaining only the pinned original bucket identity."""
import argparse,datetime,hashlib,json,os,re,subprocess
from pathlib import Path


def prepare(java,yaml,yaml_pin,source,source_pin,candidate,connection,output):
    java,yaml,source,candidate,connection,output=map(Path,(java,yaml,source,candidate,connection,output))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if output.exists() or not re.fullmatch('[a-f0-9]{64}',source_pin) or sha(source)!=source_pin or source.stat().st_size>65536:raise ValueError('FRESH_OVERLAY_AND_PINNED_SOURCE_REQUIRED')
    if sha(yaml)!=yaml_pin or yaml_pin!='1467931448a0817696ae2805b7b8b20bfb082652bf9c4efaed528930dc49389b':raise ValueError('EXISTING_YAML_PIN_MISMATCH')
    before=sha(candidate);connection_pin=sha(connection)
    if candidate.stat().st_size>256*1024 or connection.stat().st_size>4096:raise ValueError('BOUNDED_PRIVATE_INPUTS_REQUIRED')
    output.mkdir();classes=output/'classes';classes.mkdir();here=Path(__file__).resolve().parent
    sources=[here/'java'/name for name in ('OriginalBusinessConfigInventory.java','OriginalBusinessObjectStoreOverlay.java','ObjectStoreOverlayFixture.java')]
    env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
    def run(command,name):
        value=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=30,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));(output/(name+'.private.log')).write_bytes(value.stdout+value.stderr)
        if value.returncode!=0:raise RuntimeError('OWN_OBJECT_STORE_'+name.upper()+'_FAILED')
        return value.stdout
    run([java/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-cp',yaml,'-d',classes,*sources],'compile')
    cp=os.pathsep.join(map(str,(classes,yaml)))
    if b'OBJECT_STORE_OVERLAY_FIXTURE_CHECKS=18' not in run([java/'bin/java.exe','-Xmx64m','-cp',cp,'xnby.replica.ObjectStoreOverlayFixture'],'fixture'):raise RuntimeError('OBJECT_STORE_OVERLAY_FIXTURE_INCOMPLETE')
    target=output/'application.private.properties'
    run([java/'bin/java.exe','-Xmx64m','-cp',cp,'xnby.replica.OriginalBusinessObjectStoreOverlay',source,source_pin,candidate,connection,target],'prepare')
    if sha(source)!=source_pin or sha(candidate)!=before or sha(connection)!=connection_pin:raise ValueError('OBJECT_STORE_OVERLAY_INPUT_CHANGED')
    result={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'originalConfigSHA256':source_pin,'inputCandidateSHA256':before,'privateConnectionSHA256':connection_pin,'preparedConfigSHA256':sha(target),'fixtureChecks':18,'originalBucketIdentityCopied':True,'originalCredentialsCopied':False,'ownCredentialsOnly':True,'applicationStarted':False,'fullCloneReady':False}
    (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('java-home','yaml-jar','yaml-sha256','source-config','source-sha256','candidate-properties','private-connection','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(json.dumps(prepare(a.java_home,a.yaml_jar,a.yaml_sha256,a.source_config,a.source_sha256,a.candidate_properties,a.private_connection,a.output)))


if __name__=='__main__':main()
