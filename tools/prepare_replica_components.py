"""Rebuild original dedicated components locally, without source .env or GIS.

Run npm ci --ignore-scripts with the generated pinned package-lock, then
node node_modules/vite/bin/vite.js build --config vite.candidate.ts.
This prepares code only; it does not start servers, create users or publish.
"""
from pathlib import Path
import hashlib,json,re,shutil
import argparse
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--reference-project',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
A=Path(__file__).resolve().parents[1];ref=args.reference_project.resolve();R=ref.parent;W=args.output.resolve();E=W/'evidence'
if W.exists() or W==ref or ref.is_relative_to(W) or W.is_relative_to(ref):raise ValueError('Use a fresh output outside the reference source')
W.mkdir(parents=True);E.mkdir()

project=W/'safety';project.mkdir();records=[]
for directory in ['src','components','public','typings']:
 source=ref/directory
 if not source.exists():continue
 for p in source.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(ref)
  if {'node_modules','.git','__MACOSX','map','maps','GIS'}.intersection(rel.parts) or p.suffix.lower() in ('.exe','.dll','.sqlite','.db','.osgb','.las','.laz','.zip','.map') or p.name.startswith('.env') or rel.as_posix()=='public/qrcode.png':continue
  target=project/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
  records.append(dict(path=rel.as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
shutil.copy2(ref/'index.html',project/'index.html')
# Explicit local build configuration. Never load the reference .env or copy its API/map credentials.
p=project/'src/config/setting.ts';setting=p.read_text('utf-8');setting=re.sub(r'export const MAP_KEY\s*=\s*[^;]+;',"export const MAP_KEY = '';",setting);p.write_text(setting,encoding='utf-8')
package=json.loads((ref/'package.json').read_text('utf-8'));lock=(ref/'pnpm-lock.yaml').read_text('utf-8').split('\npackages:')[0]
versions={};name=None
for line in lock.splitlines():
 m=re.match(r'      ([^ ].*):$',line)
 if m:name=m[1].strip("'\"")
 m=re.match(r'        version: (.+)$',line)
 if m and name:versions[name]=m[1].strip("'\"").split('(')[0]
skip={'eslint','eslint-config-prettier','eslint-plugin-prettier','eslint-plugin-vue','prettier','vue-eslint-parser','vue-tsc','rimraf','execa','esno','vite-plugin-dts'}
dependencies={name:versions[name] for name in package['devDependencies'] if name not in skip and not name.startswith('@typescript-eslint/')}
assert all(re.fullmatch(r'\d+\.\d+\.\d+(?:-[\w.]+)?',v) for v in dependencies.values())
(project/'package.json').write_text(json.dumps(dict(name='xnby-reference-component-candidate',version='0.0.0',private=True,type='module',dependencies=dependencies),indent=2),encoding='utf-8')
config='''import {defineConfig} from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import Components from 'unplugin-vue-components/vite';
import {ElementPlusResolver} from 'unplugin-vue-components/resolvers';
import {EleAdminResolver} from './components/utils/resolvers';
const root=fileURLToPath(new URL('.',import.meta.url));
export default defineConfig({root,base:'/safety/',envDir:resolve(root,'isolated-empty-environment'),
resolve:{alias:{'ele-admin-plus/es':resolve(root,'components'),'ele-admin-plus':resolve(root,'components'),'@/':resolve(root,'src')+'/', 'vue-i18n':'vue-i18n/dist/vue-i18n.cjs.js','./as-needed':'./global-import'}},
plugins:[vue(),vueJsx(),Components({dts:false,resolvers:[ElementPlusResolver({importStyle:'sass'}),EleAdminResolver({importStyle:'sass'})]})],
define:{'import.meta.env.VITE_API_URL':JSON.stringify('/replica-api'),'import.meta.env.VITE_APP_NAME':JSON.stringify('驻马店重大风险防控'),'import.meta.env.VITE_APP_BASE_PATH':JSON.stringify('/safety/'),'import.meta.env.VITE_ORG_ID':JSON.stringify('zhumadian-project'),'import.meta.env.VITE_FILE_BUCKET':JSON.stringify('project-materials'),'import.meta.env.VITE_FILE_BUCKET_KM':JSON.stringify('project-materials')},
css:{preprocessorOptions:{scss:{additionalData:'@use "@/styles/variables.scss" as *;'}}},
build:{outDir:resolve(root,'dist'),emptyOutDir:false,sourcemap:false,reportCompressedSize:false},
server:{host:'127.0.0.1',fs:{strict:true},headers:{'Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; frame-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'"}}
});
'''
(project/'vite.candidate.ts').write_text(config,encoding='utf-8')
manifest=dict(reference=ref.relative_to(R).as_posix(),files=records,copiedFiles=len(records),bytes=sum(r['bytes'] for r in records),dependencyVersions=dependencies,sourcePackageSha256=hashlib.sha256((ref/'package.json').read_bytes()).hexdigest(),sourceLockSha256=hashlib.sha256((ref/'pnpm-lock.yaml').read_bytes()).hexdigest(),originalSourceModified=False,referenceEnvironmentCopied=False,mapCredentialCopied=False,licenseChecksRemoved=False,referenceGISIncluded=False,built=False,runtimeAccepted=False,productionDeployed=False)
(E/'source_snapshot_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(project=str(project),files=len(records),bytes=manifest['bytes'],dependencies=len(dependencies),environment='isolated local candidate, no reference .env'),ensure_ascii=False))


P=project
home=P/'src/views/home/index.vue';content=home.read_text('utf-8').replace('天津南港危化品智慧物流综合服务中心','驻马店高新开发区重大风险防控').replace('/qrcode.png','/home-access-qr.svg');home.write_text(content,encoding='utf-8')
shutil.copyfile(A/'web/src/home-access-qr.svg',P/'public/home-access-qr.svg')
# Replace reference organization branding with a project-owned code-native mark.
logo=P/'src/assets/xnby-logo.svg';logo.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><path fill="#7de1ea" d="M4 7h11l21 26H25z"/><path fill="#a9bfff" d="M25 7h11L15 33H4z"/><path fill="white" d="m14 20 6-7 6 7-6 7z"/></svg>',encoding='utf-8')
layout=P/'src/layout/index.vue';layout.write_text(layout.read_text('utf-8').replace('@/assets/logo.png','@/assets/xnby-logo.svg'),encoding='utf-8')
shutil.copyfile(A/'deploy/reference_components/package-lock.json',P/'package-lock.json')

changes=[]
def edit(rel,old,new):
 p=P/rel;s=p.read_text('utf-8');assert old in s,(rel,old[:60]);s=s.replace(old,new);p.write_text(s,encoding='utf-8');changes.append(rel)
token='''/** Local candidate uses a real HttpOnly server session. This readable nonce
 * is CSRF only; it cannot authenticate without the independent session cookie. */
export function getToken(): string | null {
 const part=document.cookie.split('; ').find(v=>v.startsWith('XNBY_REPLICA_CSRF='));
 return part ? decodeURIComponent(part.slice('XNBY_REPLICA_CSRF='.length)) : null;
}
export function setToken() { throw new Error('Use the candidate server login'); }
export function removeToken() { document.cookie='XNBY_REPLICA_CSRF=; Path=/; Max-Age=0; SameSite=Strict'; }
'''
(P/'src/utils/token-util.ts').write_text(token,encoding='utf-8');changes.append('src/utils/token-util.ts')
edit('src/utils/request.ts','config.headers["Authorization"] = token;','config.headers["X-XNBY-CSRF"] = token;')
edit('src/utils/request.ts','const msg = error.response.data.message || error.response.data.msg;','if (error.response?.status === 401) window.location.assign("/candidate/login");\n        const msg = error.response?.data?.message || error.response?.data?.msg || "请求失败";')
api='''import request from "@/utils/request";
const base="/serv/riskLevel/";
const keys=new WeakMap<object,string>();
function command(params) {
 let key=keys.get(params); if (!key) {key=crypto.randomUUID().replaceAll("-",""); keys.set(params,key);}
 return {headers:{"Idempotency-Key":key}};
}
const fields=["department","departmentId","person","personId","analysisObject","analysisUnit","riskLevel","coordinate","coordinateSystem"];
function form(params,edit=false) { const result=Object.fromEntries(fields.filter(k=>params[k]!==undefined).map(k=>[k,params[k]])); if(edit){result.id=params.id;result.revision=params.revision;}return result; }
export const getPage=params=>request.get(base+"getPage",params);
export const getById=params=>request.get(base+"getById",params);
export const save=params=>request.post(base+"save",form(params),command(params));
export const updateById=params=>request.post(base+"updateById",form(params,true),command(params));
export const removeById=params=>request.post(base+"removeById",params,command(params));
export const exportExcel=params=>request.download(base+"export",params);
export const importExcel=params=>request.post(base+"importExcel",params);
export const downloadTemplate=()=>request.download(base+"getModel");
'''
(P/'src/api/hiddenInvestigate/riskAnalysisUnit/index.ts').write_text(api,encoding='utf-8');changes.append('src/api/hiddenInvestigate/riskAnalysisUnit/index.ts')
edit('src/views/hiddenInvestigate/riskAnalysisUnit/index.vue','{ id: params.id },','{ id: params.id, revision: params.revision },')
form='src/views/hiddenInvestigate/riskAnalysisUnit/info/addOrEdit.vue'
edit(form,'v-model="field.department"','v-model="field.departmentId"')
edit(form,"value: 'fullName'","value: 'id'")
edit(form,'v-model="field.person" placeholder="请选择" clearable filterable','v-model="field.personId" placeholder="请选择" clearable filterable @change="id => field.person = userList.find(x => x.id === id)?.realName"')
edit(form,':value="item.realName"',':value="item.id"')
edit(form,'if (item.fullName === fullName)','if (item.id === fullName)')
edit(form,'const departmentChange = val => {','const departmentChange = val => {\n  field.value.department = findObjectByFullName(orgTree.value,val)?.fullName;\n  field.value.person = undefined; field.value.personId = undefined;')
edit(form,'findObjectByFullName(orgTree.value, field.value.department)','findObjectByFullName(orgTree.value, field.value.departmentId)')
edit(form,'department: userStore.authDeptName','department: userStore.authDeptName, departmentId: userStore.authDeptId')
edit(form,'departmentChange(field.value.department);','departmentChange(field.value.departmentId);')
# Do not silently present the reference Tianjin map as a Zhumadian map.
# Map adapter remains unchanged and unaccepted; source GIS has not been copied.
(E/'component_adapter_manifest.json').write_text(json.dumps({'files':[{'path':r,'sha256':hashlib.sha256((P/r).read_bytes()).hexdigest()} for r in sorted(set(changes))],'mapAdapted':False,'fullParity':False,'productionDeployed':False},ensure_ascii=False,indent=2),encoding='utf-8')


edit('src/layout/components/header-notice.vue',':value="total" :hidden="false"',':value="total" :hidden="!!loadError"')
edit('src/layout/components/header-notice.vue','description="已完成所有任务"',':description="loadError || \'已完成所有任务\'"')
edit('src/layout/components/header-notice.vue','const total = ref(0);',"const total = ref(0);\nconst loadError = ref('待办接口加载中');\nlet unsupported = false;")
edit('src/layout/components/header-notice.vue','query();\nlet timer = setInterval(query, 1000 * 60);',"const refresh = async () => {\n  if (unsupported) return;\n  try { await query(); loadError.value = ''; }\n  catch (error: any) {\n    unsupported = error.response?.status === 501;\n    loadError.value = unsupported ? '待办接口尚未适配' : '待办加载失败，请稍后重试';\n  }\n};\nrefresh();\nlet timer = setInterval(refresh, 1000 * 60);")

# Final adapter receipt includes metadata/branding and late error-handling edits.
original={item['path']:item['sha256'] for item in records}
candidate_paths=[p for folder in ('src','components','public','typings') for p in (project/folder).rglob('*') if p.is_file()]
candidate_paths += [project/name for name in ('index.html','package.json','package-lock.json','vite.candidate.ts')]
adapted=[dict(path=p.relative_to(project).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in candidate_paths if original.get(p.relative_to(project).as_posix())!=hashlib.sha256(p.read_bytes()).hexdigest()]
(E/'component_adapter_manifest.json').write_text(json.dumps(dict(files=adapted,mapAdapted=False,fullParity=False,productionDeployed=False),ensure_ascii=False,indent=2),encoding='utf-8')
