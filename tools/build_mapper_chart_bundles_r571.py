from pathlib import Path, PurePosixPath
import copy, hashlib, importlib.util, json, os, shutil, sys
sys.dont_write_bytecode = True
R, V = Path('D:/Project/Zhumadian'), Path(__file__).resolve().parent
D = R/'Document/Deployment/mapper_chart_candidate_r44_20261104'
O = R/'work/mapper-chart-bundles-r571'
J = lambda p: json.loads(p.read_bytes())
enc = lambda x: (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m
runtimePath = V/'original_public_test_update_r44_mapper_chart_r570.py'
runtime = load('mapper_chart_r44_runtime', runtimePath)
assert sha(runtimePath) == J(D/'prepared-runtime-r570.json')['runtimeSHA256']
stylesRoot = R/'work/workplace-style-delivery-r564/payload'
UPDATER = 'tools/original_public_test_update.py'
def put(p, b):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b)
def linked(src, dest, row):
    assert src.is_file() and src.stat().st_size == row['bytes'] and sha(src) == row.get('sha256', row.get('SHA256'))
    dest.parent.mkdir(parents=True, exist_ok=True)
    os.link(src, dest)
def compose(base, old_payload, out, label):
    assert label in ['r36','r37'] and not out.exists()
    plan, release, payload = map(copy.deepcopy, [J(base/'update-manifest.json'), J(base/'payload/release-manifest.json'), J(base/'payload/payload-manifest.json')])
    assert 'businessSupervisionPdf' not in release and 'workplacePeriodHeaders' not in release
    updater = {'bytes':runtimePath.stat().st_size, 'sha256':sha(runtimePath)}
    payload['files'].update(copy.deepcopy(runtime.R44_STYLE_ROWS))
    if UPDATER in payload['files']: payload['files'][UPDATER] = updater
    payload_raw = enc(payload)
    release['payloadManifestSHA256'] = hashlib.sha256(payload_raw).hexdigest()
    release['controllerFiles'][UPDATER] = updater['sha256']
    release['publicTestRevision'] = runtime.R38_REVISION
    release[runtime.R44_STYLE_FIELD] = copy.deepcopy(runtime.R44_STYLE_CONTRACT)
    release_raw = enc(release)
    rows = copy.deepcopy(plan['files'])
    rows[UPDATER] = {'bytes':updater['bytes'], 'SHA256':updater['sha256']}
    for n, p in runtime.R44_STYLE_ROWS.items(): rows[n] = {'bytes':p['bytes'], 'SHA256':p['sha256']}
    raw = {'payload-manifest.json':payload_raw, 'release-manifest.json':release_raw}
    for n, b in raw.items(): rows[n] = {'bytes':len(b), 'SHA256':hashlib.sha256(b).hexdigest()}
    assert len(rows) <= 1000 and sum(p['bytes'] for p in rows.values()) <= 32*1024**2
    plan.update(updateId='20261104-r44-mapper-chart-from-'+label, files=rows,
        oldPayloadFiles={n:old_payload['files'][n] for n in rows if n in old_payload['files']},
        newReleaseSHA256=hashlib.sha256(release_raw).hexdigest(), newPayloadManifestSHA256=release['payloadManifestSHA256'])
    for n, p in rows.items():
        name = PurePosixPath(n)
        assert str(name) == n and not name.is_absolute() and '..' not in name.parts
        assert not n.startswith(('private/','UserData/','Assets/','seed/','runtime/'))
        target = out/'payload'/n
        if n in raw: put(target, raw[n])
        else: linked(runtimePath if n == UPDATER else stylesRoot/n if n in runtime.R44_STYLE_ROWS else base/'payload'/n, target, p)
    put(out/'update-manifest.json', enc(plan))
    return {'bundle':str(out), 'manifestSHA256':sha(out/'update-manifest.json'),
        'newReleaseSHA256':plan['newReleaseSHA256'], 'writes':len(rows),
        'removedFrontendPaths':len(plan['removedFrontendFiles']), 'payloadLogicalBytes':sum(p['bytes'] for p in rows.values())}
def main():
    assert not O.exists() and shutil.disk_usage(R).free > 2*1024**3+128*1024**2
    originals = J(R/'Document/Deployment/supervision_public_runtime_r552_20261104/prepared-bundles-r553.json')['variants']
    variants = {}
    for label in ['r36','r37']:
        base = R/('work/r42-mapper-equivalence-r457/'+label+'/bundle')
        assert sha(base/'update-manifest.json') == originals[label]['baseManifestSHA256']
        old = R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle' if label == 'r36' else R/'work/r39-plan-runtime-unified-r1/original-r37-contract'
        variants[label] = compose(base, J(old/'payload/payload-manifest.json'), O/label/'bundle', label)
    assert variants['r36']['newReleaseSHA256'] == variants['r37']['newReleaseSHA256']
    put(D/'prepared-bundles-r571.json', enc({'prepared':True, 'variants':variants, 'sameFinalApplicationAcrossBases':True,
        'runtimeSHA256':sha(runtimePath), 'onlyR42PlusTwoStyleFilesAndExactUpdaterMetadata':True,
        'servicesStartedOrPublicTouched':False, 'lifecycleAndPublicAcceptanceStillPending':True, 'fullCloneReady':False}))
    print(json.dumps({'prepared':True,'variants':variants,'publicDeployed':False}))
if __name__ == '__main__': main()
