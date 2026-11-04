from pathlib import Path
import ast, copy, gzip, hashlib, io, json, shutil, sys, warnings, zipfile
sys.dont_write_bytecode = True
R, V = Path('D:/Project/Zhumadian'), Path(__file__).resolve().parent
D = R/'Document/Deployment/public_test_mapper_chart_r44_20261104'
O = R/'work/v44-r574'
J = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists() and shutil.disk_usage(R).free > 512*1024**2
manifest, prepared = J(D/'delivery-manifest.json'), J(D/'preparation-result-r573.json')
assert sha(D/'delivery-manifest.json') == prepared['manifestSHA256']
assert (D/'delivery/delivery-manifest.json').read_bytes() == (D/'delivery-manifest.json').read_bytes()
assert set(p.name for p in (D/'delivery').iterdir()) == set(manifest['files'])|{'delivery-manifest.json'}
for n, pin in manifest['files'].items():
    p = D/'delivery'/n
    assert p.stat().st_size == pin['bytes'] and sha(p) == pin['sha256']
assert len(list((D/'delivery').iterdir())) == 8
assert (D/'delivery/r44_update_runtime.py').read_bytes() == (V/'original_public_test_update_r44_mapper_chart_r570.py').read_bytes()
S = D/'delivery/deploy_mapper_chart_r44.py'
ns = {'__file__':str(S), '__name__':'closed_transport_r574'}
exec(compile(S.read_bytes(), str(S), 'exec'), ns)
archive = D/'delivery'/ns['ARCHIVE_NAME']
assert sha(archive) == ns['ARCHIVE_SHA']
assert prepared['maximumExtractionPathCharacters']+len(str(O/'extract-r36'))-len(str(ns['APP'])) < 250
O.mkdir()
rows = []
def reject(name, call):
    try: call()
    except (ValueError, KeyError, zipfile.BadZipFile):
        rows.append({'case':name, 'passed':True})
        return
    raise AssertionError('EXPECTED_REJECTION:'+name)
for old, base in ns['BASES'].items():
    with zipfile.ZipFile(archive) as z:
        plan = ns['validate_archive'](z, base)
        assert set(plan['acceptedOldReleases']) == {old}
    stage = O/('extract-'+base['label'])
    ns['extract_selected_archive'](archive, stage, base)
    assert sha(stage/'update-manifest.json') == base['manifestSHA256']
    assert (stage/'web.config').read_bytes() == (D/'delivery/web.config').read_bytes()
    assert not (stage/'variants').exists()
    for n, pin in plan['files'].items():
        p = stage/'payload'/n
        assert p.stat().st_size == pin['bytes'] and sha(p) == pin['SHA256']
    assert len(plan['files']) == 190 and len(plan['removedFrontendFiles']) == 178
    rows.append({'case':base['label']+'-closed-193-members-extract-all-190-pins','passed':True})
    reject(base['label']+'-existing-stage-rejected', lambda:ns['extract_selected_archive'](archive, stage, base))
with zipfile.ZipFile(archive) as z: members = {x.filename:z.read(x.filename) for x in z.infolist()}
base = next(iter(ns['BASES'].values()))
css_member = next(n for n in members if n.startswith('payload/frontend/security_pc/assets/css/xnby-workplace-period-'))
html_member = 'payload/frontend/security_pc/index.html'
def bad_zip(name, change):
    p = O/(name+'.zip')
    data = change(list(members.items()))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(p, 'x', zipfile.ZIP_DEFLATED) as z:
            for n, raw in data: z.writestr(n, raw)
    try:
        def check():
            with zipfile.ZipFile(p) as z: ns['validate_archive'](z, base)
        reject(name, check)
    finally: p.unlink()
bad_zip('new-css-byte-drift', lambda rs:[(n,b+b'own corruption' if n == css_member else b) for n,b in rs])
bad_zip('html-link-byte-drift', lambda rs:[(n,b+b'own corruption' if n == html_member else b) for n,b in rs])
bad_zip('new-css-missing', lambda rs:[(n,b) for n,b in rs if n != css_member])
bad_zip('new-css-duplicate', lambda rs:rs+[(css_member,members[css_member])])
bad_zip('extra-private-member', lambda rs:rs+[('payload/private/unapproved.json',b'{}')])
bad_zip('extra-parent-path', lambda rs:rs+[('../unapproved.txt',b'own')])
static = ns['STATIC_EXPECTED']
parent = R/'Document/Deployment/public_test_mapper_equivalence_r42_20261104/delivery/deploy_mapper_equivalence_r42.py'
pt = ast.parse(parent.read_bytes())
original_static = ast.literal_eval(next(n.value for n in pt.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id == 'STATIC_EXPECTED'))
assert all(static.get(n) == p for n,p in original_static.items()) and len(static) == len(original_static)+1
css_url = next(n for n in static if 'xnby-workplace-period-' in n)
body = members[css_member]
headers = {'cache-control':'public, max-age=31536000, immutable', 'content-encoding':'gzip', 'vary':'Accept-Encoding'}
assert ns['validate_static_response'](css_url,'gzip',200,headers,gzip.compress(body))['decodedContentMatched']
assert ns['validate_static_response'](css_url,'identity',200,{'cache-control':headers['cache-control']},body)['decodedContentMatched']
rows.append({'case':'real-candidate-css-gzip-and-identity-bytes','passed':True})
reject('css-corrupt-http-body', lambda:ns['validate_static_response'](css_url,'gzip',200,headers,gzip.compress(body+b'own corruption')))
reject('css-http-cache-wrong', lambda:ns['validate_static_response'](css_url,'gzip',200,{**headers,'cache-control':'no-store'},gzip.compress(body)))
reject('css-http-vary-missing', lambda:ns['validate_static_response'](css_url,'gzip',200,{k:v for k,v in headers.items() if k != 'vary'},gzip.compress(body)))
reject('css-http-503', lambda:ns['validate_static_response'](css_url,'gzip',503,headers,gzip.compress(body)))
def functions(text): return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
before = functions(parent.read_text('utf-8').replace('R42','R44').replace('r42','r44'))
after = functions(S.read_text('utf-8'))
assert set(before) == set(after)
assert {n for n in before if before[n] != after[n]} == {'validate_archive','verify_static_gateway_and_iis'}
proof = {'passed':True,'checks':rows,'transportFiles':8,'transportBytes':prepared['transportBytes'],'fixedManifestSHA256':prepared['manifestSHA256'],
    'twoActualClosedArchiveExtractionsAndAllFilePinsPassed':True,'staticResponseTestsUseActualCSSBytesNotArbitraryMarker':True,
    'allPriorStaticExpectedRowsRetained':True,'otherWrapperFunctionASTRetainedAgainstR42':True,
    'maximumPublicExtractionCharacters':prepared['maximumExtractionPathCharacters'],'publicOrDatabaseServicesOrDesktopTouched':False,
    'actualIISHTTPSAndR44LifecycleStillPending':True,'fullCloneReady':False}
(D/'verified-transport-r574.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'checks':len(rows),'actualVariantExtractions':2,'members':193,'transportFiles':8,'publicTouched':False}))
