"""Prepare a pinned lifecycle compatibility proof without starting the original application.

Uses the existing original Spring 2 dependencies and Java 8; does not execute JNI,
open a database, copy third-party dependencies, or modify frozen prior receipts.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

KIND = 'xnby.original-bigscreen.lifecycle.v1'
GUARDS = ('OriginalBigscreenProcessBoundary.java', 'OriginalBigscreenLaunch.java',
          'OriginalBigscreenObservation.java')
LIFECYCLE = 'CandidateLifecycleObservation.java'
FIXTURE = 'BigscreenLifecycleFixture.java'


def require(value, code):
    if not value: raise ValueError(code)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def document(path):
    path = Path(path); info = path.lstat()
    require(path.is_file() and not path.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400
            and 0 < info.st_size <= 65536, 'REGULAR_BOUNDED_LIFECYCLE_RECEIPT_REQUIRED')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'DUPLICATE_LIFECYCLE_RECEIPT_KEY'); result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=pairs)


def selection_requested(receipt, pin):
    require((receipt is None) == (pin is None), 'LIFECYCLE_RECEIPT_AND_PIN_REQUIRED_TOGETHER')
    if pin is not None: require(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin), 'LIFECYCLE_RECEIPT_PIN_REQUIRED')
    return receipt is not None


def class_member(value):
    require(isinstance(value, str) and re.fullmatch(r'xnby/replica/CandidateLifecycleObservation(?:\$[A-Za-z0-9_]+)?\.class', value),
            'EXACT_LIFECYCLE_CLASS_MEMBER_REQUIRED')
    return value


def verify_class_pins(root, pins):
    require(isinstance(pins, dict) and 'xnby/replica/CandidateLifecycleObservation.class' in pins,
            'LIFECYCLE_MAIN_CLASS_REQUIRED')
    for name, pin in pins.items():
        class_member(name); require(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin), 'LIFECYCLE_CLASS_PIN_REQUIRED')
        path = Path(root) / name; info = path.lstat()
        require(path.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True))
                and path.is_file() and not path.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                'REGULAR_OWN_LIFECYCLE_CLASS_REQUIRED')
        require(sha(path) == pin, 'LIFECYCLE_CLASS_CHANGED')


def validate_shape(record):
    require(record.get('kind') == KIND and record.get('checks') == 5 and record.get('ownExitCode') == 0
            and record.get('eventConstructorArity') in (3, 4)
            and record.get('originalApplicationStarted') is False and record.get('nativeCodeExecuted') is False
            and record.get('databaseConnected') is False, 'ACTUAL_OWN_LIFECYCLE_FIXTURE_REQUIRED')


def baseline(workspace):
    from original_bigscreen_runtime import ARCHIVE_SHA256, DATABASE_SHA256, HELPER_SHA256, NATIVE_SHA256
    w = Path(workspace).resolve(strict=True); a = w.parents[1]
    native = w / 'own-bigscreen-native-cli-r1'; meta = document(native / 'preparation.json'); proof = document(native / 'receipt.json')
    require(proof.get('passedChecks') == 13 and proof.get('ownExitCode') == 0
            and proof.get('referenceAndCopyDatabaseUnchanged') is True, 'PRIOR_NATIVE_VERIFICATION_REQUIRED')
    for path, pin in ((meta['sourceArchive'], ARCHIVE_SHA256), (meta['referenceDatabase'], DATABASE_SHA256),
                      (meta['helperJar'], HELPER_SHA256), (native / 'native/sqlitejdbc.dll', NATIVE_SHA256)):
        require(sha(path) == pin, 'UNCHANGED_BIGSCREEN_BASELINE_REQUIRED')
    for name in GUARDS:
        require(sha(a / 'tools/java' / name) == meta['sourceSHA256'][name], 'UNCHANGED_BIGSCREEN_GUARD_SOURCE_REQUIRED')
    runtime = document(w / 'own-pboot-r32/preparation.json'); jdk = Path(meta['javaHome']).resolve(strict=True)
    require(jdk == Path(runtime['platformJavaHome']).resolve(strict=True), 'KNOWN_ORIGINAL_JAVA8_REQUIRED')
    for name, pin in runtime['platformRuntimePins'].items():
        require(sha(jdk / name) == pin, 'PINNED_JAVA8_RUNTIME_REQUIRED')
    deps = Path(meta['dependencyRoot']).resolve(strict=True)
    require(deps.is_relative_to(w), 'EXISTING_OWN_DEPENDENCIES_REQUIRED')
    return w, a, native, meta, jdk, deps, runtime['platformRuntimePins']


def prepare(workspace, output):
    w, a, native, meta, jdk, deps, java_pins = baseline(workspace)
    root = Path(output).absolute(); require(root.is_relative_to(w) and not root.exists()
        and root.parent.resolve(strict=True) == root.parent, 'FRESH_OWN_LIFECYCLE_PROOF_REQUIRED')
    root.mkdir(); (root / 'classes').mkdir(); (root / 'fixture').mkdir()
    sources = [a / 'tools/java' / n for n in (LIFECYCLE, FIXTURE)]
    cp = os.pathsep.join(map(str, [root / 'classes', *sorted(deps.glob('*.jar'))]))
    env = {k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
    def run(command, label):
        result = subprocess.run(command, cwd=root, env=env, capture_output=True, timeout=40,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (root / (label + '.log')).write_bytes(result.stdout + result.stderr)
        require(result.returncode == 0, 'OWN_LIFECYCLE_' + label.upper() + '_FAILED')
        return result.stdout
    run([str(jdk/'bin/javac.exe'), '-proc:none', '-source', '1.8', '-target', '1.8', '-encoding', 'UTF-8',
         '-cp', cp, '-d', str(root/'classes'), *map(str, sources)], 'compile')
    stdout = run([str(jdk/'bin/java.exe'), '-Xmx64m', '-Dfile.encoding=UTF-8', '-cp', cp,
                  'xnby.replica.BigscreenLifecycleFixture', str(root/'fixture')], 'fixture')
    match = re.search(rb'BIGSCREEN_LIFECYCLE_FIXTURE_CHECKS=5 EVENT_CONSTRUCTOR_ARITY=([34])', stdout)
    require(match is not None, 'ACTUAL_LIFECYCLE_FIVE_CHECKS_REQUIRED')
    pins = {p.relative_to(root/'classes').as_posix(): sha(p) for p in (root/'classes').rglob('CandidateLifecycleObservation*.class')}
    verify_class_pins(root/'classes', pins)
    record = {'kind':KIND, 'recordedAt':datetime.datetime.now().astimezone().isoformat(),
        'nativePreparationSHA256':sha(native/'preparation.json'), 'nativeReceiptSHA256':sha(native/'receipt.json'),
        'lifecycleSourceSHA256':sha(sources[0]), 'fixtureSourceSHA256':sha(sources[1]),
        'javaRuntimePins':java_pins, 'dependencySHA256':{p.name:sha(p) for p in sorted(deps.glob('*.jar'))},
        'compiledLifecycleClassesSHA256':pins, 'fixtureLogSHA256':sha(root/'fixture.log'),
        'checks':5, 'eventConstructorArity':int(match.group(1)), 'ownExitCode':0,
        'originalApplicationStarted':False, 'nativeCodeExecuted':False, 'databaseConnected':False}
    validate_shape(record); target=root/'receipt.json'
    target.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    return target


def select(workspace, receipt, pin):
    if not selection_requested(receipt, pin): return None
    requested = Path(receipt).absolute(); record=document(requested)
    require(requested.parent.resolve(strict=True)==requested.parent, 'DIRECT_OWN_LIFECYCLE_RECEIPT_PARENT_REQUIRED')
    path = requested.resolve(strict=True); w=Path(workspace).resolve(strict=True)
    require(path.is_relative_to(w) and sha(path)==pin, 'PINNED_OWN_LIFECYCLE_RECEIPT_REQUIRED')
    validate_shape(record)
    _, a, native, _, _, deps, java_pins=baseline(w)
    require(sha(native/'preparation.json')==record['nativePreparationSHA256']
            and sha(native/'receipt.json')==record['nativeReceiptSHA256'], 'NATIVE_BASELINE_RECEIPTS_CHANGED')
    require(sha(a/'tools/java'/LIFECYCLE)==record['lifecycleSourceSHA256']
            and sha(a/'tools/java'/FIXTURE)==record['fixtureSourceSHA256'], 'VERIFIED_LIFECYCLE_SOURCE_CHANGED')
    require(java_pins==record['javaRuntimePins'] and {p.name:sha(p) for p in sorted(deps.glob('*.jar'))}==record['dependencySHA256'],
            'LIFECYCLE_RUNTIME_OR_DEPENDENCIES_CHANGED')
    verify_class_pins(path.parent/'classes', record['compiledLifecycleClassesSHA256'])
    require(sha(path.parent/'fixture.log')==record['fixtureLogSHA256'] and sha(path)==pin,
            'LIFECYCLE_PROOF_CHANGED_DURING_READ')
    return record


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    receipt=prepare(args.workspace,args.output);pin=sha(receipt);record=select(args.workspace,receipt,pin)
    print(json.dumps({'receiptSHA256':pin,'checks':record['checks'],
                      'eventConstructorArity':record['eventConstructorArity'],
                      'originalApplicationStarted':False,'nativeCodeExecuted':False,'databaseConnected':False}))


if __name__=='__main__': main()
