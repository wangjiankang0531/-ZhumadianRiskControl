"""Prepare a checked continuation of the terminated R1015 file fixture."""
from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent
oldp=V/'verify_r48_r2_real_file_contract_r1015.py'
newp=V/'verify_r48_r2_real_file_contract_r1018.py'
assert not newp.exists()
assert hashlib.sha256(oldp.read_bytes()).hexdigest()=='b2150671b78acd6c4ac12db2b6fcd29496a22bd6f6a4ad86199a83683a38114f'
s=oldp.read_text('utf8')
s=s.replace('verified-real-files-r1015.json','verified-real-files-r1018.json')
s=s.replace("assert not W.exists() and not REPORT.exists()", "assert W.is_dir() and not REPORT.exists()\nassert J(W/'own-r48-file-fixture.json') == {'ownedProgramsOnly':True,'noServicesOrAccountBusinessSeedGISData':True,'hardlinkLogicalBytesNotPhysicalStorage':True}")
old="W.mkdir();(W/'own-r48-file-fixture.json').write_bytes(enc({'ownedProgramsOnly':True,'noServicesOrAccountBusinessSeedGISData':True,'hardlinkLogicalBytesNotPhysicalStorage':True}))"
new="""# The previous execution is terminal exit 1. Accept only pinned program files
# from its initial r45 materialization; no metadata or mutable data may exist.
assert not (W/'r47').exists()
existing=0
for p in W.rglob('*'):
 assert not p.is_symlink() and not p.lstat().st_file_attributes&0x400
 if not p.is_file():continue
 if p==W/'own-r48-file-fixture.json':continue
 rel=p.relative_to(W).as_posix();assert rel.startswith('r45/')
 name=rel[len('r45/'):];pin=resolution['bases']['r45']['programs'].get(name)
 assert pin and p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'] and os.path.samefile(p,pin['source']), 'UNKNOWN_PARTIAL_FIXTURE_FILE'
 existing+=1
print(json.dumps({'phase':'verified-terminal-partial-fixture','pinnedFiles':existing}),flush=True)
copy_fallback={'files':0,'bytes':0}
"""
assert s.count(old)==1;s=s.replace(old,new)
old=" dest.parent.mkdir(parents=True,exist_ok=True);os.link(source,dest);assert os.path.samefile(source,dest)"
new=""" dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():
  assert dest.stat().st_size==pin['bytes'] and sha(dest)==pin['sha256'] and os.path.samefile(source,dest), 'PARTIAL_PROGRAM_DRIFT'
  return
 try:
  os.link(source,dest);assert os.path.samefile(source,dest)
 except OSError as exc:
  # Only the observed Windows per-file link-count limit is eligible. The
  # fallback is bounded tiny frontend PNG bytes, never GIS directories.
  assert exc.winerror==1142, 'UNEXPECTED_LINK_FAILURE'
  assert '/frontend/tiles/' in dest.as_posix() and dest.suffix=='.png' and pin['bytes']<=4096, 'TINY_FRONTEND_TILE_ONLY'
  assert copy_fallback['bytes']+pin['bytes']<=16*1024**2, 'COPY_FALLBACK_BUDGET'
  raw=source.read_bytes();assert len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256']
  with dest.open('xb') as f:f.write(raw)
  assert sha(dest)==pin['sha256']
  copy_fallback['files']+=1;copy_fallback['bytes']+=len(raw)
"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("app.mkdir();(bundle/'payload').mkdir(parents=True)","app.mkdir(exist_ok=True);(bundle/'payload').mkdir(parents=True,exist_ok=True)")
s=s.replace("'publicOrServicesTouched':False,", "'publicOrServicesTouched':False,'tinyFrontendTileLinkLimitFallback':copy_fallback,'partialR1015InitialProgramFilesVerified':existing,")
ast.parse(s);newp.write_text(s,encoding='utf8')
report={'preparedOnly':True,'newScript':str(newp),'sha256':hashlib.sha256(newp.read_bytes()).hexdigest(),
 'priorSession':43797,'priorSessionTerminalExitCode':1,'failure':'WinError1142 per-file hardlink count',
 'resumeRequiresExactPartialProgramSHAAndSamefile':True,'fallbackOnlyTinyPinnedFrontendPNGsMax16MiB':True,
 'originalGenericAndR48FileLoadersUnmodified':True,'notExecutedByPreparation':True}
(V/'prepared-link-limit-resume-r1018.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
