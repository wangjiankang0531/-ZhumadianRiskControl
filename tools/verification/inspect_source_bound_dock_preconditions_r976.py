from pathlib import Path
import json,hashlib,urllib.parse
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;G=R/'_g/Application'
source=R/'Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/后端代码/后端源码-maven/cloud-endanger/src/main/java/com/iemp/endanger/util/http/DockUtil.java'
code=source.read_text('utf8');cfg=json.loads((G/'private/server-configuration.json').read_bytes())['configuration']['business'];rows=[]
names=['riskReportUrl','safetyEmergencyUrl','workReportUrl','otherWorkReportUrl','otherRiskReportUrl','otherThirdUrl']
for name in names:
 assert '${'+name+'}'in code and name in cfg and isinstance(cfg[name],str)
 value=cfg[name];u=urllib.parse.urlsplit(value);kind='empty'if not value else'loopback'if u.hostname in ['localhost','127.0.0.1','::1']else'non-loopback-url'if u.scheme in ['http','https']else'non-url-or-unresolved'
 rows.append({'configurationField':name,'classification':kind,'rawValueTokenOrCredentialsPrinted':False,'reboundToNewOwnedReceiverAndIdentityVerified':False})
out={'originalDockSourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'sixFieldsDerivedFromActualSourceBindings':True,'notificationFields':rows,'previousNameHeuristicEmptyResultWasNotEndpointAbsenceProof':True,'readyForNewEventCreation':False,'mustBindAllSixToNewOwnLoopbackReceiversBeforeAnyCreate':True,'originalNetworkBoundaryMustNotBeRelaxed':True,'doesNotProveRealExternalDockDelivery':True,'businessPrivateConfigurationOrServicesWritten':False}
p=V/'source-bound-dock-preconditions-r976.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
