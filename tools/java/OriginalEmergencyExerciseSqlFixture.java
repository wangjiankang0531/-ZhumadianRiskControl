package xnby.replica;
import com.iemp.endanger.server.emergency.entity.*;
import com.iemp.endanger.server.emergency.entity.dto.*;
import com.iemp.endanger.server.emergency.mapper.*;
import com.iemp.endanger.server.emergency.service.*;
import com.iemp.endanger.server.emergency.service.impl.EmergencyExerciseServiceImpl;
import com.iemp.endanger.base.entity.BaseFile;
import com.iemp.endanger.base.mapper.BaseFileMapper;
import com.iemp.endanger.base.service.impl.BaseFileServiceImpl;
import com.baomidou.mybatisplus.core.*;
import com.baomidou.mybatisplus.core.config.GlobalConfig;
import com.baomidou.mybatisplus.core.incrementer.DefaultIdentifierGenerator;
import com.baomidou.mybatisplus.core.toolkit.GlobalConfigUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.yulichang.injector.MPJSqlInjector;
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
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.sql.*;
import java.time.LocalDateTime;
import java.util.*;
import java.util.regex.*;

/** Original/candidate batch methods on two connection-local shadow tables. */
@SuppressWarnings({"removal","unchecked"})
public final class OriginalEmergencyExerciseSqlFixture {
    static final Set<String> TABLES=new LinkedHashSet<>(List.of("emergency_exercise","base_file"));
    static final LocalDateTime OLD=LocalDateTime.of(2026,10,29,10,0),NEW=OLD.plusHours(1),START=OLD.minusHours(1);
    static void need(boolean ok,String code){if(!ok)throw new IllegalStateException(code);}
    static String hash(byte[] raw)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}
    static String hash(String text)throws Exception{return hash(text.getBytes(StandardCharsets.UTF_8));}
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
        for(String t:TABLES){String schema=ddl(c,t,temporary);if(temporary)schema=schema.replaceAll(" AUTO_INCREMENT=\\d+", "");List<String> rows=new ArrayList<>();
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
                    case Types.VARCHAR,Types.CHAR,Types.LONGVARCHAR -> "0";
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
    static void wire(Object object,String name,Object value)throws Exception {
        for(Class<?> c=object.getClass();c!=Object.class;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(object,value);return;}catch(NoSuchFieldException ignored){}
        throw new IllegalStateException("EXPECTED_FIELD");
    }
    static final String EXERCISE="emergency_exercise", FILE="base_file";
    static void seed(Connection c)throws Exception {
        need(c.getAutoCommit(),"NO_OPEN_TX_BEFORE_SEED");for(String t:List.of(FILE,EXERCISE)){ddl(c,t,true);try(Statement s=c.createStatement()){s.executeUpdate("DELETE FROM `"+t+"`");}}
        seedRow(c,EXERCISE,Map.of("id","OWN_EXIST","emergency_plan_id","OWN_PLAN","exercise_location","OWN_BASE_LOCATION","created_at",OLD));
        seedRow(c,EXERCISE,Map.of("id","OWN_OTHER","emergency_plan_id","OWN_OTHER_PLAN","exercise_location","OWN_OTHER_LOCATION","created_at",OLD));
        seedRow(c,FILE,Map.of("id","4001","correlation_id","OWN_EXIST","file_name","OWN_OLD_FILE","file_url","https://synthetic.invalid/old","created_at",OLD));
        seedRow(c,FILE,Map.of("id","4002","correlation_id","OWN_OTHER","file_name","OWN_OTHER_FILE","file_url","https://synthetic.invalid/other","created_at",OLD));
    }
    static Map<String,Object> row(Connection c,String table,String id)throws Exception{ddl(c,table,true);try(PreparedStatement p=c.prepareStatement("SELECT * FROM `"+table+"` WHERE id=?")){p.setString(1,id);try(ResultSet r=p.executeQuery()){need(r.next(),"OWN_ROW_REQUIRED");Map<String,Object> v=new LinkedHashMap<>();for(int i=1;i<=r.getMetaData().getColumnCount();i++)v.put(r.getMetaData().getColumnName(i),r.getString(i));need(!r.next(),"UNIQUE_OWN_ROW");return v;}}}
    static List<Integer> codes(Throwable t){List<Integer> out=new ArrayList<>();for(int i=0;t!=null&&i<25;i++,t=t.getCause())if(t instanceof SQLException e)out.add(e.getErrorCode());return out;}
    static int width(Connection c,String table,String column)throws Exception{ddl(c,table,true);try(PreparedStatement p=c.prepareStatement("SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.columns WHERE table_schema='tj_endanger' AND table_name=? AND column_name=?")){p.setString(1,table);p.setString(2,column);try(ResultSet r=p.executeQuery()){need(r.next(),"REAL_COLUMN_WIDTH_REQUIRED");int n=r.getInt(1);need(n>0&&n<=16384,"BOUNDED_WIDTH");return n;}}}
    static BaseFile file(String name){BaseFile f=new BaseFile();f.setId("OWN_CLIENT_ID_MUST_RESET");f.setCorrelationId("OWN_CLIENT_CORRELATION_MUST_RESET");f.setFileName(name);f.setName(name+".txt");f.setFileType("txt");f.setFileUrl("https://synthetic.invalid/"+name);f.setCreatedAt(NEW);return f;}
    static EmergencyExerciseEntity input(String id,int files){EmergencyExerciseEntity e=new EmergencyExerciseEntity();e.setId(id);e.setEmergencyPlanId("OWN_INPUT_PLAN");e.setExerciseLocation("OWN_NEW_LOCATION");e.setOrganizeDepartment("OWN_ORG");e.setCommanderChief("OWN_CHIEF");e.setExerciseTime(java.time.LocalDate.of(2026,10,29));e.setParticipants("OWN_PERSON_A,OWN_PERSON_B");e.setCooperatingUnit("OWN_COOPERATING");e.setExerciseType("1");e.setExerciseDevice("OWN_DEVICES");e.setExerciseDescribe("OWN_DESCRIPTION");e.setExerciseSpecialSituation("OWN_SPECIAL");e.setProblemsAndmeasures("OWN_MEASURES");e.setCreatedAt(NEW);if(files>=0){List<BaseFile> list=new ArrayList<>();for(int i=0;i<files;i++)list.add(file("OWN_FILE_"+i));e.setFileList(list);}return e;}
    static EmergencyExerciseSave bulk(List<EmergencyExerciseEntity> list,String plan){EmergencyExerciseSave b=new EmergencyExerciseSave();b.setEmergencyPlanId(plan);b.setEmergencyExerciseEntityList(list);return b;}
    @Intercepts({@Signature(type=Executor.class,method="update",args={MappedStatement.class,Object.class}),@Signature(type=Executor.class,method="flushStatements",args={})})
    public static final class Gate implements Interceptor {
        final Connection owner;int writes,failAt,zeroAt;final List<Integer> batchCounts=new ArrayList<>();final List<String> statements=new ArrayList<>();
        Gate(Connection owner){this.owner=owner;}
        public Object intercept(Invocation call)throws Throwable{
            if(call.getMethod().getName().equals("flushStatements")){for(String t:TABLES)ddl(owner,t,true);Object result=call.proceed();for(var b:(List<org.apache.ibatis.executor.BatchResult>)result)for(int n:b.getUpdateCounts())batchCounts.add(n);return result;}
            MappedStatement ms=(MappedStatement)call.getArgs()[0];need(ms.getId().startsWith(EmergencyExerciseMapper.class.getName()+".")||ms.getId().startsWith(BaseFileMapper.class.getName()+"."),"CLOSED_MAPPER_SET");String sql=ms.getBoundSql(call.getArgs()[1]).getSql().replace("`","").replaceAll("\\s+"," ").trim().toLowerCase(Locale.ROOT);Matcher m=Pattern.compile("^(?:insert into|update|delete from) ([a-z_]+) ").matcher(sql+" ");need(m.find()&&TABLES.contains(m.group(1))&&!sql.contains(";")&&!sql.contains("."),"UNQUALIFIED_TEMP_DML_ONLY");ddl(owner,m.group(1),true);writes++;statements.add(ms.getId());if(writes==failAt)throw new SQLException("OWN_EXERCISE_WRITE_FAILURE","45000",1644);if(writes==zeroAt)return 0;return call.proceed();
        }
        void reset(int failure,int zero){writes=0;failAt=failure;zeroAt=zero;batchCounts.clear();statements.clear();}
    }
    public static void main(String[] args)throws Exception {
        need(args.length==5,"PORT_UUID_DATADIR_MODE_OUTPUT");int port=Integer.parseInt(args[0]);boolean candidate=args[3].equals("candidate");need(candidate||args[3].equals("original"),"MODE");Path data=Path.of(args[2]).toRealPath(),out=Path.of(args[4]).toAbsolutePath();need(args[1].equals("f1f395d9-12de-4d13-a5eb-f055bc58ca2d")&&data.equals(Path.of("D:/Zqa20261025/Application/UserData/OriginalServer/database/data").toRealPath())&&!Files.exists(out)&&Files.isDirectory(out.getParent()),"EXACT_QA_FRESH_OUTPUT");byte[] rawSecret=System.in.readNBytes(4097);need(rawSecret.length>0&&rawSecret.length<=4096,"BOUNDED_STDIN");Properties props=new Properties();props.setProperty("user","root");props.setProperty("password",new String(rawSecret,StandardCharsets.UTF_8));Arrays.fill(rawSecret,(byte)0);props.putAll(Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000","useAffectedRows","true"));OriginalProcessBoundary boundary=new OriginalProcessBoundary(out.getParent(),Set.of(port),false);System.setSecurityManager(boundary);var denied=boundary.deniedCounts();Map<String,Object> report=new LinkedHashMap<>();List<Object> cases=new ArrayList<>();Map<String,String> definitions=new LinkedHashMap<>();String url="jdbc:mysql://127.0.0.1:"+port+"/tj_endanger";
        try(Connection observer=DriverManager.getConnection(url,props);Connection owner=DriverManager.getConnection(url,props)){
            observer.setReadOnly(true);identity(observer,port,args[1],data);identity(owner,port,args[1],data);Map<String,Object> permanent=snapshot(observer,false);
            try{
                for(String table:TABLES){String d=ddl(observer,table,false),s=structural(d);need(d.startsWith("CREATE TABLE `"+table+"` (")&&!s.contains(";")&&!s.contains("FOREIGN KEY")&&!s.contains("TABLESPACE"),"SAFE_TEMP_SCHEMA");need(!s.matches("(?s).*`CREATED_AT` DATETIME\\([1-9].*"),"PINNED_CREATED_AT_FSP_ZERO_REQUIRED");try(Statement st=owner.createStatement()){st.execute("CREATE TEMPORARY TABLE "+d.substring("CREATE TABLE ".length()));}ddl(owner,table,true);definitions.put(table,d);}
                SingleConnectionDataSource ds=new SingleConnectionDataSource(owner,true);MybatisConfiguration cfg=new MybatisConfiguration();cfg.setLogImpl(NoLoggingImpl.class);cfg.setMapUnderscoreToCamelCase(true);cfg.setEnvironment(new Environment("own-exercise-temp",new SpringManagedTransactionFactory(),ds));GlobalConfig global=new GlobalConfig();global.setDbConfig(new GlobalConfig.DbConfig());global.getDbConfig().setColumnFormat("`%s`");DefaultIdentifierGenerator generator=new DefaultIdentifierGenerator(7L,7L);boolean[] duplicateFile={false};global.setIdentifierGenerator(new com.baomidou.mybatisplus.core.incrementer.IdentifierGenerator(){public Number nextId(Object entity){return duplicateFile[0]&&entity instanceof BaseFile?4001L:generator.nextId(entity);}});global.setSqlInjector(new MPJSqlInjector());GlobalConfigUtils.setGlobalConfig(cfg,global);cfg.addMapper(EmergencyExerciseMapper.class);cfg.addMapper(BaseFileMapper.class);Gate gate=new Gate(owner);cfg.addInterceptor(gate);SqlSessionTemplate session=new SqlSessionTemplate(new MybatisSqlSessionFactoryBuilder().build(cfg));EmergencyExerciseMapper exercises=session.getMapper(EmergencyExerciseMapper.class);BaseFileMapper files=session.getMapper(BaseFileMapper.class);BaseFileServiceImpl fileService=new BaseFileServiceImpl();wire(fileService,"baseMapper",files);EmergencyExerciseServiceImpl target=new EmergencyExerciseServiceImpl(fileService);wire(target,"baseMapper",exercises);AnnotationTransactionAttributeSource attributes=new AnnotationTransactionAttributeSource();
                for(var method:List.of(EmergencyExerciseServiceImpl.class.getMethod("save",EmergencyExerciseEntity.class),EmergencyExerciseServiceImpl.class.getMethod("saveEmergencyExerciseList",EmergencyExerciseSave.class),EmergencyExerciseServiceImpl.class.getMethod("delete",String.class)))need((attributes.getTransactionAttribute(method,EmergencyExerciseServiceImpl.class)!=null)==candidate,"EXACT_THREE_TX_ATTRIBUTES");ProxyFactory proxy=new ProxyFactory(target);proxy.setProxyTargetClass(true);proxy.addAdvice(new TransactionInterceptor(new DataSourceTransactionManager(ds),attributes));EmergencyExerciseService api=(EmergencyExerciseService)proxy.getProxy();
                try(var in=EmergencyExerciseServiceImpl.class.getResourceAsStream("EmergencyExerciseServiceImpl.class")){report.put("loadedServiceSHA256",hash(in.readAllBytes()));}try(var in=BaseFileServiceImpl.class.getResourceAsStream("BaseFileServiceImpl.class")){report.put("loadedOriginalBaseFileServiceSHA256",hash(in.readAllBytes()));}
                for(int n:List.of(-1,0,2)){
                    seed(owner);session.clearCache();var other=row(owner,EXERCISE,"OWN_OTHER");var otherFile=row(owner,FILE,"4002");gate.reset(0,0);EmergencyExerciseEntity e=input("OWN_NEW",n);need(api.save(e),"SINGLE_SAVE_SUCCESS");var saved=exercises.selectById("OWN_NEW");need(saved!=null&&saved.getExerciseLocation().equals(e.getExerciseLocation())&&saved.getParticipants().equals(e.getParticipants())&&saved.getExerciseTime().equals(e.getExerciseTime())&&saved.getCreatedAt().equals(NEW),"EXACT_SINGLE_FIELDS");var attached=fileService.getFileList("OWN_NEW");need(attached.size()==Math.max(n,0),"EXACT_ATTACHMENT_COUNT");for(BaseFile f:attached)need(f.getCorrelationId().equals("OWN_NEW")&&!f.getId().equals("OWN_CLIENT_ID_MUST_RESET")&&f.getFileUrl().startsWith("https://synthetic.invalid/"),"ORIGINAL_ATTACHMENT_ID_BINDING_AND_URL");need(other.equals(row(owner,EXERCISE,"OWN_OTHER"))&&otherFile.equals(row(owner,FILE,"4002")),"UNRELATED_ROWS");cases.add(Map.of("case","single-success-files-"+n,"fieldsAndAttachmentsReopened",true));
                }
                for(int failure:List.of(1,2,3)){
                    seed(owner);session.clearCache();var before=snapshot(owner,true);gate.reset(failure,0);Throwable error=null;try{api.save(input("OWN_NEW",2));}catch(Throwable t){error=t;}need(error!=null&&gate.writes==failure,"SINGLE_EXCEPTION_REACHED");boolean same=before.equals(snapshot(owner,true));need(same==(candidate||failure==1)&&owner.getAutoCommit(),"SINGLE_EXCEPTION_ROLLBACK");cases.add(Map.of("case","single-exception-"+failure,"rowsUnchanged",same));
                }
                for(int zero:List.of(1,2,3)){
                    seed(owner);session.clearCache();var before=snapshot(owner,true);gate.reset(0,zero);boolean result=api.save(input("OWN_NEW",2));boolean same=before.equals(snapshot(owner,true));need(result==!candidate&&same==candidate&&owner.getAutoCommit(),"SINGLE_ZERO_WRITE_ROLLBACK");cases.add(Map.of("case","single-zero-"+zero,"returnValue",result,"rowsUnchanged",same));
                }
                seed(owner);session.clearCache();var before=snapshot(owner,true);gate.reset(0,0);duplicateFile[0]=true;Throwable real=null;try{api.save(input("OWN_NEW",2));}catch(Throwable t){real=t;}finally{duplicateFile[0]=false;}need(codes(real).contains(1062)&&before.equals(snapshot(owner,true))==candidate,"REAL_ATTACHMENT_PK1062_ROLLBACK");cases.add(Map.of("case","single-real-file-1062","rowsUnchanged",candidate,"SQLCodes",codes(real)));
                seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,0);var large=input("OWN_NEW",2);large.getFileList().get(1).setFileName("Z".repeat(width(owner,FILE,"file_name")+1));real=null;try{api.save(large);}catch(Throwable t){real=t;}need(codes(real).contains(1406)&&before.equals(snapshot(owner,true))==candidate,"REAL_LATE_FILE_1406_ROLLBACK");cases.add(Map.of("case","single-real-late-file-1406","rowsUnchanged",candidate,"SQLCodes",codes(real)));
                seed(owner);session.clearCache();gate.reset(0,0);var mixed=List.of(input("OWN_EXIST",1),input("OWN_NEW",1));need(api.saveEmergencyExerciseList(bulk(mixed,"OWN_BULK_PLAN")),"MIXED_BATCH_SUCCESS");for(var e:mixed)need(exercises.selectById(e.getId()).getEmergencyPlanId().equals("OWN_BULK_PLAN")&&fileService.getFileList(e.getId()).size()==(e.getId().equals("OWN_EXIST")?2:1),"BULK_PLAN_BINDING_AND_APPENDED_FILES");cases.add(Map.of("case","bulk-existing-new-success","originalAppendAndPlanBinding",true));
                seed(owner);session.clearCache();gate.reset(0,0);var generated=List.of(input(null,1),input(null,1));need(api.saveEmergencyExerciseList(bulk(generated,"OWN_BULK_PLAN")),"GENERATED_IDS_BATCH_SUCCESS");need(generated.get(0).getId()!=null&&!generated.get(0).getId().equals(generated.get(1).getId())&&fileService.getFileList(generated.get(0).getId()).size()==1&&fileService.getFileList(generated.get(1).getId()).size()==1,"GENERATED_IDS_FILES");cases.add(Map.of("case","bulk-generated-ids","reopened",true));
                seed(owner);session.clearCache();gate.reset(0,0);var first=input("OWN_EXIST",1);first.setExerciseLocation("OWN_FIRST_VALUE");var last=input("OWN_EXIST",1);last.setExerciseLocation("OWN_LAST_VALUE");need(api.saveEmergencyExerciseList(bulk(List.of(first,last),"OWN_BULK_PLAN"))&&exercises.selectById("OWN_EXIST").getExerciseLocation().equals("OWN_LAST_VALUE")&&fileService.getFileList("OWN_EXIST").size()==3,"DUPLICATE_ID_LAST_VALUE_AND_BOTH_FILE_LISTS");cases.add(Map.of("case","bulk-duplicate-id-last-wins","preserved",true));
                seed(owner);session.clearCache();gate.reset(0,0);first=input("OWN_EXIST",1);first.setExerciseLocation("OWN_FIRST_ALIAS_VALUE");last=input("own_exist",1);last.setExerciseLocation("OWN_LAST_ALIAS_VALUE");need(api.saveEmergencyExerciseList(bulk(List.of(first,last),"OWN_BULK_PLAN"))&&exercises.selectById("OWN_EXIST").getExerciseLocation().equals("OWN_LAST_ALIAS_VALUE")&&fileService.getFileList("OWN_EXIST").size()==3,"COLLATION_EQUIVALENT_DUPLICATE_IDS_LAST_VALUE_AND_ALL_FILES");cases.add(Map.of("case","bulk-collation-equivalent-id-last-wins","preserved",true));
                for(int failure:List.of(1,2,3,4)){
                    seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(failure,0);Throwable error=null;try{api.saveEmergencyExerciseList(bulk(List.of(input("OWN_NEW_A",1),input("OWN_NEW_B",1)),"OWN_BULK_PLAN"));}catch(Throwable t){error=t;}need(error!=null&&gate.writes==failure,"BULK_EXCEPTION_REACHED");boolean same=before.equals(snapshot(owner,true));need((!candidate||same)&&owner.getAutoCommit(),"BULK_EXCEPTION_ROLLBACK");if(!candidate&&failure>=3)need(!same,"ORIGINAL_BULK_PARTIAL_PARENT_COMMIT_REPRODUCED");cases.add(Map.of("case","bulk-exception-"+failure,"rowsUnchanged",same));
                }
                for(int zero:List.of(1,2,3,4)){
                    seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,zero);boolean result=api.saveEmergencyExerciseList(bulk(List.of(input("OWN_NEW_A",1),input("OWN_NEW_B",1)),"OWN_BULK_PLAN"));boolean same=before.equals(snapshot(owner,true));need(result==!candidate&&same==candidate&&owner.getAutoCommit(),"BULK_ZERO_PARENT_OR_FILE_ROLLBACK");cases.add(Map.of("case","bulk-zero-"+zero,"returnValue",result,"rowsUnchanged",same));
                }
                seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,0);var one=input("OWN_NEW_A",1);var two=input("OWN_NEW_B",1);two.getFileList().get(0).setFileName("Z".repeat(width(owner,FILE,"file_name")+1));real=null;try{api.saveEmergencyExerciseList(bulk(List.of(one,two),"OWN_BULK_PLAN"));}catch(Throwable t){real=t;}need(codes(real).contains(1406)&&before.equals(snapshot(owner,true))==candidate,"REAL_BULK_LATE_FILE_1406");cases.add(Map.of("case","bulk-real-late-file-1406","rowsUnchanged",candidate));
                seed(owner);session.clearCache();gate.reset(0,0);var unchanged=exercises.selectById("OWN_EXIST");unchanged.setFileList(List.of(file("OWN_NOOP_FILE")));need(api.saveEmergencyExerciseList(bulk(List.of(unchanged),"OWN_PLAN"))&&gate.batchCounts.contains(0)&&fileService.getFileList("OWN_EXIST").size()==2,"ACTUAL_MYSQL_BATCH_ZERO_NOOP_ACCEPTED");cases.add(Map.of("case","bulk-real-noop-zero-affected","actualBatchCounts",List.copyOf(gate.batchCounts)));
                for(String value:List.of("OWN_CHANGED_LOCATION","own_base_location")){
                    seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,1);var changed=exercises.selectById("OWN_EXIST");changed.setExerciseLocation(value);changed.setFileList(List.of(file("OWN_MUST_ROLLBACK_FILE")));boolean result=api.saveEmergencyExerciseList(bulk(List.of(changed),"OWN_PLAN"));need(result==!candidate&&before.equals(snapshot(owner,true))==candidate,"ZERO_UPDATE_CANNOT_ACCEPT_UNPERSISTED_FIELDS");cases.add(Map.of("case",value.equals("OWN_CHANGED_LOCATION")?"bulk-zero-changed-value":"bulk-zero-case-only-change","rowsUnchanged",candidate));
                }
                for(int nano:List.of(100000000,900000000)){
                    seed(owner);session.clearCache();ddl(owner,EXERCISE,true);try(PreparedStatement st=owner.prepareStatement("UPDATE emergency_exercise SET created_at=? WHERE id='OWN_EXIST'")){st.setObject(1,OLD.withNano(nano));st.executeUpdate();}var e=exercises.selectById("OWN_EXIST");e.setCreatedAt(OLD.withNano(nano));gate.reset(0,0);need(api.saveEmergencyExerciseList(bulk(List.of(e),"OWN_PLAN"))&&gate.batchCounts.contains(0),"REAL_COLUMN_TIME_PRECISION_NOOP_ACCEPTED");cases.add(Map.of("case","bulk-real-time-precision-noop-"+nano,"actualBatchCounts",List.copyOf(gate.batchCounts)));
                }
                seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,0);need(!api.saveEmergencyExerciseList(bulk(List.of(),"OWN_PLAN"))&&gate.writes==0&&before.equals(snapshot(owner,true)),"ORIGINAL_EMPTY_BATCH_FALSE");cases.add(Map.of("case","bulk-empty","unchanged",true));
                seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,0);Boolean returned=null;Throwable error=null;try{returned=api.saveEmergencyExerciseList(null);}catch(Throwable t){error=t;}need(candidate?Boolean.FALSE.equals(returned)&&error==null:error!=null,"NULL_BATCH_GUARD");need(before.equals(snapshot(owner,true)),"NULL_BATCH_NO_WRITES");cases.add(Map.of("case","bulk-null","unchanged",true));
                for(boolean emptyFiles:List.of(false,true)){
                    seed(owner);session.clearCache();if(emptyFiles){ddl(owner,FILE,true);try(Statement st=owner.createStatement()){st.executeUpdate("DELETE FROM base_file WHERE correlation_id='OWN_EXIST'");}}gate.reset(0,0);need(api.delete("OWN_EXIST")&&exercises.selectById("OWN_EXIST")==null&&fileService.getFileList("OWN_EXIST").isEmpty()&&exercises.selectById("OWN_OTHER")!=null&&files.selectById("4002")!=null,"DELETE_AND_EMPTY_FILES_SUCCESS");cases.add(Map.of("case",emptyFiles?"delete-no-attachments":"delete-with-attachments","reopened",true));
                }
                for(int failure:List.of(1,2)){
                    seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(failure,0);error=null;try{api.delete("OWN_EXIST");}catch(Throwable t){error=t;}need(error!=null&&gate.writes==failure,"DELETE_EXCEPTION_REACHED");boolean same=before.equals(snapshot(owner,true));need(same==(candidate||failure==1)&&owner.getAutoCommit(),"DELETE_EXCEPTION_ROLLBACK");cases.add(Map.of("case","delete-exception-"+failure,"rowsUnchanged",same));
                }
                for(int zero:List.of(1,2)){
                    seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,zero);boolean result=api.delete("OWN_EXIST");need(result==!candidate&&before.equals(snapshot(owner,true))==candidate&&owner.getAutoCommit(),"DELETE_ZERO_ROLLBACK");cases.add(Map.of("case","delete-zero-"+zero,"rowsUnchanged",candidate));
                }
                seed(owner);session.clearCache();seedRow(owner,FILE,Map.of("id","4003","correlation_id","OWN_MISSING","file_name","OWN_ORPHAN","created_at",OLD));before=snapshot(owner,true);gate.reset(0,0);boolean missing=api.delete("OWN_MISSING");need(missing==!candidate&&before.equals(snapshot(owner,true))==candidate,"MISSING_PARENT_MUST_KEEP_UNCLAIMED_FILES");cases.add(Map.of("case","delete-missing-with-orphan","unchanged",candidate));
                for(String id:Arrays.asList(null," ")){
                    seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,0);returned=null;error=null;try{returned=api.delete(id);}catch(Throwable t){error=t;}need(candidate?Boolean.FALSE.equals(returned)&&error==null:true,"DELETE_NULL_BLANK_RESULT");need(before.equals(snapshot(owner,true)),"DELETE_NULL_BLANK_NO_DATA_CHANGE");cases.add(Map.of("case",id==null?"delete-null":"delete-blank","unchanged",true));
                }
                seed(owner);session.clearCache();before=snapshot(owner,true);gate.reset(0,0);returned=null;error=null;try{returned=api.save((EmergencyExerciseEntity)null);}catch(Throwable t){error=t;}need(candidate?Boolean.FALSE.equals(returned)&&error==null:true,"SINGLE_NULL_RESULT");need(before.equals(snapshot(owner,true)),"SINGLE_NULL_NO_DATA_CHANGE");cases.add(Map.of("case","single-null","unchanged",true));
                report.put("threeEntryMethodsTransactional",candidate);report.put("actualOriginalBaseFileServiceAndMyBatisBatchExecuted",true);
            }finally{
                if(!owner.getAutoCommit())owner.rollback();owner.setAutoCommit(true);for(String table:definitions.keySet()){ddl(owner,table,true);try(Statement st=owner.createStatement()){st.execute("DROP TEMPORARY TABLE `"+table+"`");}need(ddl(owner,table,false).equals(definitions.get(table)),"PERMANENT_DDL_AFTER_TEMP_DROP");}need(permanent.equals(snapshot(observer,false)),"PERMANENT_ROWS_OR_DDL_CHANGED");Files.writeString(out.getParent().resolve("formal-integrity-after-cleanup.private.json"),new ObjectMapper().writeValueAsString(Map.of("before",permanent,"after",snapshot(observer,false),"temporaryTablesDropped",true))+"\n",StandardOpenOption.CREATE_NEW);
            }
            report.put("permanentBefore",permanent);report.put("permanentAfter",snapshot(observer,false));
        }finally{props.remove("password");}
        need(denied.equals(boundary.deniedCounts())&&System.getSecurityManager()==boundary,"NO_UNEXPECTED_BOUNDARY_ACTIVITY");report.put("mode",args[3]);report.put("cases",cases);report.put("permanentTwoTableRowsAndDDLUnchanged",true);report.put("temporaryTablesDropped",true);report.put("authenticationHTTPNotificationsOrRuntimeRestartUsed",false);report.put("actualProductionTransactionAccepted",false);report.put("fullCloneReady",false);Files.writeString(out,new ObjectMapper().writeValueAsString(report)+"\n",StandardOpenOption.CREATE_NEW);System.out.println("EMERGENCY_EXERCISE_SQL_CASES="+cases.size()+" MODE="+args[3]);
    }
}
