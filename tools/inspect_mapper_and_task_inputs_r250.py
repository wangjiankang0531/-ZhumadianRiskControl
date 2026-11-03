from pathlib import Path
import zipfile,re,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
rows=[]
with zipfile.ZipFile(R/'_g/Application/payload/business/application.jar')as z:
 for n in z.namelist():
  if n.endswith(('.yml','.yaml','.properties')):
   for line in z.read(n).decode('utf-8',errors='replace').splitlines():
    if re.search('mapper[-.]?[Ll]ocations',line):rows.append({'resource':n,'mapperProperty':line.strip()})
inventory=json.loads((R/'Document/Deployment/original_plan_exercise_verified_candidate_r249_20261103/original-jar-mapper-resource-inventory.json').read_bytes())['mappers']
print(json.dumps({'jarMapperConfig':rows,'originalMapperXMLCount':len(inventory),
 'originalXMLDirectoryCount':sum(n['resource'].startswith('xml/')for n in inventory),
 'planMapper':[n for n in inventory if n['resource'].endswith('EmergencyPlanMapper.xml')]}))
for name,start,end in [('verify_native_parallel_gateway_r218_20261103.mjs',70,88),('verify_full_controller_parallel_gateway_r218_20261103.py',0,40)]:
 lines=(T/name).read_text(encoding='utf-8').splitlines();print(name)
 for i in range(start,min(end,len(lines))):print(str(i+1)+':'+lines[i][:5000])
