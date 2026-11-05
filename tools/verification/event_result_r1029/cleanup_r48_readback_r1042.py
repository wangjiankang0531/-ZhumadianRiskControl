from pathlib import Path
import hashlib,json,shutil
V=Path(__file__).resolve().parent;T=V/'r48-ftp-readback-r1041'
D=Path('D:/Project/Zhumadian/Document/Deployment/public_test_event_write_results_r48_20261105');S=D/'delivery'
OUT=V/'ftp-readback-cleanup-r1042.json'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists()
proof=json.loads((D/'ftp-upload-readback-r1041.json').read_bytes())
assert proof['passed']and proof['files']==9 and proof['bytes']==25678280
assert T.resolve(strict=True)==T.absolute()and T.is_relative_to(V)and T!=V
assert not T.is_symlink()and not T.lstat().st_file_attributes&0x400
assert {p.name for p in T.iterdir()}=={r['name']for r in proof['rows']}
for row in proof['rows']:
 p=T/row['name'];assert p.is_file()and not p.is_symlink()and not p.lstat().st_file_attributes&0x400
 assert p.stat().st_size==row['bytes']and sha(p)==row['sha256']and sha(S/row['name'])==row['sha256']
before=shutil.disk_usage(V).free
shutil.rmtree(T);assert not T.exists()
after=shutil.disk_usage(V).free
out={'passed':True,'removedOnlyOwnReadbackDuplicate':str(T),'files':9,'logicalBytes':25678280,
 'fixedOriginalNineAndUploadSHAProofRetained':True,'actualTransferAlreadyCompletedAndNoFurtherUIInput':True,
 'observedDriveFreeDeltaOnly':after-before,'physicalExclusiveAttributionClaimed':False,'serverDeleted':False}
OUT.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
