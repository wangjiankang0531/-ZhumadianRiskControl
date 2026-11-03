import java.io.*;import java.nio.*;import java.nio.file.*;import java.security.*;import java.sql.*;import java.util.*;
/** Narrow fault on the one owned synthetic process; no account or session reads. */
public final class OwnNativeHistoryFaultR204 {
 static final String TRIGGER="xnby_own_r204_before_history_fault",ACTOR="a5310000000000000000000000000065";
 static void need(boolean v)throws Exception{if(!v)throw new Exception("OWN_NATIVE_HISTORY_FAULT_SCOPE_REJECTED");}
 static String hex(byte[]a){StringBuilder b=new StringBuilder();for(byte v:a)b.append(String.format(Locale.ROOT,"%02x",v&255));return b.toString();}
 static String digest(String s)throws Exception{return hex(MessageDigest.getInstance("SHA-256").digest(s.getBytes("UTF-8")));}
 static final String[] QUERIES={
  "SELECT * FROM jnpf.flow_task WHERE f_id=? ORDER BY f_id",
  "SELECT * FROM jnpf.flow_task_operator WHERE f_task_id=? ORDER BY f_id",
  "SELECT * FROM jnpf.flow_task_node WHERE f_task_id=? ORDER BY f_id",
  "SELECT * FROM jnpf.flow_task_operator_record WHERE f_task_id=? ORDER BY f_id",
  "SELECT * FROM jnpf.act_ru_task WHERE PROC_INST_ID_=? ORDER BY ID_",
  "SELECT * FROM jnpf.act_ru_execution WHERE PROC_INST_ID_=? ORDER BY ID_",
  "SELECT * FROM jnpf.act_hi_taskinst WHERE PROC_INST_ID_=? ORDER BY ID_",
  "SELECT * FROM tj_endanger.event_task WHERE id=? AND flow_id=? ORDER BY id"};
 static Properties snapshot(Connection c,String flow,String task)throws Exception{
  Properties result=new Properties();c.setReadOnly(true);c.setAutoCommit(false);
  try{for(int k=0;k<QUERIES.length;k++){MessageDigest d=MessageDigest.getInstance("SHA-256");int rows=0,total=0;
   try(PreparedStatement p=c.prepareStatement(QUERIES[k])){p.setQueryTimeout(10);p.setString(1,k==7?task:flow);if(k==7)p.setString(2,flow);
    try(ResultSet r=p.executeQuery()){int cols=r.getMetaData().getColumnCount();need(cols<=128);while(r.next()){need(++rows<=5000);for(int j=1;j<=cols;j++){byte[]v=r.getBytes(j);if(v==null)d.update(ByteBuffer.allocate(4).putInt(-1).array());else{need(v.length<=2*1024*1024&&(total+=v.length)<=16*1024*1024);d.update(ByteBuffer.allocate(4).putInt(v.length).array());d.update(v);}}}}
   }d.update(ByteBuffer.allocate(4).putInt(rows).array());result.setProperty("query"+k,hex(d.digest()));
  }}finally{c.rollback();c.setAutoCommit(true);c.setReadOnly(false);}return result;
 }
 static String existingTrigger(Connection c)throws Exception{
  try(PreparedStatement p=c.prepareStatement("SELECT ACTION_STATEMENT,EVENT_OBJECT_TABLE,ACTION_TIMING,EVENT_MANIPULATION FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='jnpf' AND TRIGGER_NAME=?")){p.setString(1,TRIGGER);try(ResultSet r=p.executeQuery()){if(!r.next())return null;String body=r.getString(1);need("flow_task_operator_record".equals(r.getString(2))&&"BEFORE".equals(r.getString(3))&&"INSERT".equals(r.getString(4))&&!r.next());return body;}}
 }
 public static void main(String[]a)throws Exception{
  need(a.length==8&&Set.of("arm","verify-drop","cleanup").contains(a[4]));Path data=Path.of(a[2]).toRealPath(),root=Path.of(a[3]).toRealPath();need(data.toString().replace('\\','/').equals("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data")&&root.toString().replace('\\','/').equals("D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r163/r102"));
  need(!Files.exists(Path.of("D:/Project/Zhumadian/_g/user-manual-protected.json")));String flow=a[5],task=a[6];need(flow.matches("[A-Za-z0-9_-]{1,64}")&&task.matches("[A-Za-z0-9_-]{1,64}")&&a[7].equals("Own serial workflow R163 r102"));
  String password=new BufferedReader(new InputStreamReader(System.in)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"));
  String body="BEGIN IF NEW.f_task_id='"+flow+"' AND NEW.f_handle_id='"+ACTOR+"' AND NEW.f_handle_status=10 AND COALESCE(NEW.f_task_operator_id,'')='' AND COALESCE(NEW.f_task_node_id,'')='' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='OWN_R204_HISTORY_SQL_FAULT'; END IF; END";
  Path scope=root.resolve("native-history-sql-fault-scope.private.properties");Properties pins=new Properties();
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+Integer.parseInt(a[0])+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=15000","root",password)){
   password=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&data.equals(Path.of(r.getString(2)).toRealPath()));}
   try(PreparedStatement p=c.prepareStatement("SELECT task_name FROM tj_endanger.event_task WHERE id=? AND flow_id=?")){p.setString(1,task);p.setString(2,flow);try(ResultSet r=p.executeQuery()){need(r.next()&&a[7].equals(r.getString(1))&&!r.next());}}
   if(!a[4].equals("cleanup"))try(PreparedStatement p=c.prepareStatement("SELECT COUNT(*) FROM jnpf.act_ru_task WHERE PROC_INST_ID_=?")){p.setString(1,flow);try(ResultSet r=p.executeQuery()){need(r.next()&&r.getInt(1)==1);}}
   if(a[4].equals("arm")){
    need(!Files.exists(scope)&&existingTrigger(c)==null);pins=snapshot(c,flow,task);pins.setProperty("bodySHA256",digest(body));pins.setProperty("flowSHA256",digest(flow));pins.setProperty("taskSHA256",digest(task));try(OutputStream out=Files.newOutputStream(scope,StandardOpenOption.CREATE_NEW)){pins.store(out,"Exact owned synthetic fault scope; no credentials");}
    try(Statement s=c.createStatement()){s.execute("CREATE TRIGGER jnpf."+TRIGGER+" BEFORE INSERT ON jnpf.flow_task_operator_record FOR EACH ROW "+body);}need(digest(existingTrigger(c)).equals(pins.getProperty("bodySHA256")));
   }else{
    try(InputStream in=Files.newInputStream(scope)){pins.load(in);}need(pins.getProperty("flowSHA256").equals(digest(flow))&&pins.getProperty("taskSHA256").equals(digest(task))&&pins.getProperty("bodySHA256").equals(digest(body)));
    String found=existingTrigger(c);need(found==null&&a[4].equals("cleanup")||found!=null&&digest(found).equals(pins.getProperty("bodySHA256")));
    if(a[4].equals("verify-drop")){Properties after=snapshot(c,flow,task);for(String key:after.stringPropertyNames())need(after.getProperty(key).equals(pins.getProperty(key)));}
    if(found!=null)try(Statement s=c.createStatement()){s.execute("DROP TRIGGER jnpf."+TRIGGER);}need(existingTrigger(c)==null);
   }
   String result="{\"passed\":true,\"mode\":\""+a[4]+"\",\"scopedTables\":8,\"allScopedDataFingerprintsUnchanged\":"+a[4].equals("verify-drop")+",\"triggerRemoved\":"+!a[4].equals("arm")+",\"onlyOwnSyntheticProcess\":true,\"accountsOrSessionsRead\":false}";
   Files.writeString(root.resolve("native-history-sql-fault-"+a[4]+".json"),result+"\n");System.out.println(result);
  }catch(SQLException e){System.err.println("OWN_HISTORY_FAULT_SQL:"+e.getSQLState()+":"+e.getErrorCode());throw e;}
 }
}
