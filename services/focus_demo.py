"""Explicit synthetic fixtures, only invoked by the independent QA launcher."""
import hashlib
from datetime import date, timedelta
from .auth import Principal
from .focus import FocusStore

def seed(store, spatial=None):
    spatial=spatial or {}
    rows=[
        ("A","A-001","模拟A企业 · 装卸区域重点问题","major",["major","spillover"],-8,"onsite"),
        ("A","A-002","模拟A企业 · 通道占用重复问题","ordinary",["repeated"],-3,"feedback"),
        ("A","A-003","模拟A企业 · 专项检查材料补充","ordinary",["special-inspection"],4,"supplement"),
        ("A","A-004","模拟A企业 · 公共道路周边跟踪","ordinary",["spillover"],7,"following"),
        ("A","A-005","模拟A企业 · 上级督办复查记录","ordinary",["supervision"],-12,"archived"),
        ("A","A-006","模拟A企业 · 高风险作业周边核实","ordinary",["high-risk"],2,"pending"),
        ("B","B-001","模拟B企业 · 仓储区域重点问题","major",["major"],-5,"onsite"),
        ("B","B-002","模拟B企业 · 车辆通道反馈待查看","ordinary",["spillover"],5,"feedback"),
        ("B","B-003","模拟B企业 · 专项检查持续关注","ordinary",["special-inspection","repeated"],-1,"inspection"),
        ("B","B-004","模拟B企业 · 园区边界复查归档","ordinary",["spillover"],-9,"archived"),
    ]
    for owner,source,title,level,flags,days,state in rows:
        with store.transaction() as db:
            if db.execute("SELECT 1 FROM issues WHERE tenant='QA' AND enterprise=? AND source_system='XNBY-DEMO' AND source_id=?",(owner,source)).fetchone():continue
        tracker=Principal("QA-"+owner,"QA",frozenset({"focus:read","focus:track"}),frozenset({owner}),False,False,"synthetic-seed-v1")
        feedback=Principal("QA-FEEDBACK-"+owner,"QA",frozenset({"focus:read","focus:feedback"}),frozenset({owner}),False,False,"synthetic-seed-v1")
        def action(principal,issue,kind,payload):
            key=hashlib.sha256((source+kind+str(payload.get("revision",0))).encode()).hexdigest()[:32]
            return store.mutate(principal,issue["id"] if issue else None,kind,payload,key)["issue"]
        payload={"enterpriseId":owner,"sourceSystem":"XNBY-DEMO","sourceId":source,"title":title,"description":"此记录为信能本源独立验收模拟数据，位置、问题内容、企业及处置过程均为演示，不用于真实监管判断。","level":level,"flags":flags,"dueDate":(date.today()+timedelta(days=days)).isoformat()}
        if owner in spatial:payload["spatialId"]=spatial[owner]
        issue=action(tracker,None,"create",payload)
        if state in ("feedback","supplement","archived"):
            issue=action(feedback,issue,"feedback",{"revision":issue["revision"],"cause":"模拟现场管理记录有待完善","measures":"模拟补充标识与检查措施","plan":"模拟按期限完成并反馈","completion":"模拟已提交整改情况，等待园区查看","improvement":"模拟定期复查和培训","materialVersion":"DEMO-v1（未上传附件）"})
        if state in ("onsite","supplement","following","inspection"):
            issue=action(tracker,issue,"track",{"revision":issue["revision"],"method":"online","note":"模拟园区跟踪记录：按重点问题关注口径核对反馈及周边风险。","status":state})
        if state=="archived":
            issue=action(tracker,issue,"review",{"revision":issue["revision"],"result":"rectified","note":"模拟复查认为已整改，仅作园区侧跟踪结论，不替代企业验收。"})
            action(tracker,issue,"archive",{"revision":issue["revision"],"note":"模拟资料归档，仍可重新关注并保留历史。"})
