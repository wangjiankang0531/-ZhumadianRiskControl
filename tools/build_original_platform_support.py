"""Rebuild only owned platform launch/configuration helpers from tracked sources.

The fixed dependency fingerprints are checked before javac. No original main,
Spring application, database, credentials or network download is used.
"""
from pathlib import Path, PurePosixPath
import argparse
import datetime
import hashlib
import json
import os
import re
import stat
import subprocess
import uuid
import zipfile

LOCK = 'original_platform_support.lock.json'
WRAPPERS = ('OriginalPlatformLaunch.java', 'OriginalJarResourceCache.java',
            'OriginalResourceCachedClassLoader.java', 'IndependentJarFileWrapper.java',
            'protocol/jar/Handler.java')
OBSERVERS = ('PlatformStartupObservation.java', 'ObservedPlatformBeanNameGenerator.java',
             'PlatformFailureObservation.java', 'PlatformJava8MetadataProbe.java')
EXISTING_OBSERVERS = ('SourceClasspathProbe.java', 'OriginalIdGeneratorShutdown.java',
                      'PlatformWritableObservation.java', 'OriginalBootstrapOrphanGuard.java')
FACTORIES = b'org.springframework.boot.SpringApplicationRunListener=xnby.platform.PlatformFailureObservation\n'


def require(value, code):
    if not value:
        raise ValueError(code)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def regular(path):
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and not path.is_symlink()
            and not getattr(info, 'st_file_attributes', 0) & 0x400,
            'REGULAR_BUILD_INPUT_REQUIRED')
    return path.resolve(strict=True)


def json_document(path):
    path = regular(path)
    require(0 < path.stat().st_size <= 1024 * 1024, 'BOUNDED_BUILD_DOCUMENT_REQUIRED')
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, 'DUPLICATE_BUILD_DOCUMENT_KEY')
            result[key] = value
        return result
    result = json.loads(path.read_bytes(), object_pairs_hook=pairs)
    require(isinstance(result, dict), 'BUILD_DOCUMENT_OBJECT_REQUIRED')
    return result


def source_names():
    return (['java/original_platform_runtime8/' + n for n in WRAPPERS + OBSERVERS]
            + ['java/OriginalPlatformConfigBuilder.java']
            + ['java/' + n for n in EXISTING_OBSERVERS])


def checked(inputs_file, output, tools=None):
    tools = Path(tools or Path(__file__).parent).resolve(strict=True)
    lock_file = tools / LOCK
    lock = json_document(lock_file)
    require(lock.get('schema') == 'xnby.original-platform-support.build.v1', 'PLATFORM_SUPPORT_LOCK_SCHEMA')
    require(set(lock['sourceSHA256']) == set(source_names()), 'EXACT_PLATFORM_SUPPORT_SOURCE_SET')
    sources = {}
    for name, pin in lock['sourceSHA256'].items():
        parts = PurePosixPath(name)
        require(not parts.is_absolute() and '..' not in parts.parts and '\\' not in name,
                'RELATIVE_PLATFORM_SUPPORT_SOURCE_REQUIRED')
        path = regular(tools / name)
        require(path.is_relative_to(tools) and digest(path) == pin, 'PLATFORM_SUPPORT_SOURCE_PIN_MISMATCH')
        sources[name] = path
    inputs = json_document(inputs_file)
    require(set(inputs) == {'schema', 'javaHome', 'bootLoader', 'guard', 'yaml', 'libraries'}
            and inputs['schema'] == 'xnby.original-platform-support.inputs.v1',
            'EXACT_PLATFORM_SUPPORT_INPUT_ROLES')
    require(isinstance(inputs['libraries'], dict)
            and set(inputs['libraries']) == set(lock['librarySHA256']), 'EXACT_PLATFORM_SUPPORT_LIBRARY_SET')
    require(set(lock['inputSHA256']) == {'bootLoader', 'guard', 'yaml'}, 'EXACT_PLATFORM_SUPPORT_PIN_ROLES')
    for name, pin in lock['inputSHA256'].items():
        require(digest(regular(inputs[name])) == pin, 'PLATFORM_SUPPORT_INPUT_PIN_MISMATCH')
    for name, pin in lock['librarySHA256'].items():
        require(digest(regular(inputs['libraries'][name])) == pin, 'PLATFORM_SUPPORT_LIBRARY_PIN_MISMATCH')
    java_home = Path(inputs['javaHome']).resolve(strict=True)
    require(set(lock['compilerSHA256']) == {'bin/java.exe', 'bin/javac.exe', 'release'}, 'EXACT_BUILD_COMPILER_PINS')
    for name, pin in lock['compilerSHA256'].items():
        require(digest(regular(java_home / name)) == pin, 'PLATFORM_SUPPORT_COMPILER_PIN_MISMATCH')
    require(re.search(r'(?m)^JAVA_VERSION="17\.', (java_home / 'release').read_text('utf-8')),
            'PINNED_JDK17_BUILD_COMPILER_REQUIRED')
    output = Path(output).absolute()
    require(not output.exists() and not output.is_symlink() and output.parent.is_dir(), 'FRESH_BUILD_OUTPUT_REQUIRED')
    require(output.parent.resolve(strict=True) == output.parent and not output.is_relative_to(java_home),
            'BUILD_OUTPUT_REDIRECTION_OR_JDK_WRITE_REJECTED')
    require(len(lock['expectedClassSHA256']) == lock['expectedClassCount'] == 21, 'EXACT_PLATFORM_SUPPORT_CLASS_SET')
    return tools, lock, inputs, output, sources, digest(lock_file)


def build(inputs_file, output, tools=None):
    tools, lock, inputs, output, sources, lock_sha = checked(inputs_file, output, tools)
    output.mkdir()
    env = {key: value for key, value in os.environ.items()
           if key.upper() not in {'JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS',
                                  'CLASSPATH', 'PYTHONPATH', 'PYTHONHOME'}
           and not key.upper().startswith('LOADER_')}
    (output / 'tmp').mkdir(); env['TMP'] = env['TEMP'] = str(output / 'tmp')
    receipt = {'schema': 'xnby.original-platform-support.result.v1', 'ownerId': str(uuid.uuid4()),
               'startedAt': datetime.datetime.now().astimezone().isoformat(), 'lockSHA256': lock_sha,
               'originalApplicationStarted': False, 'databaseConnected': False,
               'originalArchiveRead': False, 'originalClassesModified': False,
               'passed': False}
    def compile_group(name, target, classpath, source_files):
        destination = output / target; destination.mkdir()
        command = [str(Path(inputs['javaHome']) / 'bin/javac.exe'), '-proc:none', '--release',
                   str(17 if target == 'builder-classes' else 8), '-encoding', 'UTF-8',
                   '-cp', os.pathsep.join(map(str, classpath)), '-d', str(destination),
                   *map(str, source_files)]
        run = subprocess.run(command, cwd=output, env=env, capture_output=True, timeout=40,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        (output / (name + '.private.log')).write_bytes(run.stdout + run.stderr)
        require(run.returncode == 0, 'PLATFORM_SUPPORT_COMPILE_FAILED_' + name.upper())
    try:
        compile_group('wrappers', 'wrapper-classes', [inputs['bootLoader'], inputs['guard']],
                      [sources['java/original_platform_runtime8/' + n] for n in WRAPPERS])
        compile_group('observers', 'observer-classes', [inputs['guard'], *inputs['libraries'].values()],
                      [sources['java/original_platform_runtime8/' + n] for n in OBSERVERS]
                      + [sources['java/' + n] for n in EXISTING_OBSERVERS])
        compile_group('builder', 'builder-classes', [inputs['yaml']],
                      [sources['java/OriginalPlatformConfigBuilder.java']])
        classes = {p.relative_to(output).as_posix(): digest(p) for group in
                   ['wrapper-classes', 'observer-classes', 'builder-classes']
                   for p in (output / group).rglob('*.class')}
        require(classes == lock['expectedClassSHA256'], 'PLATFORM_SUPPORT_COMPILED_BYTES_MISMATCH')
        jar = output / 'own-platform-observation.jar'
        with zipfile.ZipFile(jar, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            def write(name, raw):
                member = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                member.compress_type = zipfile.ZIP_DEFLATED
                member.external_attr = 0o100644 << 16
                archive.writestr(member, raw)
            write('META-INF/spring.factories', FACTORIES)
            for path in sorted((output / 'observer-classes').rglob('*.class')):
                write(path.relative_to(output / 'observer-classes').as_posix(), path.read_bytes())
        # Inputs must still match after compilation; no success receipt for changed sources.
        for name, path in sources.items():
            require(digest(path) == lock['sourceSHA256'][name], 'PLATFORM_SUPPORT_SOURCE_CHANGED_DURING_BUILD')
        for name, pin in lock['inputSHA256'].items():
            require(digest(inputs[name]) == pin, 'PLATFORM_SUPPORT_INPUT_CHANGED_DURING_BUILD')
        for name, pin in lock['librarySHA256'].items():
            require(digest(inputs['libraries'][name]) == pin, 'PLATFORM_SUPPORT_LIBRARY_CHANGED_DURING_BUILD')
        for name, pin in lock['compilerSHA256'].items():
            require(digest(Path(inputs['javaHome']) / name) == pin, 'PLATFORM_SUPPORT_COMPILER_CHANGED_DURING_BUILD')
        total = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
        require(total < 8 * 1024**2, 'PLATFORM_SUPPORT_SMALL_OUTPUT_BOUND')
        receipt.update(passed=True, compiledClassCount=len(classes), classSHA256=classes,
                       observationJarSHA256=digest(jar), outputBytes=total,
                       originalReferenceOrTrialReceiptsUsedByBuilder=False)
    finally:
        receipt['completedAt'] = datetime.datetime.now().astimezone().isoformat()
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


def validate_support_selection(receipt, pin):
    requested = receipt is not None or pin is not None
    if requested:
        require(receipt is not None and pin is not None, 'PLATFORM_SUPPORT_RECEIPT_AND_PIN_REQUIRED_TOGETHER')
        require(isinstance(pin, str) and re.fullmatch('[0-9a-f]{64}', pin), 'EXPLICIT_PLATFORM_SUPPORT_RECEIPT_PIN_REQUIRED')
    return requested


def select_support(receipt_file, expected_sha256, lock_file=None):
    require(validate_support_selection(receipt_file, expected_sha256), 'EXPLICIT_PLATFORM_SUPPORT_SELECTION_REQUIRED')
    receipt_file = regular(receipt_file)
    require(receipt_file.name == 'receipt.json' and digest(receipt_file) == expected_sha256,
            'PLATFORM_SUPPORT_RECEIPT_PIN_MISMATCH')
    receipt = json_document(receipt_file)
    lock_file = regular(lock_file or Path(__file__).with_name(LOCK))
    lock = json_document(lock_file)
    require(lock.get('schema') == 'xnby.original-platform-support.build.v1'
            and receipt.get('lockSHA256') == digest(lock_file), 'PLATFORM_SUPPORT_BUILD_LOCK_MISMATCH')
    require(receipt.get('schema') == 'xnby.original-platform-support.result.v1'
            and receipt.get('passed') is True, 'SUCCESSFUL_PLATFORM_SUPPORT_BUILD_REQUIRED')
    owner = receipt.get('ownerId')
    require(isinstance(owner, str) and str(uuid.UUID(owner)) == owner, 'PLATFORM_SUPPORT_OWNER_UUID_REQUIRED')
    require(receipt.get('compiledClassCount') == lock.get('expectedClassCount') == 21
            and receipt.get('classSHA256') == lock.get('expectedClassSHA256'), 'PLATFORM_SUPPORT_CLASS_PROOF_MISMATCH')
    for key in ['originalApplicationStarted', 'databaseConnected', 'originalArchiveRead',
                'originalClassesModified', 'originalReferenceOrTrialReceiptsUsedByBuilder']:
        require(receipt.get(key) is False, 'PLATFORM_SUPPORT_BUILD_BOUNDARY_PROOF_REQUIRED')
    classes = lock['expectedClassSHA256']
    require(len(classes) == 21, 'EXACT_PLATFORM_SUPPORT_CLASS_SET')
    for name in classes:
        path = PurePosixPath(name)
        require(not path.is_absolute() and '..' not in path.parts and '\\' not in name
                and path.parts[0] in {'wrapper-classes', 'observer-classes', 'builder-classes'}
                and path.suffix == '.class', 'RELATIVE_PLATFORM_SUPPORT_CLASS_REQUIRED')
    root = receipt_file.parent
    require(not root.is_symlink() and not getattr(root.lstat(), 'st_file_attributes', 0) & 0x400,
            'PLATFORM_SUPPORT_ROOT_REDIRECTION_REJECTED')
    expected_files = set(classes) | {'receipt.json', 'own-platform-observation.jar',
                                     'wrappers.private.log', 'observers.private.log', 'builder.private.log'}
    expected_dirs = {'tmp'}
    for name in expected_files:
        expected_dirs.update(str(parent) for parent in PurePosixPath(name).parents if str(parent) != '.')
    found_files, found_dirs, pending = set(), set(), [root]
    optional_empty_perf_dirs = set()
    while pending:
        current = pending.pop()
        for child in current.iterdir():
            info = child.lstat()
            require(not child.is_symlink() and not getattr(info, 'st_file_attributes', 0) & 0x400,
                    'PLATFORM_SUPPORT_MEMBER_REDIRECTION_REJECTED')
            name = child.relative_to(root).as_posix()
            if stat.S_ISDIR(info.st_mode):
                # javac on Windows can leave its empty, process-owned perf directory.
                # It is outside every classpath; no file or nested directory is allowed.
                if child.parent == root / 'tmp' and re.fullmatch(r'hsperfdata_[\w.-]{1,80}', child.name):
                    require(not any(child.iterdir()) and not optional_empty_perf_dirs,
                            'EMPTY_SINGLE_COMPILER_PERF_DIRECTORY_REQUIRED')
                    optional_empty_perf_dirs.add(name)
                    continue
                require(name in expected_dirs, 'UNEXPECTED_PLATFORM_SUPPORT_DIRECTORY')
                found_dirs.add(name); pending.append(child)
            else:
                require(stat.S_ISREG(info.st_mode) and name in expected_files, 'UNEXPECTED_PLATFORM_SUPPORT_FILE')
                found_files.add(name)
                if name.endswith('.private.log'):
                    require(info.st_size <= 128 * 1024, 'BOUNDED_PLATFORM_SUPPORT_BUILD_LOG_REQUIRED')
            require(len(found_dirs) + len(found_files) <= 96, 'PLATFORM_SUPPORT_MEMBER_COUNT_BOUND')
    require(found_files == expected_files and found_dirs == expected_dirs, 'EXACT_PLATFORM_SUPPORT_OUTPUT_SET')
    for name, pin in classes.items():
        require(digest(root / name) == pin, 'PLATFORM_SUPPORT_CLASS_BYTES_MISMATCH')
    jar = root / 'own-platform-observation.jar'
    require(jar.stat().st_size <= 1024 * 1024 and digest(jar) == receipt.get('observationJarSHA256'),
            'PLATFORM_SUPPORT_OBSERVATION_JAR_MISMATCH')
    jar_classes = {name.removeprefix('observer-classes/'): pin for name, pin in classes.items()
                   if name.startswith('observer-classes/')}
    with zipfile.ZipFile(jar) as archive:
        names = archive.namelist()
        require(len(names) == 13 and set(names) == set(jar_classes) | {'META-INF/spring.factories'},
                'EXACT_PLATFORM_SUPPORT_OBSERVATION_MEMBERS')
        require(archive.read('META-INF/spring.factories') == FACTORIES, 'PLATFORM_SUPPORT_FACTORIES_MISMATCH')
        for name, pin in jar_classes.items():
            require(archive.getinfo(name).file_size <= 1024 * 1024
                    and hashlib.sha256(archive.read(name)).hexdigest() == pin,
                    'PLATFORM_SUPPORT_OBSERVATION_CLASS_MISMATCH')
    require(digest(receipt_file) == expected_sha256, 'PLATFORM_SUPPORT_RECEIPT_CHANGED_AFTER_VERIFICATION')
    return root, {'mode': 'source-rebuilt-platform-support', 'selectionSHA256': expected_sha256,
                  'lockSHA256': receipt['lockSHA256'], 'ownerId': owner, 'compiledClassCount': 21,
                  'observationJarSHA256': receipt['observationJarSHA256'],
                  'launchHelperClassSHA256': {name: pin for name, pin in classes.items()
                                             if not name.startswith('observer-classes/')},
                  'legacyPreparationReceiptsReadBySelector': False,
                  'originalArchiveReadBySelector': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True, help='Private explicit dependency paths; never commit')
    parser.add_argument('--output', type=Path, required=True, help='Fresh small build output directory')
    args = parser.parse_args()
    print(json.dumps(build(args.inputs, args.output)))


if __name__ == '__main__':
    main()
