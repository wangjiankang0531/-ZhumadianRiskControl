import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from portable_source_runtime import (SCHEMA, BINDING, PAYLOAD_DIRS, load_package,
                                     payload_name, ReadOnlySourceGuard, ready_path, object_pairs, initialize_user_layers, publish_owner_ready)

class RuntimePackage(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="zmd_portable_runtime_")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base/"package with spaces"
        self.root.mkdir()
        for name in PAYLOAD_DIRS:
            (self.root/name).mkdir()
        self.data = self.base/"installed GIS"/"Data"
        self.data.mkdir(parents=True)
        self.reader = self.root/"reader/zmd_osgb_stream_reader.exe"
        self.reader.write_bytes(b"not executable, manifest fixture only")
        raw = self.reader.read_bytes()
        self.manifest = {"schema":SCHEMA, "files":{"reader/zmd_osgb_stream_reader.exe":
            {"bytes":len(raw), "sha256":hashlib.sha256(raw).hexdigest()}},
            "readerFiles":{"zmd_osgb_stream_reader.exe":hashlib.sha256(raw).hexdigest()}}
        self.binding = {"schema":BINDING, "dataRoot":os.path.relpath(self.data, self.root)}
        self.save()
    def save(self):
        (self.root/"source_runtime_manifest.json").write_text(json.dumps(self.manifest), encoding="utf8")
        (self.root/"source_runtime_binding.json").write_text(json.dumps(self.binding), encoding="utf8")
    def test_manifest_and_external_relative_binding_survive_spaces(self):
        package = load_package(self.root)
        self.assertEqual(package["data"], self.data.resolve())
        self.assertEqual(package["root"], self.root.resolve())
    def test_regular_rejects_wrong_kind_from_authoritative_attributes(self):
        from portable_source_runtime import regular
        self.assertEqual(regular(self.reader,self.root),self.reader)
        for path,directory in ((self.reader,True),(self.root,False)):
            with self.assertRaisesRegex(ValueError,"path kind"):
                regular(path,self.root,directory=directory)

    def test_regular_refuses_symlink_and_windows_reparse_attributes(self):
        from portable_source_runtime import regular
        from unittest.mock import patch
        from types import SimpleNamespace
        import stat
        for mode,attributes in ((stat.S_IFLNK,0),(stat.S_IFDIR,0x400)):
            fact=SimpleNamespace(st_mode=mode,st_file_attributes=attributes)
            with patch("portable_source_runtime.Path.lstat",return_value=fact):
                with self.assertRaisesRegex(ValueError,"linked runtime"):
                    regular(self.reader,self.root)

    def test_modified_payload_is_refused(self):
        self.reader.write_bytes(b"corrupted")
        with self.assertRaisesRegex(ValueError, "identity differs"):
            load_package(self.root)
    def test_extra_payload_code_is_refused(self):
        (self.root/"application/unlisted.py").write_text("raise RuntimeError('must not import')")
        with self.assertRaisesRegex(ValueError, "unexpected or missing"):
            load_package(self.root)
    def test_reader_manifest_mismatch_is_refused(self):
        self.manifest["readerFiles"]["zmd_osgb_stream_reader.exe"] = "0"*64
        self.save()
        with self.assertRaisesRegex(ValueError, "reader identity"):
            load_package(self.root)
    def test_unbounded_and_bool_file_sizes_are_refused(self):
        for size in (True, -1, 512*1048576+1):
            self.manifest["files"]["reader/zmd_osgb_stream_reader.exe"]["bytes"] = size
            self.save()
            with self.assertRaises(ValueError):
                load_package(self.root)
    def test_binding_must_select_data_and_cannot_cover_package_root(self):
        for binding in (str(self.root), str(self.base), ""):
            self.binding["dataRoot"] = binding
            self.save()
            with self.assertRaises(ValueError):
                load_package(self.root)
    def test_wrong_schema_or_extra_binding_keys_are_refused(self):
        for update in ({"schema":"other"}, {"unexpected":True}):
            self.binding = {"schema":BINDING, "dataRoot":str(self.data), **update}
            self.save()
            with self.assertRaises(ValueError):
                load_package(self.root)
    def test_payload_paths_cannot_escape_or_become_mutable_user_data(self):
        for name in ("../reader.exe", "reader/../x", "reader/", "/reader/x", "reader\\x",
                     "reader/x:y", "UserData/code.py", "reader/a\n.py", "C:/file.exe"):
            with self.assertRaises(ValueError):
                payload_name(name)
        self.assertEqual(payload_name("resources/企业/icon.png"), "resources/企业/icon.png")
    def test_duplicate_json_keys_are_refused(self):
        with self.assertRaises(ValueError):
            object_pairs([("schema",1),("schema",2)])
    def test_owner_ready_identity_is_exclusive_and_user_data_is_separate(self):
        name = "a"*32
        path = ready_path(self.root, name)
        self.assertEqual(path, self.root/"UserData/Run"/(name+".json"))
        path.write_text("{}")
        with self.assertRaises(FileExistsError):
            ready_path(self.root, name)
        self.assertEqual(load_package(self.root)["data"], self.data.resolve())
        for name in ("../escape", "b"*31, "Z"*32):
            with self.assertRaises(ValueError):
                ready_path(self.root, name)
    def test_user_layers_copy_once_and_keep_all_edits_after_restart(self):
        document = {"schema":"hongtu.landscape.layers.v1", "scene":"zhumadian",
            "coordinates":{"srs":"EPSG:32650", "unit":"metre", "axes":"east,north,up", "origin":[0,0,0]},
            "layers":[]}
        source = self.root/"defaults/editor_layers.json"
        source.write_text(json.dumps(document), encoding="utf8")
        target = initialize_user_layers(self.root)
        self.assertEqual(json.loads(target.read_text()), document)
        document["layers"].append({"id":"user", "name":"My edited layer", "features":[]})
        edited = json.dumps(document).encode()
        target.write_bytes(edited)
        self.assertEqual(initialize_user_layers(self.root).read_bytes(), edited)
        self.assertEqual(json.loads(source.read_text())["layers"], [])
    def test_invalid_existing_user_layers_are_preserved_and_reported(self):
        (self.root/"UserData").mkdir()
        target = self.root/"UserData/layers.json"
        target.write_bytes(b"not JSON; keep for diagnosis")
        with self.assertRaises(ValueError):
            initialize_user_layers(self.root)
        self.assertEqual(target.read_bytes(), b"not JSON; keep for diagnosis")
    def test_readonly_guard_blocks_real_source_targets_and_other_processes(self):
        guard = ReadOnlySourceGuard(load_package(self.root))
        for event,args in (("open",(str(self.data/"source.osgb"),"wb",os.O_WRONLY)),
                           ("open",(str(self.reader),"r+b",os.O_RDWR)),
                           ("os.rename",(str(self.data/"a"),str(self.data/"b"))),
                           ("subprocess.Popen",(str(self.root/"other.exe"),))):
            with self.assertRaises(PermissionError):
                guard(event,args)
        guard("open",(str(self.data/"source.osgb"),"rb",os.O_RDONLY))
        guard("open",(str(self.root/"UserData/Run/log.txt"),"wb",os.O_WRONLY))
        guard("subprocess.Popen",(str(self.reader),))
        self.assertEqual(len(guard.violations),4)


    def test_ready_publication_is_complete_before_concurrent_reader_can_open_it(self):
        import threading,time
        from unittest.mock import patch
        target=ready_path(self.root,'d'*32);started=threading.Event();errors=[]
        result={'state':'ready','launchId':'d'*32,'preflight':{'values':list(range(32))}}
        def slow_dump(value,stream,**kwargs):
            for chunk in json.JSONEncoder(indent=2).iterencode(value):
                stream.write(chunk);stream.flush();started.set();time.sleep(.001)
        def writer():
            try:publish_owner_ready(target,result)
            except BaseException as error:errors.append(error)
        with patch('portable_source_runtime.json.dump',slow_dump):
            thread=threading.Thread(target=writer);thread.start();self.assertTrue(started.wait(2))
            self.assertFalse(target.exists())
            observations=0
            while thread.is_alive():
                if target.exists():
                    self.assertEqual(json.loads(target.read_text('utf8')),result);observations+=1
                time.sleep(.001)
            thread.join()
        self.assertFalse(errors);self.assertEqual(json.loads(target.read_text('utf8')),result)
        self.assertFalse(target.with_name(target.stem+'.ready.pending.json').exists())
    def test_ready_publication_never_overwrites_existing_or_interrupted_owner_state(self):
        target=ready_path(self.root,'e'*32);target.write_bytes(b'previous run retained')
        with self.assertRaises(FileExistsError):publish_owner_ready(target,{'state':'ready'})
        self.assertEqual(target.read_bytes(),b'previous run retained');target.unlink()
        pending=target.with_name(target.stem+'.ready.pending.json');pending.write_bytes(b'interrupted retained')
        with self.assertRaises(FileExistsError):publish_owner_ready(target,{'state':'ready'})
        self.assertFalse(target.exists());self.assertEqual(pending.read_bytes(),b'interrupted retained')


if __name__ == "__main__":
    unittest.main()
