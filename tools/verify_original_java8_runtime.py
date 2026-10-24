"""Verify installed Windows JDK8 prerequisites for isolated original-platform testing.

The checks exercise process-local integration constraints and fixed JDK graphics,
not a hostile-code OS sandbox or original application behavior. No database,
original JAR, credentials, network download, CAPTCHA generation or login is used.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile

JAVA_SOURCES = ('Java8IO.java', 'OriginalProcessBoundary.java',
                'OriginalProcessBoundaryFixture.java', 'BoundaryClassLoadingCanary.java',
                'OwnJava8GraphicsProbe.java')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(java_home, output):
    java_home = Path(java_home).resolve(strict=True)
    output = Path(output).resolve()
    if os.name != 'nt':
        raise ValueError('Windows JDK8 verification requires Windows')
    if output.exists():
        raise ValueError('Fresh verification output directory required')
    if output == java_home or output in java_home.parents or java_home in output.parents:
        raise ValueError('Output must be independent of the installed JDK')
    release = (java_home / 'release').read_text('utf-8')
    match = re.search(r'(?m)^JAVA_VERSION="(1\.8\.[^"]+)"$', release)
    if not match:
        raise ValueError('An existing full JDK8 installation is required')
    runtime_names = ('bin/java.exe', 'bin/javac.exe', 'jre/bin/server/jvm.dll',
                     'jre/lib/rt.jar', 'jre/lib/ext/nashorn.jar',
                     'jre/bin/awt.dll', 'jre/bin/fontmanager.dll', 'jre/bin/lcms.dll',
                     'jre/bin/freetype.dll', 'jre/bin/jpeg.dll')
    runtime_pins = {name: digest(java_home / name) for name in runtime_names}
    sources = Path(__file__).resolve().parent / 'java/original_runtime8'
    source_pins = {name: digest(sources / name) for name in JAVA_SOURCES}
    output.mkdir(parents=True)
    for name in ('classes', 'tmp', 'boundary', 'graphics'):
        (output / name).mkdir()
    (output / 'graphics/tmp').mkdir()
    env = {key: value for key, value in os.environ.items()
           if key.upper() not in ('JAVA_TOOL_OPTIONS', 'JDK_JAVA_OPTIONS', '_JAVA_OPTIONS', 'CLASSPATH')}
    env['TEMP'] = env['TMP'] = str(output / 'tmp')
    receipt = {'recordedAt': datetime.datetime.now().astimezone().isoformat(),
               'javaVersion': match.group(1), 'runtimeSHA256': runtime_pins,
               'sourceSHA256': source_pins, 'passed': False,
               'originalApplicationStarted': False, 'databaseConnected': False,
               'credentialsUsed': False, 'captchaGeneratedOrSolved': False,
               'operatingSystemSettingsChanged': False,
               'constraintScope': 'process-local integration, not hostile-code OS isolation'}

    def run(label, command, timeout=30):
        try:
            result = subprocess.run(command, cwd=output, env=env, capture_output=True,
                                    timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
        except subprocess.TimeoutExpired as error:
            # subprocess.run has killed and waited for this owned child.
            (output / (label + '.private.log')).write_bytes((error.stdout or b'') + (error.stderr or b''))
            receipt[label + 'TimedOutOwnedChildStopped'] = True
            raise RuntimeError('Owned ' + label + ' check timed out') from None
        (output / (label + '.private.log')).write_bytes(result.stdout + result.stderr)
        receipt[label + 'ExitCode'] = result.returncode
        if result.returncode:
            raise RuntimeError('Owned ' + label + ' check failed; inspect its private log')
        return result.stdout

    try:
        run('compile', [str(java_home / 'bin/javac.exe'), '-J-Xmx128m', '-proc:none',
                        '-source', '1.8', '-target', '1.8', '-encoding', 'UTF-8',
                        '-d', str(output / 'classes'), *[str(sources / name) for name in JAVA_SOURCES]])
        for file in (output / 'classes').rglob('*.class'):
            if int.from_bytes(file.read_bytes()[6:8], 'big') != 52:
                raise RuntimeError('Unexpected class compatibility target')
        canary = output / 'own-loader-canary.jar'
        with zipfile.ZipFile(canary, 'x') as archive:
            archive.writestr('xnby/replica/BoundaryClassLoadingCanary.class',
                             (output / 'classes/xnby/replica/BoundaryClassLoadingCanary.class').read_bytes())
        policy = output / 'own-process-only.policy'
        policy.write_text('grant { permission java.security.AllPermission; };\n', encoding='ascii')
        common = [str(java_home / 'bin/java.exe'), '-Xmx128m', '-Down.boundary.trace=true',
                  '-Djava.security.policy==' + policy.as_uri()]
        raw = run('boundary', common + ['-Down.canary.jar=' + str(canary),
                  '-cp', str(output / 'classes'), 'xnby.replica.OriginalProcessBoundaryFixture',
                  str(output / 'boundary')])
        result = json.loads(next(line.partition(' ')[2] for line in raw.decode('utf-8').splitlines()
                                 if line.startswith('BOUNDARY_FIXTURE_RESULT ')))
        if result['passedCases'] != 26 or not result['outsideCanaryUnchanged'] or result['ownLoopbackConnections'] != 1:
            raise RuntimeError('Boundary fixture result did not meet its declared scope')
        receipt['boundary'] = result
        run('graphics', common + ['-Djava.awt.headless=true', '-Duser.home=' + str(output / 'graphics'),
                  '-Djava.io.tmpdir=' + str(output / 'graphics/tmp'), '-cp', str(output / 'classes'),
                  'xnby.platform.OwnJava8GraphicsProbe', str(output / 'graphics')])
        png, jpeg = output / 'graphics/jdk-font-probe.png', output / 'graphics/jdk-font-probe.jpg'
        if not png.read_bytes().startswith(b'\x89PNG\r\n\x1a\n') or not jpeg.read_bytes().startswith(b'\xff\xd8\xff'):
            raise RuntimeError('Actual JDK image signatures did not match PNG/JPEG')
        receipt['graphics'] = {'headlessFontPNG': True, 'JPEG': True,
                               'pngBytes': png.stat().st_size, 'jpegBytes': jpeg.stat().st_size}
        receipt['passed'] = True
    except Exception as error:
        receipt['failureType'] = type(error).__name__
        raise
    finally:
        receipt['finishedAt'] = datetime.datetime.now().astimezone().isoformat()
        (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--java-home', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.java_home, args.output)
    print(json.dumps({'passed': result['passed'], 'javaVersion': result['javaVersion'],
                      'boundaryCases': result['boundary']['passedCases'], 'headlessFontPNG': True,
                      'JPEG': True, 'originalApplicationStarted': False, 'databaseConnected': False}))


if __name__ == '__main__':
    main()
