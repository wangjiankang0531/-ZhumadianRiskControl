from pathlib import Path
import datetime,hashlib,json,re,ssl,urllib.request,urllib.parse
R=Path('D:/Project/Zhumadian');F=R/'work/user_feedback_20261031/emergency-workflow-source-r11/dist';B=R/'work/user_feedback_20261031/emergency-workflow-source-r11';C=R/'work/event_delivery_consistency_20261030/full-controller-r133'
J=lambda p:json.loads(p.read_bytes());m=J(B/'build-result.json');routes=set()
needle='"/src/views/emergencyResources/firstAidTeams/info/detail.vue"'
for p in(F/'assets/js').glob('*.js'):
    for match in re.finditer(re.escape(needle)+r':\(\)=>.{0,35}?import\("([^"\r\n]+)"\)',p.read_text(encoding='utf-8')):routes.add((p.parent/match[1]).resolve().relative_to(F.resolve()).as_posix())
assert len(routes)==1;rel=next(iter(routes));pin=m['files'][rel];context=ssl.create_default_context();rows=[]
for route,exact in [('/zhumadian/',None),('/zhumadian/emergency/',None),('/zhumadian/emergency/'+rel,pin)]:
    url='https://www.joinlinksmart.com'+route;request=urllib.request.Request(url,headers={'User-Agent':'Zhumadian-owned-release-readonly-check/1','Cache-Control':'no-cache'})
    with urllib.request.urlopen(request,context=context,timeout=20)as response:
        final=urllib.parse.urlsplit(response.geturl());assert final.scheme=='https'and final.netloc=='www.joinlinksmart.com';body=response.read(4*1024*1024+1);assert response.status==200 and len(body)<=4*1024*1024;digest=hashlib.sha256(body).hexdigest()
        if exact:assert len(body)==exact['bytes']and digest==exact['sha256']
        rows.append({'route':route,'status':response.status,'bytes':len(body),'sha256':digest,'R25TeamDetailFacadeByteExact':bool(exact)})
proof={'at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'defaultTLSVerificationUsed':True,'anonymousPublicGETsOnly':True,'publicNativeTeamDetailStillMatchesR25WF11':True,'authenticatedBusinessFlowAccepted':False,'rows':rows,'desktopOrServerControlUsed':False}
(C/'public-readonly-recheck.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps({'publicHTTPSRechecked':True,'anonymousGETs':len(rows),'publicTeamDetailStillR25WF11':True,'authenticatedBusinessAcceptance':False}))
