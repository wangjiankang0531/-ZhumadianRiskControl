from pathlib import Path
import datetime,hashlib,json
V=Path(__file__).resolve().parent
D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_event_write_results_r48_20261105')
S=D/'delivery';T=V/'r48-ftp-readback-r1041';OUT=D/'ftp-upload-readback-r1041.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists()
assert sha(S/'delivery-manifest.json')=='ad07cf7a88b15ec93c003a52ac34a652297ab2c18dbae15985f975bf56a56f1a'
expected={p.name:p for p in S.iterdir()if p.is_file()}
assert len(expected)==9 and {p.name for p in T.iterdir()}==set(expected)
rows=[]
for name,source in sorted(expected.items()):
 target=T/name;assert not target.is_symlink()and not target.lstat().st_file_attributes&0x400
 assert target.stat().st_size==source.stat().st_size and sha(target)==sha(source),name
 rows.append({'name':name,'bytes':target.stat().st_size,'sha256':sha(target),'matched':True})
out={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'files':len(rows),'bytes':sum(x['bytes']for x in rows),
 'manifestSHA256':sha(S/'delivery-manifest.json'),'targetFTP':'/Zhumadian/Zhumadian_Event_Write_Results_20261105_R48/',
 'transportMode':'binary','allNineActuallyDownloadedAndCompared':True,'rows':rows,
 'serverPreflightOrDeploymentPerformed':False,'serverVersionsDeleted':False,'desktopReturnedForManualCMDNext':True}
OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in out.items()if k!='rows'}))
