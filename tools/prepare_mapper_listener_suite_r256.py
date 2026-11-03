from pathlib import Path
import ast,subprocess,sys,json
V=Path(__file__).parent
java=(V/'OwnMapperRegistrationObservationR255.java').read_text(encoding='utf-8').replace('R255','R256')
java=java.replace('implements ApplicationContextInitializer<ConfigurableApplicationContext>','implements ApplicationListener<ApplicationReadyEvent>')
java=java.replace(' public void initialize(final ConfigurableApplicationContext context){',' public void onApplicationEvent(final ApplicationReadyEvent event){\n  final ConfigurableApplicationContext context=event.getApplicationContext();')
a='  context.addApplicationListener(event->{\n   if(!(event instanceof ApplicationReadyEvent)||((ApplicationReadyEvent)event).getApplicationContext()!=context)return;\n';assert java.count(a)==1;java=java.replace(a,'')
assert java.count('  });\n')==1;java=java.replace('  });\n','')
p=V/'OwnMapperRegistrationObservationR256.java';assert not p.exists();p.write_text(java,encoding='utf-8')
s=(V/'prepare_mapper_observation_suite_r255.py').read_text(encoding='utf-8').replace('r255','r256').replace('R255','R256').replace('r123','r125').replace('r124','r126')
s=s.replace('import ast,hashlib,json,subprocess,os','import ast,hashlib,json,subprocess,os,zipfile')
a="compiled=list(classes.rglob('*.class'));assert len(compiled)==1"
b=a+"\nwith zipfile.ZipFile(D/'own-mapper-observation-r256.jar','w',compression=zipfile.ZIP_DEFLATED)as archive:\n archive.write(compiled[0],compiled[0].relative_to(classes).as_posix());archive.writestr('META-INF/spring.factories','org.springframework.context.ApplicationListener=xnby.own.OwnMapperRegistrationObservationR256\\n')"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace("classrel='payload/business/run-template/classes/xnby/own/OwnMapperRegistrationObservationR256.class'","classrel='payload/business/run-template/own-mapper-observation-r256.jar'")
a="cfg=J(A/'private/server-configuration.json');business=cfg['configuration']['business'];key='context.initializer.classes';initializer='xnby.own.OwnMapperRegistrationObservationR256';old=business.get(key,'');assert initializer not in old\n+ business[key]=','.join([x for x in old.split(',')if x]+[initializer])".replace('\n+ ','\n ')
b="cfg=J(A/'private/server-configuration.json');business=cfg['configuration']['business'];arguments=cfg['businessArguments'];indexes=[i for i,x in enumerate(arguments)if 'application.jar' in x and ';' in x];assert len(indexes)==1\n cpindex=indexes[0];newjar='${application}/payload/business/run-template/own-mapper-observation-r256.jar';assert newjar not in arguments[cpindex];arguments[cpindex]+=';'+newjar"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace("classrel:(D/'classes/xnby/own/OwnMapperRegistrationObservationR256.class').read_bytes()","classrel:(D/'own-mapper-observation-r256.jar').read_bytes()")
s=s.replace("'onlyOwnSyntheticConfigurationAndObserverClass':True","'onlyOwnSyntheticClasspathAndListenerJar':True")
s=s.replace("'onlyOwnObserverClassRemoved':True","'onlyOwnListenerJarRemoved':True")
p=V/'prepare_mapper_observation_suite_r256.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
s=(V/'prepare_mapper_fixture_r255.py').read_text(encoding='utf-8').replace('r255','r256').replace('r123','r125').replace('r124','r126')
p2=V/'prepare_mapper_fixture_r256.py';assert not p2.exists();ast.parse(s);p2.write_text(s,encoding='utf-8')
r=subprocess.run([sys.executable,str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf-8',errors='replace')[-1000:];print(r.stdout.decode())
