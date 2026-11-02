package xnby.replica;

import com.baomidou.mybatisplus.core.*;
import com.baomidou.mybatisplus.core.config.GlobalConfig;
import com.baomidou.mybatisplus.core.incrementer.DefaultIdentifierGenerator;
import com.baomidou.mybatisplus.core.toolkit.GlobalConfigUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yulichang.injector.MPJSqlInjector;
import com.iemp.endanger.server.work.entity.*;
import com.iemp.endanger.server.work.entity.basic.Work;
import com.iemp.endanger.server.work.entity.vo.WorkReservationBaseVo;
import com.iemp.endanger.server.work.service.impl.WorkReservationBaseServiceImpl;
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
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.transaction.annotation.AnnotationTransactionAttributeSource;
import org.springframework.transaction.interceptor.TransactionInterceptor;
import org.springframework.aop.framework.ProxyFactory;
import com.iemp.endanger.server.work.service.WorkReservationBaseService;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.*;
import java.time.LocalDateTime;
import java.util.*;
import java.util.regex.*;

/** The original edit method and real MyBatis mappers on ten connection-local tables.
 * Permanent tables are read/hash-only. No authentication, HTTP or live runtime change. */
@SuppressWarnings({"removal","unchecked"})
public final class OriginalWorkReservationSqlFixture {
    static final String BASE="work_reservation_base",PERSON="work_reservation_personnel";
    static final Map<String,String> ENTITIES=OriginalWorkReservationEndTimeFixture.TYPES;
    static final List<String> WORK_TABLES=List.of("work_blind","work_finite_space","work_groundbreaking","work_hot","work_high","work_hoisting","work_open_circuit","work_temporary_electricity");
    static final Set<String> TABLES=new LinkedHashSet<>();
    static {TABLES.add(BASE);TABLES.add(PERSON);TABLES.addAll(WORK_TABLES);}
    static final LocalDateTime OLD=LocalDateTime.of(2026,10,29,10,0),NEW=OLD.plusHours(1),START=OLD.minusHours(1);
    static void need(boolean ok,String code){if(!ok)throw new IllegalStateException(code);}
    static String hash(byte[] raw)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
    static String hash(String text)throws Exception{return hash(text.getBytes(StandardCharsets.UTF_8));}
    static String table(String type){int n=new ArrayList<>(ENTITIES.keySet()).indexOf(type);need(n>=0,"EXACT_WORK_TYPE");return WORK_TABLES.get(n);}
    static String ddl(Connection c,String t,boolean temporary)throws Exception{
        need(TABLES.contains(t),"CLOSED_TABLE_SET");
        try(Statement s=c.createStatement()){s.setQueryTimeout(5);try(ResultSet r=s.executeQuery("SHOW CREATE TABLE `"+t+"`")){
            need(r.next(),"TABLE_REQUIRED");String d=r.getString(2);
            need(d.startsWith(temporary?"CREATE TEMPORARY TABLE":"CREATE TABLE")&&d.contains("ENGINE=InnoDB"),"EXACT_TABLE_KIND_REQUIRED");return d;
        }}
    }
    static String structural(String ddl){
        StringBuilder out=new StringBuilder();boolean quoted=false;
        for(int i=0;i<ddl.length();i++) {char ch=ddl.charAt(i);
            if(quoted){if(ch==92){need(++i<ddl.length(),"CLOSED_ESCAPE");}else if(ch==39){if(i+1<ddl.length()&&ddl.charAt(i+1)==39)i++;else quoted=false;}}
            else if(ch==39){quoted=true;out.append("'STRING'");}else out.append(ch);
        }need(!quoted,"CLOSED_LITERAL");return out.toString().toUpperCase(Locale.ROOT);
    }
    static Map<String,Object> snapshot(Connection c,boolean temporary)throws Exception {
        Map<String,Object> result=new LinkedHashMap<>();
        for(String t:TABLES){String schema=ddl(c,t,temporary);List<String> rows=new ArrayList<>();
            try(Statement s=c.createStatement()){s.setQueryTimeout(10);try(ResultSet r=s.executeQuery("SELECT * FROM `"+t+"`")){
                var md=r.getMetaData();while(r.next()){need(rows.size()<10000,"ROW_BOUND");StringBuilder row=new StringBuilder();
                    for(int i=1;i<=md.getColumnCount();i++){String v=r.getString(i);row.append(md.getColumnName(i)).append(':').append(v==null?"NULL":v.length()+":"+v).append('\n');}
                    need(row.length()<1048576,"ROW_BYTES_BOUND");rows.add(hash(row.toString()));
                }
            }}Collections.sort(rows);result.put(t,Map.of("rows",rows.size(),"rowMultisetSHA256",hash(String.join("\n",rows)),"schemaSHA256",hash(schema)));
        }return result;
    }
    static void identity(Connection c,int port,String uuid,Path data)throws Exception {
        try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,@@event_scheduler,DATABASE()")){
            need(r.next()&&uuid.equals(r.getString(1))&&port==r.getInt(2)&&data.equals(Path.of(r.getString(3)).toRealPath())&&"OFF".equals(r.getString(4))&&"tj_endanger".equals(r.getString(5)),"EXACT_LOCAL_TEST_DATABASE_REQUIRED");
        }
    }
    static void seedRow(Connection c,String t,Map<String,Object> input)throws Exception {
        ddl(c,t,true);Map<String,Object> values=new LinkedHashMap<>(input);
        try(ResultSet cols=c.getMetaData().getColumns(null,"tj_endanger",t,null)){
            while(cols.next()){String n=cols.getString("COLUMN_NAME");
                if(values.containsKey(n)||cols.getInt("NULLABLE")!=0||cols.getString("COLUMN_DEF")!=null||"YES".equals(cols.getString("IS_AUTOINCREMENT")))continue;
                Object v=switch(cols.getInt("DATA_TYPE")){
                    case Types.VARCHAR,Types.CHAR,Types.LONGVARCHAR -> "OWN_REQUIRED";
                    case Types.INTEGER,Types.SMALLINT,Types.TINYINT,Types.BIGINT,Types.NUMERIC,Types.DECIMAL,Types.DOUBLE,Types.FLOAT,Types.REAL,Types.BIT,Types.BOOLEAN -> 0;
                    case Types.DATE -> java.sql.Date.valueOf("2026-10-29");
                    case Types.TIMESTAMP -> Timestamp.valueOf(OLD);
                    case Types.TIME -> Time.valueOf("10:00:00");
                    default -> throw new IllegalStateException("UNSUPPORTED_REQUIRED_SEED_COLUMN");
                };values.put(n,v);
            }
        }
        need(values.keySet().stream().allMatch(n->n.matches("[a-z_]+")),"CLOSED_COLUMN_NAMES");
        String names=String.join(",",values.keySet().stream().map(n->"`"+n+"`").toList());
        try(PreparedStatement p=c.prepareStatement("INSERT INTO `"+t+"` ("+names+") VALUES ("+String.join(",",Collections.nCopies(values.size(),"?"))+")")){
            int i=1;for(Object v:values.values())p.setObject(i++,v);need(p.executeUpdate()==1,"ONE_SEED_ROW");
        }
    }
    static void seed(Connection c,String type)throws Exception {
        need(c.getAutoCommit(),"NO_OPEN_TEST_TRANSACTION");
        for(String t:TABLES){ddl(c,t,true);try(Statement s=c.createStatement()){s.executeUpdate("DELETE FROM `"+t+"`");}}
        seedRow(c,BASE,Map.of("id","OWN_BASE","job_type",type,"process_name","暂存","start_time",START,"end_time",OLD,"work_no","OWN_SQL_FIXTURE","job_content","OWN_OLD_CONTENT"));
        seedRow(c,table(type),Map.of("id","OWN_WORK","work_reservation_base_id","OWN_BASE","process_name","暂存","start_time",START,"end_time",OLD,"job_content","OWN_OLD_CONTENT"));
        seedRow(c,PERSON,Map.of("id","OWN_OLD_PERSON","work_reservation_base_id","OWN_BASE","type","2","person_name","OWN_OLD"));
    }
    static WorkReservationBaseVo dto(String type)throws Exception {
        WorkReservationBase b=new WorkReservationBase();b.setId("OWN_BASE");b.setJobType(type);b.setProcessName("暂存");b.setWorkNo("OWN_SQL_FIXTURE");b.setStartTime(START);b.setEndTime(NEW);b.setJobContent("OWN_NEW_CONTENT");b.setOtherId(null);
        Work w=(Work)Class.forName("com.iemp.endanger.server.work.entity."+ENTITIES.get(type)).getDeclaredConstructor().newInstance();w.setId("OWN_WORK");w.setJobContent("OWN_NEW_CONTENT");
        List<WorkReservationPersonnel> people=new ArrayList<>();for(String role:List.of("2","4")){WorkReservationPersonnel p=new WorkReservationPersonnel();p.setType(role);p.setPersonName("OWN_ROLE_"+role);p.setRelatedPersonnelId("OWN_PERSON");people.add(p);}
        WorkReservationBaseVo result=new WorkReservationBaseVo();result.setBase(b);result.setWork(w);result.setList(people);return result;
    }
    @Intercepts(@Signature(type=Executor.class,method="update",args={MappedStatement.class,Object.class}))
    public static final class Gate implements Interceptor {
        final Connection owner;final Set<String> mapperNames;int writes,failAt;
        Gate(Connection c,Set<String> names){owner=c;mapperNames=names;}
        public Object intercept(Invocation call)throws Throwable {
            MappedStatement ms=(MappedStatement)call.getArgs()[0];String id=ms.getId();need(mapperNames.stream().anyMatch(n->id.startsWith(n+".")),"CLOSED_MAPPER_SET");
            String sql=ms.getBoundSql(call.getArgs()[1]).getSql().replace("`","").replaceAll("\\s+"," ").trim().toLowerCase(Locale.ROOT);
            Matcher m=Pattern.compile("^(?:update|insert into|delete from) ([a-z_]+) ").matcher(sql+" ");need(m.find()&&TABLES.contains(m.group(1))&&!sql.contains(";")&&!sql.contains("."),"UNQUALIFIED_SHADOW_TABLE_DML_ONLY");
            ddl(owner,m.group(1),true);writes++;if(failAt==writes)throw new SQLException("OWN_FORCED_THIRD_WRITE_FAILURE","45000",1644);
            return call.proceed();
        }
        void reset(int fail){writes=0;failAt=fail;}
    }
    static void wire(Object object,String name,Object value)throws Exception {
        for(Class<?> c=object.getClass();c!=Object.class;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(object,value);return;}catch(NoSuchFieldException ignored){}
        throw new IllegalStateException("EXPECTED_FIELD");
    }
    static LocalDateTime end(Connection c,String t,String id)throws Exception {
        ddl(c,t,true);try(PreparedStatement p=c.prepareStatement("SELECT end_time FROM `"+t+"` WHERE id=?")){p.setString(1,id);try(ResultSet r=p.executeQuery()){need(r.next(),"EXACT_TEST_ROW");return r.getObject(1,LocalDateTime.class);}}
    }
    static void assertRows(Connection c,String type,boolean candidate)throws Exception {
        need(NEW.equals(end(c,BASE,"OWN_BASE"))&&(candidate?NEW:OLD).equals(end(c,table(type),"OWN_WORK")),"EXPECTED_TYPED_END_TIME_SQL_RESULT");
        for(String t:List.of(BASE,table(type)))try(PreparedStatement p=c.prepareStatement("SELECT start_time,process_name,job_content FROM `"+t+"` WHERE id=?")){
            p.setString(1,t.equals(BASE)?"OWN_BASE":"OWN_WORK");try(ResultSet r=p.executeQuery()){need(r.next()&&START.equals(r.getObject(1,LocalDateTime.class))&&"暂存".equals(r.getString(2))&&"OWN_NEW_CONTENT".equals(r.getString(3)),"OTHER_FIELDS_PRESERVED_IN_SQL");}
        }
        try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT type,COUNT(*) FROM work_reservation_personnel GROUP BY type")){
            Set<String> roles=new HashSet<>();while(r.next()){roles.add(r.getString(1));need(r.getInt(2)==1,"ONE_ROW_PER_ROLE");}need(roles.equals(Set.of("2","4")),"PERSON_ROLES_PERSISTED");
        }
    }
    public static void main(String[] args)throws Exception {
        need(args.length==5,"PORT_UUID_DATADIR_MODE_OUTPUT_REQUIRED");int port=Integer.parseInt(args[0]);boolean candidate=args[3].equals("candidate");need(candidate||args[3].equals("original"),"EXACT_MODE");Path data=Path.of(args[2]).toRealPath(),out=Path.of(args[4]).toAbsolutePath();need(!Files.exists(out)&&Files.isDirectory(out.getParent()),"FRESH_OUTPUT");
        byte[] secret=System.in.readNBytes(4097);need(secret.length>0&&secret.length<=4096,"STDIN_SECRET_BOUND");Properties props=new Properties();props.setProperty("user","root");props.setProperty("password",new String(secret,StandardCharsets.UTF_8));Arrays.fill(secret,(byte)0);
        props.putAll(Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000"));
        OriginalProcessBoundary guard=new OriginalProcessBoundary(out.getParent(),Set.of(port),false);System.setSecurityManager(guard);
        int self=0;try{guard.checkConnect("synthetic.invalid",443);}catch(SecurityException e){self++;}try{guard.checkExec("OWN_NEVER_EXECUTED");}catch(SecurityException e){self++;}need(self==2,"BOUNDARY_SELF_TESTS");var denials=guard.deniedCounts();
        Map<String,Object> report=new LinkedHashMap<>();List<Object> cases=new ArrayList<>();
        String url="jdbc:mysql://127.0.0.1:"+port+"/tj_endanger";
        try(Connection observer=DriverManager.getConnection(url,props);Connection owner=DriverManager.getConnection(url,props)){
            observer.setReadOnly(true);identity(observer,port,args[1],data);identity(owner,port,args[1],data);Map<String,Object> before=snapshot(observer,false);
            Map<String,String> definitions=new LinkedHashMap<>();
            try {
                for(String t:TABLES){String d=ddl(observer,t,false),s=structural(d);need(d.startsWith("CREATE TABLE `"+t+"` (")&&!s.contains(";")&&!s.contains("FOREIGN KEY")&&!s.contains("TABLESPACE"),"BOUNDED_TEMP_DDL_REQUIRED");definitions.put(t,d);try(Statement st=owner.createStatement()){st.execute("CREATE TEMPORARY TABLE "+d.substring("CREATE TABLE ".length()));}ddl(owner,t,true);}
                SingleConnectionDataSource ds=new SingleConnectionDataSource(owner,true);MybatisConfiguration cfg=new MybatisConfiguration();cfg.setLogImpl(NoLoggingImpl.class);cfg.setMapUnderscoreToCamelCase(true);cfg.setEnvironment(new Environment("own-reservation-temp",new SpringManagedTransactionFactory(),ds));
                GlobalConfig gc=new GlobalConfig();gc.setDbConfig(new GlobalConfig.DbConfig());gc.getDbConfig().setColumnFormat("`%s`");gc.setIdentifierGenerator(new DefaultIdentifierGenerator(7L,7L));gc.setSqlInjector(new MPJSqlInjector());GlobalConfigUtils.setGlobalConfig(cfg,gc);
                Map<Class<?>,Object> mappers=new LinkedHashMap<>();Set<String> names=new LinkedHashSet<>();List<String> simple=new ArrayList<>(ENTITIES.values());simple.addAll(List.of("WorkReservationBase","WorkReservationPersonnel"));
                for(String n:simple){Class<?> cls=Class.forName("com.iemp.endanger.server.work.mapper."+n+"Mapper");cfg.addMapper(cls);mappers.put(cls,null);names.add(cls.getName());}
                try(var xml=OriginalWorkReservationSqlFixture.class.getClassLoader().getResourceAsStream("xml/WorkReservationPersonnelMapper.xml")){need(xml!=null,"ORIGINAL_PERSON_XML");new XMLMapperBuilder(xml,cfg,"personnel",cfg.getSqlFragments()).parse();}
                Gate gate=new Gate(owner,names);cfg.addInterceptor(gate);SqlSessionTemplate session=new SqlSessionTemplate(new MybatisSqlSessionFactoryBuilder().build(cfg));for(Class<?> cls:mappers.keySet())mappers.put(cls,session.getMapper(cls));
                Constructor<?>[] cs=WorkReservationBaseServiceImpl.class.getDeclaredConstructors();need(cs.length==1,"ORIGINAL_CONSTRUCTOR");Object[] deps=Arrays.stream(cs[0].getParameterTypes()).map(mappers::get).toArray();WorkReservationBaseServiceImpl service=(WorkReservationBaseServiceImpl)cs[0].newInstance(deps);wire(service,"baseMapper",mappers.get(Class.forName("com.iemp.endanger.server.work.mapper.WorkReservationBaseMapper")));
                boolean annotated=new AnnotationTransactionAttributeSource().getTransactionAttribute(WorkReservationBaseServiceImpl.class.getMethod("updateById",WorkReservationBaseVo.class),WorkReservationBaseServiceImpl.class)!=null;
                report.put("serviceMethodHasTransactionAttribute",annotated);
                WorkReservationBaseService api=service;
                if(annotated){ProxyFactory pf=new ProxyFactory(service);pf.addAdvice(new TransactionInterceptor(new DataSourceTransactionManager(ds),new AnnotationTransactionAttributeSource()));api=(WorkReservationBaseService)pf.getProxy();}
                for(String type:ENTITIES.keySet()){
                    seed(owner,type);session.clearCache();gate.reset(0);need(api.updateById(dto(type))&&gate.writes==4,"FOUR_ORIGINAL_WRITES");
                    Files.writeString(out.getParent().resolve("latest-synthetic-time-values.json"),new ObjectMapper().writeValueAsString(Map.of("type",type,"base",end(owner,BASE,"OWN_BASE").toString(),"work",end(owner,table(type),"OWN_WORK").toString(),"expectedBase",NEW.toString(),"candidate",candidate))+"\n");
                    assertRows(owner,type,candidate);cases.add(Map.of("type",type,"case",candidate?"both-end-times-synchronized":"original-work-end-time-stale","personRolesAndOtherFieldsPreserved",true));
                }
                String type="动火作业";seed(owner,type);session.clearCache();gate.reset(3);Throwable failure=null;try{service.updateById(dto(type));}catch(Throwable error){failure=error;}
                need(failure!=null&&gate.writes==3&&OLD.equals(end(owner,BASE,"OWN_BASE"))&&(candidate?NEW:OLD).equals(end(owner,table(type),"OWN_WORK")),"DIRECT_UNPROXIED_PARTIAL_WRITE_CHARACTERIZED");
                cases.add(Map.of("case","direct-unproxied-third-write-fault","partiallyChangedTemporaryRows",true,"notAProductionTransactionConclusion",true));
                seed(owner,type);session.clearCache();Map<String,Object> testBefore=snapshot(owner,true);gate.reset(3);failure=null;
                try{new TransactionTemplate(new DataSourceTransactionManager(ds)).execute(status->{need(service.updateById(uncheckedDto(type)),"TEST_TX_UPDATE");return true;});}catch(Throwable error){failure=error;}
                need(failure!=null&&gate.writes==3&&testBefore.equals(snapshot(owner,true)),"EXPLICIT_TEST_TRANSACTION_ROLLBACK_REQUIRED");
                cases.add(Map.of("case","explicit-test-transaction-third-write-fault","temporaryRowsRolledBack",true,"notAProductionTransactionConclusion",true));
                if(annotated){
                    seed(owner,type);session.clearCache();Map<String,Object> atomicBefore=snapshot(owner,true);gate.reset(3);failure=null;
                    try{api.updateById(dto(type));}catch(Throwable error){failure=error;}
                    need(failure!=null&&gate.writes==3&&atomicBefore.equals(snapshot(owner,true)),"ANNOTATION_DRIVEN_REAL_SPRING_ROLLBACK_REQUIRED");
                    cases.add(Map.of("case","candidate-annotation-driven-third-write-fault","temporaryRowsRolledBack",true,"actualRuntimeBeanStillPending",true));
                }
            }finally{
                if(!owner.getAutoCommit())owner.rollback();owner.setAutoCommit(true);
                for(String t:definitions.keySet()){ddl(owner,t,true);try(Statement s=owner.createStatement()){s.execute("DROP TEMPORARY TABLE `"+t+"`");}need(ddl(owner,t,false).equals(definitions.get(t)),"ORIGINAL_SCHEMA_AFTER_TEMP_DROP");}
                Map<String,Object> afterCleanup=snapshot(observer,false);need(before.equals(afterCleanup),"PERMANENT_TABLES_CHANGED_DURING_CLEANUP");
                Files.writeString(out.getParent().resolve("formal-integrity-after-cleanup.private.json"),new ObjectMapper().writeValueAsString(Map.of("before",before,"after",afterCleanup,"tenTableRowsAndSchemasUnchanged",true,"temporaryTablesDropped",true))+"\n",StandardOpenOption.CREATE_NEW);
            }
            Map<String,Object> after=snapshot(observer,false);need(before.equals(after),"PERMANENT_TABLES_CHANGED");report.put("formalBefore",before);report.put("formalAfter",after);
        }finally{props.remove("password");}
        need(denials.equals(guard.deniedCounts())&&System.getSecurityManager()==guard,"NO_UNEXPECTED_BOUNDARY_ACTIVITY");
        try(var stream=WorkReservationBaseServiceImpl.class.getResourceAsStream("WorkReservationBaseServiceImpl.class")){need(stream!=null,"LOADED_CLASS_REQUIRED");report.put("loadedServiceClassSHA256",hash(stream.readAllBytes()));}
        report.put("mode",args[3]);report.put("cases",cases);report.put("permanentRowsAndSchemasUnchanged",true);report.put("temporaryTablesDropped",true);report.put("actualServiceAndOriginalMyBatisMappersExecuted",true);report.put("realAuthenticationOrHttpUsed",false);report.put("runtimeRestarted",false);report.put("productionTransactionOrFullCloneAccepted",false);
        Files.writeString(out,new ObjectMapper().writeValueAsString(report)+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);System.out.println("RESERVATION_SQL_CASES="+cases.size()+" MODE="+args[3]);
    }
    static WorkReservationBaseVo uncheckedDto(String type){try{return dto(type);}catch(Exception e){throw new IllegalStateException(e);}}
}
