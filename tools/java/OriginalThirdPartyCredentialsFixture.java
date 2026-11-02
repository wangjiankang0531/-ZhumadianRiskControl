package xnby.replica;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.cqweh.cloud.security.core.SessionManager;
import com.cqweh.cloud.security.model.LoginUser;
import com.cqweh.cloud.security.model.Session;
import com.cqweh.cloud.security.util.SecurityContextHolder;
import com.iemp.endanger.server.safetyBasic.entity.*;
import com.iemp.endanger.server.safetyBasic.entity.vo.ThirdPartyUnitInfoVo;
import com.iemp.endanger.server.safetyBasic.service.impl.ThirdPartyUnitInfoServiceImpl;
import com.iemp.endanger.util.http.DockUtil;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.context.ApplicationContext;
import org.springframework.web.context.request.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.time.*;
import java.util.*;

/** Real packaged save method, synthetic identity, closed in-memory mappers and
 * a recording docking replacement. No SQL, login, Redis, HTTP or real docking. */
@SuppressWarnings({"removal", "unchecked"})
public final class OriginalThirdPartyCredentialsFixture {
    static final ObjectMapper JSON = new ObjectMapper();
    static final String USER="OWN_THIRD_PARTY_USER", DEPT="OWN_THIRD_PARTY_DEPT";
    static void need(boolean yes,String message){if(!yes)throw new IllegalStateException(message);}
    static final class SyntheticSessions extends SessionManager {
        int reads;final String user;
        static com.cqweh.cloud.cache.core.CacheManager cache(){
            return (com.cqweh.cloud.cache.core.CacheManager)Proxy.newProxyInstance(
                OriginalThirdPartyCredentialsFixture.class.getClassLoader(),
                new Class<?>[]{com.cqweh.cloud.cache.core.CacheManager.class},(p,m,a)->{
                    need(m.getName().equals("getCache")&&a.length==1&&"session".equals(a[0]),"CONSTRUCTOR_ONLY_SYNTHETIC_CACHE");return null;});
        }
        SyntheticSessions()throws Exception{super(cache(),null,null);user=JSON.writeValueAsString(new LoginUser().setUserId(USER).setDeptId(DEPT).setName("Own synthetic person").setUserName("own-synthetic-person"));}
        @Override public String getUser(String key){need(key!=null&&key.endsWith(USER),"SYNTHETIC_USER_KEY_ONLY");reads++;return user;}
        @Override public Session getOrCreateSession(String key){throw new IllegalStateException("NO_AUTH_SESSION_CREATION");}
        @Override public void deleteSession(String key){throw new IllegalStateException("NO_AUTH_SESSION_DELETION");}
    }
    static Object zero(Class<?> t){if(!t.isPrimitive())return null;if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;throw new IllegalStateException("UNEXPECTED_PRIMITIVE");}
    static void syntheticContext(SyntheticSessions sessions){
        HttpServletRequest request=(HttpServletRequest)Proxy.newProxyInstance(OriginalThirdPartyCredentialsFixture.class.getClassLoader(),new Class<?>[]{HttpServletRequest.class},(p,m,a)->{
            if(m.getName().equals("getHeader")||m.getName().equals("getAttribute")){need("X-UID".equals(a[0]),"ONLY_SYNTHETIC_UID");return USER;}return zero(m.getReturnType());});
        ApplicationContext app=(ApplicationContext)Proxy.newProxyInstance(OriginalThirdPartyCredentialsFixture.class.getClassLoader(),new Class<?>[]{ApplicationContext.class},(p,m,a)->{
            need(m.getName().equals("getBean")&&a.length==1&&a[0] instanceof Class,"CLOSED_SYNTHETIC_CONTEXT");
            if(a[0]==SessionManager.class)return sessions;
            need(((Class<?>)a[0]).getName().equals("com.cqweh.cloud.security.core.PermissionManager"),"NO_REAL_BEAN_ACCESS");return null;});
        new SecurityContextHolder().setApplicationContext(app);RequestContextHolder.setRequestAttributes(new ServletRequestAttributes(request));
    }
    static final class RecordingDock extends DockUtil {
        int calls;
        @Override public String sendDockMessage6(Object value){need(value instanceof com.iemp.endanger.base.entity.SendDock,"ORIGINAL_DOCK_ENVELOPE");calls++;return "OWN_RECORDING_ONLY";}
    }
    static final class Capture implements InvocationHandler {
        final List<String> calls=new ArrayList<>();
        final List<ThirdPartyUnitInfoCredential> credentials=new ArrayList<>();
        int accidents,appraisals,logs;boolean duplicate;
        public Object invoke(Object p,Method m,Object[] a){
            if(m.getDeclaringClass()==Object.class)return switch(m.getName()){
                case "toString"->"OWN_CLOSED_MAPPER";case "hashCode"->System.identityHashCode(p);case "equals"->p==a[0];default->throw new IllegalStateException("OBJECT_METHOD");};
            String owner=p.getClass().getInterfaces()[0].getSimpleName();
            if(owner.equals("ThirdPartyUnitInfoMapper")&&m.getName().equals("selectCount")){calls.add("duplicate-check");return duplicate?1L:0L;}
            if(owner.equals("ThirdPartyUnitInfoMapper")&&m.getName().equals("insert")){
                ThirdPartyUnitInfo info=(ThirdPartyUnitInfo)a[0];need(USER.equals(info.getCreatedBy())&&DEPT.equals(info.getCreateDept()),"ORIGINAL_SYNTHETIC_OWNERSHIP");info.setId("OWN_THIRD_PARTY_INFO");calls.add("main-insert");return 1;}
            if(owner.equals("DockLogMapper")&&m.getName().equals("insert")){logs++;return 1;}
            if(m.getName().equals("insertBatch")&&a.length==1){
                calls.add(owner+"-batch");
                Collection<?> rows=(Collection<?>)a[0];if(rows==null||rows.isEmpty())throw new IllegalStateException("OWN_EMPTY_BATCH_REJECTED");
                for(Object row:rows){
                    try {need(row.getClass().getMethod("getId").invoke(row)!=null&&"OWN-SOCIAL-CODE".equals(row.getClass().getMethod("getSocialCode").invoke(row)),"ORIGINAL_CHILD_ID_AND_SOCIAL_CODE");}
                    catch(ReflectiveOperationException error){throw new IllegalStateException(error);}
                }
                if(owner.equals("ThirdPartyUnitInfoCredentialMapper"))credentials.addAll((Collection<ThirdPartyUnitInfoCredential>)rows);
                else if(owner.equals("ThirdPartyUnitInfoAccidentMapper"))accidents+=rows.size();
                else if(owner.equals("ThirdPartyUnitInfoAppraisalMapper"))appraisals+=rows.size();
                else throw new IllegalStateException("UNEXPECTED_BATCH_MAPPER");return rows.size();
            }
            throw new IllegalStateException("UNEXPECTED_MAPPER_CALL:"+owner+":"+m.getName());
        }
        Object proxy(Class<?> type){return Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},this);}
    }
    static ThirdPartyUnitInfoServiceImpl service(Capture c,RecordingDock dock)throws Exception{
        ThirdPartyUnitInfoServiceImpl s=new ThirdPartyUnitInfoServiceImpl();boolean base=false;
        for(Class<?> cls=s.getClass();cls!=Object.class;cls=cls.getSuperclass())for(Field f:cls.getDeclaredFields()){
            if(f.getName().equals("baseMapper")){f.setAccessible(true);f.set(s,c.proxy(Class.forName("com.iemp.endanger.server.safetyBasic.mapper.ThirdPartyUnitInfoMapper")));base=true;}
            else if(f.getName().equals("dockUtil")){f.setAccessible(true);f.set(s,dock);}
            else if(f.getType().isInterface()&&f.getType().getSimpleName().endsWith("Mapper")){f.setAccessible(true);f.set(s,c.proxy(f.getType()));}
        }need(base,"REAL_BASE_MAPPER_REQUIRED");return s;
    }
    static ThirdPartyUnitInfoVo input(int count,boolean accident,boolean appraisal){
        ThirdPartyUnitInfo info=new ThirdPartyUnitInfo();info.setSocialCode("OWN-SOCIAL-CODE");info.setEnterpriseName("Own synthetic organization");info.setEnterpriseType("服务类承包商");info.setCreatedAt(LocalDateTime.of(2026,10,28,12,0));info.setUpdatedAt(info.getCreatedAt());
        ThirdPartyUnitInfoVo vo=new ThirdPartyUnitInfoVo();vo.setInfo(info);
        if(count>=0){List<ThirdPartyUnitInfoCredential> rows=new ArrayList<>();for(int i=0;i<count;i++){var row=new ThirdPartyUnitInfoCredential();row.setLicenceCode("OWN-CRED-"+i);row.setLicenceName("OWN-CERT-"+i);row.setLicenceType("其他相关业务资质证书");row.setStartDate(LocalDate.of(2026,10,28));row.setEndDate(LocalDate.of(2026,10,29));rows.add(row);}vo.setCredentials(rows);}
        var accidents=new ArrayList<ThirdPartyUnitInfoAccident>();if(accident){var row=new ThirdPartyUnitInfoAccident();row.setAccidentType("OWN_SYNTHETIC_ACCIDENT");row.setAccidentTime(info.getCreatedAt());accidents.add(row);}vo.setAccidents(accidents);
        var appraisals=new ArrayList<ThirdPartyUnitInfoAppraisal>();if(appraisal){var row=new ThirdPartyUnitInfoAppraisal();row.setAppraisalDate(info.getCreatedAt());row.setProjectName("Own synthetic appraisal");appraisals.add(row);}vo.setAppraisals(appraisals);return vo;
    }
    static void one(int count,boolean accident,boolean appraisal,boolean candidate,List<Object> cases)throws Exception{
        var c=new Capture();var dock=new RecordingDock();var s=service(c,dock);var vo=input(count,accident,appraisal);boolean rejected=false;
        try{need(s.save(vo),"REAL_SAVE_TRUE");}catch(IllegalStateException error){need(!candidate&&accident&&count<=0&&error.getMessage().equals("OWN_EMPTY_BATCH_REJECTED"),"ONLY_ORIGINAL_EMPTY_BATCH_FAILURE");rejected=true;}
        int expectedCredentials=(candidate||accident)?Math.max(count,0):0;
        need(c.credentials.size()==expectedCredentials,"CREDENTIAL_COUNT");
        need(c.calls.get(0).equals("duplicate-check")&&c.calls.get(1).equals("main-insert"),"ORIGINAL_MAIN_SEQUENCE");
        if(rejected){need(c.accidents==0&&c.appraisals==0&&dock.calls==0,"ORIGINAL_PARTIAL_CAPTURE_ONLY");}
        else {
            need(c.accidents==(accident?1:0)&&c.appraisals==(appraisal?1:0),"OTHER_CHILDREN_PRESERVED");
            need(dock.calls==1+Math.max(count,0)+(accident?1:0)+(appraisal?1:0)&&dock.calls==c.logs,"ORIGINAL_DOCK_SHAPE_RECORDED_WITHOUT_IO");
            for(int i=0;i<c.credentials.size();i++){var row=c.credentials.get(i);need(row==vo.getCredentials().get(i)&&row.getLicenceCode().equals("OWN-CRED-"+i)&&row.getStartDate().equals(LocalDate.of(2026,10,28))&&row.getEndDate().equals(LocalDate.of(2026,10,29))&&row.getUrl()==null,"CHILD_FIELDS_PRESERVED");}
        }
        cases.add(Map.of("credentialInputCount",count,"accident",accident,"appraisal",appraisal,"capturedCredentialRows",c.credentials.size(),"originalEmptyBatchRejected",rejected,"recordedDockCallsNoNetwork",dock.calls));
    }
    public static void main(String[] args)throws Exception{
        need(args.length==2&&(args[0].equals("candidate")||args[0].equals("original")),"EXACT_MODE_AND_OUTPUT");boolean candidate=args[0].equals("candidate");Path out=Path.of(args[1]).toAbsolutePath();need(!Files.exists(out)&&Files.isDirectory(out.getParent()),"FRESH_OUTPUT");
        var sessions=new SyntheticSessions();syntheticContext(sessions);
        var boundary=new OriginalProcessBoundary(out.getParent(),Set.of(),false);System.setSecurityManager(boundary);int checks=0;
        try{boundary.checkConnect("synthetic.invalid",443);}catch(SecurityException e){checks++;}
        try{boundary.checkExec("OWN_NEVER_EXECUTED");}catch(SecurityException e){checks++;}need(checks==2,"BOUNDARY_SELF_CHECKS");var denials=boundary.deniedCounts();
        List<Object> cases=new ArrayList<>();for(int n:new int[]{-1,0,1,2})for(boolean accident:new boolean[]{false,true})for(boolean appraisal:new boolean[]{false,true})one(n,accident,appraisal,candidate,cases);
        var duplicate=new Capture();duplicate.duplicate=true;var dock=new RecordingDock();int before=sessions.reads;boolean rejected=false;
        try{service(duplicate,dock).save(input(1,false,false));}catch(com.iemp.endanger.util.response.ServiceException error){need(error.getMessage().equals("已经存在该信用代码或企业名"),"ORIGINAL_DUPLICATE_MESSAGE");rejected=true;}
        need(rejected&&duplicate.calls.equals(List.of("duplicate-check"))&&sessions.reads==before&&dock.calls==0,"DUPLICATE_GUARD_PRECEDES_IDENTITY_AND_WRITES");cases.add(Map.of("case","duplicate-rejected-before-write","passed",true));
        // Real database field is varchar(16); validation must precede identity and writes.
        var over=new Capture();var overDock=new RecordingDock();var overDto=input(1,false,false);overDto.getCredentials().get(0).setLicenceName("ABCDEFGHIJKLMNOPQ");int beforeOver=sessions.reads;boolean overRejected=false;
        try{need(service(over,overDock).save(overDto),"OVERSIZE_BASELINE_SAVE_TRUE");}catch(com.iemp.endanger.util.response.ServiceException e){need(candidate&&e.getMessage().equals("证书名称不能超过16个字符"),"EXACT_LENGTH_MESSAGE");overRejected=true;}
        if(candidate)need(overRejected&&over.calls.equals(List.of("duplicate-check"))&&sessions.reads==beforeOver&&overDock.calls==0,"OVERSIZE_REJECTED_BEFORE_IDENTITY_AND_WRITES");
        else need(!overRejected&&over.credentials.isEmpty()&&over.calls.contains("main-insert"),"ORIGINAL_OVERSIZE_WITH_NO_ACCIDENT_STILL_LOST");
        cases.add(Map.of("case","oversize-17-character-name","rejectedBeforeWrite",overRejected));
        for(String name:List.of("save","updateById")){var tx=ThirdPartyUnitInfoServiceImpl.class.getMethod(name,ThirdPartyUnitInfoVo.class).getAnnotation(org.springframework.transaction.annotation.Transactional.class);need(candidate?(tx!=null&&Arrays.asList(tx.rollbackFor()).contains(Exception.class)):tx==null,"SAVE_AND_EDIT_EXCEPTION_ROLLBACK_DECLARATIONS");}
        need(denials.equals(boundary.deniedCounts()),"NO_UNEXPECTED_IO");String pin;
        try(var in=ThirdPartyUnitInfoServiceImpl.class.getResourceAsStream("ThirdPartyUnitInfoServiceImpl.class")){need(in!=null,"ACTUAL_CLASS_BYTES");pin=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(in.readAllBytes()));}
        var result=new LinkedHashMap<String,Object>();result.put("mode",args[0]);result.put("cases",cases);result.put("loadedServiceClassSHA256",pin);result.put("actualOriginalOrCandidateServiceExecuted",true);result.put("syntheticIdentityHelperReads",sessions.reads);result.put("databaseRealLoginHttpOrDockingUsed",false);result.put("transactionRollbackOrInstalledRuntimeProven",false);
        Files.writeString(out,JSON.writeValueAsString(result)+"\n",StandardOpenOption.CREATE_NEW);System.out.println("THIRD_PARTY_SAVE_CASES="+cases.size()+" MODE="+args[0]);
    }
}
