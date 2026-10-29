package xnby.replica;
import com.iemp.endanger.server.emergencyResponse.entity.*;
import com.iemp.endanger.server.emergencyResponse.mapper.*;
import com.iemp.endanger.server.emergencyResponse.service.*;
import com.iemp.endanger.server.emergencyResponse.service.impl.EventDisposalRecordServiceImpl;

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
public final class OriginalEventDisposalSqlFixture {
    static final Set<String> TABLES=new LinkedHashSet<>(List.of("event_info","event_disposal_record"));
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
    static final String EVENT="event_info", RECORD="event_disposal_record";
    static void seed(Connection c,String status)throws Exception{
        need(c.getAutoCommit(),"NO_OPEN_TEST_TRANSACTION");
        for(String table:List.of(RECORD,EVENT)){ddl(c,table,true);try(Statement s=c.createStatement()){s.executeUpdate("DELETE FROM `"+table+"`");}}
        seedRow(c,EVENT,Map.of("id","OWN_EVENT","deleted","0","event_name","OWN_EVENT_NAME","research_status",status));
        seedRow(c,EVENT,Map.of("id","OWN_OTHER_EVENT","deleted","0","event_name","OWN_OTHER_EVENT_NAME","research_status","1"));
        seedRow(c,RECORD,Map.of("id",4001L,"event_id","OWN_EVENT","description","OWN_OLD_DESCRIPTION","username","OWN_OLD_OPERATOR","create_time",OLD));
        seedRow(c,RECORD,Map.of("id",4002L,"event_id","OWN_OTHER_EVENT","description","OWN_UNRELATED_RECORD","username","OWN_OTHER_OPERATOR","create_time",OLD));
    }
    static EventDisposalRecord input(boolean defaultTime){EventDisposalRecord r=new EventDisposalRecord();r.setId(4003L);r.setEventId("OWN_EVENT");r.setDescription("OWN_NEW_DESCRIPTION");r.setUsername("OWN_NEW_OPERATOR");r.setAttachments("OWN_FILE_A,OWN_FILE_B");if(!defaultTime)r.setCreateTime(NEW);return r;}
    static String status(Connection c)throws Exception{ddl(c,EVENT,true);try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT research_status FROM event_info WHERE id='OWN_EVENT'")){need(r.next(),"OWN_EVENT_REQUIRED");return r.getString(1);}}
    static Map<String,Object> row(Connection c,String table,String id)throws Exception{ddl(c,table,true);try(PreparedStatement p=c.prepareStatement("SELECT * FROM `"+table+"` WHERE id=?")){p.setString(1,id);try(ResultSet r=p.executeQuery()){need(r.next(),"OWN_ROW_REQUIRED");Map<String,Object> v=new LinkedHashMap<>();for(int i=1;i<=r.getMetaData().getColumnCount();i++)v.put(r.getMetaData().getColumnName(i),r.getString(i));need(!r.next(),"UNIQUE_OWN_ROW");return v;}}}
    static List<Integer> sqlCodes(Throwable t){List<Integer> codes=new ArrayList<>();for(int i=0;i<25&&t!=null;i++,t=t.getCause())if(t instanceof SQLException e)codes.add(e.getErrorCode());return codes;}
    @Intercepts(@Signature(type=Executor.class,method="update",args={MappedStatement.class,Object.class}))
    public static final class Gate implements Interceptor {
        final Connection owner;final Set<String> names;int writes,failAt,zeroAt;final List<String> statements=new ArrayList<>();
        Gate(Connection owner,Set<String> names){this.owner=owner;this.names=names;}
        public Object intercept(Invocation call)throws Throwable{
            MappedStatement ms=(MappedStatement)call.getArgs()[0];need(names.stream().anyMatch(n->ms.getId().startsWith(n+".")),"CLOSED_MAPPER_SET");String sql=ms.getBoundSql(call.getArgs()[1]).getSql().replace("`","").replaceAll("\\s+"," ").trim().toLowerCase(Locale.ROOT);Matcher m=Pattern.compile("^(?:insert into|update|delete from) ([a-z_]+) ").matcher(sql+" ");need(m.find()&&TABLES.contains(m.group(1))&&!sql.contains(";")&&!sql.contains("."),"UNQUALIFIED_TEMP_DML_ONLY");ddl(owner,m.group(1),true);writes++;statements.add(ms.getId());if(writes==failAt)throw new SQLException("OWN_DISPOSAL_WRITE_FAILURE","45000",1644);if(writes==zeroAt)return 0;return call.proceed();
        }
        void reset(int failure,int zero){writes=0;failAt=failure;zeroAt=zero;statements.clear();}
    }
    public static void main(String[] args)throws Exception{
        need(args.length==5,"PORT_UUID_DATADIR_MODE_OUTPUT_REQUIRED");int port=Integer.parseInt(args[0]);boolean candidate=args[3].equals("candidate");need(candidate||args[3].equals("original"),"EXACT_MODE");Path data=Path.of(args[2]).toRealPath(),out=Path.of(args[4]).toAbsolutePath();need(args[1].equals("f1f395d9-12de-4d13-a5eb-f055bc58ca2d")&&data.equals(Path.of("D:/Zqa20261025/Application/UserData/OriginalServer/database/data").toRealPath())&&!Files.exists(out)&&Files.isDirectory(out.getParent()),"EXACT_QA_AND_FRESH_OUTPUT");
        byte[] secret=System.in.readNBytes(4097);need(secret.length>0&&secret.length<=4096,"BOUNDED_STDIN_SECRET");Properties props=new Properties();props.setProperty("user","root");props.setProperty("password",new String(secret,StandardCharsets.UTF_8));Arrays.fill(secret,(byte)0);props.putAll(Map.of("useSSL","false","allowPublicKeyRetrieval","true","autoReconnect","false","allowMultiQueries","false","characterEncoding","UTF-8","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000","useAffectedRows","true"));
        OriginalProcessBoundary boundary=new OriginalProcessBoundary(out.getParent(),Set.of(port),false);System.setSecurityManager(boundary);int checks=0;try{boundary.checkConnect("synthetic.invalid",443);}catch(SecurityException e){checks++;}try{boundary.checkExec("OWN_NEVER_EXECUTED");}catch(SecurityException e){checks++;}need(checks==2,"BOUNDARY_SELF_TESTS");var denied=boundary.deniedCounts();Map<String,Object> report=new LinkedHashMap<>();List<Object> cases=new ArrayList<>();String url="jdbc:mysql://127.0.0.1:"+port+"/tj_endanger";
        try(Connection observer=DriverManager.getConnection(url,props);Connection owner=DriverManager.getConnection(url,props)){
            observer.setReadOnly(true);identity(observer,port,args[1],data);identity(owner,port,args[1],data);Map<String,Object> permanent=snapshot(observer,false);Map<String,String> definitions=new LinkedHashMap<>();
            try{
                for(String table:TABLES){String d=ddl(observer,table,false),s=structural(d);need(d.startsWith("CREATE TABLE `"+table+"` (")&&!s.contains(";")&&!s.contains("FOREIGN KEY")&&!s.contains("TABLESPACE"),"SAFE_ORIGINAL_TEMPORARY_SCHEMA");try(Statement st=owner.createStatement()){st.execute("CREATE TEMPORARY TABLE "+d.substring("CREATE TABLE ".length()));}ddl(owner,table,true);definitions.put(table,d);}
                SingleConnectionDataSource ds=new SingleConnectionDataSource(owner,true);MybatisConfiguration cfg=new MybatisConfiguration();cfg.setLogImpl(NoLoggingImpl.class);cfg.setMapUnderscoreToCamelCase(true);cfg.setEnvironment(new Environment("own-event-disposal-temp",new SpringManagedTransactionFactory(),ds));GlobalConfig global=new GlobalConfig();global.setDbConfig(new GlobalConfig.DbConfig());global.getDbConfig().setColumnFormat("`%s`");global.setIdentifierGenerator(new DefaultIdentifierGenerator(7L,7L));global.setSqlInjector(new MPJSqlInjector());GlobalConfigUtils.setGlobalConfig(cfg,global);cfg.addMapper(EventInfoMapper.class);cfg.addMapper(EventDisposalRecordMapper.class);Gate gate=new Gate(owner,Set.of(EventInfoMapper.class.getName(),EventDisposalRecordMapper.class.getName()));cfg.addInterceptor(gate);SqlSessionTemplate session=new SqlSessionTemplate(new MybatisSqlSessionFactoryBuilder().build(cfg));EventInfoMapper event=session.getMapper(EventInfoMapper.class);EventDisposalRecordMapper records=session.getMapper(EventDisposalRecordMapper.class);EventDisposalRecordServiceImpl target=new EventDisposalRecordServiceImpl();wire(target,"baseMapper",records);wire(target,"infoMapper",event);
                boolean annotated=new AnnotationTransactionAttributeSource().getTransactionAttribute(EventDisposalRecordServiceImpl.class.getMethod("saveRecord",EventDisposalRecord.class),EventDisposalRecordServiceImpl.class)!=null;need(annotated==candidate,"EXACT_TRANSACTION_ATTRIBUTE");EventDisposalRecordService api=target;if(annotated){ProxyFactory factory=new ProxyFactory(target);factory.addAdvice(new TransactionInterceptor(new DataSourceTransactionManager(ds),new AnnotationTransactionAttributeSource()));api=(EventDisposalRecordService)factory.getProxy();}
                try(var raw=EventDisposalRecordServiceImpl.class.getResourceAsStream("EventDisposalRecordServiceImpl.class")){need(raw!=null,"LOADED_SERVICE_BYTES");report.put("loadedClassSHA256",hash(raw.readAllBytes()));}
                for(boolean defaultTime:List.of(false,true)){
                    seed(owner,"1");session.clearCache();var oldOther=row(owner,EVENT,"OWN_OTHER_EVENT");var oldRecord=row(owner,RECORD,"4002");gate.reset(0,0);EventDisposalRecord input=input(defaultTime);LocalDateTime started=LocalDateTime.now().minusSeconds(2);need(api.saveRecord(input)&&gate.writes==2&&"2".equals(status(owner)),"PARENT_AND_CHILD_SAVED");EventDisposalRecord saved=records.selectById(4003L);need(saved!=null&&saved.getEventId().equals("OWN_EVENT")&&saved.getDescription().equals("OWN_NEW_DESCRIPTION")&&saved.getUsername().equals("OWN_NEW_OPERATOR")&&saved.getAttachments().equals("OWN_FILE_A,OWN_FILE_B"),"EXACT_REOPENED_FIELDS");need(defaultTime?!saved.getCreateTime().isBefore(started)&&!saved.getCreateTime().isAfter(LocalDateTime.now().plusSeconds(2)):NEW.equals(saved.getCreateTime()),"ORIGINAL_EXPLICIT_OR_DEFAULT_TIME");need(oldOther.equals(row(owner,EVENT,"OWN_OTHER_EVENT"))&&oldRecord.equals(row(owner,RECORD,"4002")),"UNRELATED_ROWS_PRESERVED");cases.add(Map.of("case",defaultTime?"default-time-success":"explicit-time-success","fieldsReopened",true));
                }
                for(int failure:List.of(1,2)){
                    seed(owner,"1");session.clearCache();var before=snapshot(owner,true);gate.reset(failure,0);Throwable error=null;try{api.saveRecord(input(false));}catch(Throwable t){error=t;}need(error!=null&&gate.writes==failure,"INJECTED_WRITE_FAILURE_REACHED");boolean same=before.equals(snapshot(owner,true));need(same==(candidate||failure==1)&&owner.getAutoCommit(),"EXCEPTION_ROLLBACK");cases.add(Map.of("case","write-exception-"+failure,"rowsUnchanged",same,"SQLCodes",sqlCodes(error)));
                }
                seed(owner,"1");session.clearCache();var before=snapshot(owner,true);gate.reset(0,0);EventDisposalRecord duplicate=input(false);duplicate.setId(4001L);Throwable duplicateError=null;try{api.saveRecord(duplicate);}catch(Throwable t){duplicateError=t;}need(sqlCodes(duplicateError).contains(1062)&&gate.writes==2,"ACTUAL_MYSQL_DUPLICATE_KEY_1062");need(before.equals(snapshot(owner,true))==candidate&&owner.getAutoCommit(),"REAL_SQL_FAILURE_ROLLBACK");cases.add(Map.of("case","real-duplicate-key-1062","rowsUnchanged",candidate,"SQLCodes",sqlCodes(duplicateError)));
                for(int zero:List.of(1,2)){
                    seed(owner,"1");session.clearCache();before=snapshot(owner,true);gate.reset(0,zero);boolean result=api.saveRecord(input(false));boolean same=before.equals(snapshot(owner,true));need(result==(!candidate&&zero==1)&&same==candidate&&owner.getAutoCommit(),"FALSE_WRITE_MUST_NOT_PARTIALLY_COMMIT");cases.add(Map.of("case","zero-row-write-"+zero,"returnValue",result,"rowsUnchanged",same,"executedWrites",gate.writes));
                }
                seed(owner,"2");session.clearCache();gate.reset(0,0);need(api.saveRecord(input(false))&&"2".equals(status(owner))&&gate.writes==2,"ALREADY_PROCESSING_REAL_ZERO_AFFECTED_UPDATE_ACCEPTED");cases.add(Map.of("case","already-processing-real-noop-update","success",true));
                seed(owner,"1");session.clearCache();before=snapshot(owner,true);gate.reset(0,0);EventDisposalRecord missing=input(false);missing.setEventId("OWN_MISSING_EVENT");boolean result=api.saveRecord(missing);need(result==!candidate&&before.equals(snapshot(owner,true))==candidate,"MISSING_PARENT_RESULT_AND_NO_ORPHAN");cases.add(Map.of("case","missing-parent","returnValue",result,"rowsUnchanged",candidate));
                seed(owner,"1");session.clearCache();before=snapshot(owner,true);gate.reset(0,0);Boolean value=null;Throwable nullError=null;try{value=api.saveRecord(null);}catch(Throwable t){nullError=t;}need(candidate?Boolean.FALSE.equals(value)&&nullError==null:nullError!=null,"NULL_RECORD_GUARD");need(before.equals(snapshot(owner,true))&&gate.writes==0,"NULL_RECORD_NO_WRITES");cases.add(Map.of("case","null-record","candidateReturnsFalse",candidate));
                seed(owner,"1");session.clearCache();before=snapshot(owner,true);gate.reset(0,0);EventDisposalRecord blank=input(false);blank.setEventId(" ");result=api.saveRecord(blank);need(result==!candidate&&before.equals(snapshot(owner,true))==candidate,"BLANK_PARENT_RESULT_AND_NO_ORPHAN");cases.add(Map.of("case","blank-parent","returnValue",result,"rowsUnchanged",candidate));
                report.put("transactionAttribute",annotated);report.put("actualOriginalServiceAndMyBatisMappersExecuted",true);
            }finally{
                if(!owner.getAutoCommit())owner.rollback();owner.setAutoCommit(true);for(String table:definitions.keySet()){ddl(owner,table,true);try(Statement s=owner.createStatement()){s.execute("DROP TEMPORARY TABLE `"+table+"`");}need(ddl(owner,table,false).equals(definitions.get(table)),"ORIGINAL_DDL_AFTER_TEMP_DROP");}Map<String,Object> after=snapshot(observer,false);need(permanent.equals(after),"PERMANENT_ROWS_OR_DDL_CHANGED");Files.writeString(out.getParent().resolve("formal-integrity-after-cleanup.private.json"),new ObjectMapper().writeValueAsString(Map.of("before",permanent,"after",after,"temporaryTablesDropped",true))+"\n",StandardOpenOption.CREATE_NEW);
            }
            report.put("permanentBefore",permanent);report.put("permanentAfter",snapshot(observer,false));
        }finally{props.remove("password");}
        need(denied.equals(boundary.deniedCounts())&&System.getSecurityManager()==boundary,"NO_UNEXPECTED_BOUNDARY_ACTIVITY");need(cases.size()==11,"EXACT_ELEVEN_CASES");report.put("mode",args[3]);report.put("cases",cases);report.put("permanentTwoTableRowsAndDDLUnchanged",true);report.put("temporaryTablesDropped",true);report.put("temporaryRollbackStructureComparisonExcludesAutoIncrementCounter",true);report.put("authenticationHTTPNotificationOrRuntimeRestartUsed",false);report.put("actualProductionTransactionAccepted",false);report.put("fullCloneReady",false);Files.writeString(out,new ObjectMapper().writeValueAsString(report)+"\n",StandardOpenOption.CREATE_NEW);System.out.println("EVENT_DISPOSAL_SQL_CASES="+cases.size()+" MODE="+args[3]);
    }
}
