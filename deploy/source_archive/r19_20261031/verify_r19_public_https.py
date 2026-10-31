from pathlib import Path
import concurrent.futures,datetime,hashlib,json,sys,urllib.request,urllib.error,urllib.parse
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
stage=R/'work/user_feedback_20261031/workplace-security-build-r1'
dist=stage/'build/dist'
proof=json.loads((stage/'compiled-static-verification.json').read_text(encoding='utf-8'))
css='xnby-home-viewport-97d8e3adeed9.css'
assets=[css,*proof['compiledChunks']]
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
def request(path,method='GET',follow=True):
    req=urllib.request.Request('https://www.joinlinksmart.com'+path,
        headers={'User-Agent':'Mozilla/5.0','Accept-Encoding':'identity','Cache-Control':'no-cache'},method=method)
    op=urllib.request.build_opener()if follow else urllib.request.build_opener(NoRedirect())
    try:
        response=op.open(req,timeout=20)
    except urllib.error.HTTPError as e:response=e
    with response:
        body=response.read(4000000)
        return response.status,response.url,response.headers.get_content_type(),response.headers.get('Location'),body
def verify(path):
    try:
        status,url,mime,location,body=request(path)
        row={'path':path,'status':status,'mime':mime,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
        if path.startswith('/zhumadian/assets/')or path.endswith('.css'):
            expected=(dist/path.removeprefix('/zhumadian/')).read_bytes()
            row['exactCompiledBytesMatched']=body==expected
            expected_wire=expected.replace(b'/zhumadian/assets/',b'/zhumadian/branding-20261025/assets/')
            row['knownExistingBrandAssetPathRewrites']=expected.count(b'/zhumadian/assets/')
            row['exactExistingBrandingWireBytesMatched']=body==expected_wire
            row['passed']=status==200 and body==expected_wire and(mime=='text/css'if path.endswith('.css')else mime in ('application/javascript','text/javascript'))
        else:
            row['passed']=status==200 and mime=='text/html'
            if path in ['/zhumadian','/zhumadian/']:
                row['homeStyleRetained']=body.count(b'data-xnby-home-viewport="20261031"')==1
                row['passed']=row['passed']and row['homeStyleRetained']
        return row
    except Exception as e:return{'path':path,'passed':False,'errorType':type(e).__name__}
def redirect_case(path,method,expected):
    try:
        status,url,mime,location,body=request(path,method,False)
        relative=urllib.parse.urlsplit(urllib.parse.urljoin('https://www.joinlinksmart.com',location or''))
        actual=relative.path+('?' +relative.query if relative.query else'')
        return{'path':path,'method':method,'status':status,'location':actual,
            'passed':status==301 and actual==expected and relative.netloc=='www.joinlinksmart.com'}
    except Exception as e:return{'path':path,'method':method,'passed':False,'errorType':type(e).__name__}
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    paths=['/zhumadian','/zhumadian/','/zhumadian/emergency/','/zhumadian/h5/',*['/zhumadian/'+p for p in assets]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as pool:checks=list(pool.map(verify,paths))
    redirects=[redirect_case('/zhumadian','GET','/zhumadian/'),redirect_case('/zhumadian','HEAD','/zhumadian/'),
        redirect_case('/zhumadian?viewport_probe=1','GET','/zhumadian/?viewport_probe=1')]
    result={'at':datetime.datetime.now().astimezone().isoformat(),'TLSVerificationEnabled':True,
        'checks':checks,'redirects':redirects,'allPassed':all(x['passed']for x in checks+redirects),
        'loggedInWorkplaceLayoutVerified':False,'sheetG3G4G5Updated':False}
    (V/'r19-public-https-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))
