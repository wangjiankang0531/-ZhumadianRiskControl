"""Build-boundary failures must precede javac/output; actual compilation is checked separately."""
import json
import ast
import os
import types
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
import zipfile
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


class RuntimeSupportSelection(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); self.payload = self.root / 'support'; self.payload.mkdir()
        (self.payload / 'tmp').mkdir(); self.classes = {}
        for group, count in [('wrapper-classes', 8), ('observer-classes', 12), ('builder-classes', 1)]:
            for index in range(count):
                name = group + '/fixture/Helper' + str(index) + '.class'
                file = self.payload / name; file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b'synthetic metadata fixture, never loaded by Java: ' + name.encode())
                self.classes[name] = support.digest(file)
        for name in ['wrappers.private.log', 'observers.private.log', 'builder.private.log']:
            (self.payload / name).write_bytes(b'')
        self.jar = self.payload / 'own-platform-observation.jar'; self.write_jar()
        self.lock_file = self.root / 'lock.json'
        self.lock_file.write_text(json.dumps({'schema': 'xnby.original-platform-support.build.v1',
            'expectedClassCount': 21, 'expectedClassSHA256': self.classes}), encoding='utf-8')
        self.receipt_file = self.payload / 'receipt.json'
        self.receipt = {'schema': 'xnby.original-platform-support.result.v1', 'ownerId': str(uuid.uuid4()),
            'lockSHA256': support.digest(self.lock_file), 'passed': True, 'compiledClassCount': 21,
            'classSHA256': self.classes, 'observationJarSHA256': support.digest(self.jar),
            **{name: False for name in ['originalApplicationStarted', 'databaseConnected', 'originalArchiveRead',
                'originalClassesModified', 'originalReferenceOrTrialReceiptsUsedByBuilder']}}
        self.save_receipt()

    def write_jar(self, factories=support.FACTORIES):
        with zipfile.ZipFile(self.jar, 'w') as archive:
            archive.writestr('META-INF/spring.factories', factories)
            for name in self.classes:
                if name.startswith('observer-classes/'):
                    archive.writestr(name.removeprefix('observer-classes/'), (self.payload / name).read_bytes())

    def save_receipt(self):
        self.receipt_file.write_text(json.dumps(self.receipt), encoding='utf-8')
        self.pin = support.digest(self.receipt_file)

    def select(self):
        return support.select_support(self.receipt_file, self.pin, self.lock_file)

    def test_complete_payload_selects_without_a_workspace_or_old_preparation_receipts(self):
        root, proof = self.select()
        self.assertEqual(root, self.payload)
        self.assertEqual(proof['compiledClassCount'], 21)
        self.assertFalse(proof['legacyPreparationReceiptsReadBySelector'])
        self.assertFalse(proof['originalArchiveReadBySelector'])

    def test_missing_or_invalid_explicit_pin_is_rejected(self):
        self.assertFalse(support.validate_support_selection(None, None))
        for receipt, pin in [(self.receipt_file, None), (None, self.pin), (self.receipt_file, 'bad')]:
            with self.subTest(pin=pin), self.assertRaises(ValueError): support.select_support(receipt, pin, self.lock_file)
        with self.assertRaisesRegex(ValueError, 'RECEIPT_PIN_MISMATCH'):
            support.select_support(self.receipt_file, '0' * 64, self.lock_file)

    def test_changed_class_cannot_be_selected(self):
        (self.payload / next(iter(self.classes))).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'CLASS_BYTES_MISMATCH'): self.select()

    def test_unexpected_file_cannot_extend_the_runtime_classpath(self):
        (self.payload / 'wrapper-classes/fixture/Extra.class').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_PLATFORM_SUPPORT_FILE'): self.select()

    def test_unexpected_directory_is_rejected_before_descent(self):
        (self.payload / 'other-runtime').mkdir()
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_PLATFORM_SUPPORT_DIRECTORY'): self.select()

    def test_compiler_perf_directory_must_be_empty_and_outside_classpaths(self):
        perf = self.payload / 'tmp/hsperfdata_fixture'; perf.mkdir()
        self.select()
        (perf / 'unexpected.class').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'EMPTY_SINGLE_COMPILER_PERF_DIRECTORY_REQUIRED'): self.select()

    def test_missing_class_is_rejected(self):
        (self.payload / next(iter(self.classes))).unlink()
        with self.assertRaisesRegex(ValueError, 'EXACT_PLATFORM_SUPPORT_OUTPUT_SET'): self.select()

    def test_changed_factories_is_rejected_even_with_matching_new_jar_and_receipt_pins(self):
        self.write_jar(b'fixture.unexpected.Listener=fixture.Other\n')
        self.receipt['observationJarSHA256'] = support.digest(self.jar); self.save_receipt()
        with self.assertRaisesRegex(ValueError, 'FACTORIES_MISMATCH'): self.select()

    def test_extra_jar_member_is_rejected_even_with_matching_new_jar_and_receipt_pins(self):
        with zipfile.ZipFile(self.jar, 'a') as archive: archive.writestr('fixture/Extra.class', b'changed')
        self.receipt['observationJarSHA256'] = support.digest(self.jar); self.save_receipt()
        with self.assertRaisesRegex(ValueError, 'EXACT_PLATFORM_SUPPORT_OBSERVATION_MEMBERS'): self.select()

    def test_failed_or_changed_class_proof_cannot_be_selected(self):
        self.receipt['passed'] = False; self.save_receipt()
        with self.assertRaisesRegex(ValueError, 'SUCCESSFUL_PLATFORM_SUPPORT_BUILD_REQUIRED'): self.select()
        self.receipt['passed'] = True; self.receipt['classSHA256'] = {}; self.save_receipt()
        with self.assertRaisesRegex(ValueError, 'CLASS_PROOF_MISMATCH'): self.select()

    def test_controller_rejects_corruption_during_helper_copy(self):
        root, proof = self.select(); destination = self.root / 'installed'; destination.mkdir()
        tree = ast.parse(Path(__file__).with_name('serve_original_integrated_candidate.py').read_text('utf-8'))
        loop = next(n for n in tree.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'directory')
        def corrupt_copy(source, target): Path(target).write_bytes(b'corrupted during copy')
        with self.assertRaisesRegex(AssertionError, 'OWN_INSTALLED_PLATFORM_HELPER_CHANGED'):
            exec(compile(ast.Module(body=[loop], type_ignores=[]), 'actual-controller-copy', 'exec'),
                 {'platform_support_root': root, 'platform_support_proof': proof, 'platform_root': destination,
                  'support_requested': True, 'shutil': types.SimpleNamespace(copyfile=corrupt_copy),
                  'os': os, 'sha': support.digest})

    def test_controller_rechecks_observation_jar_before_opening_it(self):
        root, proof = self.select()
        tree = ast.parse(Path(__file__).with_name('serve_original_integrated_candidate.py').read_text('utf-8'))
        check = next(n for n in tree.body if isinstance(n, ast.If) and any(isinstance(x, ast.Assert)
                     and isinstance(x.msg, ast.Constant) and x.msg.value == 'OWN_SELECTED_PLATFORM_OBSERVATION_CHANGED'
                     for x in n.body))
        self.jar.write_bytes(b'changed after selection')
        with self.assertRaisesRegex(AssertionError, 'OWN_SELECTED_PLATFORM_OBSERVATION_CHANGED'):
            exec(compile(ast.Module(body=[check], type_ignores=[]), 'actual-controller-jar-check', 'exec'),
                 {'platform_support_root': root, 'platform_support_proof': proof,
                  'support_requested': True, 'sha': support.digest})

    def test_integrated_bad_flags_fail_before_workspace_creation(self):
        workspace = self.root / 'must-not-be-created'
        command = [sys.executable, '-B', str(Path(__file__).with_name('serve_original_integrated_candidate.py')),
                   '--workspace', str(workspace), '--name', 'own-j999', '--previous-receipt', str(self.root / 'absent.json')]
        for flags, reason in [(['--platform-support-receipt', 'absent.json'], b'PLATFORM_SUPPORT_RECEIPT_AND_PIN_REQUIRED_TOGETHER'),
                              (['--platform-support-receipt', 'absent.json', '--platform-support-sha256', 'bad'], b'EXPLICIT_PLATFORM_SUPPORT_RECEIPT_PIN_REQUIRED')]:
            run = subprocess.run(command + flags, capture_output=True, timeout=8,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            self.assertNotEqual(run.returncode, 0); self.assertIn(reason, run.stderr)
            self.assertFalse(workspace.exists())


if __name__ == '__main__':
    unittest.main()
