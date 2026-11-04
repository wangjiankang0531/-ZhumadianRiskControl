"""Group only modules proven absent from the anonymous login static closure."""
from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent
R=Path('D:/Project/Zhumadian')
old=R/'work/authenticated-installer-full-r818'
mapped=R/'work/authenticated-installer-map-r828'
J=lambda p:json.loads(p.read_bytes())
a=J(old/'verified-bounded-full-build-r673.json');b=J(mapped/'verified-bounded-full-build-r673.json')
assert a['passed']and b['passed']and a['files']==b['files']
assert J(old/'actual-compiled-source-files.json')==J(mapped/'actual-compiled-source-files.json')
mapping=J(mapped/'emitted-modules.private.json')
analysis=J(V/'authenticated-installer-analysis-r819/result.json')
early=set(analysis['candidate']['loginClosure']['names'])
roots=[n for n in mapping if 'OriginalAuthenticatedInstallerR817' in n]
assert len(roots)==1
seen=set();stack=list(roots)
while stack:
    name=stack.pop()
    if name in seen:continue
    assert name in mapping
    seen.add(name);stack.extend(mapping[name]['imports'])
late=seen-early
earlyModules={m for n in early for m in mapping[n]['modules']}
lateModules={m for n in late for m in mapping[n]['modules']}
assert lateModules and not earlyModules&lateModules and len(late)>10
pin=hashlib.sha256((mapped/'emitted-modules.private.json').read_bytes()).hexdigest()
plan={'mappingSHA256':pin,'lateChunks':sorted(late),'lateModules':sorted(lateModules),
    'earlyModulesExcluded':True,'productSourcesUnchangedFromR818':True}
target=V/'grouped-installer-r829-plan.private.json';assert not target.exists();target.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf8')
source=(V/'run_authenticated_installer_full_build_r818.py').read_text(encoding='utf8')
source=source.replace('authenticated-installer-full-r818','authenticated-installer-grouped-r829').replace('authenticated_installer_full_build_r818_20261104','authenticated_installer_grouped_r829_20261104')
source=source.replace('build_authenticated_installer_bootstrap_r818.mjs','build_grouped_installer_bootstrap_r829.mjs').replace('verified-full-build-r818.json','verified-full-build-r829.json')
ast.parse(source);target=V/'run_grouped_installer_full_build_r829.py';assert not target.exists();target.write_text(source,encoding='utf8')
node=(V/'build_authenticated_installer_full_r818.mjs').read_text(encoding='utf8').replace('authenticated-installer-full-r818','authenticated-installer-grouped-r829')
setup=f'''
const groupedPlan=JSON.parse(await fs.readFile({json.dumps((V/'grouped-installer-r829-plan.private.json').as_posix())},'utf8'));
const mapRaw=await fs.readFile('D:/Project/Zhumadian/work/authenticated-installer-map-r828/emitted-modules.private.json');
const {{createHash}}=await import('node:crypto');
if(createHash('sha256').update(mapRaw).digest('hex')!=={json.dumps(pin)})throw Error('EXACT_ACTUAL_MODULE_MAP_REQUIRED');
const groupedModules=new Set(groupedPlan.lateModules),seenGroupedModules=new Set();
'''
anchor='await fs.symlink(deps,P+\'/node_modules\',\'junction\');'
assert node.count(anchor)==1;node=node.replace(anchor,setup+anchor)
anchor="rollupOptions:{output:{entryFileNames:"
replacement="rollupOptions:{output:{onlyExplicitManualChunks:true,manualChunks(id){if(groupedModules.has(id)){seenGroupedModules.add(id);return 'authenticated-components';}},entryFileNames:"
assert node.count(anchor)==1;node=node.replace(anchor,replacement)
anchor='await build({root:P,'
plugin="""await build({root:P,plugins:[{name:'verify-explicit-authenticated-module-group-r829',async generateBundle(_options,bundle){
 if(seenGroupedModules.size!==groupedModules.size)throw Error('ALL_ACTUAL_LATE_MODULES_MUST_MATCH');
 const rows={};for(const [name,c] of Object.entries(bundle))if(c.type==='chunk')rows[name]={imports:c.imports,dynamicImports:c.dynamicImports,modules:Object.keys(c.modules)};
 const grouped=Object.values(rows).filter(r=>r.modules.some(m=>groupedModules.has(m)));
 if(grouped.length!==1||grouped[0].modules.some(m=>!groupedModules.has(m)))throw Error('EXACT_EXPLICIT_LATE_GROUP_REQUIRED');
 await fs.writeFile(W+'/emitted-modules.private.json',JSON.stringify(rows,null,2)+'\\n',{flag:'wx'});
 await fs.writeFile(W+'/grouping-proof.json',JSON.stringify({passed:true,lateModuleCount:groupedModules.size,sourceLateChunkCount:groupedPlan.lateChunks.length,groupedChunks:1,earlyModulesMoved:false,onlyExplicitManualChunks:true})+'\\n',{flag:'wx'});
}}],"""
assert node.count(anchor)==1;node=node.replace(anchor,plugin)
target=V/'build_grouped_installer_full_r829.mjs';assert not target.exists();target.write_text(node,encoding='utf8')
boot=(V/'build_authenticated_installer_bootstrap_r818.mjs').read_text(encoding='utf8').replace('build_authenticated_installer_full_r818.mjs','build_grouped_installer_full_r829.mjs')
target=V/'build_grouped_installer_bootstrap_r829.mjs';assert not target.exists();target.write_text(boot,encoding='utf8')
print(json.dumps({'prepared':True,'sameSourceAndArtifactMappingBuildVerified':True,'lateChunks':len(late),'lateModules':len(lateModules),'earlyModuleOverlap':False}))
