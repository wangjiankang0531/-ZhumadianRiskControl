"""Explicit synthetic public gas scenarios. Not imported or seeded by the ordinary API."""
import hashlib
from datetime import datetime,timedelta,timezone
from .auth import Principal

PERMS=frozenset({'gas:read','gas:ingest','gas:verify','gas:cooperate','gas:handoff'})
def seed(store,points,tenant='QA'):
    source=Principal('QA-GAS-SOURCE',tenant,PERMS,frozenset(),False,True,'synthetic-gas-v1')
    operator=Principal('QA-A',tenant,PERMS,frozenset({'A'}),False,True,'synthetic-gas-v1')
    now=datetime.now(timezone.utc)
    scenarios=[('GAS-001','合成公共道路 · 装卸区外侧','QA-CH4','%LEL','12.5000','online','alarm','persistent'),('GAS-002','合成公共道路 · 管廊周边','QA-H2S','ppm','1.2500','online','alarm','needs-verification'),('GAS-003','合成公共道路 · 仓储外围','QA-VOC','mg/m3','0.8500','online','unknown','short-fluctuation'),('GAS-004','合成公共点位 · 设备状态核对','QA-CH4','%LEL',None,'offline','unknown','suspected-device'),('GAS-005','合成公共道路 · 应急关注场景','QA-CH4','%LEL','15.0000','online','alarm','emergency-concern'),('GAS-006','合成公共点位 · 无明显异常归档','QA-H2S','ppm','0.0000','online','normal','needs-verification')]
    points=tuple(sorted(points))
    if not points:raise ValueError('synthetic gas scenarios need explicit existing public points')
    for i,(identity,area,gas,unit,value,device,alarm,classification) in enumerate(scenarios):
        with store.transaction() as db:
            if db.execute('SELECT 1 FROM gas_alerts WHERE tenant=? AND source_system=? AND source_id=?',(tenant,'XNBY-GAS-DEMO',identity)).fetchone():continue
        at=(now-timedelta(minutes=10+i)).isoformat()
        payload={'schema':'xnby.gas.source.v1','sourceSystem':'XNBY-GAS-DEMO','sourceEventId':identity,'sourceRevision':1,'spatialId':points[i%len(points)],'area':area,'gasCode':gas,'unit':unit,'observedAt':at,'concentration':value,'deviceState':device,'alarmState':alarm,'trend':[] if value is None else [{'at':(now-timedelta(minutes=12+i)).isoformat(),'value':value},{'at':at,'value':value}]}
        key=lambda action:hashlib.sha256((identity+action).encode()).hexdigest()[:32]
        event=store.ingest(source,points,payload,key('source'))['event']
        if classification!='needs-verification':event=store.mutate(operator,points,event['id'],'classify',{'revision':event['revision'],'classification':classification,'note':'合成场景分类；不代表实际监测判定'},key('classify'))['event']
        # Deliberately do not seed a verified/archived or received emergency result.
        # These are manual test steps; no automatic GPS, threshold or response is invented.
    return len(scenarios)
