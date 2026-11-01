from pathlib import Path
import importlib.util,subprocess,json,hashlib
V=Path(__file__).parent;A=Path('D:/Project/Zhumadian/_g/Application');C=Path('D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r139/pool-policy-checks');root=C/'binding-cases';classes=C/'binding-classes';classes.mkdir()
s=importlib.util.spec_from_file_location('policy',V/'original_connection_pool_policy_r139_20261101.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
for p in root.glob('*.properties'):
 values=dict(line.split('=',1)for line in p.read_text(encoding='ascii').splitlines());business={'spring.datasource.dynamic.datasource.'+n+'.url':'jdbc:mysql://127.0.0.1:9/own_layout'for n in ['master','tow']}
 spec={'configuration':{'platform':values,'business':business}};budget=m.connection_pool_budget(spec);rows=[r for r in budget['datasources']if r['side']=='platform'];_,implicit=m._pool_layout(values,'platform')
 expected={'generated':str(implicit is not None).lower(),'count':str(len(rows))}
 for r in rows:
  expected.update({r['name']+'.'+k:str(r[v])for k,v in [('maximum','hikariMaximum'),('minimum','hikariMinimumIdle'),('timeout','hikariConnectionTimeoutMillis')]})
 p.with_name(p.stem+'.expected.properties').write_text(''.join(k+'='+v+'\n'for k,v in expected.items()),encoding='ascii')
jar=A/'payload/platform/original-platform.jar';jdk=A/'runtime/jdk17/bin';source=V/'java/OwnOriginalPoolLayoutBinding.java'
assert not(A.parent/'user-manual-protected.json').exists() and json.loads((A.parent/'own-fixture.json').read_bytes())['ownedSyntheticFixtureOnly']
assert hashlib.sha256(jar.read_bytes()).hexdigest()=='294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8'
cmd=[str(jdk/'javac.exe'),'-J-Xmx128m','--release','17','-proc:none','-encoding','UTF-8','-cp',str(jar),'-d',str(classes),str(source)]
r=subprocess.run(cmd,capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
if r.returncode:raise RuntimeError('COMPILE_FAILED:'+r.stderr.decode(errors='replace')[:2000])
r=subprocess.run([str(jdk/'java.exe'),'-Xmx192m','-cp',str(classes)+';'+str(jar),'OwnOriginalPoolLayoutBinding',str(jar),str(root),str(C/'actual-original-binding.json')],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
(C/'binding-process-result.json').write_text(json.dumps({'exitCode':r.returncode,'sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest()}),encoding='utf-8')
if r.returncode:raise RuntimeError('ORIGINAL_BINDING_FAILED:'+r.stderr.decode(errors='replace')[-3500:])
print((C/'actual-original-binding.json').read_text(encoding='utf-8'))
