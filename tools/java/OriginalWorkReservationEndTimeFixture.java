package xnby.replica;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.iemp.endanger.server.work.entity.WorkReservationBase;
import com.iemp.endanger.server.work.entity.WorkReservationPersonnel;
import com.iemp.endanger.server.work.entity.basic.Work;
import com.iemp.endanger.server.work.entity.vo.WorkReservationBaseVo;
import com.iemp.endanger.server.work.service.impl.WorkReservationBaseServiceImpl;
import java.lang.reflect.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.security.MessageDigest;
import java.util.*;

/** Executes the real service update method with strict in-memory mapper captures.
 * No SQL, authentication, HTTP, workflow or service restart is performed. */
@SuppressWarnings({"removal", "unchecked"})
public final class OriginalWorkReservationEndTimeFixture {
    static final Map<String,String> TYPES = new LinkedHashMap<>();
    static {
        TYPES.put("盲板抽堵作业", "WorkBlind");
        TYPES.put("受限空间作业", "WorkFiniteSpace");
        TYPES.put("动土作业", "WorkGroundbreaking");
        TYPES.put("动火作业", "WorkHot");
        TYPES.put("高处作业", "WorkHigh");
        TYPES.put("吊装作业", "WorkHoisting");
        TYPES.put("断路作业", "WorkOpenCircuit");
        TYPES.put("临时用电作业", "WorkTemporaryElectricity");
    }
    static void need(boolean ok, String code) {
        if (!ok) throw new IllegalStateException(code);
    }
    static final class Capture implements InvocationHandler {
        final List<String> calls = new ArrayList<>();
        Work work;
        WorkReservationBase base;
        List<WorkReservationPersonnel> people;
        public Object invoke(Object proxy, Method method, Object[] args) {
            if (method.getDeclaringClass()==Object.class) {
                return switch(method.getName()) {
                    case "toString" -> "OWN_CAPTURE_MAPPER";
                    case "hashCode" -> System.identityHashCode(proxy);
                    case "equals" -> proxy == args[0];
                    default -> throw new IllegalStateException("OBJECT_METHOD_NOT_ALLOWED");
                };
            }
            String owner=method.getDeclaringClass().getName();
            if (method.getName().equals("delete") && args.length==1) {
                calls.add("person-delete"); return 1;
            }
            if (method.getName().equals("updateById") && args.length==1) {
                if(args[0] instanceof Work w) {
                    need(work==null,"SINGLE_WORK_WRITE"); work=w; calls.add("work-update");
                } else if(args[0] instanceof WorkReservationBase b) {
                    need(base==null,"SINGLE_BASE_WRITE"); base=b; calls.add("base-update");
                } else throw new IllegalStateException("UNKNOWN_UPDATE_ENTITY");
                return 1;
            }
            if (method.getName().equals("insertBatch") && args.length==1) {
                people = new ArrayList<>((Collection<WorkReservationPersonnel>)args[0]);
                calls.add("person-insert"); return people.size();
            }
            throw new IllegalStateException("UNEXPECTED_MAPPER_METHOD:"+owner+":"+method.getName());
        }
        Object proxy(Class<?> cls) {
            return Proxy.newProxyInstance(cls.getClassLoader(),new Class<?>[]{cls},this);
        }
    }
    static WorkReservationBaseServiceImpl service(Capture c) throws Exception {
        Constructor<?>[] constructors=WorkReservationBaseServiceImpl.class.getDeclaredConstructors();
        need(constructors.length==1,"ONE_REAL_SERVICE_CONSTRUCTOR");
        Constructor<?> ctor=constructors[0]; Object[] deps=new Object[ctor.getParameterCount()];
        for(int i=0;i<deps.length;i++) {
            Class<?> type=ctor.getParameterTypes()[i];
            deps[i]=type.isInterface()?c.proxy(type):null;
        }
        WorkReservationBaseServiceImpl result=(WorkReservationBaseServiceImpl)ctor.newInstance(deps);
        boolean set=false;
        for(Class<?> type=result.getClass();type!=Object.class;type=type.getSuperclass()) {
            for(Field field:type.getDeclaredFields()) if(field.getName().equals("baseMapper")) {
                field.setAccessible(true);
                field.set(result,c.proxy(Class.forName("com.iemp.endanger.server.work.mapper.WorkReservationBaseMapper")));
                set=true;
            }
        }
        need(set,"REAL_BASE_MAPPER_FIELD_REQUIRED"); return result;
    }
    static void one(String type, boolean candidate, boolean endPresent, List<Object> cases) throws Exception {
        Capture c=new Capture(); WorkReservationBaseServiceImpl service=service(c);
        WorkReservationBase b=new WorkReservationBase();
        b.setId("OWN_BASE"); b.setWorkNo("OWN_NO"); b.setJobType(type);
        b.setProcessName("暂存"); b.setWorkPerson("OWN_PERSON");
        b.setStartTime(LocalDateTime.of(2026,10,29,9,0));
        b.setEndTime(endPresent?LocalDateTime.of(2026,10,29,11,0):null);
        b.setOtherId(null);
        Work w=(Work)Class.forName("com.iemp.endanger.server.work.entity."+TYPES.get(type)).getDeclaredConstructor().newInstance();
        w.setId("OWN_WORK"); w.setJobContent("OWN_EDITED_CONTENT");
        WorkReservationPersonnel p=new WorkReservationPersonnel();p.setId("OWN_PRIOR_PERSON");p.setType("2");
        WorkReservationBaseVo vo=new WorkReservationBaseVo();vo.setBase(b);vo.setWork(w);vo.setList(new ArrayList<>(List.of(p)));
        need(service.updateById(vo),"REAL_EDIT_TRUE_REQUIRED");
        need(c.calls.equals(List.of("person-delete","work-update","person-insert","base-update")),"ORIGINAL_WRITE_SEQUENCE_PRESERVED");
        need(c.work!=null && c.work.getClass()==w.getClass() && c.work.getId().equals("OWN_WORK"),"CORRECT_TYPED_WORK_AND_ID");
        need(b.getStartTime().equals(c.work.getStartTime()),"START_TIME_UNCHANGED");
        need("OWN_EDITED_CONTENT".equals(c.work.getJobContent()) && "暂存".equals(c.work.getProcessName()),"CONTENT_AND_DRAFT_STATUS_UNCHANGED");
        need(c.base==b && c.people.size()==1 && c.people.get(0).getWorkReservationBaseId().equals("OWN_BASE") && !c.people.get(0).getId().equals("OWN_PRIOR_PERSON"),"ORIGINAL_PERSON_REPLACEMENT_PRESERVED");
        if(candidate)need(Objects.equals(b.getEndTime(),c.work.getEndTime()),"END_TIME_SYNCHRONIZED");
        else need(c.work.getEndTime()==null && b.getEndTime()!=null,"ORIGINAL_MISSING_END_ASSIGNMENT_REPRODUCED");
        cases.add(Map.of("type",type,"endPresent",endPresent,"typedEntityPreserved",true,"startContentStatusAndPersonBehaviorPreserved",true,"endAssignmentExpected",candidate));
    }
    public static void main(String[] args) throws Exception {
        need(args.length==2,"MODE_AND_FRESH_OUTPUT_REQUIRED");
        boolean candidate=args[0].equals("candidate"); need(candidate||args[0].equals("original"),"EXACT_MODE_REQUIRED");
        Path out=Path.of(args[1]).toAbsolutePath(); need(!Files.exists(out)&&Files.isDirectory(out.getParent()),"FRESH_OUTPUT_REQUIRED");
        OriginalProcessBoundary boundary=new OriginalProcessBoundary(out.getParent(),Set.of(),false);
        System.setSecurityManager(boundary);
        int checks=0;
        try {boundary.checkConnect("synthetic.invalid",443);}catch(SecurityException e){checks++;}
        try {boundary.checkExec("OWN_NEVER_EXECUTED");}catch(SecurityException e){checks++;}
        need(checks==2,"BOUNDARY_SELF_CHECKS_REQUIRED");
        Map<String,Integer> denials=boundary.deniedCounts(); List<Object> cases=new ArrayList<>();
        for(String type:TYPES.keySet()) {
            one(type,candidate,true,cases);
            if(candidate)one(type,true,false,cases);
        }
        need(denials.equals(boundary.deniedCounts()),"NO_UNEXPECTED_IO_ALLOWED");
        Map<String,Object> result=new LinkedHashMap<>();
        result.put("mode",args[0]);result.put("cases",cases);result.put("realServiceMethodExecuted",true);
        var edit=WorkReservationBaseServiceImpl.class.getMethod("updateById",WorkReservationBaseVo.class);
        var tx=edit.getAnnotation(org.springframework.transaction.annotation.Transactional.class);
        if(candidate)need(tx!=null&&Arrays.asList(tx.rollbackFor()).contains(Exception.class),"EXPLICIT_EDIT_EXCEPTION_ROLLBACK_REQUIRED");
        result.put("explicitEditRollbackForException",tx!=null&&Arrays.asList(tx.rollbackFor()).contains(Exception.class));
        try (var stream=WorkReservationBaseServiceImpl.class.getResourceAsStream("WorkReservationBaseServiceImpl.class")) {
            need(stream!=null,"LOADED_SERVICE_BYTES_REQUIRED");
            result.put("loadedServiceClassSHA256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(stream.readAllBytes())));
        }
        result.put("strictInMemoryMapperCapture",true);result.put("databaseOrAuthenticationUsed",false);
        result.put("networkAttemptsAfterSelfChecks",0);result.put("runtimeRestartedOrInstalled",false);
        Files.writeString(out,new ObjectMapper().writeValueAsString(result)+"\n",StandardOpenOption.CREATE_NEW);
        System.out.println("WORK_RESERVATION_END_TIME_CASES="+cases.size()+" MODE="+args[0]);
    }
}
