"""Optional, explicitly synthetic nearby geometry and business records for manual QA only."""
def extend(probe):
    rows=[
      ('qa-near-boundary-a','合成A企业边界','region',[[-250,-2290,65],[-150,-2290,65],[-150,-2190,65],[-250,-2190,65]],'enterprise-boundary','A'),
      ('qa-near-video','合成公共视频点','point',[[-190,-2230,65]],'video',None),
      ('qa-near-access','合成公共卡口','point',[[-230,-2240,65]],'access',None),
      ('qa-near-fire','合成公共消防设施','point',[[-200,-2280,65]],'firefighting',None),
      ('qa-near-team','合成公共应急队伍位置','point',[[-170,-2240,65]],'emergency-team',None),
      ('qa-near-store-a','合成A企业物资库','point',[[-200,-2190,65]],'emergency-store','A'),
      ('qa-near-route','合成公共疏散通道','line',[[-1500,-2260,65],[1500,-2260,65]],'road',None),
      ('qa-near-boundary-b','合成B企业专属近邻点','point',[[-200,-2241,65]],'enterprise','B'),
      ('qa-near-unlisted','合成未授权近邻点','point',[[-200,-2242,65]],'public-area',None),
      ('qa-near-far-video','合成一公里外公共视频点','point',[[-200,-1240,65]],'video',None),
      ('qa-near-public-area','合成公共区域边界','region',[[-260,-2300,65],[-140,-2300,65],[-140,-2180,65],[-260,-2180,65]],'public-area',None),
    ]
    objects=[];public=[]
    for ident,name,kind,positions,category,owner in rows:
        feature={'id':ident,'name':name,'type':kind,'positions':positions,'style':{'color':'#33B6C5','fillColor':'#23A6AD','fillOpacity':.12,'icon':'pin'},'label':{'text':name}}
        if owner:
            binding={'sourceSystem':'QA','objectType':('emergency-resource' if category=='emergency-store' else category),'businessId':ident,'enterpriseId':owner};feature['business']=binding
            attributes=[{'label':'数据用途','value':'全部为合成验收信息，不用于实际监管或应急调度'}]
            if category=='enterprise-boundary':attributes.extend([{'label':'风险等级（合成）','value':'测试分组A，非正式风险定级'},{'label':'联系人（合成）','value':'合成联系人A，无真实电话'},{'label':'分包监管人员（合成）','value':'合成监管岗位A'}])
            if category=='emergency-store':attributes.extend([{'label':'物资说明（合成）','value':'合成测试物资，不代表实际可用库存'},{'label':'值守岗位（合成）','value':'合成A企业物资岗位'}])
            probe.records['records'].append({**binding,'name':name+'台账','updatedAt':probe.records['exportedAt'],'attributes':attributes})
        elif ident!='qa-near-unlisted':public.append(ident)
        probe.layers['layers'][0]['features'].append(feature);objects.append({'spatialId':ident,'category':category})
    probe.write('business.json',probe.records)
    return objects,public
