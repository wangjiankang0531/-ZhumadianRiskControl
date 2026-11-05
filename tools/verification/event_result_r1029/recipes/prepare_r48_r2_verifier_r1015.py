"""Prepare source and a continuation receipt only; NEVER execute the verifier."""
from pathlib import Path
import ast, hashlib, json

V = Path(__file__).resolve().parent
R = Path('D:/Project/Zhumadian')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_bytes())
emit = lambda p, value: p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
OLD = V/'verify_r48_real_file_contract_r1008.py'
NEW = V/'verify_r48_r2_real_file_contract_r1015.py'
R2 = V/'r48-retained-preflight-r2-r1013'
UNIT = V/'verified-retained-preflight-unit-r1014.json'
CHECKPOINT = V/'postfix-r2-continuation-r1015.json'
assert not NEW.exists() and not CHECKPOINT.exists()
assert sha(OLD) == '28776d71422565fccb76bfed1b974607339481887b4b233b08b2d4f83dfd096c'
assert read(UNIT)['passed'] and read(UNIT)['checks'] == 9
prepared = read(R2/'prepared-r2-r1013.json')
assert prepared['newUpdaterSHA256'] == sha(R2/'source/original_public_test_update.py')
assert not (R/'work/f48').exists() and not (R/'work/f482').exists()
old = OLD.read_text(encoding='utf8')
new = '"""R2 physical-file verifier source. Requires normal approval before execution.\nDo not run superseded R1008. No service startup or public deployment.\n"""\n' + old
a = "D=R/'Document/Deployment/event_result_runtime_r1000_20261105';W=R/'work/f48'"
b = "D=V/'r48-retained-preflight-r2-r1013';W=R/'work/f482';REPORT=R/'Document/Deployment/event_result_runtime_r1015_20261105/verified-real-files-r1015.json'"
assert new.count(a) == 1
new = new.replace(a, b)
new = new.replace("assert not W.exists()and not(D/'verified-real-files-r1008.json').exists()",
                  "assert not W.exists() and not REPORT.exists()\nassert REPORT.parent.is_dir(), 'PREPARE_EXACT_REVIEWED_REPORT_DIRECTORY_FIRST'\nassert J(V/'verified-retained-preflight-unit-r1014.json')['passed']\nassert sha(D/'source/original_public_test_update.py') == '43d3096f73f766e6500da330868d63ba13a869b9e075cfa0092e27ee511ecfa7'")
marker = "resolution=J(V/'r48-file-source-resolution-r1007.private.json');assert not resolution['unresolved']"
assert new.count(marker) == 1
new = new.replace(marker, marker + "\n# Override only the two changed-control sources; immutable retained programs use the prior resolution.\nfor relative in ['tools/original_public_test_update.py','tools/original_public_test_base_r46.py']:\n source=D/'source'/Path(relative).name\n resolution['newSources'][relative]={'source':str(source),'bytes':source.stat().st_size,'sha256':sha(source)}")
new = new.replace("(D/'verified-real-files-r1008.json').write_bytes(enc(out))", "REPORT.write_bytes(enc(out))")
assert 'verified-real-files-r1008.json' not in new
ast.parse(new)
NEW.write_text(new, encoding='utf8')
previous = read(V/'postfix-verified-checkpoint-r1012.json')
checkpoint = {
    'goalStatus': 'active', 'fullCloneReady': False,
    'previousNativeAndRestoreProof': {'receipt': str(V/'postfix-verified-checkpoint-r1012.json'),
        'sha256': sha(V/'postfix-verified-checkpoint-r1012.json'),
        'nativeUIAssertionsIncludingRepeats': previous['selectedUIAssertionsIncludingRepeats'],
        'actualNormalSixComponentLifecycles': previous['actualNormalSixComponentLifecycles'],
        'currentCodeAndCachePreimageHashesLastAudited': previous['currentProgramAndCachePreimageHashesMatched'],
        'notFreshlyRerunThisPreparation': True},
    'R2Preparation': prepared,
    'focusedUnitRegression': {'receipt': str(UNIT), 'sha256': sha(UNIT),
        'checks': 9, 'passed': True, 'poolFileHelperIOExplicitlyStubbed': True},
    'futureVerifier': {'source': str(NEW), 'sha256': sha(NEW), 'executed': False,
        'fixtureRoot': str(R/'work/f482'),
        'output': str(R/'Document/Deployment/event_result_runtime_r1015_20261105/verified-real-files-r1015.json'),
        'reportDirectoryNotYetCreated': True,
        'requiresNormalApprovalBeforeExecution': True,
        'sourcePreparationDoesNotBypassBlockedR1008': True},
    'supersededInstruction': 'Do not execute R1012 next-step item naming the old R1008 verifier; R2 changes updater bytes and source resolution.',
    'nextRequiredWork': [
        'After review becomes available, authorize and run the exact new R1015 physical-file verifier; do not rerun old R1008.',
        'Validate exact R2 controller preflight and normal/fault sparse-update recovery before preparing transport.',
        'Persist validated sources, receipts and accurate stage documentation to the project and existing local branches through normal approval.',
        'Recheck server base and all installed 3D differences before any future public update.'
    ],
    'pendingPublicR47FinalPreflightResult': True,
    'R47FixedTransportAndApproved193PublicGitScopeUnchanged': True,
    'newProjectGitOrPublicWritesThisPreparation': False,
    'approvalOutage': {'blockedActionNotExecuted': True, 'notASafetyDetermination': True,
        'noRetryOrAlternateToolBypassPerformed': True}
}
emit(CHECKPOINT, checkpoint)
print(json.dumps({'preparedOnly': True, 'verifierExecuted': False, 'checkpoint': str(CHECKPOINT),
                  'R2ReleaseSHA256': prepared['newReleaseSHA256']}))
