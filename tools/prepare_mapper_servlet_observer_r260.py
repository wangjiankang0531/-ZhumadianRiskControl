from pathlib import Path
import ast,subprocess,sys,zipfile,xml.etree.ElementTree as ET,json
V=Path(__file__).parent;R=Path('D:/Project/Zhumadian')
with zipfile.ZipFile(R/'_g/Application/payload/business/application.jar')as z:
 names=[n for n in z.namelist()if n.startswith('xml/')and n.endswith('.xml')]
 expected=sum(sum(e.tag in {'select','insert','update','delete'}for e in ET.fromstring(z.read(n)))for n in names)
assert len(names)==96 and expected>0
java=(V/'OwnMapperRegistrationObservationR257.java').read_text(encoding='utf-8').replace('R257','R260')
a='  final ConfigurableApplicationContext context=event.getApplicationContext();';assert java.count(a)==1
java=java.replace(a,a+'\n  if(!(context instanceof org.springframework.boot.web.servlet.context.ServletWebServerApplicationContext))return;')
java=java.replace('expected.size()>100','expected.size()=='+str(expected))
a='   }catch(Exception e){throw new IllegalStateException("OWN_MAPPER_OBSERVATION_FAILED",e);}';assert java.count(a)==1
b='   }catch(Exception e){try{Map<String,Object> failed=new LinkedHashMap<>();failed.put("observationSucceeded",false);failed.put("exceptionClass",e.getClass().getName());failed.put("actualApplicationReadySpringFactoryObservation",false);Files.write(root.resolve("own-mapper-observation.json"),new ObjectMapper().writeValueAsBytes(failed),StandardOpenOption.CREATE_NEW);}catch(Exception ignored){System.err.println("OWN_MAPPER_OBSERVATION_REPORT_FAILED");}}'
java=java.replace(a,b)
p=V/'OwnMapperRegistrationObservationR260.java';assert not p.exists();p.write_text(java,encoding='utf-8')
s=(V/'prepare_mapper_observation_suite_r257.py').read_text(encoding='utf-8').replace('r257','r260').replace('R257','R260').replace('r127','r129').replace('r128','r130')
p=V/'prepare_mapper_observation_suite_r260.py';assert not p.exists();ast.parse(s);p.write_text(s,encoding='utf-8')
s=(V/'prepare_mapper_fixture_r257.py').read_text(encoding='utf-8').replace('r257','r260').replace('r127','r129').replace('r128','r130')
p2=V/'prepare_mapper_fixture_r260.py';assert not p2.exists();ast.parse(s);p2.write_text(s,encoding='utf-8')
r=subprocess.run([sys.executable,str(p)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);assert r.returncode==0,r.stderr.decode('utf-8',errors='replace')[-1000:]
print(json.dumps({'originalXMLResources':len(names),'exactOriginalCustomSQLStatements':expected,'servletBusinessContextOnly':True,'observerFailureDoesNotAbortOriginalApplication':True}));print(r.stdout.decode())
