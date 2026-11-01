package xnby.replica;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.sql.*;import java.util.*;import com.fasterxml.jackson.databind.ObjectMapper;
/** Closed synthetic workflow data on the exact fresh server only. No original rows, accounts or sessions. */
public final class OriginalPublishedWorkflowSeed {
 static void need(boolean value,String code){if(!value)throw new IllegalStateException(code);}
 static String id(int value){return String.format(Locale.ROOT,"a531%028x",value);}
 static void insert(Connection c,String table,Map<String,Object> values)throws Exception{
  need(Set.of("base_data_interface","event_info").contains(table),"CLOSED_WORKFLOW_SEED_TABLE");Set<String> columnsPresent=new HashSet<>();try(var metadata=c.getMetaData().getColumns(c.getCatalog(),null,table,null)){while(metadata.next())columnsPresent.add(metadata.getString("COLUMN_NAME").toLowerCase(Locale.ROOT));}need(columnsPresent.containsAll(values.keySet()),"SEED_FIELDS_MUST_MATCH_ORIGINAL_PHYSICAL_COLUMNS");String columns=String.join(",",values.keySet().stream().map(k->"`"+k+"`").toList());String marks=String.join(",",Collections.nCopies(values.size(),"?"));try(var s=c.prepareStatement("INSERT INTO `"+table+"` ("+columns+") VALUES("+marks+")")){int i=1;for(Object value:values.values())s.setObject(i++,value);need(s.executeUpdate()==1,"ONE_OWN_WORKFLOW_SEED_ROW");}
 }
 public static void main(String[] a)throws Exception{
  need(a.length==4,"OWN_WORKFLOW_DATA_ARGS");Path root=Path.of(a[0]).toRealPath();need(root.getFileName().toString().matches("full-business-main-r[1-9][0-9]*"),"OWN_WORKFLOW_DATA_ROOT");int port=Integer.parseInt(a[1]);String uuid=a[2],mode=a[3];need(mode.equals("seed")||mode.equals("cleanup"),"CLOSED_WORKFLOW_DATA_MODE");byte[] raw=System.in.readNBytes(4097);need(raw.length==32,"SYNTHETIC_SECRET_STDIN");Properties props=new Properties();props.putAll(Map.of("user","xnby_whole_main","password",new String(raw,StandardCharsets.US_ASCII),"useSSL","false","allowPublicKeyRetrieval","true","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000"));Arrays.fill(raw,(byte)0);var mapper=new ObjectMapper();var definition=mapper.readTree(Files.readString(root.resolve("own-workflow-definition.json")));var guard=new OriginalSocketProcessBoundary(root,Set.of(port),false);System.setSecurityManager(guard);
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf",props)){
   try(var s=c.createStatement();var r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){need(r.next()&&uuid.equals(r.getString(1))&&port==r.getInt(2)&&Path.of(r.getString(3)).toRealPath().equals(root.resolve("data").toRealPath())&&"jnpf".equals(r.getString(4)),"EXACT_OWN_WORKFLOW_SERVER_IDENTITY");}
   if(mode.equals("cleanup")){
    var ownership=mapper.readTree(Files.readString(root.resolve("own-form-ownership.json")));
    try(var s=c.createStatement();var rows=s.executeQuery("SHOW CREATE TABLE jnpf.own_approval_form")){need(rows.next()&&ownership.path("ddl").asText().equals(rows.getString(2)),"EXACT_OWN_FORM_MODEL_BEFORE_CLEANUP");}
    try(var s=c.createStatement();var rows=s.executeQuery("SELECT COUNT(*) FROM jnpf.own_approval_form")){need(rows.next()&&rows.getInt(1)<=10,"BOUNDED_OWN_FORM_ROWS_BEFORE_CLEANUP");}
    try(var s=c.createStatement()){s.execute("DROP TABLE jnpf.own_approval_form");}
    Files.writeString(root.resolve("workflow-own-form-cleanup.json"),mapper.writeValueAsString(Map.of("onlyOwnScratchFormTableDropped",true,"original398ModelsOrDataChanged",false)));return;
   }
   if(mode.equals("seed")){
    try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='jnpf' AND table_name='own_approval_form'")){need(r.next()&&r.getInt(1)==0,"NEW_OWN_FORM_TABLE_REQUIRED");}
    try(var s=c.createStatement()){s.execute("CREATE TABLE own_approval_form (f_id VARCHAR(128) NOT NULL PRIMARY KEY, f_flow_id VARCHAR(128), f_flow_task_id VARCHAR(128), f_version INT DEFAULT 0, approval_note VARCHAR(512)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4");}
    try(var s=c.createStatement();var rows=s.executeQuery("SHOW CREATE TABLE jnpf.own_approval_form")){need(rows.next(),"OWN_FORM_MODEL_REQUIRED");Files.writeString(root.resolve("own-form-ownership.json"),mapper.writeValueAsString(Map.of("ddl",rows.getString(2),"onlySyntheticScratchForm",true)));}
    Map<String,Object> api=new LinkedHashMap<>();api.put("f_id",definition.path("interfaceId").asText());api.put("f_full_name","Own original workflow callback");api.put("f_en_code","OWN_NORMAL_WORKFLOW_CALLBACK");api.put("f_type",3);api.put("f_has_page",0);api.put("f_is_postposition",0);api.put("f_parameter_json","[]");api.put("f_data_count_json","");api.put("f_data_echo_json","");api.put("f_field_json","[]");api.put("f_data_exception_json","");api.put("f_data_js_json","");api.put("f_data_config_json",definition.path("interfaceConfiguration").toString());api.put("f_enabled_mark",1);api.put("f_delete_mark",0);api.put("f_creator_user_id",id(100));insert(c,"base_data_interface",api);
    c.setCatalog("tj_endanger");insert(c,"event_info",new LinkedHashMap<>(Map.of("id",definition.path("eventId").asText(),"event_number","OWN-NORMAL-WORKFLOW-EVENT","event_name","Own workflow event","create_dept",id(1),"deleted","0")));c.setCatalog("jnpf");
    Files.writeString(root.resolve("workflow-data-seed-result.json"),mapper.writeValueAsString(Map.of("freshOwnFormTableCreated",true,"syntheticCallbackDefinitions",1,"syntheticEvents",1,"realRowsOrAccountsImported",false,"tokensOrSessionsCreated",false)));
   }else{
    c.setReadOnly(true);var out=new LinkedHashMap<String,Object>();
    for(String table:List.of("flow_template","flow_template_json","flow_form_relation","flow_task","flow_task_operator","flow_task_operator_record","act_ru_task","act_hi_procinst","own_approval_form"))out.put(table,rows(c,table));c.setCatalog("tj_endanger");for(String table:List.of("event_task","xnby_task_dispatch","xnby_event_delivery"))out.put(table,rows(c,table));Files.writeString(root.resolve("workflow-"+mode+".json"),mapper.writeValueAsString(out));
   }
  }
 }
 static List<Map<String,String>> rows(Connection c,String table)throws Exception{
  var out=new ArrayList<Map<String,String>>();try(var s=c.createStatement();var r=s.executeQuery("SELECT * FROM `"+table+"` LIMIT 10")){while(r.next()){var row=new LinkedHashMap<String,String>();for(int i=1;i<=r.getMetaData().getColumnCount();i++){String name=r.getMetaData().getColumnName(i).toLowerCase(Locale.ROOT).replace("_","");if(Set.of("fflowtemplatejson","fnodeproperties","fpropertyjson","fdatajson","content","taskcontent").contains(name))continue;row.put(name,r.getString(i));}out.add(row);}}return out;
 }
}
