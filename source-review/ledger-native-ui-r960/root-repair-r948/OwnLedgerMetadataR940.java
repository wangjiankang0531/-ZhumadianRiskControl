import java.io.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.security.MessageDigest;import java.sql.*;import java.util.*;
/** Own G metadata only, using original menu/button/group mechanics; no user/role/business tables. */
public final class OwnLedgerMetadataR940 {
 static final Path ROOT=Path.of("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/ledger-ui-r941");
 static final Set<String> TABLES=new LinkedHashSet<>(List.of("base_system","base_module","base_module_button","base_authorize","base_dictionary_type","base_dictionary_data"));
 static String id(int n){return "a531"+String.format("%028x",n);}
 static void need(boolean v,String code){if(!v)throw new IllegalStateException(code);}
 static Map<String,Object> get(Connection c,String table,String key)throws Exception{
  need(TABLES.contains(table),"ONLY_OWN_METADATA_TABLES");try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+table+" WHERE f_id=?")){p.setString(1,key);try(ResultSet r=p.executeQuery()){
   need(r.next(),"EXACT_EXISTING_OWN_METADATA_DONOR_REQUIRED");Map<String,Object>v=new LinkedHashMap<>();for(int i=1;i<=r.getMetaData().getColumnCount();i++)v.put(r.getMetaData().getColumnName(i).toLowerCase(),r.getObject(i));need(!r.next(),"UNIQUE_OWN_DONOR");return v;
  }}
 }
 static Map<String,Object> copy(Map<String,Object>v,Object...pairs){Map<String,Object>r=new LinkedHashMap<>(v);for(int i=0;i<pairs.length;i+=2)r.put((String)pairs[i],pairs[i+1]);return r;}
 static boolean exact(Connection c,String table,Map<String,Object>v)throws Exception{
  try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+table+" WHERE f_id=?")){p.setObject(1,v.get("f_id"));try(ResultSet r=p.executeQuery()){
   if(!r.next())return false;for(var e:v.entrySet())need(Objects.equals(Objects.toString(e.getValue(),null),Objects.toString(r.getObject(e.getKey()),null)),"OWN_LEDGER_METADATA_ROW_DRIFT");need(!r.next(),"UNIQUE_OWN_ROW");return true;
  }}
 }
 static void insert(Connection c,String table,Map<String,Object>v)throws Exception{
  need(TABLES.contains(table)&&!table.equals("base_system"),"EXACT_NEW_METADATA_ONLY");
  try(PreparedStatement p=c.prepareStatement("INSERT INTO jnpf."+table+"("+String.join(",",v.keySet())+") VALUES("+String.join(",",Collections.nCopies(v.size(),"?"))+")")){int i=1;for(Object x:v.values())p.setObject(i++,x);need(p.executeUpdate()==1,"ONE_SYNTHETIC_METADATA_ROW");}
 }
 static String digest(Connection c,String table,Set<String>excluded)throws Exception{
  need(TABLES.contains(table),"METADATA_DIGEST_ONLY");MessageDigest d=MessageDigest.getInstance("SHA-256");
  try(Statement s=c.createStatement()){s.setQueryTimeout(15);try(ResultSet r=s.executeQuery("SELECT * FROM jnpf."+table+" ORDER BY f_id")){
   int count=0;while(r.next()){if(excluded.contains(r.getString("f_id")))continue;need(++count<20000,"BOUNDED_METADATA");for(int i=1;i<=r.getMetaData().getColumnCount();i++){
    String x=r.getString(i);byte[]b=x==null?new byte[0]:x.getBytes(StandardCharsets.UTF_8);d.update((byte)(x==null?0:1));d.update(java.nio.ByteBuffer.allocate(4).putInt(b.length).array());d.update(b);
   }}
  }}return HexFormat.of().formatHex(d.digest());
 }
 static void save(Path p,Properties props)throws Exception{
  Path temp=p.resolveSibling(p.getFileName()+".r940.tmp");need(!Files.exists(temp),"NO_FOREIGN_METADATA_TEMP");try(OutputStream out=Files.newOutputStream(temp,StandardOpenOption.CREATE_NEW)){props.store(out,"own synthetic menu/dictionary metadata; no raw rows or secret");}Files.move(temp,p,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
 }
 static String type(Connection c,String code)throws Exception{
  try(PreparedStatement p=c.prepareStatement("SELECT f_id,f_parent_id FROM jnpf.base_dictionary_type WHERE f_en_code=?")){p.setString(1,code);try(ResultSet r=p.executeQuery()){
   if(!r.next())return null;String value=r.getString(1);need(value.startsWith("a531")&&id(1000).equals(r.getString(2))&&!r.next(),"EXACT_OWN_EXISTING_DICTIONARY_TYPE");return value;
  }}
 }
 public static void main(String[]a)throws Exception{
  need(a.length==6&&Set.of("repair-root","readback").contains(a[4])&&Set.of("first-start","normal-restart").contains(a[5])&&a[4].equals(a[5].equals("first-start")?"repair-root":"readback"),"EXACT_ONE_OWN_ROOT_REPAIR_OR_READBACK_ARGUMENTS");boolean repair=a[4].equals("repair-root");int port=Integer.parseInt(a[0]);need(port>1024&&port<65536&&port!=3306,"OWN_DYNAMIC_PORT");need(a[1].matches("[0-9a-f-]{36}"),"OWN_DB_IDENTITY");
  Path data=Path.of(a[2]).toAbsolutePath().normalize();need(data.toString().replace('\\','/').equals("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data"),"ONLY_EXISTING_OWN_G");
  need(Path.of(a[3]).toAbsolutePath().normalize().equals(ROOT)&&Files.readString(ROOT.resolve("own-ledger-ui.marker")).equals("own-ledger-ui-r941\n"),"EXACT_UNISSUED_LEDGER_ATTEMPT");
  need(!Files.exists(Path.of("D:/Project/Zhumadian/_g/user-manual-protected.json")),"NEVER_USER_DELIVERED_FIXTURE_ONLY");
  Path journal=ROOT.resolve("ledger-metadata-journal.private.properties"),result=ROOT.resolve("metadata-"+a[4]+"-r948-"+a[5]+".private.properties");boolean prepare=a[4].equals("prepare");need(!Files.exists(result)&&(prepare?!Files.exists(journal):Files.isRegularFile(journal)),"NO_UNKNOWN_PREVIOUS_PREPARATION_OR_REPLAY");
  String secret=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(secret!=null&&secret.matches("[0-9a-f]{32}"),"OWN_STDIN_SECRET");
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=20000","root",secret)){
   secret=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){need(r.next()&&a[1].equals(r.getString(1))&&port==r.getInt(2)&&data.equals(Path.of(r.getString(3)).toAbsolutePath().normalize())&&"jnpf".equals(r.getString(4)),"LIVE_OWN_DB_MUST_MATCH");}
   Map<String,Object>system=get(c,"base_system",id(14)),parent=get(c,"base_module",id(600)),page=get(c,"base_module",id(603)),button=get(c,"base_module_button",id(801)),grant=get(c,"base_authorize",id(703)),bg=get(c,"base_authorize",id(901));
   need("safety".equals(system.get("f_en_code"))&&"Own safety workflow portal".equals(system.get("f_full_name"))&&"/emergencyResponse/taskSend".equals(page.get("f_path")),"ORIGINAL_SYNTHETIC_SAFETY_AND_TASK_DONORS");
   need(id(30).equals(grant.get("f_object_id"))&&"module".equals(grant.get("f_item_type"))&&"button".equals(bg.get("f_item_type")),"ORIGINAL_NORMAL_PERMISSION_GROUP_MECHANICS");
   for(int n:new int[]{1400,1401}){Map<String,Object>s=get(c,"base_authorize",id(n));need(id(14).equals(s.get("f_item_id"))&&"system".equals(s.get("f_item_type"))&&id(n==1400?30:31).equals(s.get("f_object_id")),"EXISTING_SAFETY_ACCESS_NOT_CREATED_BY_THIS_TEST");}
   Map<String,LinkedHashMap<String,Map<String,Object>>>wanted=new LinkedHashMap<>();for(String t:TABLES)wanted.put(t,new LinkedHashMap<>());
   Map<String,Object>root=copy(parent,"f_id",id(100100),"f_parent_id","-1","f_type",1,"f_system_id",id(14),"f_full_name","双重预防管理","f_en_code","OWN_LEDGER_R941_ROOT","f_path",repair?"/hiddenInvestigate":"/own-ledger-r941","f_url_address","","f_sort_code",100100);
   Map<String,Object>list=copy(page,"f_id",id(100101),"f_parent_id",id(100100),"f_system_id",id(14),"f_full_name","隐患台账","f_en_code","OWN_LEDGER_R941_LIST","f_path","/hiddenInvestigate/perilLedger","f_url_address","/hiddenInvestigate/perilLedger","f_sort_code",100101,"f_is_button_authorize",1);
   wanted.get("base_module").put(id(100100),root);wanted.get("base_module").put(id(100101),list);
   Map<String,Object>detail=copy(button,"f_id",id(100102),"f_module_id",id(100101),"f_full_name","台账详情","f_en_code","OWN_LEDGER_R941_DETAIL","f_path","/hiddenInvestigate/perilLedger/detail","f_url_address","/hiddenInvestigate/perilLedger/info/index","f_sort_code",1);wanted.get("base_module_button").put(id(100102),detail);
   int next=100110;for(int group:new int[]{30,31}){
    for(int module:new int[]{100100,100101}){Map<String,Object>r=copy(grant,"f_id",id(next++),"f_item_id",id(module),"f_object_id",id(group));wanted.get("base_authorize").put((String)r.get("f_id"),r);}
    Map<String,Object>r=copy(bg,"f_id",id(next++),"f_item_id",id(100102),"f_object_id",id(group));wanted.get("base_authorize").put((String)r.get("f_id"),r);
   }
   Map<String,Object>dictroot=get(c,"base_dictionary_type",id(1000)),dict=get(c,"base_dictionary_type",id(1001)),value=get(c,"base_dictionary_data",id(1002));need("safetycode".equals(dictroot.get("f_en_code")),"ORIGINAL_OWN_DICTIONARY_ROOT");
   String[]codes={"hiddenDangerStatusData","hiddenDangerTypeData","hazardLevelData","troubleshootTypeData"};int reused=0;
   for(int i=0;i<codes.length;i++){
    String existing=type(c,codes[i]);int key=100200+i*2;
    if(existing!=null&&!existing.equals(id(key))){reused++;continue;}
    Map<String,Object>t=copy(dict,"f_id",id(key),"f_parent_id",id(1000),"f_full_name","Own ledger "+codes[i],"f_en_code",codes[i],"f_is_tree",0,"f_sort_code",key);wanted.get("base_dictionary_type").put(id(key),t);
    Map<String,Object>v=copy(value,"f_id",id(key+1),"f_dictionary_type_id",id(key),"f_full_name",i==0?"待整改":"自有台账测试选项","f_en_code",i==0?"待整改":"OWN_LEDGER_R941_"+i,"f_sort_code",1);wanted.get("base_dictionary_data").put(id(key+1),v);
   }
   Properties state=new Properties();if(!prepare){try(InputStream in=Files.newInputStream(journal)){state.load(in);}need("committed-readback-verified".equals(state.getProperty("phase")),"NO_UNKNOWN_TRANSACTION_REPLAY");c.setReadOnly(!repair);}
   c.setAutoCommit(false);Map<String,String>before=new TreeMap<>();int expected=0;for(var table:wanted.entrySet()){
    before.put(table.getKey(),digest(c,table.getKey(),table.getValue().keySet()));for(var r:table.getValue().values()){boolean exists=exact(c,table.getKey(),r);need(prepare?!exists:exists,"EXACT_PREPARE_ABSENCE_OR_READBACK_ROW");expected++;}
   }
   if(prepare){state.setProperty("phase","sql-intent-recorded");state.setProperty("metadataRows",Integer.toString(expected));state.setProperty("reusedDictionaryTypes",Integer.toString(reused));for(var e:before.entrySet())state.setProperty("otherRowsSHA256."+e.getKey(),e.getValue());save(journal,state);}
   Path repairJournal=ROOT.resolve("ledger-root-placement-r948.private.properties");Properties repairState=new Properties();
   if(repair){need(!Files.exists(repairJournal),"NO_REPLAY_OF_ROOT_METADATA_REPAIR");for(var e:before.entrySet())need(e.getValue().equals(state.getProperty("otherRowsSHA256."+e.getKey())),"ORIGINAL_OTHER_METADATA_BEFORE_REPAIR");repairState.setProperty("phase","single-owned-root-path-update-intent");repairState.setProperty("rowId",id(100100));repairState.setProperty("beforePath","/hiddenInvestigate");repairState.setProperty("afterPath","/own-ledger-r941");save(repairJournal,repairState);}
   else{try(InputStream in=Files.newInputStream(repairJournal)){repairState.load(in);}need("committed-readback-verified".equals(repairState.getProperty("phase")),"EXACT_PRIOR_ROOT_REPAIR_COMMIT_REQUIRED");}
   try{
    if(repair){try(PreparedStatement patch=c.prepareStatement("UPDATE jnpf.base_module SET f_path=? WHERE f_id=? AND f_path=?")){patch.setString(1,"/own-ledger-r941");patch.setString(2,id(100100));patch.setString(3,"/hiddenInvestigate");need(patch.executeUpdate()==1,"ONLY_THE_ONE_OWN_ROOT_PATH_CHANGED");}wanted.get("base_module").get(id(100100)).put("f_path","/own-ledger-r941");}
    if(prepare)for(var table:wanted.entrySet())for(var r:table.getValue().values())insert(c,table.getKey(),r);
    for(var table:wanted.entrySet()){
     for(var r:table.getValue().values())need(exact(c,table.getKey(),r),"EXACT_NEW_METADATA_READBACK");
     need(digest(c,table.getKey(),table.getValue().keySet()).equals(state.getProperty("otherRowsSHA256."+table.getKey())),"ALL_OTHER_METADATA_REMAINS_EXACT");
    }
    c.commit();if(repair){repairState.setProperty("phase","committed-readback-verified");repairState.setProperty("onlyOneOwnMetadataPathChanged","true");save(repairJournal,repairState);}
   }catch(Exception e){c.rollback();throw e;}
   state.setProperty("phase","committed-readback-verified");state.setProperty("usersRolesAccountsBusinessRowsAndSchemaWritten","false");state.setProperty("persistentWritesIssued",Boolean.toString(repair));state.setProperty("verifiedMetadataRows",Integer.toString(expected));
   if(prepare)save(journal,state);save(result,state);System.out.println("OWN_LEDGER_METADATA_"+a[4].toUpperCase()+"_VERIFIED");
  }finally{secret=null;}
 }
}
