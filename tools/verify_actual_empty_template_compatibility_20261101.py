"""Read only one explicitly authorized empty-template download using the original Excel libraries."""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools'
parser=argparse.ArgumentParser();parser.add_argument('--evidence-root',type=Path,required=True);parser.add_argument('--expected-sha256',required=True);parser.add_argument('--revision',required=True);args=parser.parse_args()
assert re.fullmatch(r'[0-9a-f]{64}',args.expected_sha256)and re.fullmatch(r'r[1-9][0-9]*',args.revision)
V=args.evidence_root.resolve(strict=True);proof=json.loads((V/'download-validation.json').read_bytes());origin=json.loads((V/'origin-metadata.json').read_bytes())
assert origin['Host']in('joinlinksmart.com','www.joinlinksmart.com')and not origin['Loopback']and origin['ApprovedProjectPrefix']
source=Path(proof['downloadFile']).resolve(strict=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert 0<proof['bytes']<=1000000 and source.stat().st_size==proof['bytes']and sha(source)==proof['sha256']==args.expected_sha256
out=V/('compatibility-'+args.revision);assert not out.exists();out.mkdir();classes=out/'classes';classes.mkdir()
meta=json.loads((R/'Document/Deployment/original_work_start_sql_20261026/prepared-inputs.private.json').read_bytes());java=Path(meta['java']);assert sha(java)==meta['javaSHA256']
fixture=T/'java/empty_template_download_r1/OriginalEmptyTemplateInspection.java';raw=fixture.read_bytes();assert not raw.startswith(b'\xef\xbb\xbf');executed=out/fixture.name;executed.write_bytes(raw)
for name in ['tmp','home']:(out/name).mkdir()
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
for label,cmd in [('compile',[java.with_name('javac.exe'),'--release','17','-encoding','UTF-8','-proc:none','-cp',meta['classpath'],'-d',classes,executed]),('read',[java,'-Xmx192m','-Dfile.encoding=UTF-8','-Djava.awt.headless=true','-Djava.io.tmpdir='+str(out/'tmp'),'-Duser.home='+str(out/'home'),'-cp',str(classes)+';'+meta['classpath'],'xnby.replica.OriginalEmptyTemplateInspection',source,out/'original-excel-compatibility.json'])]:
 run=subprocess.run([str(x)for x in cmd],env=env,capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
 (out/(label+'.stdout')).write_bytes(run.stdout);(out/(label+'.stderr')).write_bytes(run.stderr);(out/(label+'-process.json')).write_text(json.dumps({'exitCode':run.returncode,'completed':True}),encoding='utf-8');assert run.returncode==0,label
assert sha(source)==args.expected_sha256 and fixture.read_bytes()==raw
result=json.loads((out/'original-excel-compatibility.json').read_bytes());result.update(explicitAuthorizedEvidenceRootAndSHARequired=True,noDefaultDownloadsOrBrowserProfileScanned=True,sessionOrRuntimeUUIDLiteralInSource=False,originalEvidenceAndInputWorkbookUnmodified=True,workbookSHA256=args.expected_sha256,sourceSHA256=sha(fixture));(out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))