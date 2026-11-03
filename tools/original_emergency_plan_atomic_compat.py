"""Pinned original plan service: atomic parent/relations/files without model changes."""
from hashlib import sha256
PIN='b9cebe7b016f30f24d34061c0710f5c392d74f78831ba12bf26fbca6ca1dc5b0'
ANNOTATION='    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)\n'
RELATIONS=[('emergencyPlanExpertRelatedMapper','EmergencyPlanExpertRelatedEntity'),('emergencyPlanGoodsManageRelatedMapper','EmergencyPlanGoodsManageRelatedEntity'),('emergencyPlanTeamRelatedMapper','EmergencyPlanTeamRelatedEntity'),('emergencyPlanCompanyMapper','EmergencyPlanCompanyEntity'),('emergencyPlanDeputyHeadMapper','EmergencyPlanDeputyHeadEntity'),('emergencyPlanOthermemberMapper','EmergencyPlanOthermemberEntity')]
FIELDS=['EmergencyPlanName','EmergencyPlanType','AccidentType','CommanderName','CommanderPhone','DisposalMeasures','IsFilings','FilingsNumber','CreateDept','CreatedBy','UpdatedBy']
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('EXACT_ORIGINAL_PLAN_ANCHOR_REQUIRED:'+a[:55])
 return s.replace(a,b,1)
def reference(raw):
 if sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_PLAN_SOURCE_REQUIRED')
 s=raw.decode('utf-8').replace('\r\n','\n');s=one(s,'@RequiredArgsConstructor\n','')
 fields=[('EmergencyExpertsMapper','emergencyExpertMapper'),('MaterialsMapper','emergencyGoodsManageMapper'),('FirstAidTeamsMapper','emergencyTeamMapper'),*[(e.replace('Entity','Mapper'),m) for m,e in [*RELATIONS[3:],*RELATIONS[:3]]],('BaseFileService','baseFileService')]
 ctor='\n    public EmergencyPlanServiceImpl('+','.join(t+' '+n for t,n in fields)+') {\n'+''.join('        this.'+n+'='+n+';\n' for t,n in fields)+'    }\n'
 pos=s.rfind('\n}');return s[:pos]+ctor+s[pos:]
def candidate(raw):
 s=reference(raw)
 for signature in ['    public Boolean insert(EmergencyPlanEntity emergencyPlan) {','    public Boolean modify(EmergencyPlanEntity emergencyPlan) {','    public Boolean delete(String id) {']:s=one(s,signature,ANNOTATION+signature)
 s=one(s,'        EmergencyPlanEntity emergencyPlanEntity = getById(id);','        EmergencyPlanEntity emergencyPlanEntity = getById(id);\n        if(emergencyPlanEntity == null) return null;')
 s=one(s,'        LoginUser loginUser = SecurityContextHolder.getLoginUser();','        if(emergencyPlan == null) return false;\n        LoginUser loginUser = SecurityContextHolder.getLoginUser();')
 s=one(s,'        save(emergencyPlan);','        if(!save(emergencyPlan)) return rollbackPlanFalse();')
 s=one(s,'            baseFileService.insertFile(emergencyPlan.getFileList(),emergencyPlan.getId());','            persistPlanFiles(emergencyPlan.getFileList(),emergencyPlan.getId());')
 s=one(s,'        updateById(emergencyPlan);','''        if(emergencyPlan == null || emergencyPlan.getId() == null || emergencyPlan.getId().isBlank()) return false;
        EmergencyPlanEntity before = getBaseMapper().selectOne(new QueryWrapper<EmergencyPlanEntity>().eq("id",emergencyPlan.getId()).last("FOR UPDATE"));
        if(before == null) return false;
        if(!updateById(emergencyPlan) && !matchesRequestedPlan(emergencyPlan)) return rollbackPlanFalse();''')
 for owner,entity in RELATIONS:
  a='        '+owner+'.delete(Wrappers.<'+entity+'>lambdaQuery().eq('+entity+'::getEmergencyPlanId, emergencyPlan.getId()));'
  s=one(s,a,a+'\n        requirePlanChildrenCleared('+owner+'.selectCount(new QueryWrapper<'+entity+'>().eq("emergency_plan_id", emergencyPlan.getId())));')
 s=one(s,'            baseFileService.modifyFile(emergencyPlan.getFileList(),emergencyPlan.getId());','''            baseFileService.deleteFile(emergencyPlan.getId());
            requirePlanFilesCleared(emergencyPlan.getId());
            persistPlanFiles(emergencyPlan.getFileList(),emergencyPlan.getId());''')
 s=one(s,'        removeById(id);','''        if(id == null || id.isBlank()) return false;
        EmergencyPlanEntity before = getBaseMapper().selectOne(new QueryWrapper<EmergencyPlanEntity>().eq("id",id).last("FOR UPDATE"));
        if(before == null) return false;
        if(!removeById(id)) return rollbackPlanFalse();''')
 for owner,entity in RELATIONS:
  a='        '+owner+'.delete(Wrappers.<'+entity+'>lambdaQuery().eq('+entity+'::getEmergencyPlanId, id));'
  s=one(s,a,a+'\n        requirePlanChildrenCleared('+owner+'.selectCount(new QueryWrapper<'+entity+'>().eq("emergency_plan_id", id)));')
 s=one(s,'        baseFileService.deleteFile(id);','        baseFileService.deleteFile(id);\n        requirePlanFilesCleared(id);')
 for owner,var in [('emergencyPlanExpertRelatedMapper','emergencyPlanExpertRelated'),('emergencyPlanGoodsManageRelatedMapper','emergencyPlanGoodsManageRelated'),('emergencyPlanTeamRelatedMapper','emergencyPlanTeamRelated'),('emergencyPlanCompanyMapper','emergencyPlanCompany'),('emergencyPlanDeputyHeadMapper','emergencyPlanDeputyHead'),('emergencyPlanOthermemberMapper','emergencyPlanOthermember')]:
  s=one(s,'                '+owner+'.insert('+var+');','                requirePlanWrite('+owner+'.insert('+var+'));')
 helper='''
    private boolean rollbackPlanFalse() {
        org.springframework.transaction.interceptor.TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
        return false;
    }
    private void requirePlanWrite(int affected) {
        if(affected < 1) throw new IllegalStateException("OWN_PLAN_ASSOCIATION_WRITE_NOT_COMPLETED");
    }
    private void requirePlanChildrenCleared(Long remaining) {
        if(remaining == null || remaining != 0L) throw new IllegalStateException("OWN_PLAN_ASSOCIATION_DELETE_NOT_COMPLETED");
    }
    private void requirePlanFilesCleared(String id) {
        List<BaseFile> remaining=baseFileService.getFileList(id);
        if(remaining == null || !remaining.isEmpty()) throw new IllegalStateException("OWN_PLAN_ATTACHMENT_DELETE_NOT_COMPLETED");
    }
    private void persistPlanFiles(List<BaseFile> files,String id) {
        for(BaseFile file:files) {
            file.setCorrelationId(id);
            file.setId(null);
            if(!baseFileService.save(file)) throw new IllegalStateException("OWN_PLAN_ATTACHMENT_WRITE_NOT_COMPLETED");
        }
    }
    private boolean matchesRequestedPlan(EmergencyPlanEntity entity) {
        QueryWrapper<EmergencyPlanEntity> q=new QueryWrapper<>();
        q.eq("id",entity.getId());
'''
 helper+='''        var table=com.baomidou.mybatisplus.core.metadata.TableInfoHelper.getTableInfo(EmergencyPlanEntity.class);
        if(table == null) return false;
        var values=org.apache.ibatis.reflection.SystemMetaObject.forObject(entity);
        for(var field:table.getFieldList()) {
            if(field.isLogicDelete()) continue;
            if(field.getUpdate() != null && !field.getUpdate().isBlank()) return false;
            String column=field.getColumn().replace("`", "");
            if(!column.matches("[a-z_]+")) return false;
            Object value=values.getValue(field.getProperty());
            boolean included=field.isWithUpdateFill();
            if(!included) {
                switch(field.getUpdateStrategy().name()) {
                    case "ALWAYS": case "IGNORED": included=true; break;
                    case "NOT_NULL": included=value != null; break;
                    case "NOT_EMPTY": included=value != null && (!(value instanceof CharSequence) || ((CharSequence)value).length() != 0); break;
                    case "NEVER": included=false; break;
                    default: return false;
                }
            }
            if(!included) continue;
            if(value == null) q.isNull("`"+column+"`");
            else if(value instanceof CharSequence) q.apply("BINARY `"+column+"` = BINARY {0}",value);
            else if(value instanceof java.time.LocalDateTime) q.apply("`"+column+"` = CAST({0} AS DATETIME(0))",value);
            else if(value instanceof Number || value instanceof Boolean) q.eq("`"+column+"`",value);
            else return false;
        }
        return getBaseMapper().selectOne(q.last("FOR UPDATE")) != null;
    }
'''
 pos=s.rfind('\n}');return (s[:pos]+helper+s[pos:]).encode('utf-8')
