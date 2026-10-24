"""Compare pinned original Nacos config key coverage without writing original values."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

def require(value,code):
 if not value:raise ValueError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audit(java_home,yaml_jar,yaml_pin,source,source_pin,candidate,output):
 java_home,yaml_jar,source,candidate,output=map(Path,(java_home,yaml_jar,source,candidate,output))
 require(not output.exists(),'FRESH_OUTPUT_REQUIRED')
 for pin in (yaml_pin,source_pin):require(re.fullmatch('[0-9a-f]{64}',pin),'EXPLICIT_SHA256_REQUIRED')
 for path,limit in ((source,65536),(candidate,256*1024),(yaml_jar,4*1024**2)):
  stat=path.lstat();require(path.is_file() and not path.is_symlink() and not getattr(stat,'st_file_attributes',0)&0x400 and stat.st_size<=limit,'REGULAR_BOUNDED_INPUT_REQUIRED')
 require(sha(source)==source_pin and sha(yaml_jar)==yaml_pin,'SOURCE_OR_DEPENDENCY_PIN_MISMATCH')
 require((java_home/'bin/java.exe').is_file() and (java_home/'bin/javac.exe').is_file(),'EXPLICIT_EXISTING_JDK_REQUIRED')
 output.mkdir();classes=output/'classes';classes.mkdir();sources=[Path(__file__).parent/'java'/n for n in ('OriginalBusinessConfigInventory.java','BusinessConfigInventoryFixture.java')]
 env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')};flags=subprocess.CREATE_NO_WINDOW
 def run(command,name):
  result=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=30,creationflags=flags)
  (output/(name+'.private.log')).write_bytes(result.stdout+result.stderr);require(result.returncode==0,'CONFIG_INVENTORY_'+name.upper()+'_FAILED');return result.stdout
 run([java_home/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-cp',yaml_jar,'-d',classes,*sources],'compile')
 cp=os.pathsep.join(map(str,(classes,yaml_jar)))
 fixture=run([java_home/'bin/java.exe','-Xmx64m','-cp',cp,'xnby.replica.BusinessConfigInventoryFixture'],'fixture');require(b'CONFIG_INVENTORY_FIXTURE_CHECKS=7' in fixture,'FIXTURE_CHECK_COUNT')
 report=output/'key-coverage.properties'
 run([java_home/'bin/java.exe','-Xmx64m','-cp',cp,'xnby.replica.OriginalBusinessConfigInventory',source,source_pin,candidate,report],'audit')
 require(sha(source)==source_pin and sha(yaml_jar)==yaml_pin,'INPUT_CHANGED')
 values={line.split('=',1)[0]:line.split('=',1)[1] for line in report.read_text('ascii').splitlines() if line and not line.startswith(('#','!'))}
 receipt={'recordedAt':datetime.datetime.now().astimezone().isoformat(),'originalConfigSHA256':source_pin,'candidateConfigSHA256':sha(candidate),'yamlJarSHA256':yaml_pin,'sourceSHA256':{p.name:sha(p) for p in sources},'fixtureChecks':7,'sourceProperties':int(values['sourceProperties']),'nonSensitiveMissing':int(values['nonSensitiveMissing']),'nonSensitiveDifferent':int(values['nonSensitiveDifferent']),'nonSensitiveEqual':int(values['nonSensitiveEqual']),'sensitiveRedacted':int(values['sensitiveRedacted']),'originalJdbcTimezones':{side:values['originalJdbcTimezone.'+side] for side in ('master','tow')},'reportSHA256':sha(report),'originalValuesWritten':False,'sourceDatabaseConnected':False,'applicationStarted':False,'fullCloneReady':False}
 (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');return receipt
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ('java-home','yaml-jar','yaml-sha256','source-config','source-sha256','candidate-properties','output'):p.add_argument('--'+key,required=True)
 a=p.parse_args();print(json.dumps(audit(a.java_home,a.yaml_jar,a.yaml_sha256,a.source_config,a.source_sha256,a.candidate_properties,a.output)))
if __name__=='__main__':main()
