package xnby.platform.history;

import com.baomidou.dynamic.datasource.DynamicRoutingDataSource;
import com.baomidou.dynamic.datasource.tx.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.sql.*;
import java.security.MessageDigest;
import java.util.*;
import javax.sql.DataSource;
import jnpf.engine.entity.FlowTaskOperatorRecordEntity;
import jnpf.engine.mapper.FlowTaskOperatorRecordMapper;
import org.apache.ibatis.session.*;
import org.apache.ibatis.mapping.*;
import org.apache.ibatis.transaction.managed.ManagedTransactionFactory;
import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.MybatisSqlSessionFactoryBuilder;
import com.baomidou.mybatisplus.core.config.GlobalConfig;
import com.baomidou.mybatisplus.core.toolkit.GlobalConfigUtils;

/** Fresh loopback MySQL and the shipped DS transaction implementation; never an installed database. */
public final class OwnAddsignMybatisFixture {
  private static String password, url, uuid;
  private static int port;
  private static Path root, data;
  private static final String ACTOR="OWN_REVIEWER_B", PROCESS="OWN_PROCESS_R180", SOURCE="OWN_SOURCE_RECORD_R180";
  private static final List<String> cases=new ArrayList<>();
  private static final TransactionalTemplate TRANSACTIONS=new TransactionalTemplate();
  private static DynamicRoutingDataSource routing;
  private interface Work { Object run() throws Throwable; }
  private static void need(boolean ok,String code) { if(!ok)throw new IllegalStateException(code); }
  private static final class OwnDataSource implements DataSource {
    public Connection getConnection()throws SQLException{Connection c=DriverManager.getConnection(url,"xnby_history_r180",password);try(Statement s=c.createStatement()){s.execute("SET time_zone='+08:00'");}return c;}
    public Connection getConnection(String user,String pass)throws SQLException{throw new SQLException("NO_ALTERNATE_IDENTITY");}
    public PrintWriter getLogWriter(){return null;}public void setLogWriter(PrintWriter out){}
    public void setLoginTimeout(int seconds){}public int getLoginTimeout(){return 0;}
    public java.util.logging.Logger getParentLogger(){return java.util.logging.Logger.getLogger("own-history-fixture");}
    public <T>T unwrap(Class<T> type)throws SQLException{throw new SQLException("NO_UNWRAP");}
    public boolean isWrapperFor(Class<?> type){return false;}
  }
  private static Connection raw()throws Exception {
    Connection c=new OwnDataSource().getConnection();
    try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){
      need(r.next()&&uuid.equals(r.getString(1))&&r.getInt(2)==port&&data.equals(Path.of(r.getString(3)).toRealPath())&&"jnpf".equals(r.getString(4)),"ONLY_FRESH_OWN_MYSQL_IDENTITY");
    }return c;
  }
  @SuppressWarnings("unchecked") private static Object transaction(Work work)throws Throwable {
    Object result=TRANSACTIONS.execute(new TransactionalExecutor(){
      public Object execute()throws Throwable{return work.run();}
      public TransactionalInfo getTransactionInfo(){TransactionalInfo i=new TransactionalInfo();i.setPropagation(DsPropagation.REQUIRED);i.setRollbackFor(new Class[]{Exception.class});i.setNoRollbackFor(new Class[0]);return i;}
    });
    need(TransactionContext.getXID()==null&&OriginalAddsignOpinionHistory.transactionStateCleared(),"NATIVE_TX_CONTEXT_CLEARED_AFTER_COMMIT");return result;
  }
  private static void update(Connection c,int status,String opinion)throws Exception {
    try(PreparedStatement p=c.prepareStatement("UPDATE flow_task_operator_record SET f_handle_status=?,f_handle_opinion=?,f_creator_time=CURRENT_TIMESTAMP,f_handle_time=IF(?=1,CURRENT_TIMESTAMP,NULL) WHERE f_id=?")){
      p.setInt(1,status);p.setString(2,opinion);p.setInt(3,status);p.setString(4,SOURCE);need(p.executeUpdate()==1,"ONE_OWN_NATIVE_RECORD_UPDATED");
    }
  }
  private static String rows()throws Exception {
    MessageDigest digest=MessageDigest.getInstance("SHA-256");
    try(Connection c=raw()){c.setReadOnly(true);try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT * FROM flow_task_operator_record ORDER BY f_id")){
      int n=0;while(r.next()){need(++n<=8,"BOUNDED_OWN_HISTORY_ROWS");for(int k=1;k<=r.getMetaData().getColumnCount();k++){String x=r.getString(k);byte[] b=(x==null?"<NULL>":x).getBytes(StandardCharsets.UTF_8);digest.update(java.nio.ByteBuffer.allocate(4).putInt(b.length).array());digest.update(b);}}
    }}return HexFormat.of().formatHex(digest.digest());
  }
  private static long count(String where)throws Exception {
    need(Set.of("1=1","f_task_operator_id=''","f_task_node_id='OWN_NATIVE_NODE_B'","f_task_operator_id='OWN_NATIVE_OPERATOR_B'").contains(where),"FIXED_OWN_COUNT_SCOPE");
    try(Connection c=raw();Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT COUNT(*) FROM flow_task_operator_record WHERE "+where)){need(r.next(),"OWN_COUNT");return r.getLong(1);}
  }
  private static void verifyHistory()throws Exception {
    try(Connection c=raw();PreparedStatement p=c.prepareStatement("SELECT f_handle_status,f_handle_opinion,f_handle_id,f_handle_time,f_task_node_id,f_task_operator_id FROM flow_task_operator_record WHERE f_task_operator_id='' ORDER BY f_handle_opinion" );ResultSet r=p.executeQuery()){
      List<String> opinions=new ArrayList<>();while(r.next()){need(r.getInt(1)==10&&ACTOR.equals(r.getString(3))&&r.getTimestamp(4)!=null&&"".equals(r.getString(5))&&"".equals(r.getString(6)),"TIMED_NATIVE_HISTORY_DETACHED_FROM_ACTIVE_TASK");opinions.add(r.getString(2));}
      need(opinions.equals(List.of("OWN_BEFORE_ADDSIGN_FIRST","OWN_BEFORE_ADDSIGN_SECOND")),"BOTH_SUCCESSFUL_ADDSIGN_OPINIONS_RETAINED");
    }
    need(count("1=1")==3&&count("f_task_operator_id=''")==2&&count("f_task_node_id='OWN_NATIVE_NODE_B'")==1&&count("f_task_operator_id='OWN_NATIVE_OPERATOR_B'")==1,"HISTORY_CANNOT_DUPLICATE_ACTIVE_LOOKUP");
  }
  private static SqlSessionFactory factory(boolean simulateServiceScope)throws Exception {
    MybatisConfiguration config=new MybatisConfiguration();
    config.setEnvironment(new Environment("own-native-history",new ManagedTransactionFactory(),routing));
    config.setLogImpl(org.apache.ibatis.logging.nologging.NoLoggingImpl.class);
    GlobalConfig global=new GlobalConfig();global.setDbConfig(new GlobalConfig.DbConfig());
    GlobalConfigUtils.setGlobalConfig(config,global);
    config.addInterceptor(simulateServiceScope?new OriginalBeforeAddsignHistoryInterceptor(()->true):new OriginalBeforeAddsignHistoryInterceptor());
    config.addMapper(FlowTaskOperatorRecordMapper.class);
    MappedStatement nativeUpdate=config.getMappedStatement("jnpf.engine.mapper.FlowTaskOperatorRecordMapper.updateById");
    config.addMappedStatement(new MappedStatement.Builder(config,"own.nonTargetUpdate",nativeUpdate.getSqlSource(),SqlCommandType.UPDATE).build());
    return new MybatisSqlSessionFactoryBuilder().build(config);
  }
  private static void mapperUpdate(SqlSessionFactory factory,ExecutorType type,int status,String opinion,boolean nonTarget)throws Exception {
    try(SqlSession session=factory.openSession(type,false)){
      FlowTaskOperatorRecordMapper mapper=session.getMapper(FlowTaskOperatorRecordMapper.class);
      FlowTaskOperatorRecordEntity entity=mapper.selectById(SOURCE);
      need(entity!=null&&PROCESS.equals(entity.getTaskId())&&ACTOR.equals(entity.getHandleId()),"ORIGINAL_MAPPER_AND_ENTITY_READ_OWN_ROW");
      entity.setHandleStatus(status);entity.setHandleOpinion(opinion);entity.setCreatorTime(new java.util.Date());if(status==10&&!opinion.equals("OWN_MISSING_NATIVE_TIMESTAMP"))entity.setHandleTime(new java.util.Date());
      if(nonTarget)session.update("own.nonTargetUpdate",Map.of("et",entity));else mapper.updateById(entity);
      session.commit();
    }
  }
  private static boolean sqlState(Throwable error,String expected){for(Throwable p=error;p!=null;p=p.getCause())if(p instanceof SQLException&&expected.equals(((SQLException)p).getSQLState()))return true;return false;}
  public static void main(String[]args)throws Throwable {
    need(args.length==5,"OWN_HISTORY_FIXTURE_ARGUMENTS");root=Path.of(args[0]).toRealPath();need(root.toString().replace('\\','/').equals("D:/Project/Zhumadian/work/addsign-history-r180/mybatis-lab-r191"),"EXACT_FRESH_FIXTURE_ROOT");data=root.resolve("data").toRealPath();port=Integer.parseInt(args[1]);uuid=args[2];need(uuid.matches("[0-9a-f-]{36}")&&Files.readString(data.resolve("auto.cnf")).contains("server-uuid="+uuid),"OWN_DATA_DIRECTORY_UUID");String mode=args[3];need(Set.of("exercise","verify","stop").contains(mode),"EXPLICIT_OWN_MODE");password=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"),"OWN_EPHEMERAL_CREDENTIAL_STDIN_ONLY");url="jdbc:mysql://127.0.0.1:"+port+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=15000";
    try(Connection c=raw()){
      if(mode.equals("stop")){try(Statement s=c.createStatement()){s.execute("SHUTDOWN");}password=null;System.out.println("OWN_HISTORY_SQL_SHUTDOWN_SENT");return;}
    }
    if(mode.equals("verify")){verifyHistory();need(rows().equals(Files.readString(root.resolve("durable-row-sha.txt")).trim()),"SAME_ROWS_AFTER_NORMAL_MYSQL_RESTART");password=null;System.out.println("OWN_HISTORY_RESTART_DURABILITY_PASSED");return;}
    Path ddl=Path.of(args[4]).toRealPath();need(ddl.equals(root.resolve("original-record-ddl.sql")),"OWN_ORIGINAL_DDL_FILE");String schema=Files.readString(ddl);need(schema.startsWith("CREATE TABLE `flow_task_operator_record`")&&!schema.contains("FOREIGN KEY")&&schema.length()<16000,"ORIGINAL_RECORD_SCHEMA_ONLY");
    try(Connection c=raw();Statement s=c.createStatement()){s.execute(schema);s.executeUpdate("INSERT INTO flow_task_operator_record(f_id,f_node_code,f_node_name,f_handle_status,f_handle_id,f_task_operator_id,f_task_node_id,f_task_id,f_delete_mark) VALUES('"+SOURCE+"','OWN_APPROVE','OWN_NODE',18,'"+ACTOR+"','OWN_NATIVE_OPERATOR_B','OWN_NATIVE_NODE_B','"+PROCESS+"',0)");}
    routing=new DynamicRoutingDataSource(List.of());routing.setPrimary("jnpf");routing.addDataSource("jnpf",new OwnDataSource());
    SqlSessionFactory defaultFactory=factory(false),nativeFactory=factory(true);
    mapperUpdate(defaultFactory,ExecutorType.SIMPLE,10,"OWN_OUTSIDE_NATIVE_SERVICE",false);
    need(count("f_task_operator_id=''")==0,"ORDINARY_MAPPER_CALL_MUST_NOT_CREATE_HISTORY");cases.add("default-original-service-call-gate-leaves-ordinary-mapper-unchanged");
    try(Connection c=raw()){update(c,18,"OWN_BASELINE");}String before=rows();
    try{mapperUpdate(nativeFactory,ExecutorType.SIMPLE,10,"OWN_NO_NATIVE_TRANSACTION",false);throw new AssertionError("MAPPER_WRITE_WITHOUT_NATIVE_TX_ACCEPTED");}catch(RuntimeException expected){need(rows().equals(before),"TX_REFUSAL_BEFORE_ORIGINAL_UPDATE");}
    cases.add("missing-native-transaction-refused-before-mapper-update");
    transaction(()->{mapperUpdate(nativeFactory,ExecutorType.SIMPLE,10,"OWN_BEFORE_ADDSIGN_FIRST",false);return null;});
    try(Connection c=raw();Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT (h.f_handle_time=s.f_handle_time),ABS(TIMESTAMPDIFF(SECOND,s.f_handle_time,CURRENT_TIMESTAMP)) FROM flow_task_operator_record h JOIN flow_task_operator_record s ON s.f_id='"+SOURCE+"' WHERE h.f_task_operator_id=''")){need(r.next()&&r.getBoolean(1)&&r.getLong(2)>7*3600&&!r.next(),"NATIVE_DATE_EXACT_WITH_EIGHT_HOUR_SQL_SESSION_OFFSET");}cases.add("history-copies-original-java-date-despite-eight-hour-session-clock-offset");
    need(count("f_task_operator_id=''")==1,"ORIGINAL_SIMPLE_UPDATE_CREATED_ONE_HISTORY");try(Connection c=raw()){update(c,1,"OWN_LATER_APPROVAL_FIRST");}cases.add("original-mapper-simple-executor-appends-history-in-native-transaction");
    try(Connection c=raw()){update(c,18,"OWN_BASELINE_SECOND");}
    transaction(()->{mapperUpdate(nativeFactory,ExecutorType.BATCH,10,"OWN_BEFORE_ADDSIGN_SECOND",false);return null;});
    try(Connection c=raw()){update(c,1,"OWN_LATER_APPROVAL_SECOND");}verifyHistory();cases.add("original-mapper-batch-executor-flush-and-history-commit");
    before=rows();
    try{transaction(()->{mapperUpdate(nativeFactory,ExecutorType.BATCH,10,"OWN_ROLLBACK_AFTER_BATCH_HISTORY",false);throw new IOException("OWN_AFTER_NATIVE_BATCH_HISTORY");});throw new AssertionError("NATIVE_BATCH_FAILURE_NOT_THROWN");}catch(IOException expected){need(expected.getMessage().equals("OWN_AFTER_NATIVE_BATCH_HISTORY"),"EXPECTED_BATCH_FAULT_ONLY");}
    need(rows().equals(before)&&OriginalAddsignOpinionHistory.transactionStateCleared()&&TransactionContext.getXID()==null,"NATIVE_MAPPER_SOURCE_AND_HISTORY_ROLLED_BACK");cases.add("post-mapper-batch-failure-rolls-back-original-and-history");
    try(Connection c=raw();Statement statement=c.createStatement()){statement.execute("CREATE TRIGGER own_r181_history_fault BEFORE INSERT ON flow_task_operator_record FOR EACH ROW BEGIN IF NEW.f_task_operator_id='' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='OWN_NATIVE_HISTORY_INSERT_FAULT'; END IF; END");}
    try{transaction(()->{mapperUpdate(nativeFactory,ExecutorType.SIMPLE,10,"OWN_NATIVE_SQL_INSERT_FAULT",false);return null;});throw new AssertionError("NATIVE_HISTORY_SQL_FAULT_NOT_THROWN");}catch(Throwable expected){need(sqlState(expected,"45000"),"ONLY_EXPECTED_NATIVE_SQL_TRIGGER_FAULT");}finally{try(Connection c=raw();Statement statement=c.createStatement()){statement.execute("DROP TRIGGER own_r181_history_fault");}}
    need(rows().equals(before)&&OriginalAddsignOpinionHistory.transactionStateCleared(),"REAL_MAPPER_TRIGGER_FAILURE_ROLLED_BACK_EXACT_ROWS");cases.add("history-sql-fault-rolls-back-actual-native-mapper-update");
    transaction(()->{mapperUpdate(nativeFactory,ExecutorType.SIMPLE,10,"OWN_NON_TARGET_STATEMENT",true);return null;});need(count("f_task_operator_id=''")==2,"OTHER_MAPPED_STATEMENT_MUST_NOT_CREATE_HISTORY");cases.add("non-target-mapped-statement-unmodified");
    mapperUpdate(nativeFactory,ExecutorType.SIMPLE,1,"OWN_FINAL_ORDINARY_APPROVAL",false);verifyHistory();cases.add("ordinary-approval-status-and-current-task-lookups-preserved");
    try(Connection c=raw()){update(c,18,"OWN_BEFORE_MISSING_TIME");}before=rows();
    try{transaction(()->{mapperUpdate(nativeFactory,ExecutorType.SIMPLE,10,"OWN_MISSING_NATIVE_TIMESTAMP",false);return null;});throw new AssertionError("MISSING_NATIVE_TIME_ACCEPTED");}catch(Throwable expected){need(sqlState(expected,"S1000")||sqlState(expected,"HY000")||expected.toString().contains("EXACT_NATIVE_BEFORE_ADDSIGN_RECORD_NOT_UPDATED"),"MISSING_TIME_REJECTED_IN_NATIVE_TRANSACTION");}
    need(rows().equals(before)&&OriginalAddsignOpinionHistory.transactionStateCleared(),"MISSING_NATIVE_TIME_REJECTION_ROLLS_BACK_SOURCE_AND_HISTORY");cases.add("missing-original-native-date-refused-with-complete-transaction-rollback");
    Files.writeString(root.resolve("durable-row-sha.txt"),rows()+"\n");String json="{\"passed\":true,\"realOriginalDynamicTransactionTemplate\":true,\"actualMySQL\":true,\"originalRecordDDLUnchanged\":true,\"cases\":"+cases.size()+",\"caseNames\":["+String.join(",",cases.stream().map(x->"\""+x+"\"").toList())+"],\"realOriginalMapperEntityAndMybatisPlus\":true,\"originalServiceCallContextSimulatedOnly\":true,\"normalRoleOrEngineIntegrationVerified\":false,\"productOrPublicInstalled\":false}";Files.writeString(root.resolve("sql-result.json"),json+"\n");routing.destroy();password=null;System.out.println(json);
  }
}
