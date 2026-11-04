import java.security.*;
import java.io.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.sql.*;import java.util.*;
/** Exact owned event/task/engine/form readback. No data mutation or raw row dump. */
public final class OwnManagerBusinessReadbackR783{
 static final Path APP=Path.of("D:/Project/Zhumadian/_g/Application"),ROOT=Path.of("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/feedback-r880");
 static final String EVENT="a5320000000000000000000000000006",A="a5310000000000000000000000000064",B="a5310000000000000000000000000065";
 static void need(boolean x,String code){if(!x)throw new IllegalStateException(code);}
 static String col(Connection c,String schema,String table,String logical)throws Exception{
  List<String> names=new ArrayList<>();try(ResultSet r=c.getMetaData().getColumns(schema,null,table,null)){while(r.next()){String n=r.getString("COLUMN_NAME");if(n.replace("_","").equalsIgnoreCase(logical)){need(n.matches("[A-Za-z_][A-Za-z0-9_]*"),"ORIGINAL_IDENTIFIER_REQUIRED");names.add(n);}}}need(names.size()==1,"EXACT_ORIGINAL_COLUMN_REQUIRED:"+logical);return "`"+names.get(0)+"`";
 }
 static long count(Connection c,String sql,String...v)throws Exception{try(PreparedStatement p=c.prepareStatement(sql)){p.setQueryTimeout(10);for(int i=0;i<v.length;i++)p.setString(i+1,v[i]);try(ResultSet r=p.executeQuery()){need(r.next(),"COUNT_REQUIRED");long n=r.getLong(1);need(!r.next(),"SINGLE_COUNT_REQUIRED");return n;}}}
 static String safe(String s){need(s!=null&&s.matches("[A-Za-z0-9_-]{1,128}"),"BOUNDED_GENERATED_OWN_ID_REQUIRED");return s;}
 public static void main(String[]a)throws Exception{
  need(a.length==5&&Set.of("inspect","submitted","wrong","approved","restarted","pending-resume","feedback").contains(a[4]),"EXACT_OWN_BUSINESS_STAGE_REQUIRED");int port=Integer.parseInt(a[0]);need(port>1024&&port<65536&&!Set.of(8767,18891,18892).contains(port),"ONLY_OWN_DATABASE_PORT");UUID.fromString(a[1]);
  Path data=Path.of(a[2]).toRealPath();need(data.equals(APP.resolve("UserData/OriginalServer/database/data").toRealPath())&&ROOT.toRealPath().equals(ROOT)&&Files.readString(ROOT.getParent().resolve("own-normal-manager-test.marker")).equals("own-original-manager-full-lifecycle-r609\n")&&!Files.exists(APP.getParent().resolve("user-manual-protected.json")),"EXACT_OWN_MANAGER_DATA_SCOPE_REQUIRED");
  Properties input=new Properties();try(InputStream in=Files.newInputStream(ROOT.resolve("flight.private.properties"))){input.load(in);}need(input.size()==4&&input.getProperty("nonce","").matches("[0-9a-f]{32}")&&input.getProperty("taskName").equals("OWN_MANAGER_"+input.getProperty("nonce"))&&input.getProperty("formTable","").matches("mt[0-9]+")&&input.getProperty("approval").equals("OWN_MANAGER_APPROVAL_"+input.getProperty("nonce")),"FIXED_OWN_BUSINESS_INPUT_REQUIRED");
  Path output=Path.of(a[3]).toAbsolutePath().normalize();need(output.equals(ROOT.resolve("snapshot-r889-"+a[4]+".properties"))&&!Files.exists(output),"EXACT_NEW_OWN_SNAPSHOT_REQUIRED");
  String secret=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(secret!=null&&secret.matches("[0-9a-f]{32}"),"ONLY_OWN_STDIN_SECRET");Properties auth=new Properties();auth.setProperty("user","root");auth.setProperty("password",secret);secret=null;auth.setProperty("useSSL","false");auth.setProperty("allowPublicKeyRetrieval","true");auth.setProperty("connectTimeout","5000");auth.setProperty("socketTimeout","15000");auth.setProperty("allowMultiQueries","false");auth.setProperty("autoReconnect","false");Properties result=new Properties();
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf",auth)){
   c.setReadOnly(true);c.setTransactionIsolation(Connection.TRANSACTION_REPEATABLE_READ);c.setAutoCommit(false);
   try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){need(r.next()&&a[1].equals(r.getString(1))&&port==r.getInt(2)&&data.equals(Path.of(r.getString(3)).toRealPath())&&"jnpf".equals(r.getString(4))&&!r.next(),"EXACT_LIVE_OWN_DATABASE_REQUIRED");}
   String taskName=col(c,"tj_endanger","event_task","taskname"),taskId=col(c,"tj_endanger","event_task","id"),flow=col(c,"tj_endanger","event_task","flowid"),status=col(c,"tj_endanger","event_task","taskstatus"),info=col(c,"tj_endanger","event_task","infoid");
   if(a[4].equals("inspect")){
    need(count(c,"SELECT COUNT(*) FROM tj_endanger.event_info WHERE id=? AND event_number=? AND event_name=?",EVENT,"OWN-NORMAL-WORKFLOW-EVENT","Own workflow event")==1,"EXACT_EXISTING_SYNTHETIC_EVENT_REQUIRED");
    String research;try(PreparedStatement p=c.prepareStatement("SELECT "+col(c,"tj_endanger","event_info","researchstatus")+" FROM tj_endanger.event_info WHERE id=?")){p.setString(1,EVENT);p.setQueryTimeout(10);try(ResultSet r=p.executeQuery()){need(r.next(),"EXACT_OWN_RESEARCH_EVENT_REQUIRED");research=r.getString(1);need(!r.next()&&Set.of("0","1").contains(research),"NORMAL_OWN_EVENT_RESEARCH_STATE_REQUIRED");}}
    result.setProperty("existingOwnedEventConfirmed",Boolean.toString("1".equals(research)));
    need(count(c,"SELECT COUNT(*) FROM tj_endanger.event_task WHERE "+taskName+"=?",input.getProperty("taskName"))==0,"OWN_TASK_NAME_MUST_BE_ABSENT");result.setProperty("existingOwnedEventMatched","true");result.setProperty("newTaskAbsent","true");
   }else{
    String id,instance,businessStatus;
    try(PreparedStatement p=c.prepareStatement("SELECT "+taskId+","+flow+","+status+","+info+" FROM tj_endanger.event_task WHERE "+taskName+"=?")){
     p.setQueryTimeout(10);p.setString(1,input.getProperty("taskName"));try(ResultSet r=p.executeQuery()){need(r.next()&&EVENT.equals(r.getString(4)),"EXACT_ONE_OWN_TASK_AND_EVENT_REQUIRED");id=safe(r.getString(1));instance=safe(r.getString(2));businessStatus=r.getString(3);need(!r.next(),"OWN_TASK_MUST_BE_UNIQUE");}
    }
    if(Set.of("feedback","approved","restarted").contains(a[4])){
     try(PreparedStatement p=c.prepareStatement("SELECT "+col(c,"tj_endanger","event_task","feedbackinfo")+","+col(c,"tj_endanger","event_task","evaluationsum")+","+col(c,"tj_endanger","event_task","disposetime")+" FROM tj_endanger.event_task WHERE "+taskId+"=?")){
      p.setQueryTimeout(10);p.setString(1,id);try(ResultSet r=p.executeQuery()){
       need(r.next()&&("OWN_FEEDBACK_"+input.getProperty("nonce")).equals(r.getString(1))&&("OWN_EVALUATION_"+input.getProperty("nonce")).equals(r.getString(2))&&r.getTimestamp(3)!=null&&r.getTimestamp(3).toLocalDateTime().equals(java.time.LocalDateTime.of(2026,11,4,17,30))&&!r.next(),"EXACT_ORIGINAL_FEEDBACK_EVALUATION_AND_TIME_REQUIRED");
      }
     }result.setProperty("originalFeedbackEvaluationTimeMatched","true");
    }
    boolean ended;try(PreparedStatement p=c.prepareStatement("SELECT END_TIME_ FROM act_hi_procinst WHERE ID_=?")){p.setString(1,instance);p.setQueryTimeout(10);try(ResultSet r=p.executeQuery()){need(r.next(),"EXACT_ORIGINAL_PROCESS_HISTORY_REQUIRED");ended=r.getTimestamp(1)!=null;need(!r.next(),"ONE_ORIGINAL_PROCESS_HISTORY_REQUIRED");}}
    long active=count(c,"SELECT COUNT(*) FROM act_ru_task WHERE PROC_INST_ID_=?",instance);
    result.setProperty("taskId",id);result.setProperty("instanceId",instance);result.setProperty("taskStatus",businessStatus);result.setProperty("originalProcessEnded",Boolean.toString(ended));result.setProperty("activeEngineTasks",Long.toString(active));
    if(Set.of("submitted","wrong","pending-resume","feedback").contains(a[4])){
     need((a[4].equals("feedback")?"1":"2").equals(businessStatus)&&!ended&&active==1,"ONE_REAL_PENDING_ORIGINAL_PROCESS_REQUIRED");
     String fid=col(c,"jnpf","flow_task_operator","fid"),node=col(c,"jnpf","flow_task_operator","ftasknodeid"),handle=col(c,"jnpf","flow_task_operator","fhandleid"),task=col(c,"jnpf","flow_task_operator","ftaskid");
     try(PreparedStatement p=c.prepareStatement("SELECT "+fid+","+node+" FROM flow_task_operator WHERE "+task+"=? AND "+handle+"=?")){p.setQueryTimeout(10);p.setString(1,instance);p.setString(2,B);try(ResultSet r=p.executeQuery()){need(r.next(),"ACTUAL_NORMAL_MANAGER_OPERATOR_REQUIRED");result.setProperty("operatorId",safe(r.getString(1)));result.setProperty("nodeId",safe(r.getString(2)));need(!r.next(),"ONE_ORIGINAL_MANAGER_OPERATOR_REQUIRED");}}
     try(PreparedStatement p=c.prepareStatement("SELECT ID_ FROM act_ru_task WHERE PROC_INST_ID_=?")){p.setString(1,instance);try(ResultSet r=p.executeQuery()){need(r.next(),"ONE_ENGINE_TASK_REQUIRED");result.setProperty("engineTaskId",safe(r.getString(1)));need(!r.next(),"EXACT_ENGINE_TASK_REQUIRED");}}
     result.setProperty("actualManagerBAssignmentMatched","true");
    }else{
     need("1".equals(businessStatus)&&ended&&active==0,"APPROVAL_AND_ORIGINAL_BUSINESS_CALLBACK_STATE_REQUIRED");
     String table=input.getProperty("formTable");
     Properties submitted=new Properties();try(InputStream source=Files.newInputStream(ROOT.resolve("snapshot-r889-submitted.properties"))){submitted.load(source);}
     String formKey;try(PreparedStatement p=c.prepareStatement("SELECT FORM_KEY_,END_TIME_ FROM act_hi_taskinst WHERE ID_=? AND PROC_INST_ID_=?")){p.setString(1,submitted.getProperty("engineTaskId"));p.setString(2,instance);p.setQueryTimeout(10);try(ResultSet r=p.executeQuery()){need(r.next()&&r.getTimestamp(2)!=null,"EXACT_COMPLETED_OWN_MANAGER_TASK_REQUIRED");formKey=r.getString(1);need(!r.next(),"ONE_HISTORIC_OWN_MANAGER_TASK_REQUIRED");}}
     Properties models=new Properties();try(InputStream source=Files.newInputStream(ROOT.getParent().resolve("model-presence-input.properties"))){models.load(source);}
     String[] parts=formKey.split("@document@",-1);need(parts.length==2&&models.getProperty("a.form").equals(parts[0])&&!parts[1].isEmpty()&&parts[1].length()<256,"ORIGINAL_FORM_DOCUMENT_KEY_REQUIRED");String document=parts[1];
     String where=" FROM `"+table+"` WHERE `f_id`=?";
     long rows=count(c,"SELECT COUNT(*)"+where,document),taskValue=count(c,"SELECT COUNT(*)"+where+" AND `inputField101`=?",document,id),instanceValue=count(c,"SELECT COUNT(*)"+where+" AND `inputField101`=?",document,instance),attemptedValue=count(c,"SELECT COUNT(*)"+where+" AND `inputField101`=?",document,input.getProperty("approval"));
     Properties baseline=new Properties();try(InputStream source=Files.newInputStream(ROOT.resolve("original-field-baseline-r880.private.properties"))){baseline.load(source);}
     need("xnby.original-manager-field-baseline.r806.v1".equals(baseline.getProperty("schema"))&&baseline.getProperty("databaseFieldCanonicalSHA256","").matches("[0-9a-f]{64}"),"EXACT_NATIVE_READONLY_BASELINE_REQUIRED");
     String actualHash;try(PreparedStatement p=c.prepareStatement("SELECT inputField101 FROM `"+table+"` WHERE f_id=?")){p.setString(1,document);p.setQueryTimeout(10);try(ResultSet r=p.executeQuery()){need(r.next(),"EXACT_ORIGINAL_FORM_DOCUMENT_ROW_REQUIRED");String value=r.getString(1),canonical=value==null?"null":"string:"+value;actualHash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(canonical.getBytes(StandardCharsets.UTF_8)));need(!r.next(),"ONE_ORIGINAL_DOCUMENT_ROW_REQUIRED");}}
     boolean nativeValueMatched=actualHash.equals(baseline.getProperty("databaseFieldCanonicalSHA256"));
     result.setProperty("nativeReadonlyValueSHA256Matched",Boolean.toString(nativeValueMatched));result.setProperty("originalNativeFieldType",baseline.getProperty("nativeFieldType"));
     String recordTask=col(c,"jnpf","flow_task_operator_record","ftaskid"),recordActor=col(c,"jnpf","flow_task_operator_record","fhandleid"),recordOpinion=col(c,"jnpf","flow_task_operator_record","fhandleopinion");
     long opinions=count(c,"SELECT COUNT(*) FROM flow_task_operator_record WHERE "+recordTask+"=? AND "+recordActor+"=? AND "+recordOpinion+"=?",instance,B,input.getProperty("approval"));
     result.setProperty("ownFormRowsByTaskOrInstance",Long.toString(rows));result.setProperty("ownReadOnlyFormTaskValueCount",Long.toString(taskValue));result.setProperty("ownReadOnlyFormInstanceValueCount",Long.toString(instanceValue));result.setProperty("attemptedReadOnlyChangeCount",Long.toString(attemptedValue));result.setProperty("ownManagerOpinionCount",Long.toString(opinions));
     result.setProperty("originalReadOnlyFormValuePreserved",Boolean.toString(rows==1&&nativeValueMatched&&attemptedValue==0));result.setProperty("originalManagerOpinionPersisted",Boolean.toString(opinions==1));
    }
   }
   c.rollback();need(c.isReadOnly(),"READ_ONLY_TRANSACTION_RETAINED");
  }finally{auth.remove("password");}
  result.setProperty("actualDatabaseIdentityMatched","true");result.setProperty("persistentWritesIssued","false");try(OutputStream out=Files.newOutputStream(output,StandardOpenOption.CREATE_NEW)){result.store(out,"Only own manager business identity and state");}System.out.println("OWN_MANAGER_BUSINESS_READBACK_MATCHED");
 }
}
