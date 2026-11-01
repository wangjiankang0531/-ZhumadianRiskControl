"""One login-call correction on exact published files, with consistent cache-busting module names.

No source rebuild or unrelated frontend candidate is substituted. All other byte
differences must invert exactly to module filename references in the input.
"""
from pathlib import Path
import hashlib
import json
import sys

T = Path('D:/Project/Zhumadian/Application/tools')
sys.path.insert(0, str(T))
from materialize_published_emergency_frontend_20261101 import materialize as original

W = Path('D:/Project/Zhumadian/work/user_feedback_20261031')
D = W / 'emergency-login-query-r1'
OLD = 'U.post("/jnpf/oauth/Login",o,{headers:{"Content-Type":"application/x-www-form-urlencoded"}})'
NEW = 'U.post("/jnpf/oauth/Login",void 0,{params:o,headers:{"Content-Type":"application/x-www-form-urlencoded"}})'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def materialize():
    source = original()
    proof = json.loads((source.parent / 'source-proof.json').read_bytes())
    inputs = {name: (source / name).read_bytes() for name in proof['files']}
    assert len(inputs) == 204
    assert sum(raw.decode('utf-8', errors='ignore').count(OLD) for raw in inputs.values()) == 1
    renamed = {name: 'assets/js/q1-' + Path(name).name for name in inputs if name.startswith('assets/js/') and name.endswith('.js')}
    assert len({Path(name).name for name in renamed}) == len(renamed)
    outputs, changes = {}, []
    for name, raw in inputs.items():
        expected = raw
        if OLD.encode() in expected:
            assert name == 'assets/js/index-D9sL7DI_.js'
            expected = expected.replace(OLD.encode(), NEW.encode(), 1)
            changes.append(name)
        result = expected
        for before, after in renamed.items():
            result = result.replace(Path(before).name.encode(), Path(after).name.encode())
        inverted = result
        for before, after in renamed.items():
            inverted = inverted.replace(Path(after).name.encode(), Path(before).name.encode())
        assert inverted == expected, 'ONLY_ONE_CALL_AND_FILENAME_REFERENCES_MAY_CHANGE'
        outputs[renamed.get(name, name)] = result
    assert changes == ['assets/js/index-D9sL7DI_.js']
    files = {name: {'bytes': len(raw), 'sha256': digest(raw)} for name, raw in outputs.items()}
    if D.exists():
        saved = json.loads((D / 'candidate-proof.json').read_bytes())
        assert saved['files'] == files
        assert {p.relative_to(D / 'frontend').as_posix() for p in (D / 'frontend').rglob('*') if p.is_file()} == set(files)
        for name, raw in outputs.items():
            assert (D / 'frontend' / name).read_bytes() == raw
        return D / 'frontend'
    D.mkdir()
    for name, raw in outputs.items():
        p = D / 'frontend' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    # Human-readable equivalent, kept outside the served tree. Existing source stays unchanged.
    api_source = Path('D:/Project/Zhumadian/Application/work/tianjin_native_20261023/emergency_pc/src/api/login/index.ts')
    text = api_source.read_text(encoding='utf-8')
    anchor = 'request.post<LoginResult>("/jnpf/oauth/Login", params, {'
    assert text.count(anchor) == 1
    changed = text.replace(anchor, 'request.post<LoginResult>("/jnpf/oauth/Login", undefined, {\n    params,', 1)
    (D / 'login-query-source-equivalent.ts').write_text(changed, encoding='utf-8')
    record = {'baseManifestSHA256': proof['manifestSHA256'], 'baseFiles': 204, 'candidateFiles': 204,
              'old206CandidateNotUsed': True, 'oneLoginCallChanged': True, 'oldCall': OLD, 'newCall': NEW,
              'credentialsTransformAndTokenStorageUnchanged': True,
              'allOtherChangesInvertExactlyToFilenameReferences': True,
              'moduleNamesConsistentlyChangedToAvoidOldBrowserCache': True,
              'renamedModules': renamed, 'files': files, 'sourceEquivalentOnlyNotClaimedAsRebuild': True,
              'originalTypeScriptSHA256': digest(api_source.read_bytes()), 'publicInstalled': False}
    (D / 'candidate-proof.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return D / 'frontend'


if __name__ == '__main__':
    print('ONE_CALL_LOGIN_QUERY_CANDIDATE', materialize())
