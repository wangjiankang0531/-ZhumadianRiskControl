"""Independent synthetic gas manual QA. Explicitly run; never starts with the normal API."""
import argparse,json,sys,threading,socket
from urllib.parse import urlsplit
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.tests.test_api import ApiTests
from services.api import Service
from services.data import fingerprint
from services.layers import LayerRepository
from services.gas_demo import seed
from tools.serve_business_portal_qa import QAHandler,configure_fixture
from tools.authenticated_portal_server import PortalServer

def configure_gas_fixture(probe,path,*,nearby_demo=False):
    configure_fixture(probe)
    points=[]
    for i,(x,y) in enumerate([(-470,-2220),(-310,-2180),(-200,-2240)],1):
        identity='qa-gas-'+str(i);points.append(identity)
        probe.layers['layers'][0]['features'].append({'id':identity,'name':'合成公共气体监测点 '+str(i),'type':'point','positions':[[x,y,65]],'style':{'icon':'warning','color':'#23A6AD'},'label':{'text':'合成气体点 '+str(i)}})
    context_objects=[];context_public=[]
    if nearby_demo:
        from tools.gas_nearby_demo import extend
        context_objects,context_public=extend(probe)
    probe.write('layers.json',probe.layers)
    catalog={'schema':'xnby.spatial.catalog.v1','scene':'zhumadian','layerFingerprint':fingerprint(probe.layers),'exportedAt':probe.records['exportedAt'],'objects':[{'spatialId':identity,'category':'gas-monitor','themes':['monitoring']} for identity in points]+context_objects}
    probe.write('spatial.json',catalog)
    for person in probe.policy['principals']:
        subject=person['subject']
        if subject=='QA-A':person['permissions']+=['gas:read','gas:verify','gas:cooperate','gas:handoff'];person['publicSpatial']=True
        elif subject=='QA-B':person['permissions']+=['gas:read','gas:cooperate'];person['publicSpatial']=True
        elif subject in ('QA-PUBLIC','QA-READER'):person['permissions']+=['gas:read'];person['publicSpatial']=True
        elif subject=='QA-FEEDBACK':person['permissions']+=['gas:read','gas:cooperate'];person['publicSpatial']=True
    for subject in ('QA-GAS-SOURCE','QA-GAS-RESULT'):
        probe.policy['principals'].append({'subject':subject,'enabled':True,'permissions':['gas:read','gas:ingest'],'enterprises':[],'publicSpatial':True})
    probe.write('policy.json',probe.policy)
    repository=LayerRepository(path)
    try:version=repository.get('QA')['revision']
    except Exception:version=0
    repository.import_bytes('QA','default',json.dumps(probe.layers,ensure_ascii=False).encode(),version)
    probe.config['businessDatabase']=str(path);probe.config['data'].update(layerDocument='default',spatial='spatial.json',publicSpatialIds=['public',*points,*context_public]);probe.config['gas']={'sourceSystem':'XNBY-GAS-DEMO','sourceSubjects':['QA-GAS-SOURCE'],'emergencySystem':'XNBY-EMERGENCY-DEMO','resultSubjects':['QA-GAS-RESULT']};probe.write('config.json',probe.config)
    service=Service(probe.root/'config.json');probe.service=service;probe.server.service=service
    from services.focus_demo import seed as seed_focus
    seed_focus(service.focus);seed(service.gas,points)
    return points

class GasQAHandler(QAHandler):
    static=None;scene_url=None
    def do_GET(self):
        route=urlsplit(self.path).path
        if route=='/':
            self.send_response(303);self.send_header('Location',self.scene_url or '/gas.html');self.send_header('Content-Length','0');self.end_headers();return
        if route.startswith(('/qa/','/api/v1/')) or route=='/application/config.json':return super().do_GET()
        return __import__('http.server',fromlist=['SimpleHTTPRequestHandler']).SimpleHTTPRequestHandler.do_GET(self)
    def do_HEAD(self):
        route=urlsplit(self.path).path
        if route=='/':return self.do_GET()
        if route.startswith('/api/v1/') or route=='/application/config.json':return super().do_HEAD()
        return __import__('http.server',fromlist=['SimpleHTTPRequestHandler']).SimpleHTTPRequestHandler.do_HEAD(self)
    def do_POST(self):
        if self.command!='POST':return self.output(405,{'error':'METHOD_NOT_ALLOWED'})
        if urlsplit(self.path).path.startswith(('/qa/oauth/','/api/v1/')):return super().do_POST()
        return self.output(405,{'error':'METHOD_NOT_ALLOWED'})
    do_PUT=do_PATCH=do_DELETE=do_OPTIONS=do_POST
    def translate_path(self,path):
        route=path.split('?',1)[0].lstrip('/')
        if route in {'gas.html','gas.css','gas-workbench.js','portal.html','portal.css','portal.js','viewer.js','source-gain-worker.js','index.html','reference-demo.html','reference-demo.js','reference-demo.css','THREE-LICENSE.txt'}:return str(self.static/route)
        return str(self.static/'_not_available')

class GasQAServer(PortalServer):
    allow_reuse_address=False
    def server_bind(self):
        if sys.platform=='win32':self.socket.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
        return super().server_bind()

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8822);p.add_argument('--database',type=Path,required=True);p.add_argument('--static',type=Path,required=True);p.add_argument('--scene-url');p.add_argument('--nearby-demo',action='store_true');a=p.parse_args()
    if not 1<=a.port<=65535:p.error('invalid port')
    if not (a.static/'gas.html').is_file():p.error('build the gas webpage first')
    if a.scene_url:
        u=urlsplit(a.scene_url)
        if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost') or u.username or u.password or u.query or u.fragment:p.error('scene URL must be an explicit loopback URL')
    ApiTests.setUpClass();probe=ApiTests();probe.setUp();points=configure_gas_fixture(probe,a.database.resolve(),nearby_demo=a.nearby_demo);origin='http://127.0.0.1:'+str(a.port);configuration={'schema':'xnby.portal.config.v1','mode':'authenticated','development':True,'oauth':{'issuer':'https://qa.identity.invalid','clientId':'qa-client','authorizationEndpoint':origin+'/qa/oauth/authorize','tokenEndpoint':origin+'/qa/oauth/token','scope':'spatial:read business:read focus:read focus:track focus:feedback gas:read gas:verify gas:cooperate gas:handoff'}}
    GasQAHandler.static=a.static.resolve();GasQAHandler.scene_url=a.scene_url;server=GasQAServer(('127.0.0.1',a.port),probe.server.server_port,configuration,GasQAHandler);server.qa_role_labels={'QA-A':'园区核实人员（合成验收）','QA-B':'模拟B企业 · 配合人员','QA-PUBLIC':'公共点位 · 只读人员','QA-FEEDBACK':'模拟A企业 · 配合人员','QA-READER':'模拟A企业 · 只读人员'};server.probe=probe;server.qa_lock=threading.Lock();server.transactions={};server.codes={}
    print(json.dumps({'pid':__import__('os').getpid(),'port':a.port,'database':str(a.database),'schema':4,'synthetic':True,'points':points}),flush=True)
    try:server.serve_forever()
    finally:server.server_close();probe.tearDown()
if __name__=='__main__':main()
