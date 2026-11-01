from pathlib import Path
import hashlib,json,zipfile,xml.etree.ElementTree as ET
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';D=R/'Document/Deployment/emergency_duty_native_r135_20261101';assert not(A.parent/'user-manual-protected.json').exists();jar=A/'payload/business/application.jar';rows=[]
with zipfile.ZipFile(jar)as z:
    for info in z.infolist():
        if not info.filename.startswith('xml/')or not info.filename.endswith('.xml'):continue
        assert info.file_size<1024**2;raw=z.read(info);root=ET.fromstring(raw);namespace=root.attrib.get('namespace','')
        if namespace and any(name in namespace for name in ['dutyPersonnel','dutySchedule','dutyLog']):
            rows.append({'resource':info.filename,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'namespace':namespace,'statementIds':[child.attrib['id']for child in root if child.tag in ['select','insert','update','delete']],'hasDefaultMapperPathCopy':(A/'payload/business/run-template/classes/mapper'/Path(info.filename).name).exists()})
proof={'schema':'xnby.r135.original-duty-mapper-resource-audit.v1','retainedOriginalJarSHA256':hashlib.sha256(jar.read_bytes()).hexdigest(),'dutyMapperResources':rows,'SQLBodiesOrBusinessRowsOrConfigurationExported':False,'actualMappingLoadedOrSQLCallPassedNotClaimedByThisAudit':True,'programsOrPublicChanged':False};(D/'original-duty-mapper-resources.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
