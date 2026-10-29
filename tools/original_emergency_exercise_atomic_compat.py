"""Compose a pinned original exercise service with checked parent/file transactions."""
from pathlib import Path
from hashlib import sha256
PIN='e4bcd5e30de058d0c7389ba6ad3c55a9b94d9179a30444dba809a81b6a074715'
ANNOTATION='    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)\n'
def once(text,old,new):
 if text.count(old)!=1:raise ValueError('EXACT_ORIGINAL_EXERCISE_ANCHOR_REQUIRED')
 return text.replace(old,new,1)
def compile_source(raw):
 if sha256(raw).hexdigest()!=PIN:raise ValueError('EXACT_ORIGINAL_EXERCISE_SOURCE_REQUIRED')
 s=raw.decode('utf8').replace('\r\n','\n');s=once(s,'@RequiredArgsConstructor\n','');end=s.rfind('\n}');assert end>0;s=s[:end]+'''\n    public EmergencyExerciseServiceImpl(BaseFileService baseFileService) {
        this.baseFileService = baseFileService;
    }
'''+s[end:];return s
def candidate(raw):
 s=compile_source(raw)
 for signature in ['    public boolean save(EmergencyExerciseEntity entity){','    public Boolean saveEmergencyExerciseList(EmergencyExerciseSave save) {','    public Boolean delete(String id) {']:s=once(s,signature,ANNOTATION+signature)
 s=once(s,'''        getBaseMapper().insert(entity);
        baseFileService.insertFile(entity.getFileList(),entity.getId());
        return true;''','''        if(entity == null) return false;
        if(getBaseMapper().insert(entity) < 1) return rollbackExerciseFalse();
        return persistExerciseFiles(entity.getFileList(),entity.getId());''')
 s=once(s,'        boolean flag = false;\n','        if(save == null) return false;\n        boolean flag = false;\n')
 s=once(s,'                emergencyExerciseEntity.setEmergencyPlanId(save.getEmergencyPlanId());','                if(emergencyExerciseEntity == null) return false;\n                emergencyExerciseEntity.setEmergencyPlanId(save.getEmergencyPlanId());')
 s=once(s,'''            if(flag){
                for (EmergencyExerciseEntity emergencyExerciseEntity : emergencyExerciseEntityList) {
                    if(emergencyExerciseEntity.getFileList() != null){
                        baseFileService.insertFile(emergencyExerciseEntity.getFileList(),emergencyExerciseEntity.getId());
                    }
                }
            }''','''            if(!flag) return rollbackExerciseFalse();
            java.util.Map<String,EmergencyExerciseEntity> finalRows = new java.util.LinkedHashMap<>();
            for(EmergencyExerciseEntity entity : emergencyExerciseEntityList) {
                if(entity.getId() == null || entity.getId().isBlank()) return rollbackExerciseFalse();
                EmergencyExerciseEntity stored = getBaseMapper().selectById(entity.getId());
                if(stored == null) return rollbackExerciseFalse();
                finalRows.put(stored.getId(),entity);
            }
            for(EmergencyExerciseEntity entity : finalRows.values()) {
                if(!matchesSavedExercise(entity)) return rollbackExerciseFalse();
            }
            for(EmergencyExerciseEntity entity : emergencyExerciseEntityList) {
                if(!persistExerciseFiles(entity.getFileList(),entity.getId())) return false;
            }''')
 s=once(s,'''        removeById(id);
        baseFileService.deleteFile(id);
        return Boolean.TRUE;''','''        if(id == null || id.isBlank()) return false;
        if(!removeById(id)) return rollbackExerciseFalse();
        baseFileService.deleteFile(id);
        List<BaseFile> remaining = baseFileService.getFileList(id);
        if(remaining == null || !remaining.isEmpty()) return rollbackExerciseFalse();
        return Boolean.TRUE;''')
 helper='''
    private boolean rollbackExerciseFalse() {
        org.springframework.transaction.interceptor.TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
        return false;
    }

    private boolean persistExerciseFiles(List<BaseFile> files,String id) {
        if(files != null) for(BaseFile file : files) {
            file.setCorrelationId(id);
            file.setId(null);
            if(!baseFileService.save(file)) return rollbackExerciseFalse();
        }
        return true;
    }

    private boolean matchesSavedExercise(EmergencyExerciseEntity entity) {
        QueryWrapper<EmergencyExerciseEntity> q = new QueryWrapper<>();
        q.eq("id",entity.getId());
'''
 fields=[('emergency_plan_id','EmergencyPlanId'),('exercise_location','ExerciseLocation'),('organize_department','OrganizeDepartment'),('commander_chief','CommanderChief'),('participants','Participants'),('cooperating_unit','CooperatingUnit'),('exercise_type','ExerciseType'),('exercise_device','ExerciseDevice'),('exercise_describe','ExerciseDescribe'),('exercise_special_situation','ExerciseSpecialSituation'),('problems_andmeasures','ProblemsAndmeasures')]
 for column,getter in fields:helper+='        q.apply(entity.get'+getter+'() != null,"BINARY `'+column+'` = BINARY {0}",entity.get'+getter+'());\n'
 helper+='''        q.eq(entity.getExerciseTime() != null,"exercise_time",entity.getExerciseTime());
        q.apply(entity.getCreatedAt() != null,"`created_at` = CAST({0} AS DATETIME(0))",entity.getCreatedAt());
        return getBaseMapper().selectOne(q.last("FOR UPDATE")) != null;
    }
'''
 end=s.rfind('\n}');return (s[:end]+helper+s[end:]).encode('utf8')
def build(source,root):
 source,root=Path(source),Path(root);raw=source.read_bytes();rel=Path('com/iemp/endanger/server/emergency/service/impl/EmergencyExerciseServiceImpl.java');rows={}
 for mode,data in [('reference',compile_source(raw).encode()),('candidate',candidate(raw))]:
  p=root/(mode+'-src')/rel
  if p.exists():raise ValueError('FRESH_EXERCISE_SOURCE_OUTPUT_REQUIRED')
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);rows[mode]={'path':str(p),'SHA256':sha256(data).hexdigest()}
 return rows
