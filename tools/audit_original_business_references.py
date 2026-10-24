"""Check configured role/form references against a sealed export without SQL or raw-value output."""
import argparse,datetime,gzip,hashlib,json,os,re,subprocess,time
from pathlib import Path
FIELDS={'base_role':['f_id','f_enabled_mark','f_delete_mark'],'base_user_relation':['f_object_id','f_object_type','f_delete_mark'],'flow_form':['f_id','f_en_code','f_enabled_mark','f_delete_mark'],'flow_form_relation':['f_form_id','f_flow_id','f_delete_mark'],'flow_template':['f_id','f_enabled_mark','f_delete_mark'],'flow_template_json':['f_template_id','F_PROCESSDEFINITIONID','f_enabled_mark','f_delete_mark'],'act_re_procdef':['ID_']}
ROLES=('safety.roleId','safety.auditRoleId','safety.env-role-id')
FORMS=('safety.hiddenDangerFormCode','safety.checkLedgerFormCode','flow.workCode','flow.inspectionHandle','flow.workReservation','flow.workProgramme','flow.eventInfoHandle','flow.eventTaskHandle')
def require(value,code):
 if not value:raise ValueError(code)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def key(value):return digest(value.encode('utf-8')) if value is not None else None
def present(row):return row['f_delete_mark'] in (None,'0')
def build_report(rows,expected):
 require(set(expected)==set(ROLES+FORMS),'ELEVEN_REFERENCE_KEYS_REQUIRED');items=[];definitions={r['ID_'] for r in rows['act_re_procdef']}
 for name in ROLES+FORMS:
  role=name in ROLES;column='f_id' if role else 'f_en_code';table='base_role' if role else 'flow_form';value=expected[name];matches=[r for r in rows[table] if key(r[column])==value] if value!='EMPTY' else [];live=[r for r in matches if present(r)]
  entry={'key':name,'kind':'role' if role else 'form','configuredNonEmpty':value!='EMPTY','exactMatches':len(matches),'nonDeletedMatches':len(live),'explicitlyEnabledMatches':sum(r['f_enabled_mark']=='1' for r in live),'uniqueNonDeletedReference':len(live)==1}
  if role:
   entry['nonDeletedLiteralRoleAssociations']=sum(present(r) and r['f_object_type']=='Role' and key(r['f_object_id'])==value for r in rows['base_user_relation'])
  else:
   form_ids={r['f_id'] for r in live};relations=[r for r in rows['flow_form_relation'] if r['f_form_id'] in form_ids and present(r)];template_ids={r['f_flow_id'] for r in relations if r['f_flow_id']};templates=[r for r in rows['flow_template'] if r['f_id'] in template_ids and present(r)];known={r['f_id'] for r in templates};versions=[r for r in rows['flow_template_json'] if r['f_template_id'] in known and present(r)];released=[r for r in versions if r['f_enabled_mark']=='1'];valid=[r for r in released if r['F_PROCESSDEFINITIONID'] in definitions]
   entry.update(nonDeletedFormFlowRelations=len(relations),linkedNonDeletedTemplates=len(templates),nonDeletedVersions=len(versions),explicitlyEnabledVersions=len(released),releasedVersionsWithExistingDefinition=len(valid),releasedVersionsWithMissingDefinition=sum(bool(r['F_PROCESSDEFINITIONID']) and r['F_PROCESSDEFINITIONID'] not in definitions for r in released),versionHasExistingDefinition=bool(valid))
  items.append(entry)
 return {'selectedTableCounts':{n:len(v) for n,v in rows.items()},'configuredReferences':items,'uniqueNonDeletedReferences':sum(r['uniqueNonDeletedReference'] for r in items),'allConfiguredRoleIdsExist':all(r['uniqueNonDeletedReference'] for r in items if r['kind']=='role'),'allConfiguredFormCodesExist':all(r['uniqueNonDeletedReference'] for r in items if r['kind']=='form'),'allConfiguredFormsHaveExistingReleasedDefinition':all(r['uniqueNonDeletedReference'] and r['versionHasExistingDefinition'] for r in items if r['kind']=='form'),'formFlowRelationTable':'flow_form_relation','runtimeImpactVerified':False,'originalValuesOrRowsWritten':False,'sourceDatabaseConnected':False,'databaseWritten':False,'authenticatedBusinessVerified':False,'workflowExecutionVerified':False,'fullCloneReady':False}

def audit(source,manifest_pin,workspace,candidate,candidate_pin,output):
 source,workspace,candidate,output=map(Path,(source,workspace,candidate,output));require(not output.exists(),'FRESH_OUTPUT_REQUIRED')
 for pin in (manifest_pin,candidate_pin):require(re.fullmatch('[0-9a-f]{64}',pin),'EXPLICIT_PIN_REQUIRED')
 require(candidate.is_file() and candidate.stat().st_size<=256*1024 and digest(candidate.read_bytes())==candidate_pin,'PRIVATE_CONFIG_PIN_MISMATCH')
 inputs={n:source/n for n in ('manifest.json','catalog.json','jnpf.rows.jsonl.gz')};before={n:(p.stat().st_size,p.stat().st_mtime_ns) for n,p in inputs.items()}
 for p in inputs.values():require(p.is_file() and not p.is_symlink() and not getattr(p.lstat(),'st_file_attributes',0)&0x400,'REGULAR_INPUT_REQUIRED')
 raw=inputs['manifest.json'].read_bytes();require(len(raw)<=1024**2 and digest(raw)==manifest_pin,'MANIFEST_PIN_MISMATCH');manifest=json.loads(raw);payload={r['name']:r for r in manifest['files']};require(set(payload)=={'catalog.json','jnpf.rows.jsonl.gz','tj_endanger.rows.jsonl.gz'},'PAYLOAD_SCOPE')
 def verify():
  require(digest(inputs['manifest.json'].read_bytes())==manifest_pin,'MANIFEST_CHANGED')
  for name in ('catalog.json','jnpf.rows.jsonl.gz'):
   p=inputs[name];require(p.stat().st_size==payload[name]['bytes'] and p.stat().st_size<=32*1024**2,'PAYLOAD_SIZE')
   with p.open('rb') as f:require(hashlib.file_digest(f,'sha256').hexdigest()==payload[name]['sha256'],'PAYLOAD_SHA')
 verify();catalog=json.loads(inputs['catalog.json'].read_bytes());columns={t['TABLE_NAME']:[c['COLUMN_NAME'] for c in t['columns'] if not c.get('GENERATION_EXPRESSION')] for t in catalog['tablesAndViews'] if t['TABLE_SCHEMA']=='jnpf' and t['TABLE_NAME'] in FIELDS};require(set(columns)==set(FIELDS),'EXPECTED_TABLES_REQUIRED')
 output.mkdir();classes=output/'classes';classes.mkdir();java=Path(json.loads((workspace/'own-pboot-r32/preparation.json').read_bytes())['javaHome']);helper=Path(__file__).parent/'java/OriginalBusinessReferenceHashes.java';env={k:v for k,v in os.environ.items() if k.upper() not in ('JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH')}
 def run(command,name):
  r=subprocess.run(list(map(str,command)),cwd=output,env=env,capture_output=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW);(output/(name+'.private.log')).write_bytes(r.stdout+r.stderr);require(r.returncode==0,'REFERENCE_'+name.upper()+'_FAILED');return r.stdout
 run([java/'bin/javac.exe','-proc:none','--release','8','-encoding','UTF-8','-d',classes,helper],'compile');hashes=output/'configured-reference-hashes.properties';require(b'BUSINESS_REFERENCE_HASHES=11' in run([java/'bin/java.exe','-Xmx64m','-cp',classes,'xnby.replica.OriginalBusinessReferenceHashes',candidate,candidate_pin,hashes],'hashes'),'REFERENCE_KEY_COUNT')
 expected={line.split('=',1)[0]:line.split('=',1)[1] for line in hashes.read_text('ascii').splitlines() if line and not line.startswith(('#','!'))};rows={n:[] for n in FIELDS};prefixes=tuple(('['+json.dumps(n)+',').encode() for n in FIELDS);size=0;streamhash=hashlib.sha256();start=time.monotonic()
 with gzip.open(inputs['jnpf.rows.jsonl.gz'],'rb') as f:
  for raw in iter(lambda:f.readline(9*1024**2+1),b''):
   require(len(raw)<=9*1024**2 and time.monotonic()-start<90,'STREAM_LIMIT');size+=len(raw);require(size<=512*1024**2,'UNCOMPRESSED_LIMIT');streamhash.update(raw)
   if not raw.startswith(prefixes):continue
   name,values=json.loads(raw);require(len(values)==len(columns[name]),'ROW_WIDTH');row={}
   for field in FIELDS[name]:
    value=values[columns[name].index(field)];row[field]=bytes.fromhex(value).decode('utf-8') if value is not None else None
   rows[name].append(row)
 counts={(r['schema'],r['table']):r['rows'] for r in manifest['tableCounts']};require(all(len(v)==counts['jnpf',n] for n,v in rows.items()),'TABLE_ROW_COUNTS');result=build_report(rows,expected);verify()
 for n,p in inputs.items():require((p.stat().st_size,p.stat().st_mtime_ns)==before[n],'INPUT_CHANGED')
 require(digest(candidate.read_bytes())==candidate_pin,'PRIVATE_INPUT_CHANGED');result.update(recordedAt=datetime.datetime.now().astimezone().isoformat(),sourceManifestSHA256=manifest_pin,inputCandidateSHA256=candidate_pin,jnpfStreamSHA256=streamhash.hexdigest(),jnpfUncompressedBytes=size,hashHelperSourceSHA256=digest(helper.read_bytes()))
 (output/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('export','manifest-sha256','workspace','candidate-properties','candidate-sha256','output'):p.add_argument('--'+n,required=True)
 a=p.parse_args();print(json.dumps(audit(a.export,a.manifest_sha256,a.workspace,a.candidate_properties,a.candidate_sha256,a.output)))
if __name__=='__main__':main()
