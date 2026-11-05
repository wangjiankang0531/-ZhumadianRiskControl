from pathlib import Path
import json,hashlib,zipfile,sqlite3,xml.etree.ElementTree as ET
R=Path('D:/Project/Zhumadian');REF=R/'Reference';V=Path(__file__).resolve().parent;D=V/'original-template-inventory-r971';assert not D.exists();D.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base=REF/'02安全风险管控平台/代码及开发环境搭建移交资料'
physical=[]
for p in base.rglob('*'):
 if not p.is_file()or '__MACOSX' in p.parts:continue
 n=p.name.lower()
 if n.endswith(('.sql','.dump','.bpmn','.bpmn20.xml','.bak')) or n.endswith('.json')and any(k in n for k in ['flow','workflow','流程']):physical.append({'path':str(p.relative_to(REF)),'bytes':p.stat().st_size,'sha256':sha(p)})
archive=base/'源码包/后端代码/后端源码-maven/cloud-endanger.zip';archiveRows=[]
with zipfile.ZipFile(archive)as z:
 infos=z.infolist();assert len(infos)<20000
 for info in infos:
  n=info.filename.lower()
  if n.endswith(('.sql','.dump','.bpmn','.bpmn20.xml','.bak'))or n.endswith('.json')and any(k in n for k in ['flow','workflow','流程']):archiveRows.append({'name':info.filename,'bytes':info.file_size,'directoryMetadataOnly':True})
opaque=[];dbbase=REF/'03敏捷应急大屏/大屏后台tjwhyq-svc/tjwhyq-svc/tjwhyq-base'
for name in ['tjwhyq.db','test.db']:
 p=dbbase/name
 with p.open('rb')as f:header=f.read(16)
 row={'path':str(p.relative_to(REF)),'bytes':p.stat().st_size,'sqliteHeader':header==b'SQLite format 3\0','schemaOnlyRead':False,'businessAccountOrSessionRowsRead':False}
 if row['sqliteHeader']:
  c=sqlite3.connect(p.as_uri()+'?mode=ro&immutable=1',uri=True)
  try:
   names=[r[0]for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
   row.update({'schemaOnlyRead':True,'tableCount':len(names),'workflowFormNamedTables':[n for n in names if any(k in n.lower()for k in ['flow','bpmn','form','process','template'])]})
  finally:c.close()
 opaque.append(row)
docs=[]
for name in ['后台管理系统操作说明.docx','后台代码结构数据库接口说明.docx','后台开发环境搭建手册.docx']:
 p=base/name
 with zipfile.ZipFile(p)as z:
  info=z.getinfo('word/document.xml')
  row={'path':str(p.relative_to(REF)),'bytes':p.stat().st_size,'sha256':sha(p),'documentXMLBytes':info.file_size,'actualDefinitionJSONOrDeployedVersionExtracted':False}
  if info.file_size>64*1024**2:
   row.update({'keywordCountsAvailable':False,'directoryMetadataOnly':True,'reason':'DOCUMENT_XML_EXCEEDS_64MIB_STREAM_SCOPE'})
  else:
   counts={k:0 for k in ['流程','模板','导出']}
   with z.open(info)as stream:
    for _,node in ET.iterparse(stream,events=['end']):
     if node.tag.endswith('}t')and node.text:
      for key in counts:counts[key]+=node.text.count(key)
     node.clear()
   row.update({'keywordCountsAvailable':True,'workflowKeywordOccurrences':counts['流程'],'templateKeywordOccurrences':counts['模板'],'exportKeywordOccurrences':counts['导出'],'onlyPerTextNodeKeywordCountsRetained':True,'splitAcrossTextNodeKeywordsMayBeUndercounted':True})
  docs.append(row)
summary={'schema':'xnby.original-template-source-extended-inventory.v1','passed':True,'physicalCommonDefinitionCandidates':len(physical),'backendArchiveEntries':len(infos),'backendArchiveDefinitionCandidateEntries':len(archiveRows),'twoOpaqueBigScreenDBHeadersInspected':True,'databaseSchemaOnlyWhereSQLite':True,'documentKeywordCountsNotTemplateDefinitionProof':True,'realNangangRuntimeDefinitionRecovered':False,'original252RuntimeOrBusinessAccountSessionRowsRead':False,'archivesOrOriginalProgramsExecuted':False,'sourceFilesModified':False,'sourceScopeIsLimitedNotProofNoOtherDefinitionExists':True,'uninspectedMDBAnd3DModelArchivesAreOutsideThisBSWorkflowInventory':True,'fullCloneReady':False}
out={'summary':summary,'physicalCandidates':physical,'backendArchiveCandidates':archiveRows,'opaqueDBMetadata':opaque,'documentMetadata':docs}
(D/'inventory.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out,ensure_ascii=True))
