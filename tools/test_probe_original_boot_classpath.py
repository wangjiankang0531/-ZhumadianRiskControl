"""Own Java fixtures check non-initialization and failure behavior, without a real app."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from probe_original_boot_classpath import java_environment, probe, resource_name


class InputSafetyTests(unittest.TestCase):
    def test_inherited_launcher_and_java_options_cannot_override_probe(self):
        env = java_environment({'PATH': 'kept', 'LOADER_MAIN': 'other.Main', 'loader_path': 'other',
                                'JAVA_TOOL_OPTIONS': '-javaagent:other.jar', '_JAVA_OPTIONS': '-Dother=true',
                                'JDK_JAVA_OPTIONS': '--module-path=other', 'CLASSPATH': 'other'}, Path('owned'))
        self.assertEqual(env, {'PATH': 'kept', 'TEMP': 'owned', 'TMP': 'owned'})

    def test_manifest_resources_cannot_escape_or_inject_rows(self):
        for value in ('/absolute', '../escape', 'a/../escape', 'a\\escape', 'a\tC\tbad', 'C:/file', 'a//file', './file'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resource_name(value)
        self.assertEqual(resource_name('own/Fixture.class', is_class=True), 'own/Fixture.class')

    def test_wrong_runtime_pin_is_rejected_before_output_or_java(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            suffix = '.exe' if os.name == 'nt' else ''
            (root / 'bin').mkdir()
            for name in ('java', 'javac'):
                (root / 'bin' / (name + suffix)).write_text('must not execute', encoding='ascii')
            runtime = root / 'runtime.jar'
            with zipfile.ZipFile(runtime, 'w') as archive:
                archive.writestr('BOOT-INF/classes/own/Fixture.class', b'not executable')
            output = root / 'output'
            args = argparse.Namespace(runtime_jar=runtime, java_home=root, runtime_sha256='0' * 64,
                                      overlay_classes=None, overlay_resources=None, output=output)
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                probe(args)
            self.assertFalse(output.exists())


class JavaProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        home = os.environ.get('SOURCE_PROBE_TEST_JAVA_HOME')
        if not home:
            raise unittest.SkipTest('Set SOURCE_PROBE_TEST_JAVA_HOME to an existing JDK for Java fixtures')
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        suffix = '.exe' if os.name == 'nt' else ''
        cls.java = str(Path(home) / 'bin' / ('java' + suffix))
        javac = str(Path(home) / 'bin' / ('javac' + suffix))
        source, compiled, visible = (cls.root / name for name in ('source', 'compiled', 'visible'))
        for path in (source, compiled, visible):
            path.mkdir()
        fixtures = {
            'Sentinel': 'package own; public class Sentinel { static { System.setProperty("xnby.sourceProbe.sentinel", "true"); } public String read(){return "own fixture";} public static void main(String[] a){if(!Boolean.getBoolean("xnby.sourceProbe.sentinel")) throw new AssertionError(); System.out.print("INITIALIZED");} }',
            'Missing': 'package own; public class Missing {}',
            'Dependent': 'package own; public class Dependent {public Missing read(){return null;}}',
        }
        for name, text in fixtures.items():
            (source / (name + '.java')).write_text(text, encoding='ascii')
        env = java_environment(dict(os.environ), cls.root)
        subprocess.run([javac, '--release', '8', '-encoding', 'UTF-8', '-d', str(compiled),
                        str(Path(__file__).with_name('java') / 'SourceClasspathProbe.java'),
                        *map(str, sorted(source.glob('*.java')))], check=True, capture_output=True,
                       env=env, timeout=45)
        # Only the fixture with a missing dependency is exposed to the inspector.
        for name in ('own/Sentinel.class', 'own/Dependent.class', 'xnby/audit/SourceClasspathProbe.class'):
            destination = visible / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((compiled / name).read_bytes())
        cls.visible = visible
        cls.env = env
        cls.base = [cls.java, '-Dfile.encoding=UTF-8', '-Djava.io.tmpdir=' + str(cls.root), '-cp', str(visible)]

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'):
            cls.temp.cleanup()

    def invoke(self, label, name, digest, result=None):
        spec = self.root / (label + '.tsv')
        result = result or self.root / (label + '_result.tsv')
        spec.write_text('C\t' + name + '\t' + digest + '\n', encoding='utf-8')
        run = subprocess.run(self.base + ['xnby.audit.SourceClasspathProbe', str(spec), str(result)],
                             env=self.env, capture_output=True, timeout=20)
        return run, result

    def fixture_sha(self, name):
        return hashlib.sha256((self.visible / name).read_bytes()).hexdigest()

    def test_static_initializer_is_effective_but_not_executed_by_inspection(self):
        positive = subprocess.run(self.base + ['own.Sentinel'], env=self.env, capture_output=True, timeout=20)
        self.assertEqual(positive.returncode, 0)
        self.assertEqual(positive.stdout, b'INITIALIZED')
        run, result = self.invoke('no_init', 'own/Sentinel.class', self.fixture_sha('own/Sentinel.class'))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('\tPASS\t', result.read_text(encoding='utf-8'))

    def test_hash_mismatch_is_failure(self):
        run, result = self.invoke('wrong_hash', 'own/Sentinel.class', '0' * 64)
        self.assertEqual(run.returncode, 4)
        self.assertIn('\tSHA_MISMATCH\t', result.read_text(encoding='utf-8'))

    def test_missing_resource_is_failure(self):
        run, result = self.invoke('missing', 'own/Absent.class', '0' * 64)
        self.assertEqual(run.returncode, 4)
        self.assertIn('\tRESOURCE_MISSING\t', result.read_text(encoding='utf-8'))

    def test_missing_method_dependency_is_failure(self):
        run, result = self.invoke('unresolved', 'own/Dependent.class', self.fixture_sha('own/Dependent.class'))
        self.assertEqual(run.returncode, 4)
        self.assertIn('\tLINKAGE_ERROR\t', result.read_text(encoding='utf-8'))

    def test_existing_evidence_cannot_be_overwritten(self):
        result = self.root / 'keep_result.tsv'
        result.write_bytes(b'preserved evidence')
        run, _ = self.invoke('keep_existing', 'own/Sentinel.class', self.fixture_sha('own/Sentinel.class'), result)
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(result.read_bytes(), b'preserved evidence')


if __name__ == '__main__':
    unittest.main()
