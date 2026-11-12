"""Retain the actual original nginx child handle in an already owned test Job."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path('D:/Project/Zhumadian');P=R/'Application/tools/experimental_source/client_resource_ingress_r2397/package'
sys.path.insert(0,str(P))
from services.layer_sync_bridge import process_creation
assert len(sys.argv)==3
root=Path(sys.argv[1]).absolute();configuration=Path(sys.argv[2]).absolute()
assert root.parent==Path('D:/Temp/Administrator/xnby-native-resource-r2405') and root.name in ('disabled','enabled')
assert configuration==root/'nginx.conf'
for p in [root,*root.parents]:assert not p.is_symlink()and not(getattr(p.lstat(),'st_file_attributes',0)&1024)
image=R/'_g/Application/runtime/nginx/nginx.exe'
assert hashlib.sha256(image.read_bytes()).hexdigest()=='c321bdc2a6eccdaad3c702e4da37e2f7bbfa4ffb3cabb9e70c586f5a5e95da44'
child=subprocess.Popen([str(image),'-p',root.as_posix()+'/', '-c',configuration.as_posix()],stdin=subprocess.DEVNULL,close_fds=True,creationflags=subprocess.CREATE_NO_WINDOW)
with(root/'actual-master.json').open('x',encoding='utf-8')as f:json.dump({'pid':child.pid,'creation':process_creation(child.pid)},f)
code=child.wait()
with(root/'actual-master-terminal.json').open('x',encoding='utf-8')as f:json.dump({'actualPopenExitCode':code,'forceTerminationUsed':False},f)
raise SystemExit(code)
