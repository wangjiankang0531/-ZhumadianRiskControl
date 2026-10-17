import tempfile,unittest,shutil,subprocess,sys
from pathlib import Path
import package_landscape_version as package

class PackageAtlasImports(unittest.TestCase):
    def test_staged_runtime_imports_all_recipes_without_developer_tools_directory(self):
        previous={'files':[{'path':'tools/native_texture_parts.py'},{'path':'tools/native_cache_policy.py'},{'path':'assets/not-copied.bin'}]}
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            for name in package.runtime_tool_names(previous):shutil.copy2(package.ROOT/'tools'/name,folder/name)
            code="import sys;sys.path.insert(0,sys.argv[1]);import native_atlas_recipe as r;assert r.policy()==r.LEGACY;assert r.layouts({'wide':(2048,512)},r.RECTANGULAR)[0][1]==(2048,520);assert r.layouts({'small':(512,512)},r.TIGHT)[0][1]==520"
            result=subprocess.run([sys.executable,'-I','-c',code,str(folder)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((folder/'assets').exists())

if __name__=='__main__':unittest.main()
