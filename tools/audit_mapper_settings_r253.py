from pathlib import Path
import json,zipfile,re
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';V=Path(__file__).parent
out={'readOnly':True,'runtimeMapperPropertyRows':[],'vendorConfigMapperConstants':[]}
for run in (A/'UserData/OriginalServer/runs').glob('j*'):
 for p in run.rglob('application.properties'):
  if p.stat().st_size>200000:continue
  for line in p.read_text(encoding='ascii',errors='replace').splitlines():
   if re.match(r'(?i)^(mybatis|mybatis-plus)[.\-]mapper[.\-]locations\s*[=:]',line):out['runtimeMapperPropertyRows'].append({'runtime':run.name,'property':line})
for p in (A/'payload/business/lib').glob('cqweh*mybatis*.jar'):
 with zipfile.ZipFile(p)as z:
  for n in z.namelist():
   if not n.endswith('.class'):continue
   b=z.read(n)
   matched=[k for k in ['setMapperLocations','getMapperLocations','classpath*:/xml','classpath*:/mapper','MybatisPlusAutoConfiguration','mybatis-plus']if k.encode()in b]
   if matched:out['vendorConfigMapperConstants'].append({'jar':p.name,'class':n,'matchedKnownConstants':matched})
(V/'mapper-settings-r253.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
