'''Read-only structural inventory for all delivered Tianjin frontends and backend.

Static extraction is a navigation aid, never evidence of runtime parity.
Does not execute reference code, load .env/application configuration, or make HTTP requests.
'''
import argparse,csv,hashlib,json,re
from collections import Counter
from pathlib import Path

BASE='02安全风险管控平台/代码及开发环境搭建移交资料/源码包'
PROJECTS={
 'safety':BASE+'/安全风险管控平台前台代码/security-risk-web',
 'emergency':BASE+'/敏捷应急管理前台代码/agile-emergency-response-dev',
 'mobile':BASE+'/移动端前端代码whwly-mobile/whwly-mobile',
 'screen':'03敏捷应急大屏/tjwhbigscreen'}
JAVA=BASE+'/后端代码/后端源码-maven/cloud-endanger/src/main/java'
SKIP={'node_modules','.git','__MACOSX','dist','target','uni_modules','lib','es','logs'}
IMPORT=re.compile(r'''from\s*["']([^"']+)["']|import\s*\(\s*(?:/\*.*?\*/\s*)?["']([^"']+)["']''',re.S)

def files(root,suffixes):
 return sorted(p for p in root.rglob('*') if p.is_file() and p.suffix in suffixes and not SKIP.intersection(p.relative_to(root).parts))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def unique(items):return list(dict.fromkeys(items))
def clean(value):return re.sub(r'\s+',' ',re.sub('<[^>]+>','',value)).strip()
def resolve(root,path,imp):
 if imp.startswith('@/'):p=root/'src'/imp[2:]
 elif imp.startswith('.'):p=path.parent/imp
 else:return None
 for q in [p,*[p.with_suffix(x) for x in ('.ts','.js','.vue')],p/'index.ts',p/'index.js',p/'index.vue']:
  try:q=q.resolve();q.relative_to(root.resolve())
  except ValueError:continue
  if q.is_file():return q
 return None
def extract(p,root):
 text=p.read_text('utf-8-sig');labels=[];buttons=[];models=[];events=[];imports=[]
 for n,line in enumerate(text.splitlines(),1):
  for m in re.finditer(r'''(?<![:\w-])(?:label|title|placeholder)\s*=\s*["']([^"']+)["']|(?:label|title)\s*:\s*["']([^"']+)["']''',line):
   label=m[1] or m[2]
   if '{{' not in label:labels.append(dict(text=label,line=n))
  for m in re.finditer(r'''v-model(?::[\w-]+)?(?:\.[\w]+)*\s*=\s*["']([^"']+)["']''',line):models.append(dict(binding=m[1],line=n))
  for m in re.finditer(r'''@(?:click|submit|change|confirm)[\w.:-]*\s*=\s*["']([^"']+)["']''',line):events.append(dict(handler=m[1],line=n))
 for m in re.finditer(r'<(?:el-button|wd-button|button|uni-button)\b[^>]*>(.*?)</(?:el-button|wd-button|button|uni-button)>',text,re.S):
  value=clean(m[1])
  if value and '{{' not in value:buttons.append(dict(text=value,line=text.count('\n',0,m.start())+1))
 for m in IMPORT.finditer(text):
  imp=m[1] or m[2];target=resolve(root,p,imp)
  imports.append(dict(specifier=imp,local=target.relative_to(root).as_posix() if target else None))
 return dict(path=p.relative_to(root).as_posix(),sha256=sha(p),labels=labels,buttons=buttons,models=models,events=events,imports=imports)

def audit(reference,out):
 out.mkdir(parents=True,exist_ok=True);projects={};rows=[]
 for code,directory in PROJECTS.items():
  root=reference/directory;allfiles=files(root/'src',{'.ts','.js','.tsx','.jsx','.vue'})
  bypath={p.resolve():extract(p,root) for p in allfiles}
  for p,item in bypath.items():
   item['apiEndpoints']=[]
   if any(part in ('api','service') for part in p.relative_to(root).parts):
    text=p.read_text('utf-8-sig')
    for m in re.finditer(r'''(?:\b(?:request|http)\.(get|post|put|delete|patch|download)(?:<[^;\n]*?>)?\s*\(\s*|\burl\s*:\s*)["'`](/[^"'`\r\n]*)["'`]''',text):
     # Only local endpoint patterns. Never preserve absolute URLs, query values or config secrets.
     route=m[2].split('?')[0]
     if not route.startswith('//'):item['apiEndpoints'].append(dict(method=('GET' if m[1]=='download' else m[1].upper()) if m[1] else 'SEE_SOURCE',transport=m[1] or 'SEE_SOURCE',path=route,line=text.count('\n',0,m.start())+1))
   if p.suffix=='.vue' and any(part in ('views','pages','pages-sub') for part in p.relative_to(root).parts):
    pending=[p];seen=set();apis=[];related=[]
    while pending:
     q=pending.pop()
     if q in seen:continue
     seen.add(q);node=bypath.get(q)
     if not node:continue
     if q!=p:related.append(node['path'])
     if any(x in ('api','service') for x in q.relative_to(root).parts):apis.append(node['path'])
     for imp in node['imports']:
      if imp['local']:pending.append((root/imp['local']).resolve())
    item['relatedLocalSources']=sorted(related);item['transitiveApiSources']=sorted(apis)
    rows.append(dict(system=code,source=item['path'],fields=' | '.join(unique(x['text'] for x in item['labels'])),buttons=' | '.join(unique(x['text'] for x in item['buttons'])),bindings=len(item['models']),apiFiles=' | '.join(sorted(apis)),sourceSha256=item['sha256'],liveObserved='待逐页核对',visualParity='未验收',functionalParity='未验收',backendParity='未验收'))
  projects[code]=dict(root=directory,sourceFiles=len(bypath),vueFiles=sum(p.suffix=='.vue' for p in bypath),viewComponents=sum(x['system']==code for x in rows),files=list(bypath.values()))
 controllers=[];entities=[];javafiles=files(reference/JAVA,{'.java'})
 for p in javafiles:
  text=p.read_text('utf-8-sig');rel=p.relative_to(reference).as_posix()
  if '@RestController' in text or '@Controller' in text:
   routes=[]
   for m in re.finditer(r'@(Request|Get|Post|Put|Delete|Patch)Mapping\s*\((.*?)\)',text,re.S):
    values=re.findall(r'"([^"\r\n]*)"',m[2]);routes.append(dict(annotation=m[1],paths=values,line=text.count('\n',0,m.start())+1))
   controllers.append(dict(path=rel,sha256=sha(p),mappings=routes,services=unique(re.findall(r'\b(\w+Service)\s+\w+\s*;',text))))
  tables=re.findall(r'@TableName\s*\(\s*"([^"\r\n]+)"',text)
  if tables:entities.append(dict(path=rel,tables=tables,sha256=sha(p),fields=re.findall(r'\bprivate\s+[\w<>?, .]+\s+(\w+)\s*;',text)))
 docs=[]
 for p in sorted(reference.rglob('*.docx')):
  if not SKIP.intersection(p.relative_to(reference).parts):docs.append(dict(path=p.relative_to(reference).as_posix(),sha256=sha(p)))
 result=dict(schema='xnby.tianjin.reference.inventory.v1',method='static metadata extraction, not semantic or runtime proof',projects=projects,backend=dict(javaFiles=len(javafiles),controllers=controllers,tableEntities=entities),documents=docs)
 (out/'source_inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 with (out/'page_acceptance_matrix.csv').open('w',encoding='utf-8-sig',newline='') as stream:
  writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 summary=dict(projects={k:{key:v[key] for key in ('sourceFiles','vueFiles','viewComponents')} for k,v in projects.items()},javaFiles=len(javafiles),controllers=len(controllers),tableEntities=len(entities),documents=len(docs),pageComponents=len(rows),runtimeParityVerified=0)
 (out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 return summary
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();print(json.dumps(audit(args.reference,args.out),ensure_ascii=False,indent=2))
