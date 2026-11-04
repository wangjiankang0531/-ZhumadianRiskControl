"""Continue with the same already-prepared home metadata, strictly read-only.
The R910 browser checked the async menu before its response completed.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,os,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');A=R/'Application';G=R/'_g/Application'
OLD=V/'home_full_r909';H=V/'home_full_r912';D=R/'Document/Deployment/home_transfer_full_candidate_r905_20261104'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not H.exists() and not(R/'work/hf912').exists()
prior=J(R/'work/hf910/verified-home-transfer-r910.json')
assert not prior['passed'] and prior['codeRestored'] and prior['privateConfigurationUnchanged'] and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and set(t['exitCodes'].values())=={0}for t in prior['terminals'])
journal=R/'work/original-manager-full-lifecycle-r609/home-transfer-r910/home-navigation-journal.private.properties'
result=R/'work/original-manager-full-lifecycle-r609/home-transfer-r910/home-navigation-result.private.properties'
props=lambda p:dict(s.split('=',1)for s in p.read_text('ascii').splitlines()if'='in s and not s.startswith('#'))
assert props(journal)['phase']=='readback-verified'and props(result)['insertedMetadataRows']=='33'and props(result)['homeSystemBefore']=='0'
pin=sha(journal);H.mkdir();(H/'classes').mkdir()
java=(V/'OwnHomeNavigationFixtureR909.java').read_text('utf8').replace('public final class OwnHomeNavigationFixtureR909','public final class OwnHomeNavigationReadbackR912')
guard='need(out.getParent().equals(journal.getParent())&&!Files.exists(out)&&!Files.exists(journal),"UNISSUED_OWN_METADATA_ATTEMPT");'
assert java.count(guard)==1
java=java.replace(guard,'need(out.toString().replace(\'\\\\\',\'/\').equals("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/home-transfer-r912/home-navigation-readback.private.properties")&&!Files.exists(out)&&Files.isRegularFile(journal),"UNISSUED_OWN_READBACK_ONLY");need(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(journal))).equals("'+pin+'"),"PINNED_PREPARED_HOME_JOURNAL_REQUIRED");')
marker='   c.setAutoCommit(false);Map<String,String>before=new TreeMap<>();int missing=0;int homeBefore=0;'
assert java.count(marker)==1
java=java[:java.index(marker)]+'''   c.setReadOnly(true);c.setAutoCommit(false);
   int verified=0;
   try(PreparedStatement p=c.prepareStatement("SELECT f_id FROM jnpf.base_system WHERE f_en_code='home'");ResultSet r=p.executeQuery()){need(r.next()&&id(99000).equals(r.getString(1))&&!r.next(),"EXACT_PREVIOUS_HOME_SYSTEM");}
   for(var table:rows.entrySet())for(var row:table.getValue().values()){need(existsExact(c,table.getKey(),row),"PREVIOUS_HOME_METADATA_CHANGED_NO_RESEED");verified++;}
   need(verified==33,"EXACT_PREVIOUS_33_ROWS");c.commit();
   result.setProperty("persistentWritesIssued","false");result.setProperty("exactPreviouslyPreparedMetadataRowsMatched","true");result.setProperty("originalDatabaseIdentityMatched","true");result.setProperty("verifiedMetadataRows","33");result.setProperty("phase","readback-verified");save(out,result);
   System.out.println("PREVIOUS_OWN_HOME_METADATA_READ_ONLY_MATCHED");
  }finally{secret=null;}
 }
}
'''
assert 'INSERT INTO'not in java and 'UPDATE jnpf'not in java and 'DELETE FROM'not in java
source=H/'OwnHomeNavigationReadbackR912.java';source.write_text(java,encoding='utf8')
for name in ['home_transfer_health_r906.py','home_transfer_gateway_r906.py','home_transfer_probe_r906.py','run_home_transfer_full_r906.py','verify_home_transfer_browser_r906.mjs']:
 s=(OLD/name).read_text('utf8').replace('home-transfer-source-pins-r910.json','home-transfer-source-pins-r912.json')
 s=s.replace("P=O/'home-transfer-r910';Z=R/'work/hf910'","P=O/'home-transfer-r912';Z=R/'work/hf912'")
 s=s.replace('original-manager-full-lifecycle-r609/home-transfer-r910','original-manager-full-lifecycle-r609/home-transfer-r912')
 s=s.replace("OUT=R/'work/home-browser-r910'","OUT=R/'work/home-browser-r912'").replace('D:/Project/Zhumadian/work/home-browser-r910','D:/Project/Zhumadian/work/home-browser-r912')
 s=s.replace("O=Path('D:/Project/Zhumadian/work/hf910')","O=Path('D:/Project/Zhumadian/work/hf912')")
 s=s.replace("prior=J(R/'work/hf906/verified-home-transfer-r906.json')","prior=J(R/'work/hf910/verified-home-transfer-r910.json')")
 s=s.replace('verified-home-transfer-r910.json','verified-home-transfer-r912.json') if name!='run_home_transfer_full_r906.py'else s
 if name=='run_home_transfer_full_r906.py':
  # Only output names change; the prior proof remains the actual failed R910.
  s=s.replace("save('verified-home-transfer-r910.json',proof)","save('verified-home-transfer-r912.json',proof)")
 s=s.replace('home-transfer-full-result-r910.json','home-transfer-full-result-r912.json')
 if name=='home_transfer_probe_r906.py':
  s=s.replace('OwnHomeNavigationFixtureR909','OwnHomeNavigationReadbackR912')
  a="journal=P/'home-navigation-journal.private.properties';metadata=P/'home-navigation-result.private.properties'"
  b="journal=R/'work/original-manager-full-lifecycle-r609/home-transfer-r910/home-navigation-journal.private.properties';metadata=P/'home-navigation-readback.private.properties'"
  assert s.count(a)==1;s=s.replace(a,b)
  a='assert not journal.exists()and not metadata.exists()';assert s.count(a)==1
  s=s.replace(a,"assert hashlib.sha256(journal.read_bytes()).hexdigest()=="+repr(pin)+"and not metadata.exists()")
  s=s.replace("checked['allOtherMetadataDigestsMatched']=='true'","checked['exactPreviouslyPreparedMetadataRowsMatched']=='true'and checked['persistentWritesIssued']=='false'")
 if name.endswith('.mjs'):
  old=" if(!await evaluate('document.querySelectorAll(\".menu-item\").length===8'))throw Error('EIGHT_ORIGINAL_HOME_NAVIGATION_ENTRIES_REQUIRED');"
  assert s.count(old)==1;s=s.replace(old," await until(()=>evaluate('document.querySelectorAll(\".menu-item\").length===8'));\n cases.push({case:'original-home-async-menu-response-renders-eight-owned-entries',passed:true});")
  # Keep original authentication guard unchanged; record bounded response shape
  # to diagnose any further contract mismatch without retaining user data.
  marker='row.businessCode=body.code;';assert s.count(marker)==1
  s=s.replace(marker,marker+"if(row.path.endsWith('/oauth/CurrentUser')){row.userInfoPresent=!!body.data?.userInfo;row.menuListIsArray=Array.isArray(body.data?.menuList);}")
 (H/name).write_text(s,encoding='utf8')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
jobs=load('home_read_jobs_r912',G/'tools/original_server_windows_job.py');policy=load('home_read_budget_r912',A/'tools/bounded_build_job_r671.py')
assert sha(G/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
snap=policy.memory_snapshot();assert min(snap['availablePhysicalBytes'],snap['availableCommitBytes'])>1024**3
with(H/'fixture-compile.private.log').open('xb')as log:
 p=subprocess.Popen([str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(source)],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 job=jobs.OwnedWindowsJob(p);cap=policy.BoundedBuildJob(job,512*1024**2);p.wait()
 while job.active_processes():time.sleep(.1)
 terminal={'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':cap.metrics()};job.close()
assert p.returncode==0,'READ_ONLY_METADATA_HELPER_COMPILE_FAILED'
compiled=H/'classes/OwnHomeNavigationReadbackR912.class'
(H/'fixture-compile-proof.json').write_text(json.dumps({'passed':True,'sourceSHA256':sha(source),'classSHA256':sha(compiled),'terminal':terminal},indent=2)+'\n',encoding='utf8')
files=[*H.glob('*.py'),H/'verify_home_transfer_browser_r906.mjs',source,compiled,H/'fixture-compile-proof.json']
for p in H.glob('*.py'):ast.parse(p.read_bytes(),filename=p.name)
assert subprocess.run(['node','--check',str(H/'verify_home_transfer_browser_r906.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
pins={'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':{str(p):sha(p)for p in files},'onlyReadOnlyMetadataReadbackAllowed':True,'previousHomeJournalSHA256':pin,'normalOriginalSDKStillPending':True}
(H/'home-transfer-source-pins-r912.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
print(json.dumps({'prepared':True,'readOnlyHelperCompiled':True,'seedWillNotBeRepeated':True,'classJobExitCode':terminal['exitCode']}))
