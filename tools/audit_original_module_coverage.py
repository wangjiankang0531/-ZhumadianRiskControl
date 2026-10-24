"""Audit sealed menu/source coverage without treating metadata as role or business parity."""
import argparse
import collections
import datetime
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import time

FIELDS={
 'base_module':['f_id','f_parent_id','f_type','f_full_name','f_url_address','f_system_id','f_enabled_mark','f_delete_mark','f_visible'],
 'base_system':['f_id','f_full_name','f_en_code','f_enabled_mark','f_delete_mark'],
 'base_db_link':['f_id','f_db_type','f_host','f_port','f_service_name','f_db_schema','f_delete_mark'],
 'base_visual_dev':['f_id','f_db_link_id','f_enabled_mark','f_delete_mark'],
}
PROJECTS={'safety':'security_pc','emergency':'emergency_pc'}
CAPTURES={'original_menu_source_matrix.json':'security_pc','042_remaining_modules_menu_source_matrix.json':'security_pc','040_safety_basic_menu_source_matrix.json':'security_pc','038_emergency_menu_source_matrix.json':'emergency_pc'}
def require(value,code):
 if not value:raise ValueError(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def signature(value):return digest((value or '').encode('utf-8'))
def active(row):return row['f_enabled_mark']=='1' and row['f_delete_mark'] in (None,'0')
def views(root,component):
 """Match the original router's two index.vue lookups; never follow an external path."""
 if not isinstance(component,str) or not component.startswith('/') or component.startswith('//'):return []
 if any(x in component for x in ('\\','?','#',':','%')) or '..' in PurePosixPath(component).parts:return []
 viewroot=(Path(root)/'src/views').resolve(strict=True);result=[]
 for suffix in ('.vue','/index.vue'):
  candidate=viewroot/(component.lstrip('/')+suffix)
  if candidate.is_file():
   resolved=candidate.resolve(strict=True);require(resolved.is_relative_to(viewroot),'VIEW_ESCAPES_SOURCE')
   result.append({'path':candidate.relative_to(Path(root)).as_posix(),'sha256':digest(candidate.read_bytes())})
 return result

def report(rows,captures,roots):
 systems={r['f_id']:r for r in rows['base_system']};seen=collections.defaultdict(list)
 modules_by_id={r['f_id']:r for r in rows['base_module']}
 def ancestry(row):
  visited={row['f_id']};parent=row.get('f_parent_id')
  while parent not in (None,'','-1','0'):
   if parent in visited:return 'cycle'
   visited.add(parent);ancestor=modules_by_id.get(parent)
   if ancestor is None:return 'missing_parent'
   if not active(ancestor):return 'inactive_parent'
   parent=ancestor.get('f_parent_id')
  return 'active_ancestry'
 for project,entries in captures:
  for entry in entries:seen[project,entry['id']].append(entry)
 groups=collections.defaultdict(list);pages=[]
 for row in rows['base_module']:
  if not active(row):continue
  system=systems.get(row['f_system_id'],{});code=system.get('f_en_code');groups[code].append(row)
  project=PROJECTS.get(code)
  if project is None:continue
  prior=seen.get((project,row['f_id']),[]);matches=views(roots[project],row['f_url_address']) if row['f_type']=='2' else []
  pages.append({'project':project,'moduleIdSHA256':signature(row['f_id']),'name':row['f_full_name'],'type':row['f_type'],
   'metadataVisible':row['f_visible']=='1','captured':bool(prior),'captureRouteMatches':all(r.get('urlAddress')==row['f_url_address'] for r in prior) if prior else None,
   'originalUIObservedInPriorCapture':any(r.get('originalUIObserved') is True for r in prior),'sourceViewCandidates':matches,
   'sourcePageMissing':row['f_type']=='2' and not matches,'metadataAncestry':ancestry(row),'roleVisibilityVerified':False,'candidateFunctionalParityVerified':False})
 links={r['f_id']:r for r in rows['base_db_link'] if r['f_delete_mark'] in (None,'0')};visuals=[r for r in rows['base_visual_dev'] if active(r)]
 link_report=[{'linkIdSHA256':signature(ident),'type':row['f_db_type'],'hostSHA256':signature(row['f_host']),'port':row['f_port'],
  'schemaIsRestored':(row['f_service_name'] or row['f_db_schema']) in ('jnpf','tj_endanger'),
  'activeVisualReferences':sum(r['f_db_link_id']==ident for r in visuals)} for ident,row in links.items()]
 summary=[{'systemCode':code,'activeMetadataModules':len(modules),'types':dict(collections.Counter(r['f_type'] for r in modules))} for code,modules in sorted(groups.items(),key=lambda pair:str(pair[0]))]
 page_rows=[p for p in pages if p['type']=='2']
 return {'selectedTableCounts':{name:len(values) for name,values in rows.items()},'systems':summary,'pageModules':len(page_rows),'pageModulesWithoutSource':sum(p['sourcePageMissing'] for p in pages),
  'uncapturedMetadataModules':sum(not p['captured'] for p in pages),'capturedRouteMismatches':sum(p['captured'] and not p['captureRouteMatches'] for p in pages),
  'dbLinks':link_report,'activeVisualDefinitions':len(visuals),'visualsWithMissingDbLink':sum(r['f_db_link_id'] not in (None,'','0') and r['f_db_link_id'] not in links for r in visuals),
  'modules':pages,'credentialsSelected':False,'sourceDatabaseConnected':False,'ownDatabaseChanged':False,'roleVisibilityVerified':False,'authenticatedBusinessVerified':False,'fullCloneReady':False}

def audit(source,pin,workspace):
 source,workspace=Path(source),Path(workspace);require(re.fullmatch('[0-9a-f]{64}',pin),'MANIFEST_PIN_SHAPE')
 inputs={n:source/n for n in ('manifest.json','catalog.json','jnpf.rows.jsonl.gz')};before={}
 for n,p in inputs.items():
  stat=p.lstat();require(p.is_file() and not p.is_symlink() and not getattr(stat,'st_file_attributes',0)&0x400,'REGULAR_INPUT_REQUIRED');before[n]=(stat.st_size,stat.st_mtime_ns)
 raw=inputs['manifest.json'].read_bytes();require(len(raw)<=1024**2 and digest(raw)==pin,'MANIFEST_PIN_MISMATCH');manifest=json.loads(raw)
 payload={r['name']:r for r in manifest['files']};require(set(payload)=={'catalog.json','jnpf.rows.jsonl.gz','tj_endanger.rows.jsonl.gz'},'PAYLOAD_SCOPE')
 def verify():
  require(digest(inputs['manifest.json'].read_bytes())==pin,'MANIFEST_CHANGED')
  for name in ('catalog.json','jnpf.rows.jsonl.gz'):
   p=inputs[name];require(p.stat().st_size==payload[name]['bytes'] and p.stat().st_size<=32*1024**2,'PAYLOAD_SIZE')
   with p.open('rb') as f:require(hashlib.file_digest(f,'sha256').hexdigest()==payload[name]['sha256'],'PAYLOAD_SHA')
 verify();catalog=json.loads(inputs['catalog.json'].read_bytes());columns={t['TABLE_NAME']:[c['COLUMN_NAME'] for c in t['columns'] if not c.get('GENERATION_EXPRESSION')] for t in catalog['tablesAndViews'] if t['TABLE_SCHEMA']=='jnpf' and t['TABLE_NAME'] in FIELDS}
 require(set(columns)==set(FIELDS),'EXPECTED_TABLES_MISSING');rows={n:[] for n in FIELDS};prefixes=tuple(('['+json.dumps(n)+',').encode() for n in FIELDS);size=0;streamhash=hashlib.sha256();start=time.monotonic()
 with gzip.open(inputs['jnpf.rows.jsonl.gz'],'rb') as f:
  for raw in iter(lambda:f.readline(9*1024**2+1),b''):
   require(len(raw)<=9*1024**2 and time.monotonic()-start<90,'STREAM_LIMIT');size+=len(raw);require(size<=512*1024**2,'UNCOMPRESSED_LIMIT');streamhash.update(raw)
   if not raw.startswith(prefixes):continue
   name,values=json.loads(raw);require(len(values)==len(columns[name]),'ROW_WIDTH');row={}
   for field in FIELDS[name]:
    value=values[columns[name].index(field)];row[field]=bytes.fromhex(value).decode('utf-8') if value is not None else None
   rows[name].append(row)
 counts={(r['schema'],r['table']):r['rows'] for r in manifest['tableCounts']}
 require(all(len(v)==counts['jnpf',n] for n,v in rows.items()),'TABLE_COUNTS')
 captures=[];capturepins={}
 for name,project in CAPTURES.items():
  p=workspace/'captured_reference_20261023'/name;raw=p.read_bytes();require(len(raw)<8*1024**2,'CAPTURE_SIZE');captures.append((project,json.loads(raw)));capturepins[name]=digest(raw)
 result=report(rows,captures,{p:workspace/p for p in PROJECTS.values()});verify()
 for name,p in inputs.items():require((p.stat().st_size,p.stat().st_mtime_ns)==before[name],'INPUT_CHANGED')
 result.update(recordedAt=datetime.datetime.now().astimezone().isoformat(),sourceManifestSHA256=pin,jnpfStreamSHA256=streamhash.hexdigest(),jnpfUncompressedBytes=size,captureSHA256=capturepins)
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--export',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();require(not args.output.exists(),'FRESH_OUTPUT_REQUIRED')
 result=audit(args.export,args.manifest_sha256,args.workspace)
 with args.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ('selectedTableCounts','systems','pageModules','pageModulesWithoutSource','uncapturedMetadataModules','capturedRouteMismatches','activeVisualDefinitions','fullCloneReady')}))
if __name__=='__main__':main()
