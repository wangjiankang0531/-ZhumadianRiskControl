"""Read-only receiver audit. No candidate code execution or project writes."""
from pathlib import Path, PurePosixPath
import ast, datetime, hashlib, json, subprocess, zipfile

V = Path(__file__).resolve().parent
R = Path('D:/Project/Zhumadian')
A = R/'Application'
MSG = R/'Document/Coordination/交接消息'
OUT = V/'d75-d76-receiver-review-r1016.json'
assert not OUT.exists()
sha = lambda data: hashlib.sha256(data).hexdigest()
specs = [
    ('D75', MSG/'驻马店三维同层对象协同合并_给驻马店3_20261105_d75.json'),
    ('D76', MSG/'驻马店三维冲突逐项比较选择接口_给驻马店3_20261105_d76.json'),
]
receipts, runtime = [], {}
for label, message in specs:
    raw_message = message.read_bytes()
    h = json.loads(raw_message)
    assert h['from'] == '驻马店三维' and h['to'] == '驻马店3'
    assert h['publicInstallRequested'] is False and h['publicChanged'] is False
    archives = []
    for key in ('sourceArchive', 'runtimeArchive'):
        path = Path(h[key])
        assert path.is_relative_to(R/'Document/Deployment') and path.stat().st_size < 32*1024**2
        assert sha(path.read_bytes()) == h[key+'SHA256']
        archives.append({'kind': key, 'bytes': path.stat().st_size, 'sha256': h[key+'SHA256']})
    with zipfile.ZipFile(h['runtimeArchive']) as z:
        names = z.namelist()
        assert len(names) == len(set(names))
        assert set(names) == set(h['runtimePins']), 'EXACT_RUNTIME_ARCHIVE_ENTRY_SET'
        assert sum(i.file_size for i in z.infolist()) < 32*1024**2
        runtime[label] = {}
        for name, pin in h['runtimePins'].items():
            path = PurePosixPath(name)
            assert not path.is_absolute() and '..' not in path.parts and ':' not in name
            raw = z.read(name)
            assert len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], name
            if name.endswith('.py'):
                ast.parse(raw.decode('utf8'), filename=name)
            runtime[label][name] = raw
    git_sources = []
    with zipfile.ZipFile(h['sourceArchive']) as z:
        assert len(z.namelist()) == len(set(z.namelist()))
        for name, expected in h['sourcePins'].items():
            matches = [n for n in z.namelist() if n == name or n.endswith('/'+name)]
            assert len(matches) == 1
            raw = z.read(matches[0])
            assert sha(raw) == expected
            got = subprocess.run(['git', '-C', str(A), 'show', h['sourceCommit']+':'+name],
                                 capture_output=True, timeout=30,
                                 creationflags=subprocess.CREATE_NO_WINDOW)
            assert got.returncode == 0 and sha(got.stdout) == expected, 'EXACT_SOURCE_GIT_BLOB:'+name
            git_sources.append({'path': name, 'sha256': expected})
    receipts.append({'handoff': label, 'messageSHA256': sha(raw_message),
        'sourceCommit': h['sourceCommit'], 'reviewCommit': h['reviewCommit'],
        'archives': archives, 'runtimeEntryPinsVerified': len(h['runtimePins']),
        'declaredArchiveSourcesAndExactGitBlobsVerified': git_sources,
        'senderTestsRerunByReceiver': False})

old, new = runtime['D75'], runtime['D76']
changed = sorted(n for n in old.keys() | new.keys() if old.get(n) != new.get(n))
expected_code = {'code/package-manifest.json', 'code/services/layer_sync_bridge.py',
                 'code/services/layer_sync_client.py', 'code/services/layer_sync_resolution.py',
                 'code/services/layer_sync_state.py'}
assert {n for n in changed if n.startswith('code/')} == expected_code
unchanged_backend = ['code/services/layer_sync_server.py', 'code/services/database.py',
    'code/services/layer_sync_transport.py', 'code/tools/serve_layer_sync.py',
    'code/tools/layer_sync_ingress.py', 'code/tools/layer_sync_gateway_transaction.py',
    'code/tools/original_server_windows_job.py']
assert all(old[n] == new[n] for n in unchanged_backend)
contract = json.loads(new['choice-contract.json'])
result = {'schema': 'xnby.receiver.read-only-candidate-review.v1',
    'at': datetime.datetime.now().astimezone().isoformat(),
    'receiver': '驻马店3', 'passed': True, 'receipts': receipts,
    'D75toD76ChangedRuntimeEntries': changed,
    'backendIngressAndNestedJobBytesVerifiedUnchangedBetweenCandidates': unchanged_backend,
    'choiceContract': contract,
    'meaning': 'Exact archives, declared Git sources, syntax and delta reviewed; no functional runtime acceptance.',
    'formalSharedAcknowledgementWritten': False,
    'formalAcknowledgementPendingNormalProjectWriteApproval': True,
    'otherThreadRealtimeNotificationSent': False,
    'serverInstallRequestedOrPerformed': False,
    'userConflictChoiceUIOrNewEXEProvided': False,
    'realPlatformLoginPublicTLSAnd252Acceptance': False,
    'projectGitHeldViewerGISDLGOrBusinessDataModified': False,
    'fullCloneReady': False}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'passed': True, 'handoffs': len(receipts),
    'runtimeEntries': [r['runtimeEntryPinsVerified'] for r in receipts],
    'declaredExactGitBlobs': sum(len(r['declaredArchiveSourcesAndExactGitBlobsVerified']) for r in receipts),
    'changedRuntimeEntries': changed, 'formalSharedAckWritten': False}))
