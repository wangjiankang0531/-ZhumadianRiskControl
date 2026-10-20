"""Isolated synthetic business workbench. Never opens the production SQLite/DLG."""
import json, sqlite3, uuid
from pathlib import Path
from contextlib import closing
from datetime import date, datetime, timezone
from services.reference_work_forms import TYPES, ENTERPRISES, normalize, synthetic_form, list_fields
from services.reference_errors import DemoError
from services.reference_plans import PlanMixin, PLAN_SCHEMA

# Names come from the recorded read-only reference navigation and 261013 requirements.
# They are not evidence that every corresponding reference page has been visited.
CATALOG = [
 ('risk-unit','双重预防','风险单元',['风险单元','风险等级','责任部门','检查频次'],['待辨识','已分级','管控中','已复核']),
 ('check-content','双重预防','检查内容',['检查项目','检查标准','适用区域','检查方式'],['草稿','已发布','执行中','已归档']),
 ('check-list','双重预防','排查清单',['清单名称','检查项目','适用区域','版本'],['草稿','已发布','执行中','已归档']),
 ('check-plan','双重预防','排查计划',['计划名称','排查周期','责任部门','覆盖区域'],['草稿','待审核','执行中','已完成']),
 ('check-task','双重预防','排查任务',['任务名称','排查区域','计划时间','检查结果'],['待执行','执行中','待复核','已完成']),
 ('hidden-danger','双重预防','隐患台账',['隐患描述','隐患级别','整改部门','整改期限'],['待关注','跟踪中','待复查','已归档']),
 ('supervision','双重预防','上级检查',['检查主题','检查来源','检查区域','整改要求'],['待反馈','整改中','待复查','已归档']),
 ('special-task','双重预防','专项任务',['专项名称','任务类别','涉及区域','完成期限'],['草稿','待执行','执行中','已完成']),
 ('inspection-point','智能巡检','巡检点位',['点位名称','区域','巡检项目','巡检频次'],['待核验','已启用','巡检中','已核验']),
 ('inspection-plan','智能巡检','巡检计划',['计划名称','路线','巡检周期','责任部门'],['草稿','待审核','执行中','已完成']),
 ('inspection-task','智能巡检','巡检任务',['任务名称','路线','计划时间','异常情况'],['待执行','执行中','待复核','已完成']),
 ('inspection-exception','智能巡检','异常记录',['异常描述','点位','异常等级','处置期限'],['待核实','处置中','待复核','已归档']),
 ('special-work','特殊作业','作业票管理',['作业票编号','作业类型','作业位置','起止时间'],['待申请','待审批','作业中','已验收']),
 ('work-monitor','特殊作业','作业监护',['作业票编号','监护区域','安全措施','监护结果'],['待确认','监护中','待验收','已完成']),
 ('major-hazard','重大危险源','危险源档案',['危险源名称','危险源级别','所属区域','监测状态'],['待辨识','已分级','监测中','已复核']),
 ('monitoring','监测预警','监测点位',['点位名称','监测类别','当前示例值','报警阈值'],['待校验','正常','预警待确认','处置完成']),
 ('alarm','监测预警','报警记录',['报警内容','点位','报警级别','发生时间'],['待确认','已确认','处置中','已解除']),
 ('fire','监测预警','消防设施',['设施名称','设施类别','所属区域','核验周期'],['待核验','可用','检修中','核验完成']),
 ('events','敏捷应急','应急响应',['事件名称','事件类型','事件级别','发生地点'],['接报待研判','响应中','处置中','已结束']),
 ('plans','敏捷应急','应急预案',['预案名称','预案类别','版本','适用范围'],['编制中','待评审','已发布','已归档']),
 ('drill','敏捷应急','应急演练',['演练名称','演练类型','演练地点','计划时间'],['计划中','待实施','实施中','已总结']),
 ('duty','敏捷应急','值班值守',['值班日期','班次','值班岗位','交接事项'],['待排班','已排班','值守中','已交班']),
 ('teams','应急资源','救援队伍',['队伍名称','队伍类别','驻地','示例人数'],['待核验','可调配','演练占用','已复核']),
 ('experts','应急资源','应急专家',['专家代号','专业领域','服务区域','联系渠道'],['待核验','可联系','演练占用','已复核']),
 ('resources','应急资源','物资装备',['物资名称','物资类别','储备库','示例数量'],['待入库','可调配','演练占用','已盘点']),
 ('warehouses','应急资源','物资库',['库房名称','库房类别','所在区域','责任部门'],['待核验','可用','盘点中','已核验']),
 ('shelters','应急资源','避难场所',['场所名称','所在区域','示例容量','设施情况'],['待核验','可用','演练占用','已复核']),
 ('medical','应急资源','医疗资源',['机构代号','服务类别','服务区域','接入方式'],['待核验','可联系','演练占用','已复核']),
 ('communication','应急资源','通讯录',['岗位代号','机构类别','值守区域','联系渠道'],['待核验','有效','待更新','已核验']),
 ('closed','封闭管理','卡口管理',['卡口名称','所在区域','通道类别','运行状态'],['待核验','正常','维护中','已复核']),
 ('vehicles','封闭管理','车辆通行',['车辆代号','通行事由','入口卡口','预约时间'],['待申请','待核验','园区内','已离园']),
 ('people','封闭管理','人员通行',['人员代号','通行事由','入口卡口','预约时间'],['待申请','待核验','园区内','已离园']),
 ('energy','能源管理','计量设施',['设施名称','能源类别','计量单位','示例读数'],['待接入','正常','异常待核实','已复核']),
 ('energy-report','能源管理','能耗报表',['报表名称','能源类别','统计周期','示例用量'],['待汇总','已汇总','待复核','已归档']),
]
MODULES={r[0]:dict(id=r[0],group=r[1],name=r[2],columns=r[3],states=r[4],referenceCoverage='recorded_navigation_or_requirement') for r in CATALOG}
for _item in json.loads(Path(__file__).with_name('reference_demo_catalog.json').read_text(encoding='utf-8')):
    _base=MODULES.get(_item['id'],dict(states=['草稿','待核验','执行中','已归档']))
    MODULES[_item['id']]={**_base,**_item}
SCHEMA='CREATE TABLE IF NOT EXISTS demo_records (\n entity TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL,\n enterprise TEXT NOT NULL, state TEXT NOT NULL, date TEXT NOT NULL,\n payload TEXT NOT NULL, PRIMARY KEY(entity,id));\nCREATE INDEX IF NOT EXISTS demo_query ON demo_records(entity,enterprise,state,date);\nCREATE TABLE IF NOT EXISTS demo_events (\n entity TEXT NOT NULL, id TEXT NOT NULL, revision INTEGER NOT NULL,\n at TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,\n PRIMARY KEY(entity,id,revision), FOREIGN KEY(entity,id) REFERENCES demo_records(entity,id));\n'

def now(): return datetime.now(timezone.utc).isoformat()

SCHEMA += PLAN_SCHEMA

class DemoStore(PlanMixin):
    def __init__(self,path):
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)
        with closing(self.connect()) as db:
            db.execute('PRAGMA journal_mode=WAL')
            if db.execute('PRAGMA user_version').fetchone()[0] not in (0,1,2,3):raise ValueError('unsupported demo schema')
            db.executescript('BEGIN IMMEDIATE;\n'+SCHEMA+'\nPRAGMA user_version=3;\nCOMMIT;')
            db.execute('BEGIN IMMEDIATE')
            for item in MODULES.values():
                for i in range(1,13):
                    identity='DEMO-'+item['id'].upper()+'-'+str(i).zfill(3)
                    fields={label:self.sample(item['id'],label,i) for label in item['columns']}
                    seed=dict(fields=fields,note='合成验收数据，不对应真实企业、人员或实时监测。')
                    if item['id']=='work-reservation':seed['workForm']=synthetic_form(i,fields)
                    payload=json.dumps(seed,ensure_ascii=False)
                    # Add missing fixture fields without losing previous edits; audit the upgrade.
                    existing=db.execute('SELECT revision,payload FROM demo_records WHERE entity=? AND id=?',(item['id'],identity)).fetchone()
                    if existing:
                        old=json.loads(existing['payload']);missing=set(fields)-set(old['fields'])
                        extend_work=item['id']=='work-reservation' and 'workForm' not in old
                        if missing or extend_work:
                            if extend_work:old['workForm']=synthetic_form(i,old['fields'])
                            old['fields'].update({key:fields[key] for key in missing});revision=existing['revision']+1
                            db.execute('UPDATE demo_records SET revision=?,payload=? WHERE entity=? AND id=?',(revision,json.dumps(old,ensure_ascii=False),item['id'],identity))
                            db.execute('INSERT INTO demo_events VALUES (?,?,?,?,?,?)',(item['id'],identity,revision,now(),'fixture_field_extension',json.dumps(dict(added=sorted(missing),workFormAdded=extend_work),ensure_ascii=False)))
                    # Seed each identity independently: restart preserves edits and is crash-safe.
                    db.execute('INSERT OR IGNORE INTO demo_records VALUES (?,?,?,?,?,?,?)',(item['id'],identity,1,'模拟企业'+['甲','乙','丙'][(i-1)%3],item['states'][(i-1)%4],f'2026-10-{12+(i%6):02}',payload))
                    db.execute('INSERT OR IGNORE INTO demo_events VALUES (?,?,?,?,?,?)',(item['id'],identity,1,'2026-10-17T00:00:00+00:00','seed','{"source":"synthetic_fixture_v1"}'))
            db.commit()
    def connect(self):
        db=sqlite3.connect(self.path,timeout=5);db.row_factory=sqlite3.Row;db.execute('PRAGMA foreign_keys=ON');return db
    @staticmethod
    def sample(entity,label,i):
        if label.startswith('是否'):return '是' if i%2 else '否'
        if '住址' in label or '身份证' in label or '联系方式' in label or '电话' in label or '证号' in label:return '未采集真实个人信息'
        if label=='值班日期':return f'2026-10-{12+(i%18):02}'
        if '级别' in label or '等级' in label: return ['低','一般','较大','重大'][(i-1)%4]
        if '企业' in label: return '模拟企业'+['甲','乙','丙'][(i-1)%3]
        if any(k in label for k in ['区域','地点','位置','驻地','场所']):return ['东部仓储区','公共道路区','北侧生产区','应急服务区'][(i-1)%4]+'（模拟）'
        if any(k in label for k in ['日期','时间','期限']):return f'2026-10-{18+(i%6):02} 09:00'
        if '责任' in label or '部门' in label:return '模拟安全管理组'+str(1+(i%3))
        if any(k in label for k in ['数量','容量','人数','读数','用量']):return str(i*12)
        if label=='计量单位':return 'kWh（模拟）'
        if label=='能源类别':return ['电','水','气','热'][(i-1)%4]
        if label=='作业类型':return TYPES[(i-1)%len(TYPES)]
        if '渠道' in label or '接入方式' in label:return '模拟联络接口，未发送通信'
        if '频次' in label or '周期' in label:return ['每班','每日','每周','每月'][(i-1)%4]
        if '版本' in label:return 'V1.'+str(i%3)
        if '阈值' in label:return '30（模拟单位）'
        if '示例值' in label:return str(10+i)
        if any(k in label for k in ['名称','描述','内容','项目','主题']):return MODULES[entity]['name']+'模拟样本'+str(i).zfill(2)
        return label+'示例'+str(i).zfill(2)
    @staticmethod
    def record(row):
        value=json.loads(row['payload'])
        if row['entity']=='work-reservation' and 'workForm' in value:value['fields']={**value['fields'],**list_fields(value['workForm'],row['id'])}
        for key in ('状态','隐患状态','排查状态','作业状态','巡检路线状态','排查清单状态'):
            if key in value['fields']:value['fields'][key]=row['state']
        return {**{k:row[k] for k in ('entity','id','revision','enterprise','state','date')},**value,'synthetic':True}
    def query_filter(self,entity,q='',state='',enterprise='',date_from='',date_to='',include_state=True):
        if entity not in MODULES:raise DemoError(404,'未知业务模块')
        if not isinstance(q,str) or len(q)>256:raise DemoError(400,'搜索内容不超过256字')
        if state and state not in MODULES[entity]['states']:raise DemoError(400,'状态无效')
        if enterprise and enterprise not in ENTERPRISES:raise DemoError(400,'模拟企业无效')
        for value in (date_from,date_to):
            if not isinstance(value,str):raise DemoError(400,'记录日期无效')
            if value:
                try:
                    if len(value)!=10 or date.fromisoformat(value).isoformat()!=value:raise ValueError()
                except ValueError:raise DemoError(400,'记录日期需为有效的YYYY-MM-DD日期')
        if date_from and date_to and date_from>date_to:raise DemoError(400,'开始日期不能晚于结束日期')
        where=['entity=?'];params=[entity]
        if enterprise:where.append('enterprise=?');params.append(enterprise)
        if include_state and state:where.append('state=?');params.append(state)
        if date_from:where.append('date>=?');params.append(date_from)
        if date_to:where.append('date<=?');params.append(date_to)
        if q:
            term=q.replace('\\','\\\\').replace('%','\\%').replace('_','\\_')
            where.append("(id LIKE ? ESCAPE '\\' OR payload LIKE ? ESCAPE '\\')");params.extend(['%'+term+'%']*2)
        return ' AND '.join(where),params

    def list(self,entity,q='',state='',enterprise='',page=1,date_from='',date_to=''):
        if type(page) is not int or not 1<=page<=100000:raise DemoError(400,'页码无效')
        args=dict(q=q,state=state,enterprise=enterprise,date_from=date_from,date_to=date_to)
        clause,params=self.query_filter(entity,**args)
        facet,facet_params=self.query_filter(entity,**args,include_state=False)
        with closing(self.connect()) as db:
            db.execute('BEGIN')
            total=db.execute('SELECT COUNT(*) FROM demo_records WHERE '+clause,params).fetchone()[0]
            rows=db.execute('SELECT * FROM demo_records WHERE '+clause+' ORDER BY id LIMIT 8 OFFSET ?',params+[(page-1)*8]).fetchall()
            counts={r[0]:r[1] for r in db.execute('SELECT state,COUNT(*) FROM demo_records WHERE '+facet+' GROUP BY state',facet_params)}
        return dict(records=[self.record(r) for r in rows],total=total,page=page,pageSize=8,counts=counts,synthetic=True,dateBasis='record_date_utc',countsBasis='same_query_except_selected_state')

    def summary(self,entity,q='',state='',enterprise='',date_from='',date_to=''):
        clause,params=self.query_filter(entity,q,state,enterprise,date_from,date_to)
        with closing(self.connect()) as db:
            data=[self.record(r) for r in db.execute('SELECT * FROM demo_records WHERE '+clause+' ORDER BY id',params)]
        counts={state:0 for state in MODULES[entity]['states']};dates={};enterprises={};groups={c:{} for c in MODULES[entity]['columns']}
        for record in data:
            counts[record['state']]+=1;dates[record['date']]=dates.get(record['date'],0)+1;enterprises[record['enterprise']]=enterprises.get(record['enterprise'],0)+1
            for key in groups:
                value=record['fields'].get(key,'未提供');groups[key][value]=groups[key].get(value,0)+1
        return dict(total=len(data),states=counts,dates=dates,enterprises=enterprises,groups=groups,synthetic=True,dateBasis='record_date_utc')
    def detail(self,entity,identity):
        with closing(self.connect()) as db:
            db.execute('BEGIN')
            row=db.execute('SELECT * FROM demo_records WHERE entity=? AND id=?',(entity,identity)).fetchone()
            if row is None:raise DemoError(404,'记录不存在')
            events=[dict(r) for r in db.execute('SELECT revision,at,kind,payload FROM demo_events WHERE entity=? AND id=? ORDER BY revision',(entity,identity))]
            plan=self._plan_load(db,identity) if entity=='plans' else None
        return dict(plan=plan,record=self.record(row),events=events,detailFields={label:self.sample(entity,label,int(identity[-3:]) if identity[-3:].isdigit() else 1) for label in ([] if plan or 'workForm' in json.loads(row['payload']) else MODULES.get(entity,{}).get('detailFields',[]))})
    def change(self,entity,identity,revision,note):
        if entity=='plans':raise DemoError(400,'请使用结构化预案评审发布操作')
        if entity not in MODULES:raise DemoError(404,'未知业务模块')
        if type(revision) is not int or not isinstance(note,str) or not note.strip() or len(note)>2000:raise DemoError(400,'需提供版本号和1至2000字的模拟处理说明')
        with closing(self.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM demo_records WHERE entity=? AND id=?',(entity,identity)).fetchone()
            if row is None:raise DemoError(404,'记录不存在')
            if row['revision']!=revision:raise DemoError(409,'记录已更新，请重新打开详情')
            states=MODULES[entity]['states'];index=states.index(row['state'])
            if index==len(states)-1:raise DemoError(409,'记录已到终态')
            if entity=='work-reservation' and index==0:
                try:normalize(json.loads(row['payload']).get('workForm'),True)
                except ValueError as error:raise DemoError(400,str(error))
            state=states[index+1];revision+=1
            db.execute('UPDATE demo_records SET revision=?,state=? WHERE entity=? AND id=?',(revision,state,entity,identity))
            db.execute('INSERT INTO demo_events VALUES (?,?,?,?,?,?)',(entity,identity,revision,now(),'simulation_transition',json.dumps(dict(previous=row['state'],state=state,note=note,actor='DEMO-OPERATOR'),ensure_ascii=False)))
            db.commit()
        return self.detail(entity,identity)
    def create(self,entity,fields,enterprise,note):
        item=MODULES.get(entity)
        if entity=='plans':raise DemoError(400,'请使用结构化预案表单')
        if entity=='work-reservation':raise DemoError(400,'请使用八类作业预约表单')
        if not item:raise DemoError(404,'未知业务模块')
        if not isinstance(fields,dict) or set(fields)!=set(item['columns']) or any(not isinstance(v,str) or not v.strip() or len(v)>256 for v in fields.values()):raise DemoError(400,'请完整填写所有字段，每项1至256字')
        if enterprise not in ['模拟企业甲','模拟企业乙','模拟企业丙']:raise DemoError(400,'只能选择模拟企业')
        if not isinstance(note,str) or len(note)>2000:raise DemoError(400,'备注不超过2000字')
        identity='DEMO-USER-'+uuid.uuid4().hex[:16];date=now()[:10];payload=json.dumps(dict(fields=fields,note=note),ensure_ascii=False)
        with closing(self.connect()) as db:
            db.execute('INSERT INTO demo_records VALUES (?,?,?,?,?,?,?)',(entity,identity,1,enterprise,item['states'][0],date,payload))
            db.execute('INSERT INTO demo_events VALUES (?,?,?,?,?,?)',(entity,identity,1,now(),'synthetic_create','{"actor":"DEMO-OPERATOR"}'));db.commit()
        return self.detail(entity,identity)

    def save_work_form(self,form,enterprise,note,action,identity,revision):
        if action not in ('draft','submit'):raise DemoError(400,'作业操作无效')
        if not isinstance(enterprise,str) or enterprise not in ENTERPRISES:raise DemoError(400,'只能选择模拟企业')
        if not isinstance(note,str) or len(note)>2000:raise DemoError(400,'备注不超过2000字')
        if identity is not None and (not isinstance(identity,str) or len(identity)>128):raise DemoError(400,'作业标识无效')
        if (identity is None and revision is not None) or (identity is not None and type(revision) is not int):raise DemoError(400,'作业版本无效')
        try:form=normalize(form,action=='submit')
        except (ValueError,TypeError) as error:raise DemoError(400,str(error))
        entity='work-reservation';states=MODULES[entity]['states'];at=now()
        with closing(self.connect()) as db:
            db.execute('BEGIN IMMEDIATE')
            previous=states[0];payload={}
            if identity is not None:
                row=db.execute('SELECT * FROM demo_records WHERE entity=? AND id=?',(entity,identity)).fetchone()
                if row is None:raise DemoError(404,'记录不存在')
                if row['revision']!=revision:raise DemoError(409,'记录已更新，请重新打开详情')
                if row['state']!=states[0]:raise DemoError(409,'仅草稿支持继续编辑')
                payload=json.loads(row['payload']);previous=row['state'];revision+=1
            else:identity='DEMO-USER-'+uuid.uuid4().hex[:16];revision=1
            payload.update(workForm=form,fields={**payload.get('fields',{}),**list_fields(form,identity)},note=note)
            state=states[1] if action=='submit' else states[0]
            if revision==1:db.execute('INSERT INTO demo_records VALUES (?,?,?,?,?,?,?)',(entity,identity,revision,enterprise,state,at[:10],json.dumps(payload,ensure_ascii=False)))
            else:db.execute('UPDATE demo_records SET revision=?,enterprise=?,state=?,payload=? WHERE entity=? AND id=?',(revision,enterprise,state,json.dumps(payload,ensure_ascii=False),entity,identity))
            event=dict(previous=previous,state=state,jobType=form['jobType'],note=note,actor='DEMO-OPERATOR')
            db.execute('INSERT INTO demo_events VALUES (?,?,?,?,?,?)',(entity,identity,revision,at,'work_simulated_submit' if action=='submit' else 'work_draft_save',json.dumps(event,ensure_ascii=False)))
            db.commit()
        return self.detail(entity,identity)
