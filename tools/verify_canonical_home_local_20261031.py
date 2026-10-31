from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import argparse

ROOT=Path(__file__).resolve().parent
R=Path('D:/Project/Zhumadian')
OUT=None
FRAMEWORK=Path('C:/Windows/Microsoft.NET/Framework64/v4.0.30319')

def call(command,log):
    result=subprocess.run([str(x) for x in command],capture_output=True,timeout=90,
                          creationflags=subprocess.CREATE_NO_WINDOW)
    (OUT/log).write_bytes(result.stdout+result.stderr)
    if result.returncode:
        raise RuntimeError('OWN_LOCAL_COMPILATION_OR_CASE_FAILED:'+log)
    return result.stdout.decode('utf-8',errors='replace')

def main():
    global OUT
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    parent=(R/'work/user_feedback_20261031').resolve(strict=True)
    OUT=Path(args.output).absolute()
    assert OUT.parent.resolve(strict=True)==parent and OUT.name.startswith('canonical-home-compile-')
    assert not OUT.exists();OUT.mkdir(parents=True)
    raw=(R/'Application/deploy/iis_canonical_home/Global.asax').read_bytes()
    text=raw.decode('utf-8')
    members=re.search(r'<script runat="server">([\s\S]+)</script>',text)[1]
    harness=r'''
using System;
using System.Web;
using System.IO;
public class OwnedCanonicalApplication : HttpApplication {
MEMBERS
}
public static class OwnedCanonicalCases {
    static int count;
    static void Check(string raw, string method, bool secure, string authority, string expected) {
        string actual=OwnedCanonicalApplication.CanonicalHomeTarget(raw,method,secure,authority);
        if(actual!=expected) throw new Exception("OWN_CANONICAL_CASE_"+count);
        count++;
    }
    public static void Main() {
        Check("/zhumadian","GET",true,"www.joinlinksmart.com","/zhumadian/");
        Check("/zhumadian","HEAD",true,"www.joinlinksmart.com","/zhumadian/");
        Check("/zhumadian?viewport_probe=1","GET",true,"www.joinlinksmart.com","/zhumadian/?viewport_probe=1");
        Check("/zhumadian?from=%2Fhome&x=a+b","GET",true,"www.joinlinksmart.com","/zhumadian/?from=%2Fhome&x=a+b");
        Check("/zhumadian","GET",true,"WWW.JOINLINKSMART.COM","/zhumadian/");
        Check("/zhumadian/","GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian/home","GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian/login","GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian/api/serv/eventTask/save","POST",true,"www.joinlinksmart.com",null);
        Check("/zhumadian","POST",true,"www.joinlinksmart.com",null);
        Check("/zhumadian","OPTIONS",true,"www.joinlinksmart.com",null);
        Check("/zhumadian","GET",false,"www.joinlinksmart.com",null);
        Check("/zhumadian","GET",true,"unrelated.invalid",null);
        Check("/zhumadian","GET",true,"www.joinlinksmart.com:8443",null);
        Check("/ZHUMADIAN","GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian2","GET",true,"www.joinlinksmart.com",null);
        Check("/", "GET",true,"www.joinlinksmart.com",null);
        Check(null,"GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian?x="+new string('a',8192),"GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian?x=a\r\nLocation: bad","GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian?x=\\bad","GET",true,"www.joinlinksmart.com",null);
        Check("/zhumadian?x=\0bad","GET",true,"www.joinlinksmart.com",null);
        Console.WriteLine("OWN_CANONICAL_HOME_CASES_PASSED_"+count);
    }
}
'''.replace('MEMBERS',members)
    source=OUT/'OwnedCanonicalCases.cs';source.write_text(harness,encoding='utf-8')
    exe=OUT/'OwnedCanonicalCases.exe'
    call([FRAMEWORK/'csc.exe','/nologo','/target:exe','/out:'+str(exe),
          '/reference:'+str(FRAMEWORK/'System.Web.dll'),source],'csc-output.txt')
    output=call([exe],'case-output.txt')
    assert 'OWN_CANONICAL_HOME_CASES_PASSED_22' in output
    site=OUT/'site';site.mkdir();(site/'Global.asax').write_bytes(raw)
    (site/'web.config').write_text('<configuration><system.web><compilation debug="false"/></system.web></configuration>',encoding='utf-8')
    call([FRAMEWORK/'aspnet_compiler.exe','-nologo','-v','/zhumadian','-p',site,OUT/'compiled-site'],
         'aspnet-compiler-output.txt')
    report={'globalAsaxSHA256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
        'actualExtractedGlobalMembersCompiled':True,'actualSystemWeb301HostedContractPassed':False,
        'unhostedResponseFixtureRejected':True,
        'cases':22,'actualASPNetSitePrecompilationPassed':True,
        'existingHTTPSHostMethodAndRawURLGuardsRetained':True,
        'onlyExactBareProjectRootRedirected':True,'queryPreserved':True,
        'existingServerGlobalAsaxAbsenceNotYetChecked':True,
        'publicInstalled':False,'R18FixedPayloadModified':False,
        'realIISHTTPIntegrationVerified':False}
    (OUT/'result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
