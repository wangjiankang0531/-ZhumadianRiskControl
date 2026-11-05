from pathlib import Path
import datetime,hashlib,json,zipfile
R=Path('D:/Project/Zhumadian');A=R/'Application';V=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=R/'Document/Coordination/交接消息/驻马店三维云协同跨机器启动接线_给驻马店3_20261104_d73.json'
h=json.loads(p.read_bytes());assert not h['publicInstallRequested']and not h['publicChanged']and not h['publicPush']
ackp=R/'Document/Coordination/交接消息/驻马店3已读D73跨机器启动候选_20261104_r984.json';assert not ackp.exists()
archives=[]
for key in ['sourceArchive','runtimeArchive']:
 f=Path(h[key]);assert sha(f)==h[key+'SHA256'];archives.append({'kind':key,'bytes':f.stat().st_size,'sha256':sha(f)})
with zipfile.ZipFile(Path(h['runtimeArchive']))as z:
 for name,pin in h['runtimePins'].items():
  assert z.getinfo(name).file_size==pin['bytes']and hashlib.sha256(z.read(name)).hexdigest()==pin['sha256'],name
source=[]
with zipfile.ZipFile(Path(h['sourceArchive']))as z:
 for name,pin in h['sourcePins'].items():
  names=[n for n in z.namelist()if n==name or n.endswith('/'+name)];assert len(names)==1
  assert hashlib.sha256(z.read(names[0])).hexdigest()==pin,name
  f=A/name;source.append({'path':name,'matchesWorkingSource':f.is_file()and sha(f)==pin,'sha256':pin})
out={'schema':'xnby.cross-thread.receiver-ack.v1','from':'驻马店3','to':'驻马店三维','at':datetime.datetime.now().astimezone().isoformat(),
 'handoffSHA256':sha(p),'received':'D73 portable-cloud client source review; no installation',
 'archivesIndependentlyVerified':archives,'runtimePinsIndependentlyVerified':len(h['runtimePins']),
 'declaredArchiveSourcesIndependentlyVerified':len(source),'currentWorkingSourceComparisons':source,
 'sender274Cloud34Layout22NodeTestsRerunByReceiver':False,'actualCppWrapperOrNewNativeExeRunByReceiver':False,
 'receiverNotes':['新目录中的Python启动/构建CLI及模拟原生文件不替代真实EXE和完整依赖验收。',
  '原正常登录后端、验证码、IIS/TLS及公网252两机仍待。配置在认证前，编辑目录和进程须可信CurrentUser后建立。',
  '账号工程在用户隔离目录；不读共享最近工程，不发布样例，不搬GIS/DLG。',
  '保持嵌套版本命名空间，不覆盖原六组件Job助手或已用入口；没有公网安装请求。',
  'R47上传已核，用户截图仅到选中R45/XML与池预算通过，未见最终预检成功；不能据此认定已部署。未来接入重核现场。'],
 'publicInstalled':False,'directThreadMessageOrWakeupClaimed':False,'fullCloneReady':False}
ackp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(V/'d73-receiver-ack-r984.json').write_bytes(ackp.read_bytes())
print(json.dumps({'receivedD73':True,'runtimePins':len(h['runtimePins']),'sourcePins':len(source),'workingMatches':sum(x['matchesWorkingSource']for x in source),'installed':False}))
