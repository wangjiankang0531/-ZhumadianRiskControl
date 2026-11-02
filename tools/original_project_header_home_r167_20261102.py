"""Use the project mark and canonical home route in an isolated emergency build."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
T=Path(__file__).resolve().parent
LAYOUT='src/layout/index.vue'
ROUTES='src/router/routes.ts'
ICON='src/assets/zhumadian-project-mark.svg'
EXPECTED={LAYOUT:'d9a6de5d165dfafd700fda2ad2b52194967e3fcf50a45f5b241c7e4ac663cea4',ROUTES:'9c0c32b7f523d0be3b4fd4a3dd55d5a0dbc8bfe96c64b6c4bf65a268ad751377'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def adapt_layout(raw):
 if sha(raw)!=EXPECTED[LAYOUT]:raise ValueError('EXACT_RETAINED_EMERGENCY_LAYOUT_REQUIRED')
 text=raw.decode('utf-8')
 old='<img src="@/assets/logo.png" style="width: 30px; height: 30px; cursor: pointer" @click="handleToHome" />'
 new='<img src="@/assets/zhumadian-project-mark.svg" alt="驻马店重大风险防控" title="返回首页" style="width: 30px; height: 30px; cursor: pointer" @click="handleToHome" />'
 if text.count(old)!=1 or text.count('push({ path: "/home" });')!=1:raise ValueError('EXACT_EMERGENCY_LOGO_AND_CLICK_REQUIRED')
 return text.replace(old,new,1).replace('push({ path: "/home" });','push({ path: "/home/index" });',1).encode('utf-8')
def adapt_routes(raw):
 if sha(raw)!=EXPECTED[ROUTES]:raise ValueError('EXACT_RETAINED_EMERGENCY_ROUTES_REQUIRED')
 text=raw.decode('utf-8');anchor='export const routes = ['
 if text.count(anchor)!=1:raise ValueError('EXACT_STATIC_ROUTES_REQUIRED')
 alias='\n  {\n    path: "/home",\n    redirect: to => ({ path: "/home/index", query: to.query, hash: to.hash })\n  },'
 return text.replace(anchor,anchor+alias,1).encode('utf-8')
@contextmanager
def project_header_override(project):
 project=Path(project).absolute()
 if project.resolve()!=project or not project.is_relative_to(Path('D:/Project/Zhumadian/work/user_feedback_20261031')):raise ValueError('ONLY_ISOLATED_EMERGENCY_BUILD_COPY')
 paths={n:project/n for n in [LAYOUT,ROUTES,ICON]}
 for p in [project,*paths.values()]:
  for q in [p,*p.parents]:
   if q.exists() and (q.is_symlink() or getattr(q.lstat(),'st_file_attributes',0)&0x400):raise ValueError('NO_REPARSE_BUILD_INPUT')
 before={n:paths[n].read_bytes() for n in [LAYOUT,ROUTES]}
 if paths[ICON].exists():raise ValueError('PROJECT_ICON_ALREADY_PRESENT')
 icon=(T.parent/'deploy/branding/zhumadian-emergency.svg').read_bytes()
 if sha(icon)!='509963a04f0b5187f6f8b5dbc53f650e44601bd563cc71656afcc606a24c7f9d':raise ValueError('PINNED_PROJECT_MARK_REQUIRED')
 after={LAYOUT:adapt_layout(before[LAYOUT]),ROUTES:adapt_routes(before[ROUTES]),ICON:icon}
 receipt={'files':{n:{'beforeSHA256':sha(before[n]) if n in before else None,'afterSHA256':sha(raw)}for n,raw in after.items()},'sourceRestored':False,'originalAuthAndMenusUnchanged':True}
 try:
  for n,raw in after.items():paths[n].write_bytes(raw)
  yield receipt
 finally:
  for n,raw in after.items():
   if paths[n].exists() and paths[n].read_bytes() not in [before.get(n),raw]:raise ValueError('FOREIGN_BUILD_DRIFT_REFUSE_RESTORE')
  for n,raw in before.items():paths[n].write_bytes(raw)
  paths[ICON].unlink(missing_ok=True)
  receipt['sourceRestored']=all(paths[n].read_bytes()==raw for n,raw in before.items()) and not paths[ICON].exists()
  if not receipt['sourceRestored']:raise ValueError('BUILD_INPUT_RESTORE_REQUIRED')
