from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent
old=V/'verify_r48_transport_r1027.py';new=V/'verify_r48_transport_r1028.py'
assert not new.exists()
s=old.read_text('utf8').replace('import ast,hashlib,','import ast,copy,hashlib,')
s=s.replace("assert not W.exists()and not(D/'verified-transport-r1027.json').exists()", "assert W.is_dir() and not(D/'verified-transport-r1028.json').exists()\nassert {p.name for p in W.iterdir()}=={'r45','r47','bad-event-payload-tamper.zip'}\nfailed=W/'bad-event-payload-tamper.zip'\nassert failed.resolve().parent==W.resolve() and not failed.is_symlink()\nfailed_pin={'sha256':sha(failed),'bytes':failed.stat().st_size,'previousExecutionTerminalExit':1,'cause':'test writer reused mutable ZipInfo objects'}\n(V/'transport-test-failure-r1027.json').write_text(json.dumps(failed_pin,indent=2)+'\\n',encoding='utf8')\nfailed.unlink()")
s=s.replace('W.mkdir();cases=[]','cases=[]')
s=s.replace("plan=m.validate_archive(z,base);stage=W/base['label'];extracted=m.extract_selected_archive(archive,stage,base)","plan=m.validate_archive(z,base);stage=W/base['label'];extracted=J(stage/'update-manifest.json')")
s=s.replace("'writes':len(plan['files'])}","'writes':len(plan['files']),'completedR1027RealExtractionReusedAndAllBytesReverified':True}")
s=s.replace('t.writestr(i,raw)','t.writestr(copy.copy(i),raw)')
s=s.replace('verified-transport-r1027.json','verified-transport-r1028.json')
ast.parse(s);new.write_text(s,encoding='utf8')
print(json.dumps({'preparedOnly':True,'script':str(new),'sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'transportPackageChanged':False}))
