"""Build-boundary failures must precede javac/output; actual compilation is checked separately."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import build_original_platform_support as support


class BuildInputBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.tools = self.root / 'tools'; self.tools.mkdir()
        self.output = self.root / 'out'; self.java = self.root / 'jdk'; self.java.mkdir()
        sources = {}
        for name in support.source_names():
            file = self.tools / name; file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'fixture source for boundary checks; not compiled')
            sources[name] = support.digest(file)
        for name in ['bin/java.exe', 'bin/javac.exe', 'release']:
            file = self.java / name; file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'JAVA_VERSION="17.0.fixture"\n' if name == 'release' else b'not an executable')
        roles = {}
        for name in ['bootLoader', 'guard', 'yaml', 'library.jar']:
            file = self.root / name; file.write_bytes(b'not a real runtime dependency'); roles[name] = str(file)
        self.inputs = {'schema': 'xnby.original-platform-support.inputs.v1', 'javaHome': str(self.java),
                       **{n: roles[n] for n in ['bootLoader', 'guard', 'yaml']},
                       'libraries': {'library.jar': roles['library.jar']}}
        self.lock = {'schema': 'xnby.original-platform-support.build.v1', 'sourceSHA256': sources,
                     'inputSHA256': {n: support.digest(roles[n]) for n in ['bootLoader', 'guard', 'yaml']},
                     'librarySHA256': {'library.jar': support.digest(roles['library.jar'])},
                     'compilerSHA256': {n: support.digest(self.java / n) for n in ['bin/java.exe', 'bin/javac.exe', 'release']},
                     'expectedClassSHA256': {'fixture' + str(i): 'a' * 64 for i in range(21)}, 'expectedClassCount': 21}
        self.input_file = self.root / 'inputs.private.json'; self.save()

    def save(self):
        self.input_file.write_text(json.dumps(self.inputs), encoding='utf-8')
        (self.tools / support.LOCK).write_text(json.dumps(self.lock), encoding='utf-8')

    def rejected_before_build(self, code):
        with patch.object(support.subprocess, 'run') as launch:
            with self.assertRaisesRegex(ValueError, code):
                support.build(self.input_file, self.output, self.tools)
            launch.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_changed_source_cannot_compile_against_an_old_lock(self):
        (self.tools / support.source_names()[0]).write_bytes(b'changed')
        self.rejected_before_build('SOURCE_PIN_MISMATCH')

    def test_missing_or_extra_library_role_is_rejected(self):
        self.inputs['libraries']['extra.jar'] = self.inputs['guard']; self.save()
        self.rejected_before_build('EXACT_PLATFORM_SUPPORT_LIBRARY_SET')

    def test_replaced_library_is_rejected(self):
        Path(self.inputs['libraries']['library.jar']).write_bytes(b'changed')
        self.rejected_before_build('LIBRARY_PIN_MISMATCH')

    def test_replaced_compiler_is_rejected(self):
        (self.java / 'bin/javac.exe').write_bytes(b'changed')
        self.rejected_before_build('COMPILER_PIN_MISMATCH')

    def test_duplicate_json_key_does_not_choose_an_input_silently(self):
        self.input_file.write_bytes(b'{"javaHome":"first","javaHome":"second"}')
        self.rejected_before_build('DUPLICATE_BUILD_DOCUMENT_KEY')

    def test_non_regular_dependency_cannot_be_selected(self):
        self.inputs['guard'] = str(self.java); self.save()
        self.rejected_before_build('REGULAR_BUILD_INPUT_REQUIRED')

    def test_source_escape_cannot_be_added_to_the_lock(self):
        self.lock['sourceSHA256']['../outside.java'] = 'a' * 64; self.save()
        self.rejected_before_build('EXACT_PLATFORM_SUPPORT_SOURCE_SET')

    def test_existing_output_is_preserved(self):
        self.output.mkdir(); canary = self.output / 'keep'; canary.write_bytes(b'keep')
        with patch.object(support.subprocess, 'run') as launch:
            with self.assertRaisesRegex(ValueError, 'FRESH_BUILD_OUTPUT_REQUIRED'):
                support.build(self.input_file, self.output, self.tools)
            launch.assert_not_called()
        self.assertEqual(canary.read_bytes(), b'keep')

    def test_compile_failure_is_recorded_as_failure_without_running_an_application(self):
        with patch.object(support.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, b'', b'fixture javac failure')) as launch:
            with self.assertRaisesRegex(ValueError, 'PLATFORM_SUPPORT_COMPILE_FAILED_WRAPPERS'):
                support.build(self.input_file, self.output, self.tools)
            self.assertEqual(launch.call_count, 1)
            self.assertIn('-proc:none', launch.call_args.args[0])
        receipt = json.loads((self.output / 'receipt.json').read_bytes())
        self.assertFalse(receipt['passed']); self.assertFalse(receipt['originalApplicationStarted'])
        self.assertFalse(receipt['databaseConnected'])
        self.assertEqual((self.output / 'wrappers.private.log').read_bytes(), b'fixture javac failure')

    def test_cli_requires_explicit_inputs_and_output(self):
        result = subprocess.run([sys.executable, '-B', support.__file__], capture_output=True, timeout=8,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'--inputs', result.stderr); self.assertIn(b'--output', result.stderr)


if __name__ == '__main__':
    unittest.main()
