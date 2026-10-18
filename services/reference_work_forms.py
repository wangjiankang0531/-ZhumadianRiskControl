"""Observed basic special-work forms; synthetic workflow, not production approval rules."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation

SCHEMA_ID = 'xnby.work_reservation.v1'
TYPES = ['动火作业','受限空间作业','盲板抽堵作业','高处作业','吊装作业','临时用电作业','动土作业','断路作业']
ROLES = ['作业人员','施工方监护人','基层单位监护人']
PERSON_COLUMNS = ['姓名','工种','身份证号','联系方式','所在单位','是否承包商']
ENTERPRISES = ['模拟企业甲','模拟企业乙','模拟企业丙']

def field(key, kind='text', required=True, options=None):
    result = dict(key=key,kind=kind,required=required,maxLength=200 if kind=='textarea' else 256)
    if options: result['options']=options
    return result

COMMON = [field('作业编号',required=False),field('作业申请单位'),field('作业申请时间','datetime'),
          field('作业区域'),field('作业内容','textarea'),field('位置坐标'),
          field('是否为承包商','select',options=['否','是']),field('作业单位'),field('作业负责人'),
          field('风险辨识结果','textarea',False),field('实施开始时间','datetime'),field('实施结束时间','datetime'),
          field('作业方案选择',required=False),field('关联作业票',required=False)]
SPECIFIC = {
 '动火作业':[field('动火级别','select',options=['特级动火作业','一级动火作业','二级动火作业']),field('动火方式'),field('动火地点及部位')],
 '受限空间作业':[field('受限空间名称'),field('受限空间内原有介质名称')],
 '盲板抽堵作业':[field(k,'textarea' if k=='盲板位置图及编号' else 'text') for k in ['作业类别','设备、管道名称','管道参数介质','管道参数温度','管道参数压力','盲板参数材质','盲板参数规格','盲板参数编号','盲板位置图及编号']],
 '高处作业':[field('作业地点'),field('作业高度','positive'),field('高处作业级别','select',options=['一级高处作业','二级高处作业','三级高处作业','四级高处作业'])],
 '吊装作业':[field('吊装地点'),field('吊具名称'),field('吊物质量(t)','positive'),field('吊装作业级别','select',options=['一级吊装作业','二级吊装作业','三级吊装作业'])],
 '临时用电作业':[field('作业地点'),field('电源接入点'),field('许可用电功率','positive'),field('工作电压','positive'),field('用电设备名称'),field('额定功率','positive')],
 '动土作业':[field('作业地点'),field('作业范围、内容、方式')],
 '断路作业':[field('涉及相关单位'),field('断路原因','textarea'),field('断路地段示意图及相关说明','textarea')],
}

def fields_for(kind):
    if kind not in TYPES: raise ValueError('请选择八类作业之一')
    return [{**f, 'key':'吊物内容'} if kind=='吊装作业' and f['key']=='作业内容' else dict(f) for f in COMMON]+SPECIFIC[kind]

def catalog_schema():
    return dict(schema=SCHEMA_ID,types=[dict(name=t,fields=fields_for(t)) for t in TYPES],roles=ROLES,
                personColumns=PERSON_COLUMNS,maxPeoplePerRole=12,
                requiredRoles={'受限空间作业':['作业人员','基层单位监护人']},defaultRequiredRoles=['作业人员'],
                policy='基础字段参考已观察页面；数值、时间及人员完整性为模拟验收规则，未接入真实审批。',timeZone='Asia/Shanghai')

def normalize(form, submit=False):
    if not isinstance(form,dict) or set(form)!={'schema','jobType','values','people'} or form.get('schema')!=SCHEMA_ID: raise ValueError('作业表单格式无效')
    definitions=fields_for(form['jobType']);known={f['key']:f for f in definitions}
    if not isinstance(form['values'],dict) or set(form['values'])-set(known):raise ValueError('存在不属于该作业类型的字段')
    values={}
    for key,f in known.items():
        value=form['values'].get(key,'')
        if not isinstance(value,str) or len(value)>f['maxLength']:raise ValueError(key+'内容过长或格式无效')
        value=value.strip()
        if submit and f['required'] and not value:raise ValueError('请填写'+key)
        if value:
            if f['kind']=='select' and value not in f['options']:raise ValueError(key+'选项无效')
            if f['kind']=='positive':
                try: number=Decimal(value)
                except InvalidOperation:raise ValueError(key+'需为有效正数')
                if not number.is_finite() or number<=0:raise ValueError(key+'需为有效正数')
            if f['kind']=='datetime':
                try:
                    moment=datetime.fromisoformat(value.replace('Z','+00:00'))
                    if moment.tzinfo is None:moment=moment.replace(tzinfo=timezone(timedelta(hours=8)))
                    value=moment.astimezone(timezone.utc).isoformat(timespec='seconds')
                except (ValueError,OverflowError):raise ValueError(key+'日期格式无效')
        values[key]=value
    if values['实施开始时间'] and values['实施结束时间'] and values['实施开始时间']>=values['实施结束时间']:raise ValueError('实施结束时间必须晚于开始时间')
    raw=form['people']
    if not isinstance(raw,dict) or set(raw)-set(ROLES):raise ValueError('人员分组无效')
    people={}
    required=['作业人员','基层单位监护人'] if form['jobType']=='受限空间作业' else ['作业人员']
    for role in ROLES:
        rows=raw.get(role,[])
        if not isinstance(rows,list) or len(rows)>12:raise ValueError(role+'最多12名模拟人员')
        if submit and role in required and not rows:raise ValueError('请添加'+role)
        people[role]=[]
        for row in rows:
            if not isinstance(row,dict) or set(row)!=set(PERSON_COLUMNS) or any(not isinstance(v,str) or len(v)>128 for v in row.values()):raise ValueError('人员字段无效')
            row={k:v.strip() for k,v in row.items()}
            if row['是否承包商'] not in ('是','否'):raise ValueError('人员承包商选项无效')
            if submit and any(not row[k] for k in PERSON_COLUMNS):raise ValueError('请完整填写'+role+'的模拟人员字段')
            people[role].append(row)
    return dict(schema=SCHEMA_ID,jobType=form['jobType'],values=values,people=people)

def list_fields(form,identity):
    v=form['values'];kind=form['jobType']
    return {'作业编号':v.get('作业编号') or identity,'作业类型':kind,'申请单位':v.get('作业申请单位',''),
            '作业级别':next((v[k] for k in ('动火级别','高处作业级别','吊装作业级别') if v.get(k)), '—'),
            '作业区域':v.get('作业区域',''),'作业内容':v.get('吊物内容' if kind=='吊装作业' else '作业内容',''),
            '开始实施时间':v.get('实施开始时间','')}

def synthetic_form(i,old_fields=None):
    old_fields=old_fields or {};old=old_fields.get('作业类型','');kind=next((t for t in TYPES if t==old or t.removesuffix('作业')==old),TYPES[(i-1)%8])
    values={}
    for f in fields_for(kind):
        k=f['key'];values[k]=f['options'][0] if f['kind']=='select' else '12' if f['kind']=='positive' else '2026-10-18T'+('11:00' if k=='实施结束时间' else '09:00')+'+08:00' if f['kind']=='datetime' else k+'模拟样本'+str(i)
    values.update({'作业申请单位':old_fields.get('申请单位','模拟企业甲'),'作业区域':old_fields.get('作业区域','模拟仓储区'),'位置坐标':'模拟本地坐标(120,80)'})
    for k in ('作业编号','作业内容'):
        if k in values and k in old_fields:values[k]=old_fields[k]
    person=dict(zip(PERSON_COLUMNS,['模拟人员甲','模拟检修','DEMO-ID-A','DEMO-CONTACT-A','模拟施工单位','否']))
    return normalize(dict(schema=SCHEMA_ID,jobType=kind,values=values,people={role:[dict(person)] for role in ROLES}),True)
