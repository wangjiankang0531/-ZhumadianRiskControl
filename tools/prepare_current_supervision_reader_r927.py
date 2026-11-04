"""Replace the obsolete test reader's output pin with one exact new attempt.
No SQL write logic or broader path permission is added; product bytes unchanged.
"""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys,time
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian');G=R/'_g/Application';A=R/'Application'
D=R/'Document/Deployment/supervision_current_full_r920_20261104';OLD=V/'supervision_full_r925';H=V/'supervision_full_r927'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not H.exists()and not(R/'work/sv927').exists()
prior=J(R/'work/sv925/verified-current-supervision-r925.json');assert not prior['passed']and prior['codeRestored']and prior['privateConfigurationUnchanged']and prior['originalCurrentPointerRestored']
assert all(t['controllerExitCode']==0 and t['actualJobDescendantsZero']and all(v==0 for v in t['exitCodes'].values())for t in prior['terminals'])
H.mkdir();(H/'classes').mkdir()
for p in OLD.glob('*'):
 if p.suffix not in ['.py','.mjs']:continue
 s=p.read_text('utf8').replace('current-supervision-r925','current-supervision-r927').replace('current-supervision-browser-r925','current-supervision-browser-r927').replace('work/sv925','work/sv927').replace("R/'work/sv925'","R/'work/sv927'").replace('current-supervision-source-pins-r925.json','current-supervision-source-pins-r927.json').replace('verified-current-supervision-r925.json','verified-current-supervision-r927.json').replace('current-supervision-full-result-r925.json','current-supervision-full-result-r927.json')
 if p.name=='home_transfer_probe_r906.py':s=s.replace('OwnHomeNavigationReadbackR912','OwnHomeNavigationReadbackR927')
 if p.name=='run_home_transfer_full_r906.py':
  marker="assert J(D/'conditional-pointer-recovery-r923.json')['passedAsScopedRecovery']"
  assert s.count(marker)==1;s=s.replace(marker,marker+"\nlatest=J(R/'work/sv925/verified-current-supervision-r925.json');assert latest['codeRestored']and latest['privateConfigurationUnchanged']and latest['originalCurrentPointerRestored']")
 if p.suffix=='.py':ast.parse(s)
 (H/p.name).write_text(s,encoding='utf8')
java=(V/'home_full_r912/OwnHomeNavigationReadbackR912.java').read_text('utf8')
java=java.replace('public final class OwnHomeNavigationReadbackR912','public final class OwnHomeNavigationReadbackR927')
oldpath='D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/home-transfer-r912/home-navigation-readback.private.properties'
newpath='D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/current-supervision-r927/home-navigation-readback.private.properties'
assert java.count(oldpath)==1;java=java.replace(oldpath,newpath)
assert 'INSERT INTO'not in java and 'UPDATE jnpf'not in java and 'DELETE FROM'not in java
source=H/'OwnHomeNavigationReadbackR927.java';source.write_text(java,encoding='utf8')
def load(n,p):s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assert sha(G/'tools/original_server_windows_job.py')=='e32f8dfa05b822534a75314419bd83d093ed5bd58255690798736366d20c8a22'
jobs=load('reader_jobs_r927',G/'tools/original_server_windows_job.py');budget=load('reader_budget_r927',A/'tools/bounded_build_job_r671.py')
assert min(budget.memory_snapshot()[k]for k in ['availablePhysicalBytes','availableCommitBytes'])>1024**3
terminals=[]
def execute(name,args):
 with(H/(name+'.private.log')).open('xb')as f:
  p=subprocess.Popen(args,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
  job=jobs.OwnedWindowsJob(p);cap=budget.BoundedBuildJob(job,512*1024**2);p.wait()
  while job.active_processes():time.sleep(.1)
  terminal={'phase':name,'exitCode':p.returncode,'actualJobDescendantsZero':True,'forceTerminationUsed':False,'budget':cap.metrics()};job.close();terminals.append(terminal)
 return p.returncode
assert execute('compile',[str(G/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(H/'classes'),str(source)])==0
compiled=H/'classes/OwnHomeNavigationReadbackR927.class'
for i,out in enumerate([oldpath,newpath.replace('current-supervision-r927','foreign')]):
 args=[str(G/'runtime/jdk17/bin/java.exe'),'-Xmx64m','-cp',str(H/'classes'),'OwnHomeNavigationReadbackR927','12345','00000000-0000-0000-0000-000000000000',str(G/'UserData/OriginalServer/database/data'),str(R/'work/original-manager-full-lifecycle-r609/home-transfer-r910/home-navigation-journal.private.properties'),out]
 assert execute('refuse-path-'+str(i),args)==1
 assert 'UNISSUED_OWN_READBACK_ONLY'in(H/('refuse-path-'+str(i)+'.private.log')).read_text('utf8')
(H/'fixture-compile-proof.json').write_text(json.dumps({'passed':True,'sourceSHA256':sha(source),'classSHA256':sha(compiled),'terminal':terminals[0],'oldAndForeignOutputRejectedBeforeSecretOrDatabase':True,'terminals':terminals},indent=2)+'\n',encoding='utf8')
assert subprocess.run(['node','--check',str(H/'verify_home_transfer_browser_r906.mjs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW).returncode==0
pins={str(p):sha(p)for p in H.rglob('*')if p.is_file()and not p.name.endswith('.private.log')};pins.update({str(A/'tools'/n):sha(A/'tools'/n)for n in ['owned_candidate_code_transaction_r543.py','owned_run_pointer_r717.py','owned_run_terminal_r709.py','bounded_build_job_r671.py']})
(H/'current-supervision-source-pins-r927.json').write_text(json.dumps({'candidatePlanSHA256':sha(D/'full-source-and-restore-plan.private.json'),'files':pins},indent=2)+'\n',encoding='utf8')
proof={'prepared':True,'candidateProductBytesUnchanged':True,'exactReadOnlyReaderOutput':newpath,'same33MetadataRowsAndOriginalJournalPinRequired':True,'noSQLWritesAdded':True,
 'javaCompileExitCode':0,'oldAndForeignOutputRejectedBeforeSecretOrDatabase':True,'allCompilerAndNegativeProbeJobsNormallyExited':True,'sourcePins':len(pins),'fullAppStillToRun':True}
(D/'prepared-reader-r927.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps(proof))
