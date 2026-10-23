"""Failure-oriented packaging checks; actual original Java startup is validated separately."""
from pathlib import Path
import tempfile
import unittest
from urllib.parse import unquote
import zipfile

import reference_flat_runtime as runtime


class FlatRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="own-flat-runtime-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.libs = self.root / "libraries with spaces"; self.libs.mkdir()
        self.dependency = self.libs / ("a-long-dependency-name-" * 4 + ".jar")
        with zipfile.ZipFile(self.dependency, "w") as jar:
            jar.writestr("own-canary.txt", b"fixture-only, no source data")
        self.source = self.root / "source.jar"
        self.app = {"sample/Main.class": b"fixture-main-not-executed", "config/default.properties": b"own=true\n", "sample/Other.class": b"fixture-other"}
        self.make_source()

    def make_source(self, extra=None, main="sample.Main"):
        with zipfile.ZipFile(self.source, "w") as jar:
            jar.writestr("META-INF/MANIFEST.MF", runtime.manifest_bytes({"Manifest-Version": "1.0", "Main-Class": "original.Loader", "Start-Class": main}))
            for name, body in self.app.items():jar.writestr(runtime.APP_PREFIX + name, body)
            jar.writestr(runtime.LIB_PREFIX + self.dependency.name, self.dependency.read_bytes())
            for name, body in (extra or {}).items():jar.writestr(name, body)

    def build(self, name="flat"):
        return runtime.build(self.source, self.libs, self.root / name, runtime.file_sha256(self.source))

    def test_preserves_all_classes_resources_dependency_order_without_copy(self):
        before = self.dependency.read_bytes(); r = self.build()
        self.assertEqual((r["compiledClassCount"], r["resourceCount"], r["dependencyCount"]), (2, 1, 1))
        self.assertEqual(r["dependencyFilesCopied"], 0)
        self.assertEqual(self.dependency.read_bytes(), before)
        self.assertFalse((self.root / "flat" / self.dependency.name).exists())
        with zipfile.ZipFile(self.root / "flat/application.jar") as flat:
            self.assertEqual([e.filename for e in flat.infolist() if not e.is_dir()], ["META-INF/MANIFEST.MF", *self.app])
            self.assertTrue(flat.getinfo("sample/").is_dir())
            self.assertTrue(flat.getinfo("config/").is_dir())
            for name, expected in self.app.items():self.assertEqual(flat.read(name), expected)
        self.assertTrue(runtime.verify(self.root / "flat")["allOriginalApplicationAndDependencyBytesEqual"])

    def test_manifest_uri_spaces_long_continuations_and_portable_main_class(self):
        self.build()
        with zipfile.ZipFile(self.root / "flat/application.jar") as flat:
            raw = flat.read("META-INF/MANIFEST.MF"); values = runtime.manifest_values(raw)
        self.assertTrue(all(len(line) + 2 <= 72 for line in raw.split(b"\r\n")))
        self.assertIn(b"\r\n ", raw)
        self.assertEqual(values["Main-Class"], "sample.Main")
        dep = (self.root / "flat" / unquote(values["Class-Path"])).resolve()
        self.assertEqual(dep, self.dependency.resolve())

    def test_reproducible_jar_bytes_across_two_sibling_output_directories(self):
        first = self.build("one"); second = self.build("two")
        self.assertEqual(first["applicationJarSHA256"], second["applicationJarSHA256"])

    def test_wrong_source_hash_refuses_before_output_creation(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_ARCHIVE_HASH_DIFFERS"):
            runtime.build(self.source, self.libs, self.root / "flat", "0" * 64)
        self.assertFalse((self.root / "flat").exists())

    def test_dependency_changed_before_build_is_rejected(self):
        self.dependency.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "DEPENDENCY_BYTES_DIFFER"):self.build()
        self.assertFalse((self.root / "flat").exists())

    def test_dependency_changed_after_build_is_rejected(self):
        self.build(); self.dependency.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "DEPENDENCY_BYTES_DIFFER"):runtime.verify(self.root / "flat")

    def test_corrupt_output_jar_is_rejected(self):
        self.build(); (self.root / "flat/application.jar").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "RUNTIME_OR_SOURCE_HASH_DIFFERS"):runtime.verify(self.root / "flat")

    def test_output_reuse_is_rejected(self):
        self.build()
        with self.assertRaisesRegex(FileExistsError, "OUTPUT_DIRECTORY_EXISTS"):self.build()

    def test_application_traversal_is_rejected(self):
        self.make_source({runtime.APP_PREFIX + "../outside.txt": b"own-fixture"})
        with self.assertRaisesRegex(ValueError, "UNSAFE_ARCHIVE_MEMBER"):self.build()

    def test_nested_dependency_directory_is_rejected(self):
        self.make_source({runtime.LIB_PREFIX + "nested/another.jar": b"own-fixture"})
        with self.assertRaisesRegex(ValueError, "UNEXPECTED_DEPENDENCY_MEMBER"):self.build()

    def test_missing_source_main_class_is_rejected(self):
        self.make_source(main="missing.Main")
        with self.assertRaisesRegex(ValueError, "SOURCE_START_CLASS_MISSING"):self.build()

    def test_application_manifest_cannot_overwrite_generated_manifest(self):
        self.make_source({runtime.APP_PREFIX + "META-INF/MANIFEST.MF": b"own-fixture"})
        with self.assertRaisesRegex(ValueError, "APPLICATION_MANIFEST_COLLISION"):self.build()

    def test_manifest_header_injection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "MANIFEST_CONTROL_CHARACTER"):
            runtime.manifest_bytes({"Main-Class": "sample.Main\r\nClass-Path: injected"})

    def test_parent_packages_exist_for_spring_style_resource_discovery(self):
        self.app["sample/deep/feature/Controller.class"] = b"fixture-controller"
        self.make_source(); self.build()
        with zipfile.ZipFile(self.root / "flat/application.jar") as flat:
            for name in ("sample/", "sample/deep/", "sample/deep/feature/", "META-INF/"):
                self.assertTrue(flat.getinfo(name).is_dir())


if __name__ == "__main__":
    unittest.main()
