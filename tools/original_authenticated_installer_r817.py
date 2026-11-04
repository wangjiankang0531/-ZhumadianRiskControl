"""Keep all original global components, load their installer after token gate."""
from contextlib import contextmanager
from pathlib import Path
import hashlib

GLOBAL='src/global-import.ts'
GUARD='src/router/index.ts'
EXTRA='src/OriginalAuthenticatedInstallerR817.ts'

def transform(files):
    original=files[GLOBAL].decode('utf8')
    guard=files[GUARD].decode('utf8')
    imports=['import ElementPlus from "element-plus/es";','import EleAdminPlus from "ele-admin-plus/es";']
    for line in imports:
        if original.count(line)!=1:raise ValueError('EXACT_FULL_COMPONENT_INSTALLER_REQUIRED')
    body='''    app.use(ElementPlus);
    app.use(EleAdminPlus);'''
    normalized=original.replace('\r\n','\n')
    if normalized.count(body)!=1:raise ValueError('EXACT_ORIGINAL_INSTALL_BODY_REQUIRED')
    lazy=normalized
    for line in imports:lazy=lazy.replace(line+'\n','')
    declaration='''let target: App | undefined;
let loading: Promise<void> | undefined;

// Share code loading only. User information, permissions and tokens remain uncached here.
export function ensureAuthenticatedComponents(): Promise<void> {
  if (!target) return Promise.reject(new Error("APPLICATION_INSTALLER_NOT_READY"));
  if (!loading) {
    loading = import("./OriginalAuthenticatedInstallerR817").then(({ default: installer }) => {
      target!.use(installer);
    }).catch(error => {
      loading = undefined;
      throw error;
    });
  }
  return loading;
}

'''
    marker='const installer: Plugin = {'
    if lazy.count(marker)!=1:raise ValueError('EXACT_PLUGIN_ANCHOR_REQUIRED')
    lazy=lazy.replace(marker,declaration+marker).replace(body,'    target = app;')
    dynamic='''/** Original complete global component registration, deferred until authenticated navigation. */
import type { App, Plugin } from "vue";
import ElementPlus from "element-plus/es";
import EleAdminPlus from "ele-admin-plus/es";

const installer: Plugin = {
  install(app: App) {
    app.use(ElementPlus);
    app.use(EleAdminPlus);
  }
};
export default installer;
'''
    anchor='import { routes, getMenuRoutes } from "./routes";'
    menu='  // 注册动态路由\n'
    guard=guard.replace('\r\n','\n')
    if guard.count(anchor)!=1 or guard.count(menu)!=1:raise ValueError('EXACT_ORIGINAL_AUTHENTICATED_GUARD_REQUIRED')
    guard=guard.replace(anchor,anchor+'\nimport { ensureAuthenticatedComponents } from "@/global-import";')
    guard=guard.replace(menu,'  await ensureAuthenticatedComponents();\n'+menu)
    return {GLOBAL:lazy.encode(),GUARD:guard.encode(),EXTRA:dynamic.encode()}

@contextmanager
def authenticated_installer_override(project):
    project=Path(project).absolute()
    assert project==Path('D:/Project/Zhumadian/work/user_feedback_20261031/event-research-level-r418/source')
    assert not (project/EXTRA).exists()
    for name in [GLOBAL,GUARD,EXTRA]:
        for p in [project/name,*(project/name).parents]:
            if p.exists():assert not p.lstat().st_file_attributes&0x400
    saved={name:(project/name).read_bytes()for name in [GLOBAL,GUARD]}
    after=transform(saved)
    proof={'sourceRestored':False,'anonymousTokenGatePreserved':True,'originalCompleteInstallerPreserved':True,
        'files':{name:{'before':hashlib.sha256(saved[name]).hexdigest()if name in saved else None,
            'after':hashlib.sha256(raw).hexdigest()}for name,raw in after.items()}}
    try:
        for name,raw in after.items():
            if name==EXTRA:
                with (project/name).open('xb')as out:out.write(raw)
            else:(project/name).write_bytes(raw)
        yield proof
    finally:
        for name,raw in after.items():assert (project/name).read_bytes()==raw,'FOREIGN_COMPONENT_INSTALLER_EDIT_REFUSED'
        for name,raw in saved.items():(project/name).write_bytes(raw)
        (project/EXTRA).unlink()
        proof['sourceRestored']=all((project/name).read_bytes()==raw for name,raw in saved.items())and not(project/EXTRA).exists()
