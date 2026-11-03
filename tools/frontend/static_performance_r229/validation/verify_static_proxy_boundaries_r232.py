from pathlib import Path
import hashlib,json,subprocess,sys
V=Path(__file__).resolve().parent;A=Path('D:/Project/Zhumadian/Application');T=A/'tools';O=V/'static-proxy-boundaries-r232';assert not O.exists();O.mkdir()
# Reuse the established real HttpWebRequest transport and thirteen security/body cases.
s=(T/'verify_original_iis_proxy.py').read_text(encoding='utf-8')
old="source=app/'deploy/iis_original/App_Code/XnbyReferenceProxy.cs'"
assert s.count(old)==1
s=s.replace(old,"source=app/'tools/frontend/static_performance_r229/XnbyReferenceProxy.cs'")
(O/'existing-transport.py').write_text(s,encoding='utf-8')
run=subprocess.run([sys.executable,str(O/'existing-transport.py'),'--output',str(O/'transport'),'--application',str(A)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=35)
(O/'transport-run.log').write_bytes(run.stdout+run.stderr);assert run.returncode==0,run.stderr
source=r'''using System;public static class StaticCases{static void Check(bool b,string n){if(!b)throw new Exception(n);}public static void Main(){
 string[] yes={"gzip","GZIP;Q=1.000","br, gzip;q=0.3","*;q=1","gzip;q=0.001","gzip;q=0,gzip;q=0.2"};
 string[] no={null,"","identity","br","gzip;q=0","gzip;q=0,*;q=1","*;q=0","gzip;q=1.1","gzip;q=-1","gzip;q=0.0001",new string('x',1025),new string(',',33)+"gzip"};
 foreach(string s in yes)Check(XnbyReferenceProxy.AcceptsGzip(s),"gzip-positive");foreach(string s in no)Check(!XnbyReferenceProxy.AcceptsGzip(s),"gzip-negative");
 Check(XnbyReferenceProxy.PublicStaticResource("/zhumadian/branding-20261025/assets/js/index-ABCDEFGH.js","GET"),"versioned-js");
 Check(XnbyReferenceProxy.PublicStaticResource("/zhumadian/emergency/assets/css/index-ABCDEFGH.css","HEAD"),"emergency-head");
 Check(!XnbyReferenceProxy.PublicStaticResource("/zhumadian/api/serv/list","GET"),"api-no-gzip");
 Check(!XnbyReferenceProxy.PublicStaticResource("/zhumadian/home","GET"),"html-no-gzip");
 Check(!XnbyReferenceProxy.PublicStaticResource("/zhumadian/assets/a.js","POST"),"post-no-gzip");
 Console.WriteLine("23 gzip negotiation and route boundaries passed");}}'''
(O/'cases.cs').write_text(source,encoding='utf-8')
exe=O/'cases.exe';q=subprocess.run(['C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','/nologo','/out:'+str(exe),'/r:System.Web.dll','/r:System.Configuration.dll',str(T/'frontend/static_performance_r229/XnbyReferenceProxy.cs'),str(O/'cases.cs')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=20);assert q.returncode==0,q.stdout
q=subprocess.run([str(exe)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=5);assert q.returncode==0,q.stderr
result={'passed':True,'originalRealTransportSecurityBodyCookieRangeCases':13,'gzipNegotiationAndRouteCases':23,'candidateProxySHA256':hashlib.sha256((T/'frontend/static_performance_r229/XnbyReferenceProxy.cs').read_bytes()).hexdigest(),'realBusinessOrIISOrDesktopTouched':False}
(O/'verified-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
