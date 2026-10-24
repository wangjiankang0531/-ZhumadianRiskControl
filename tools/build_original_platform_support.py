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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True, help='Private explicit dependency paths; never commit')
    parser.add_argument('--output', type=Path, required=True, help='Fresh small build output directory')
    args = parser.parse_args()
    print(json.dumps(build(args.inputs, args.output)))


if __name__ == '__main__':
    main()
