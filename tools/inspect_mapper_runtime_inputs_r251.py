from pathlib import Path
import json,zipfile,hashlib,re
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';V=Path(__file__).parent
out={'readOnly':True,'runtimeMapperFiles':[],'mapperImplementationClasses':[],'originalConfigurationClassCandidates':[]}
for p in (A/'payload/business/run-template/classes').rglob('*.xml'):
 out['runtimeMapperFiles'].append({'path':p.relative_to(A).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for p in (A/'payload/business/lib').glob('*mybatis*.jar'):
 with zipfile.ZipFile(p)as z:
  out['mapperImplementationClasses'] +=[{'jar':p.name,'class':n}for n in z.namelist()if n.endswith(('MybatisXMLMapperBuilder.class','MybatisConfiguration.class','MybatisSqlSessionFactoryBuilder.class','XMLMapperBuilder.class','MybatisPlusProperties.class'))]
with zipfile.ZipFile(A/'payload/business/application.jar')as z:
 for n in z.namelist():
  if n.endswith('.class')and any(w in n.lower()for w in ['config','application']):
   b=z.read(n)
   if any(w in b for w in [b'setMapperLocations',b'mapperLocations',b'classpath*:/xml',b'mapper-locations']):out['originalConfigurationClassCandidates'].append(n)
  if n.endswith(('.properties','.yml','.yaml')):
   out.setdefault('configurationResourceNames',[]).append(n)
(V/'mapper-runtime-inputs-r251.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
