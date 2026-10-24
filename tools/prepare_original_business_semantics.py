"""Prepare, but do not apply, original business codes and timezone with an owned API base."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
from audit_original_business_config import audit,require,sha

def prepare(java_home,yaml_jar,yaml_pin,source,source_pin,candidate,platform_base,output):
 java_home,yaml_jar,source,candidate,output=map(Path,(java_home,yaml_jar,source,candidate,output));require(not output.exists(),'FRESH_OUTPUT_REQUIRED');output.mkdir()
 before=audit(java_home,yaml_jar,yaml_pin,source,source_pin,candidate,output/'before')
 classes=output/'before/classes';cp=os.pathsep.join(map(str,(classes,yaml_jar)));sources=[Path(__file__).parent/'java'/n for n in ('OriginalBusinessSemantics.java','BusinessSemanticsFixture.java')]
 env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
 def run(command,name):
  result=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW);(output/(name+'.private.log')).write_bytes(result.stdout+result.stderr);require(result.returncode==0,'SEMANTICS_'+name.upper()+'_FAILED');return result.stdout
 run([java_home/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-cp',cp,'-d',classes,*sources],'compile')
 raw=run([java_home/'bin/java.exe','-Xmx64m','-cp',cp,'xnby.replica.BusinessSemanticsFixture'],'fixture');require(b'BUSINESS_SEMANTICS_FIXTURE_CHECKS=6' in raw,'SEMANTICS_FIXTURE_CHECK_COUNT')
 properties=output/'application.private.properties'
 run([java_home/'bin/java.exe','-Xmx64m','-cp',cp,'xnby.replica.OriginalBusinessSemantics',source,source_pin,candidate,platform_base,properties],'prepare')
 after=audit(java_home,yaml_jar,yaml_pin,source,source_pin,properties,output/'after')
 require(before['originalConfigSHA256']==after['originalConfigSHA256']==source_pin and sha(candidate)==before['candidateConfigSHA256'],'INPUT_CHANGED')
 summary={line.split('=',1)[0]:line.split('=',1)[1] for line in (output/'semantics-summary.properties').read_text('ascii').splitlines() if line and not line.startswith(('#','!'))}
 receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'originalConfigSHA256':source_pin,'inputCandidateSHA256':before['candidateConfigSHA256'],'preparedCandidateSHA256':sha(properties),'semanticSourceSHA256':{p.name:sha(p) for p in sources},'auditFixtureChecks':7,'semanticFixtureChecks':6,'originalSemanticKeysCopied':int(summary['originalSemanticKeysCopied']),'internalApiBasesRemapped':2,'jdbcTimezonesRestored':2,'missingNonSensitiveBefore':before['nonSensitiveMissing'],'missingNonSensitiveAfter':after['nonSensitiveMissing'],'equalNonSensitiveBefore':before['nonSensitiveEqual'],'equalNonSensitiveAfter':after['nonSensitiveEqual'],'originalCredentialsCopied':False,'appliedToRunningCandidate':False,'applicationStarted':False,'sourceDatabaseConnected':False,'remainingIntegrationsVerified':False,'fullCloneReady':False}
 (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');return receipt
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('java-home','yaml-jar','yaml-sha256','source-config','source-sha256','candidate-properties','platform-base','output'):p.add_argument('--'+key,required=True)
 a=p.parse_args();print(json.dumps(prepare(a.java_home,a.yaml_jar,a.yaml_sha256,a.source_config,a.source_sha256,a.candidate_properties,a.platform_base,a.output)))
if __name__=='__main__':main()
