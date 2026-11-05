"""Actual closed archive/extraction and rejection checks; no services or public."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shutil,zipfile
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian')
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105';DEL=D/'delivery';W=R/'work/t48'
J=lambda p:json.loads(Path(p).read_bytes())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert W.is_dir() and not(D/'verified-transport-r1028.json').exists()
assert {p.name for p in W.iterdir()}=={'r45','r47','bad-event-payload-tamper.zip'}
failed=W/'bad-event-payload-tamper.zip'
assert failed.resolve().parent==W.resolve() and not failed.is_symlink()
failed_pin={'sha256':sha(failed),'bytes':failed.stat().st_size,'previousExecutionTerminalExit':1,'cause':'test writer reused mutable ZipInfo objects'}
(V/'transport-test-failure-r1027.json').write_text(json.dumps(failed_pin,indent=2)+'\n',encoding='utf8')
failed.unlink()
assert shutil.disk_usage(R).free>2*1024**3+128*1024**2
manifest=J(DEL/'delivery-manifest.json')
assert set(p.name for p in DEL.iterdir())==set(manifest['files'])|{'delivery-manifest.json'}
for name,pin in manifest['files'].items():assert (DEL/name).stat().st_size==pin['bytes']and sha(DEL/name)==pin['sha256']
path=DEL/'deploy_event_write_results_r48.py';spec=importlib.util.spec_from_file_location('transport_r48_r1027',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=(R/'Document/Deployment/public_test_home_supervision_r47_20261104/delivery/deploy_home_supervision_r47.py').read_text('utf8').replace('R47','R48').replace('r47','r48')
functions=lambda s:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
a,b=functions(old),functions(path.read_text('utf8'))
assert set(a)==set(b)
changed=sorted(n for n in a if a[n]!=b[n]);assert changed==['extract_selected_archive','select_installed_base','validate_archive']
archive=DEL/m.ARCHIVE_NAME;assert sha(archive)==m.ARCHIVE_SHA
cases=[]
with zipfile.ZipFile(archive)as z:
 for base in m.BASES.values():
  plan=m.validate_archive(z,base);stage=W/base['label'];extracted=J(stage/'update-manifest.json')
  assert extracted==plan
  expected={'web.config','update-manifest.json'}|{'payload/'+n for n in plan['files']}
  assert {p.relative_to(stage).as_posix()for p in stage.rglob('*')if p.is_file()}==expected
  for name,pin in plan['files'].items():assert sha(stage/'payload'/name)==pin['SHA256']and(stage/'payload'/name).stat().st_size==pin['bytes']
  assert (stage/'web.config').read_bytes()==(DEL/'web.config').read_bytes()
  cases.append({'case':base['label']+'-real-archive-and-extraction','passed':True,'writes':len(plan['files']),'completedR1027RealExtractionReusedAndAllBytesReverified':True})
 base=next(iter(m.BASES.values()))
 def reject(label,build,expected):
  bad=W/('bad-'+label+'.zip');assert not bad.exists()
  with zipfile.ZipFile(bad,'x',compression=zipfile.ZIP_STORED)as target:build(target)
  try:
   with zipfile.ZipFile(bad)as altered:m.validate_archive(altered,base)
  except ValueError as error:assert str(error)==expected,(label,str(error),expected)
  else:raise AssertionError('INVALID_TRANSPORT_ACCEPTED:'+label)
  cases.append({'case':label,'passed':True,'refused':expected,'actualZipSHA256':sha(bad)})
  # Reconstructible own invalid ZIP only; retain the script and digest.
  assert bad.resolve().parent==W.resolve() and not bad.is_symlink();bad.unlink()
 reject('case-collision',lambda t:(t.writestr('A',b'a'),t.writestr('a',b'a')),'CLOSED_TRANSPORT_BOUNDS')
 reject('path-traversal',lambda t:t.writestr('../outside',b'a'),'EXACT_RELATIVE_MEMBER')
 def symlink(t):
  i=zipfile.ZipInfo('link');i.external_attr=0o120777<<16;t.writestr(i,b'target')
 reject('symlink',symlink,'REGULAR_UNENCRYPTED_MEMBERS')
 reject('manifest-tamper',lambda t:t.writestr('variants/r45/update-manifest.json',b'{}'),'FIXED_VARIANT_MANIFEST')
 def rewrite(t,change=None,extra=False):
  for i in z.infolist():
   raw=z.read(i.filename)
   if i.filename==change:raw+=b'\n'
   t.writestr(copy.copy(i),raw)
  if extra:t.writestr('unexpected.txt',b'own-test')
 reject('unknown-member',lambda t:rewrite(t,extra=True),'EXACT_CLOSED_MEMBERS')
 event=next(n for n in z.namelist()if n.endswith('wf-addOrEdit.vue_vue_type_script_setup_true_lang-o_9ZsphF.js'))
 reject('event-payload-tamper',lambda t:rewrite(t,change=event),'EXACT_ARCHIVED_PAYLOAD_PIN:'+event.removeprefix('payload/'))
 reject('deny-config-tamper',lambda t:rewrite(t,change='web.config'),'EXACT_STAGE_HTTP_DENY_CONFIG')
out={'passed':True,'checks':len(cases),'cases':cases,'realArchiveAndExtractionBytePinsVerified':True,
 'transportMainRecoveryAndStaticHTTPFunctionASTsRetainedFromR47':True,'changedFunctions':changed,
 'noFileIOOrValidationMocks':True,'fixedTransportFiles':len(list(DEL.iterdir())),
 'deliveryManifestSHA256':sha(DEL/'delivery-manifest.json'),'normalActualServerLifecycleAndIISTLSNotExecuted':True,
 'uploadedOrDeployed':False,'fullCloneReady':False}
(D/'verified-transport-r1028.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'checks':len(cases),'exactTransportFiles':len(list(DEL.iterdir())),'changedFunctions':changed}))
