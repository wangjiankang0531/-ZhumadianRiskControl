package xnby.replica;

import com.baomidou.mybatisplus.core.*;
import com.baomidou.mybatisplus.core.config.GlobalConfig;
import com.baomidou.mybatisplus.core.incrementer.DefaultIdentifierGenerator;
import com.baomidou.mybatisplus.core.toolkit.GlobalConfigUtils;
import com.github.yulichang.injector.MPJSqlInjector;
import com.iemp.endanger.server.safetyBasic.entity.*;
import com.iemp.endanger.server.safetyBasic.entity.vo.ThirdPartyUnitInfoVo;
import com.iemp.endanger.server.safetyBasic.service.impl.ThirdPartyUnitInfoServiceImpl;
import org.apache.ibatis.builder.xml.XMLMapperBuilder;
import org.apache.ibatis.executor.Executor;
import org.apache.ibatis.logging.nologging.NoLoggingImpl;
import org.apache.ibatis.mapping.*;
import org.apache.ibatis.plugin.*;
import org.apache.ibatis.session.*;
import org.mybatis.spring.SqlSessionTemplate;
import org.mybatis.spring.transaction.SpringManagedTransactionFactory;
import org.springframework.jdbc.datasource.SingleConnectionDataSource;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.transaction.annotation.AnnotationTransactionAttributeSource;
import org.springframework.transaction.interceptor.TransactionInterceptor;
import org.springframework.aop.framework.ProxyFactory;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.*;
import java.util.*;
import java.util.regex.*;

/** Actual save/detail methods + original MyBatis/XML on four connection-local
 * tables. Permanent rows/schema hash-only; identity and docking are synthetic. */
@SuppressWarnings({"removal","unchecked"})
public final class OriginalThirdPartyCredentialsSqlFixture {
    static final String MAIN="third_party_unit_info",CRED=MAIN+"_credential",ACC=MAIN+"_accident",APP=MAIN+"_appraisal";
    static final List<String> TABLES=List.of(MAIN,CRED,ACC,APP);
    static final String PACKAGE="com.iemp.endanger.server.safetyBasic.mapper.";
    static void need(boolean yes,String message){if(!yes)throw new IllegalStateException(message);}
    static String hash(byte[] value)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));}
    static String hash(String text)throws Exception{return hash(text.getBytes(StandardCharsets.UTF_8));}
    static String ddl(Connection c,String table,boolean temporary)throws Exception{
        need(TABLES.contains(table),"CLOSED_TABLE_SET");try(Statement s=c.createStatement()){s.setQueryTimeout(5);try(ResultSet r=s.executeQuery("SHOW CREATE TABLE `"+table+"`")){
            need(r.next(),"TABLE_REQUIRED");String d=r.getString(2);need(d.startsWith(temporary?"CREATE TEMPORARY TABLE":"CREATE TABLE")&&d.contains("ENGINE=InnoDB"),"EXACT_TEMPORARY_OR_PERMANENT_KIND");return d;}}
    }
    static Map<String,Object> snapshot(Connection c)throws Exception{
        return snapshot(c,false);
    }
    static Map<String,Object> snapshot(Connection c,boolean temporary)throws Exception{
        var result=new LinkedHashMap<String,Object>();for(String t:TABLES){String schema=ddl(c,t,temporary);var rows=new ArrayList<String>();try(Statement s=c.createStatement()){s.setQueryTimeout(10);try(ResultSet r=s.executeQuery("SELECT * FROM `"+t+"`")){
            var m=r.getMetaData();while(r.next()){need(rows.size()<10000,"ROW_BOUND");var b=new StringBuilder();for(int i=1;i<=m.getColumnCount();i++){String v=r.getString(i);b.append(m.getColumnName(i)).append(':').append(v==null?"NULL":v.length()+":"+v).append('\n');}need(b.length()<1048576,"ROW_BYTES_BOUND");rows.add(hash(b.toString()));}
        }}Collections.sort(rows);result.put(t,Map.of("rows",rows.size(),"rowsSHA256",hash(String.join("\n",rows)),"schemaSHA256",hash(schema)));}return result;
    }
    static void identity(Connection c,int port,String uuid,Path dir)throws Exception{
        try(Statement s=c.createStatement()){s.setQueryTimeout(5);try(ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,@@event_scheduler,DATABASE()")){
            need(r.next()&&uuid.equals(r.getString(1))&&port==r.getInt(2)&&dir.equals(Path.of(r.getString(3)).toRealPath())&&"OFF".equals(r.getString(4))&&"tj_endanger".equals(r.getString(5)),"EXACT_OWN_DATABASE");}}
    }
    static long count(Connection c,String table)throws Exception{
        ddl(c,table,true);try(Statement s=c.createStatement()){s.setQueryTimeout(5);try(ResultSet r=s.executeQuery("SELECT COUNT(*) FROM `"+table+"`")){need(r.next(),"COUNT_REQUIRED");return r.getLong(1);}}
    }
    static void clear(Connection c)throws Exception{need(c.getAutoCommit(),"NO_OPEN_TRANSACTION");for(String t:TABLES){ddl(c,t,true);try(Statement s=c.createStatement()){s.executeUpdate("DELETE FROM `"+t+"`");}}}
    static void wire(Object object,String name,Object value)throws Exception{
        for(Class<?> c=object.getClass();c!=Object.class;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(object,value);return;}catch(NoSuchFieldException ignored){}
        throw new IllegalStateException("EXPECTED_SERVICE_FIELD");
    }
    @Intercepts(@Signature(type=Executor.class,method="update",args={MappedStatement.class,Object.class}))
    public static final class Gate implements Interceptor {
        final Connection owner;int writes,failAt;
        Gate(Connection c){owner=c;}
        public Object intercept(Invocation invocation)throws Throwable{
            var ms=(MappedStatement)invocation.getArgs()[0];need(ms.getId().startsWith(PACKAGE)&&Set.of(SqlCommandType.INSERT,SqlCommandType.UPDATE,SqlCommandType.DELETE).contains(ms.getSqlCommandType()),"ONLY_FOUR_ORIGINAL_WRITE_MAPPERS");
            String sql=ms.getBoundSql(invocation.getArgs()[1]).getSql().replace("`","").replaceAll("\\s+"," ").trim().toLowerCase(Locale.ROOT);
            Matcher match=Pattern.compile("^(?:insert into|update|delete from) ([a-z_]+) ").matcher(sql+" ");need(match.find()&&TABLES.contains(match.group(1))&&!sql.contains(";")&&!sql.contains(".")&&!sql.contains(" select "),"UNQUALIFIED_FOUR_TEMP_TABLE_DML_ONLY");
            ddl(owner,match.group(1),true);writes++;if(failAt==writes)throw new SQLException("OWN_FORCED_SECOND_WRITE_FAILURE","45000",1644);return invocation.proceed();
        }
    }
    public static void main(String[] args)throws Exception{
        need(args.length==5,"PORT_UUID_DATADIR_MODE_OUTPUT");int port=Integer.parseInt(args[0]);boolean candidate=args[3].equals("candidate");need(candidate||args[3].equals("original"),"EXACT_MODE");Path dir=Path.of(args[2]).toRealPath(),out=Path.of(args[4]).toAbsolutePath();need(!Files.exists(out)&&Files.isDirectory(out.getParent()),"FRESH_OUTPUT");
        byte[] secret=System.in.readNBytes(4097);need(secret.length>0&&secret.length<=4096,"BOUNDED_STDIN_SECRET");Properties props=new Properties();props.put("user","root");props.put("password",new String(secret,StandardCharsets.UTF_8));Arrays.fill(secret,(byte)0);props.putAll(Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000"));
        var sessions=new OriginalThirdPartyCredentialsFixture.SyntheticSessions();OriginalThirdPartyCredentialsFixture.syntheticContext(sessions);
        var boundary=new OriginalProcessBoundary(out.getParent(),Set.of(port),false);System.setSecurityManager(boundary);int checks=0;try{boundary.checkConnect("synthetic.invalid",443);}catch(SecurityException e){checks++;}try{boundary.checkExec("OWN_NEVER_EXECUTED");}catch(SecurityException e){checks++;}need(checks==2,"BOUNDARY_SELF_CHECKS");var denials=boundary.deniedCounts();var cases=new ArrayList<Object>();var result=new LinkedHashMap<String,Object>();String url="jdbc:mysql://127.0.0.1:"+port+"/tj_endanger";
        try(Connection observer=DriverManager.getConnection(url,props);Connection owner=DriverManager.getConnection(url,props)){
            observer.setReadOnly(true);identity(observer,port,args[1],dir);identity(owner,port,args[1],dir);var before=snapshot(observer);var definitions=new LinkedHashMap<String,String>();
            try{
                for(String t:TABLES){String d=ddl(observer,t,false);need(d.startsWith("CREATE TABLE `"+t+"` (")&&!d.contains(";")&&!d.contains("FOREIGN KEY")&&!d.contains("TABLESPACE"),"CLOSED_TEMP_DDL");try(Statement s=owner.createStatement()){s.execute("CREATE TEMPORARY TABLE "+d.substring("CREATE TABLE ".length()));}definitions.put(t,d);ddl(owner,t,true);}
                var ds=new SingleConnectionDataSource(owner,true);var cfg=new MybatisConfiguration();cfg.setLogImpl(NoLoggingImpl.class);cfg.setMapUnderscoreToCamelCase(true);cfg.setEnvironment(new Environment("own-third-party-temp",new SpringManagedTransactionFactory(),ds));
                var gc=new GlobalConfig();gc.setDbConfig(new GlobalConfig.DbConfig());gc.getDbConfig().setColumnFormat("`%s`");gc.setIdentifierGenerator(new DefaultIdentifierGenerator(7L,7L));gc.setSqlInjector(new MPJSqlInjector());GlobalConfigUtils.setGlobalConfig(cfg,gc);
                var mapperTypes=new ArrayList<Class<?>>();for(String n:List.of("ThirdPartyUnitInfo","ThirdPartyUnitInfoCredential","ThirdPartyUnitInfoAccident","ThirdPartyUnitInfoAppraisal")){Class<?> cls=Class.forName(PACKAGE+n+"Mapper");cfg.addMapper(cls);mapperTypes.add(cls);if(!n.equals("ThirdPartyUnitInfo"))try(var xml=OriginalThirdPartyCredentialsSqlFixture.class.getClassLoader().getResourceAsStream("xml/"+n+"Mapper.xml")){need(xml!=null,"ORIGINAL_CHILD_XML");new XMLMapperBuilder(xml,cfg,n,cfg.getSqlFragments()).parse();}}
                var gate=new Gate(owner);cfg.addInterceptor(gate);var session=new SqlSessionTemplate(new MybatisSqlSessionFactoryBuilder().build(cfg));var capture=new OriginalThirdPartyCredentialsFixture.Capture();var dock=new OriginalThirdPartyCredentialsFixture.RecordingDock();var service=OriginalThirdPartyCredentialsFixture.service(capture,dock);
                for(int i=0;i<mapperTypes.size();i++)wire(service,List.of("baseMapper","credentialMapper","accidentMapper","appraisalMapper").get(i),session.getMapper(mapperTypes.get(i)));
                Class<?> ext=Class.forName(PACKAGE+"WorkUserExtendMapper");wire(service,"extendMapper",Proxy.newProxyInstance(ext.getClassLoader(),new Class<?>[]{ext},(p,m,a)->{need(m.getName().equals("selectList"),"ONLY_EMPTY_SYNTHETIC_PERSON_LOOKUP");return List.of();}));
                boolean annotated=new AnnotationTransactionAttributeSource().getTransactionAttribute(ThirdPartyUnitInfoServiceImpl.class.getMethod("save",ThirdPartyUnitInfoVo.class),ThirdPartyUnitInfoServiceImpl.class)!=null;
                need(annotated==candidate,"EXPECTED_SAVE_TRANSACTION_ATTRIBUTE");
                ThirdPartyUnitInfoServiceImpl api=service;
                if(annotated){var pf=new ProxyFactory(service);pf.setProxyTargetClass(true);pf.addAdvice(new TransactionInterceptor(new DataSourceTransactionManager(ds),new AnnotationTransactionAttributeSource()));api=(ThirdPartyUnitInfoServiceImpl)pf.getProxy();}
                for(int n:new int[]{-1,0,1,2})for(boolean accident:new boolean[]{false,true})for(boolean appraisal:new boolean[]{false,true}){
                    clear(owner);session.clearCache();gate.writes=0;int dockBefore=dock.calls;var vo=OriginalThirdPartyCredentialsFixture.input(n,accident,appraisal);vo.getInfo().setId("OWN_THIRD_PARTY_SQL");vo.getInfo().setDeleted("0");
                    if(vo.getCredentials()!=null)for(var row:vo.getCredentials())row.setLicenceName("OWN-CERT");
                    for(var row:vo.getAccidents())row.setAccidentType("01");
                    boolean rejected=false;
                    List<String> failureClasses=new ArrayList<>();
                    try{need(api.save(vo),"REAL_SAVE_TRUE");}catch(RuntimeException error){
                        if(candidate||!accident||n>0)throw new IllegalStateException("UNEXPECTED_SQL_CASE:mode="+args[3]+",credentials="+n+",accident="+accident+",appraisal="+appraisal,error);
                        Throwable cause=error;boolean sqlFailure=false,builderFailure=false;while(cause!=null){failureClasses.add(cause.getClass().getName());sqlFailure|=cause instanceof SQLException;builderFailure|=cause instanceof org.apache.ibatis.builder.BuilderException;cause=cause.getCause();}need(n<0?builderFailure:sqlFailure,"EXACT_NULL_FOREACH_OR_EMPTY_VALUES_REJECTION:"+failureClasses);rejected=true;}
                    need(count(owner,MAIN)==1&&count(owner,CRED)==((candidate||accident)?Math.max(n,0):0)&&count(owner,ACC)==(!rejected&&accident?1:0)&&count(owner,APP)==(!rejected&&appraisal?1:0),"EXPECTED_FOUR_TABLE_COUNTS");
                    if(!rejected){ThirdPartyUnitInfoVo detail=api.getById("OWN_THIRD_PARTY_SQL");need(detail.getCredentials().size()==((candidate||accident)?Math.max(n,0):0)&&detail.getAccidents().size()==(accident?1:0)&&detail.getAppraisals().size()==(appraisal?1:0)&&OriginalThirdPartyCredentialsFixture.USER.equals(detail.getInfo().getCreatedBy())&&OriginalThirdPartyCredentialsFixture.DEPT.equals(detail.getInfo().getCreateDept()),"ORIGINAL_DETAIL_REOPEN_AND_OWNERSHIP");
                        for(int i=0;i<detail.getCredentials().size();i++){var row=detail.getCredentials().get(i);need("OWN-SOCIAL-CODE".equals(row.getSocialCode())&&row.getId()!=null&&row.getLicenceName().equals("OWN-CERT")&&row.getStartDate().equals(java.time.LocalDate.of(2026,10,28))&&row.getEndDate().equals(java.time.LocalDate.of(2026,10,29))&&row.getUrl()==null,"ACTUAL_CHILD_FIELDS");}
                        need(dock.calls-dockBefore==1+Math.max(n,0)+(accident?1:0)+(appraisal?1:0),"UNCHANGED_DOCK_CALL_SHAPE_NO_IO");
                    }else need(dock.calls==dockBefore,"NO_DOCK_AFTER_SQL_FAILURE");
                    cases.add(Map.of("credentialInputCount",n,"accident",accident,"appraisal",appraisal,"originalEmptyBatchRejected",rejected,"failureClasses",failureClasses,"actualCredentialRows",count(owner,CRED),"reopenedOriginalDetail",!rejected));
                }
                // A real duplicate query must reject before another INSERT or synthetic identity read.
                int writes=gate.writes,reads=sessions.reads,docks=dock.calls;boolean rejected=false;
                try{api.save(OriginalThirdPartyCredentialsFixture.input(1,false,false));}catch(com.iemp.endanger.util.response.ServiceException e){need("已经存在该信用代码或企业名".equals(e.getMessage()),"ORIGINAL_DUPLICATE_TEXT");rejected=true;}
                need(rejected&&gate.writes==writes&&sessions.reads==reads&&dock.calls==docks&&count(owner,MAIN)==1,"DUPLICATE_BEFORE_WRITES");cases.add(Map.of("case","actual-duplicate-query-rejected-before-write","passed",true));
                clear(owner);session.clearCache();gate.writes=0;int readsBefore=sessions.reads,docksBefore=dock.calls;var oversize=OriginalThirdPartyCredentialsFixture.input(1,false,false);oversize.getInfo().setId("OWN_THIRD_PARTY_OVERSIZE");oversize.getInfo().setDeleted("0");oversize.getCredentials().get(0).setLicenceName("ABCDEFGHIJKLMNOPQ");boolean lengthRejected=false;
                try{need(api.save(oversize),"OVERSIZE_ORIGINAL_SAVE");}catch(com.iemp.endanger.util.response.ServiceException e){need(candidate&&"证书名称不能超过16个字符".equals(e.getMessage()),"OVERSIZE_EXACT_VALIDATION");lengthRejected=true;}
                if(candidate)need(lengthRejected&&gate.writes==0&&sessions.reads==readsBefore&&dock.calls==docksBefore&&count(owner,MAIN)==0&&count(owner,CRED)==0,"OVERSIZE_PREWRITE_REJECTION");
                else need(!lengthRejected&&count(owner,MAIN)==1&&count(owner,CRED)==0,"ORIGINAL_OVERSIZE_CREDENTIAL_SKIPPED");
                cases.add(Map.of("case","oversize-name-before-any-insert","rejectedBeforeWrite",lengthRejected));
                clear(owner);session.clearCache();gate.writes=0;gate.failAt=2;int beforeFaultDock=dock.calls;var fault=OriginalThirdPartyCredentialsFixture.input(1,true,false);fault.getInfo().setId("OWN_THIRD_PARTY_FAULT");fault.getInfo().setDeleted("0");fault.getAccidents().get(0).setAccidentType("01");Throwable failure=null;
                try{api.save(fault);}catch(RuntimeException e){failure=e;}
                need(failure!=null&&gate.writes==2&&dock.calls==beforeFaultDock&&count(owner,MAIN)==(candidate?0:1)&&count(owner,CRED)==0&&count(owner,ACC)==0&&count(owner,APP)==0,"ANNOTATION_ROLLBACK_OR_ORIGINAL_PARTIAL_STATE");
                gate.failAt=0;cases.add(Map.of("case","second-write-forced-failure","annotationDrivenRollback",candidate,"originalUnproxiedMainRowRemains",!candidate,"actualRuntimeBeanStillPending",true));
                clear(owner);session.clearCache();gate.writes=0;var seed=OriginalThirdPartyCredentialsFixture.input(1,true,true);seed.getInfo().setId("OWN_THIRD_PARTY_EDIT");seed.getInfo().setDeleted("0");seed.getAccidents().get(0).setAccidentType("01");need(api.save(seed),"EDIT_SEED_SAVE");
                var edit=api.getById("OWN_THIRD_PARTY_EDIT");edit.getInfo().setEnterpriseName("Own edited organization");edit.getCredentials().get(0).setLicenceName("OWN-EDIT");gate.writes=0;
                need(api.updateById(edit),"ORIGINAL_EDIT_TRUE");var reopened=api.getById("OWN_THIRD_PARTY_EDIT");need(reopened.getInfo().getEnterpriseName().equals("Own edited organization")&&reopened.getCredentials().size()==1&&reopened.getCredentials().get(0).getLicenceName().equals("OWN-EDIT")&&reopened.getCredentials().get(0).getId().equals(edit.getCredentials().get(0).getId())&&reopened.getAccidents().size()==1&&reopened.getAppraisals().size()==1,"EDIT_MAIN_CHILD_FIELDS_AND_ID_REOPEN");cases.add(Map.of("case","edit-main-and-three-child-lists-reopened","passed",true));
                var editBefore=snapshot(owner,true);reopened.getInfo().setEnterpriseName("Own fault organization");gate.writes=0;gate.failAt=3;Throwable editFailure=null;
                try{api.updateById(reopened);}catch(RuntimeException e){editFailure=e;}need(editFailure!=null&&gate.writes==3,"THIRD_EDIT_WRITE_FAULT");gate.failAt=0;
                if(candidate)need(editBefore.equals(snapshot(owner,true)),"ANNOTATION_DRIVEN_EDIT_ROLLBACK");else need(!editBefore.equals(snapshot(owner,true))&&count(owner,CRED)==0,"ORIGINAL_UNPROXIED_EDIT_PARTIAL_STATE");
                cases.add(Map.of("case","edit-third-write-forced-failure","annotationDrivenRollback",candidate,"actualRuntimeBeanStillPending",true));
                clear(owner);session.clearCache();gate.writes=0;var valid=OriginalThirdPartyCredentialsFixture.input(1,false,false);valid.getInfo().setId("OWN_THIRD_PARTY_LENGTH");valid.getInfo().setDeleted("0");need(api.save(valid),"LENGTH_EDIT_SEED");var invalidEdit=api.getById("OWN_THIRD_PARTY_LENGTH");invalidEdit.setCredentials(valid.getCredentials());invalidEdit.getCredentials().get(0).setLicenceName("ABCDEFGHIJKLMNOPQ");var lengthBefore=snapshot(owner,true);gate.writes=0;Throwable lengthFailure=null;
                try{api.updateById(invalidEdit);}catch(RuntimeException e){lengthFailure=e;}need(lengthFailure!=null,"OVERSIZE_EDIT_MUST_FAIL");
                if(candidate)need(lengthFailure instanceof com.iemp.endanger.util.response.ServiceException&&lengthFailure.getMessage().equals("证书名称不能超过16个字符")&&gate.writes==0&&lengthBefore.equals(snapshot(owner,true)),"EDIT_LENGTH_REJECTED_BEFORE_WRITES");
                else need(gate.writes>0,"ORIGINAL_LENGTH_FAILURE_AFTER_PARTIAL_WRITES");
                cases.add(Map.of("case","oversize-edit-name","rejectedBeforeAnyWrite",candidate));
                result.put("serviceSaveHasTransactionAttribute",annotated);
            }finally{
                if(!owner.getAutoCommit())owner.rollback();owner.setAutoCommit(true);for(String t:definitions.keySet()){ddl(owner,t,true);try(Statement s=owner.createStatement()){s.execute("DROP TEMPORARY TABLE `"+t+"`");}need(ddl(owner,t,false).equals(definitions.get(t)),"FORMAL_SCHEMA_RESTORED_AFTER_TEMP_DROP");}
                var after=snapshot(observer);need(before.equals(after),"PERMANENT_ROWS_AND_SCHEMAS_CHANGED");Files.writeString(out.getParent().resolve("formal-integrity.private.json"),OriginalThirdPartyCredentialsFixture.JSON.writeValueAsString(Map.of("before",before,"after",after,"temporaryTablesDropped",true))+"\n",StandardOpenOption.CREATE_NEW);result.put("permanentBefore",before);result.put("permanentAfter",after);
            }
        }finally{props.remove("password");}
        need(denials.equals(boundary.deniedCounts()),"NO_UNEXPECTED_BOUNDARY_ACTIVITY");try(var in=ThirdPartyUnitInfoServiceImpl.class.getResourceAsStream("ThirdPartyUnitInfoServiceImpl.class")){need(in!=null,"ACTUAL_LOADED_CLASS");result.put("loadedServiceClassSHA256",hash(in.readAllBytes()));}
        result.put("mode",args[3]);result.put("cases",cases);result.put("permanentFourTableRowsAndSchemasUnchanged",true);result.put("temporaryTablesDropped",true);result.put("actualOriginalServiceMappersAndXmlExecuted",true);result.put("realLoginHttpOrDockingUsed",false);result.put("transactionRollbackOrInstalledRuntimeAccepted",false);Files.writeString(out,OriginalThirdPartyCredentialsFixture.JSON.writeValueAsString(result)+"\n",StandardOpenOption.CREATE_NEW);System.out.println("THIRD_PARTY_SQL_CASES="+cases.size()+" MODE="+args[3]);
    }
}
