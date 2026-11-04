import java.io.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.sql.*;import java.util.*;import java.security.MessageDigest;
/** Own synthetic G only. Add absent home-system/navigation metadata; never alter
 * users, roles, existing grants, business rows, schema, signing or authentication.
 */
public final class OwnHomeNavigationReadbackR931 {
 static String id(int n){return "a531"+String.format("%028x",n);}
 static void need(boolean b,String code){if(!b)throw new IllegalStateException(code);}
 static final Set<String> TABLES=Set.of("base_system","base_module","base_authorize");
 static Map<String,Object> get(Connection c,String table,String key)throws Exception{
  need(TABLES.contains(table),"OWN_THREE_METADATA_TABLES_ONLY");
  try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+table+" WHERE f_id=?")){p.setString(1,key);try(ResultSet r=p.executeQuery()){need(r.next(),"EXISTING_OWN_METADATA_DONOR_REQUIRED");Map<String,Object>v=new LinkedHashMap<>();ResultSetMetaData m=r.getMetaData();for(int i=1;i<=m.getColumnCount();i++)v.put(m.getColumnName(i).toLowerCase(),r.getObject(i));need(!r.next(),"UNIQUE_OWN_DONOR_REQUIRED");return v;}}
 }
 static Map<String,Object> copy(Map<String,Object>v,Object...pairs){Map<String,Object>r=new LinkedHashMap<>(v);for(int i=0;i<pairs.length;i+=2)r.put((String)pairs[i],pairs[i+1]);return r;}
 static String digest(Connection c,String table,Set<String>excluded)throws Exception{
  need(TABLES.contains(table),"OWN_METADATA_DIGEST_ONLY");MessageDigest d=MessageDigest.getInstance("SHA-256");
  try(Statement s=c.createStatement()){s.setQueryTimeout(10);try(ResultSet r=s.executeQuery("SELECT * FROM jnpf."+table+" ORDER BY f_id")){
   int count=0;while(r.next()){if(excluded.contains(r.getString("f_id")))continue;need(++count<20000,"BOUNDED_OWN_METADATA");
    for(int i=1;i<=r.getMetaData().getColumnCount();i++){String x=r.getString(i);byte[] b=x==null?new byte[0]:x.getBytes(StandardCharsets.UTF_8);d.update((byte)(x==null?0:1));d.update(java.nio.ByteBuffer.allocate(4).putInt(b.length).array());d.update(b);}
   }
  }}return HexFormat.of().formatHex(d.digest());
 }
 static boolean existsExact(Connection c,String table,Map<String,Object>v)throws Exception{
  need(TABLES.contains(table),"OWN_METADATA_ONLY");
  try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+table+" WHERE f_id=?")){p.setObject(1,v.get("f_id"));try(ResultSet r=p.executeQuery()){
   if(!r.next())return false;for(var e:v.entrySet())need(Objects.equals(Objects.toString(e.getValue(),null),Objects.toString(r.getObject(e.getKey()),null)),"OWN_EXISTING_ROW_DRIFT_REFUSE");need(!r.next(),"UNIQUE_METADATA_ROW");return true;
  }}
 }
 static void save(Path target,Properties p)throws Exception{
  Path tmp=target.resolveSibling(target.getFileName()+".own.tmp");need(!Files.exists(tmp),"NO_FOREIGN_JOURNAL_TEMP");try(OutputStream out=Files.newOutputStream(tmp,StandardOpenOption.CREATE_NEW)){p.store(out,"owned synthetic home fixture; no raw row or credential");}
  Files.move(tmp,target,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
 }
 public static void main(String[] a)throws Exception{
  need(a.length==5,"EXACT_OWN_HOME_FIXTURE_ARGUMENTS");int port=Integer.parseInt(a[0]);need(port>1024&&port<65536&&port!=3306,"OWN_DYNAMIC_DATABASE_PORT");
  need(a[1].matches("[0-9a-f-]{36}"),"OWN_DATABASE_IDENTITY");Path data=Path.of(a[2]).toAbsolutePath().normalize();need(data.toString().replace('\\','/').equals("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data"),"ONLY_EXISTING_OWN_G");
  Path journal=Path.of(a[3]).toAbsolutePath().normalize();need(journal.toString().replace('\\','/').equals("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/home-transfer-r910/home-navigation-journal.private.properties"),"EXACT_NEW_HOME_FIXTURE_JOURNAL");
  Path out=Path.of(a[4]).toAbsolutePath().normalize();need(out.toString().replace('\\','/').equals("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/exact-supervision-r931/home-navigation-readback.private.properties")&&!Files.exists(out)&&Files.isRegularFile(journal),"UNISSUED_OWN_READBACK_ONLY");need(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(journal))).equals("0ef4df36821e5b6eb94e2e7df005956f9629ad783ab1113a1f4be1daca8eb48d"),"PINNED_PREPARED_HOME_JOURNAL_REQUIRED");
  need(Files.readString(Path.of("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609/own-normal-manager-test.marker")).equals("own-original-manager-full-lifecycle-r609\n"),"OWN_FIXTURE_MARKER");
  String secret=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(secret!=null&&secret.matches("[0-9a-f]{32}"),"OWN_STDIN_SECRET_ONLY");
  Properties result=new Properties();result.setProperty("accountsRolesBusinessTablesAndSchemaWritten","false");
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=15000","root",secret)){
   secret=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){need(r.next()&&a[1].equals(r.getString(1))&&port==r.getInt(2)&&data.equals(Path.of(r.getString(3)).toAbsolutePath().normalize())&&"jnpf".equals(r.getString(4)),"EXACT_LIVE_OWN_DATABASE");}
   Map<String,Object>system=get(c,"base_system",id(13)),parent=get(c,"base_module",id(600)),page=get(c,"base_module",id(603)),grant=get(c,"base_authorize",id(703)),systemGrant=get(c,"base_authorize",id(650));
   need("emergency".equals(system.get("f_en_code"))&&id(13).equals(page.get("f_system_id"))&&"/emergencyResponse/taskSend".equals(page.get("f_path")),"EXACT_EXISTING_SYNTHETIC_SYSTEM_AND_PAGE");
   need(id(30).equals(grant.get("f_object_id"))&&"module".equals(grant.get("f_item_type"))&&"system".equals(systemGrant.get("f_item_type")),"ORIGINAL_OWN_NORMAL_PERMISSION_GROUP_TEMPLATE");
   LinkedHashMap<String,Map<String,Map<String,Object>>> rows=new LinkedHashMap<>();for(String t:List.of("base_system","base_module","base_authorize"))rows.put(t,new LinkedHashMap<>());
   Map<String,Object>home=copy(system,"f_id",id(99000),"f_en_code","home","f_full_name","Own isolated navigation home","f_is_main",0,"f_sort_code",99000);rows.get("base_system").put(id(99000),home);
   for(int i=0;i<2;i++){int key=99001+i;rows.get("base_module").put(id(key),copy(parent,"f_id",id(key),"f_parent_id","-1","f_full_name",i==0?"系统导航":"快捷链接","f_en_code",i==0?"xtdh":"kjlj","f_system_id",id(99000),"f_path",i==0?"/own-home-system":"/own-home-shortcuts","f_url_address","","f_sort_code",i+1));}
   String[][] entries={{"安全风险智能管控平台","/zhumadian/workplace"},{"敏捷应急管理","/zhumadian/emergency/home/index"},{"双重预防","/zhumadian/hiddenInvestigate/riskAnalysisUnit"},{"智能巡检","/zhumadian/intelligentInspection/inspectionPlan"},{"特殊作业","/zhumadian/specialWork/workPermit"},{"重大危险源","/zhumadian/majorHazard/hazardSource"},{"应急处置","/zhumadian/emergency/emergencyResponse/response"},{"我的待办","/zhumadian/emergency/workflow/flowTodo"}};
   for(int i=0;i<entries.length;i++){int key=99010+i;rows.get("base_module").put(id(key),copy(page,"f_id",id(key),"f_parent_id",id(i<2?99001:99002),"f_system_id",id(99000),"f_full_name",entries[i][0],"f_en_code","OWN_HOME_LINK_"+i,"f_path",entries[i][1],"f_url_address",entries[i][1],"f_sort_code",i+1));}
   int next=99100;for(int group:new int[]{30,31}){
    Map<String,Object>sys=copy(systemGrant,"f_id",id(next++),"f_item_id",id(99000),"f_object_id",id(group));rows.get("base_authorize").put((String)sys.get("f_id"),sys);
    for(String key:rows.get("base_module").keySet()){Map<String,Object>v=copy(grant,"f_id",id(next++),"f_item_id",key,"f_object_id",id(group));rows.get("base_authorize").put((String)v.get("f_id"),v);}
   }
   c.setReadOnly(true);c.setAutoCommit(false);
   int verified=0;
   try(PreparedStatement p=c.prepareStatement("SELECT f_id FROM jnpf.base_system WHERE f_en_code='home'");ResultSet r=p.executeQuery()){need(r.next()&&id(99000).equals(r.getString(1))&&!r.next(),"EXACT_PREVIOUS_HOME_SYSTEM");}
   for(var table:rows.entrySet())for(var row:table.getValue().values()){need(existsExact(c,table.getKey(),row),"PREVIOUS_HOME_METADATA_CHANGED_NO_RESEED");verified++;}
   need(verified==33,"EXACT_PREVIOUS_33_ROWS");c.commit();
   result.setProperty("persistentWritesIssued","false");result.setProperty("exactPreviouslyPreparedMetadataRowsMatched","true");result.setProperty("originalDatabaseIdentityMatched","true");result.setProperty("verifiedMetadataRows","33");result.setProperty("phase","readback-verified");save(out,result);
   System.out.println("PREVIOUS_OWN_HOME_METADATA_READ_ONLY_MATCHED");
  }finally{secret=null;}
 }
}
