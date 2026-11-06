import java.io.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.nio.*;import java.sql.*;import java.util.*;import java.security.MessageDigest;
/** Only the never-user-delivered _g fixture. Twelve absent menu/button/grant/
 * dictionary rows for existing synthetic E; no user, existing grant or business write. */
public final class OwnHazardFormMetadataR1214 {
 static final Path ROOT=Path.of("D:/Project/Zhumadian/work/hazard-transaction-probe-r1214");
 static final List<String>TABLES=List.of("base_role","base_permission_group","base_user","base_user_relation","base_module","base_authorize","base_module_button","base_dictionary_type","base_dictionary_data");
 static final Set<String>NEW=new HashSet<>();static{for(int n:new int[]{120100,120101,120102,120103,120110,120111,120112,120113,120120,120121,120122,120123})NEW.add(id(n));}
 static void need(boolean b,String s){if(!b)throw new IllegalStateException(s);}
 static String id(int n){return "a531"+String.format("%028x",n);}
 static Map<String,Object> get(Connection c,String t,int n)throws Exception{
  need(TABLES.contains(t),"CLOSED_METADATA_TABLES");try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+t+" WHERE f_id=?")){p.setString(1,id(n));try(ResultSet r=p.executeQuery()){need(r.next(),"OWN_METADATA_DONOR_REQUIRED");Map<String,Object>v=new LinkedHashMap<>();for(int i=1;i<=r.getMetaData().getColumnCount();i++)v.put(r.getMetaData().getColumnName(i).toLowerCase(),r.getObject(i));need(!r.next(),"UNIQUE_DONOR");return v;}}
 }
 static Map<String,Object> copy(Map<String,Object>v,Object...pairs){return OwnHazardStatisticsMenuFixtureR1172.copy(v,pairs);}
 static void part(MessageDigest d,String s){OwnHazardStatisticsMenuFixtureR1172.part(d,s);}
 static String digest(Connection c)throws Exception{
  Set<String>identity=Set.of("f_id","f_account","f_real_name","f_password","f_secretkey","f_is_administrator","f_role_id","f_system_id","f_app_system_id","f_manager_id","f_organize_id","f_enabled_mark","f_group_id","f_position_id");
  MessageDigest d=MessageDigest.getInstance("SHA-256");for(String t:TABLES){part(d,t);try(Statement s=c.createStatement()){s.setQueryTimeout(15);try(ResultSet r=s.executeQuery("SELECT * FROM jnpf."+t+" ORDER BY f_id")){int count=0;while(r.next()){need(++count<20000,"BOUNDED_OWN_METADATA");if(NEW.contains(r.getString("f_id")))continue;for(int i=1;i<=r.getMetaData().getColumnCount();i++)if(!t.equals("base_user")||identity.contains(r.getMetaData().getColumnName(i).toLowerCase()))part(d,r.getString(i));}}}}
  return HexFormat.of().formatHex(d.digest());
 }
 static void store(Path p,Properties v)throws Exception{OwnHazardStatisticsMenuFixtureR1172.store(p,v);}
 static void zero(Connection c,String sql,String...args)throws Exception{try(PreparedStatement p=c.prepareStatement(sql)){p.setQueryTimeout(15);for(int i=0;i<args.length;i++)p.setString(i+1,args[i]);try(ResultSet r=p.executeQuery()){need(r.next()&&r.getInt(1)==0,"ABSENT_OWN_SCOPE_REQUIRED:"+sql);}}}
 static void insert(Connection c,String t,Map<String,Object>v)throws Exception{
  need(TABLES.contains(t)&&!t.equals("base_user")&&NEW.contains(v.get("f_id")),"ONLY_TWELVE_DECLARED_INSERTS");
  String cols=String.join(",",v.keySet().stream().map(k->"`"+k+"`").toList());try(PreparedStatement p=c.prepareStatement("INSERT INTO jnpf."+t+"("+cols+") VALUES("+String.join(",",Collections.nCopies(v.size(),"?"))+")")){int i=1;for(Object x:v.values())p.setObject(i++,x);need(p.executeUpdate()==1,"EXACT_ONE_INSERT");}
 }
 static void run(String[]a)throws Exception{
  need(a.length==4&&a[1].matches("[0-9a-f-]{36}"),"EXACT_OWN_METADATA_ARGS");int port=Integer.parseInt(a[0]);need(port>1024&&port<65536&&port!=3306,"OWN_DYNAMIC_PORT");
  String mode=a[2];need(Set.of("verify").contains(mode),"CLOSED_METADATA_MODE");Path out=Path.of(a[3]).toAbsolutePath().normalize();need(out.startsWith(ROOT)&&!Files.exists(out),"FRESH_OWN_METADATA_RESULT");
  need(Files.readString(ROOT.resolve("own-normal-manager-test.marker")).equals("own-original-manager-full-lifecycle-r609\n")&&!Files.exists(Path.of("D:/Project/Zhumadian/_g/user-manual-protected.json")),"OWN_SYNTHETIC_FIXTURE_ONLY");
  String secret=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(secret!=null&&secret.matches("[0-9a-f]{32}"),"OWN_STDIN_SECRET");
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=20000","root",secret)){
   secret=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){need(r.next()&&a[1].equals(r.getString(1))&&port==r.getInt(2)&&Path.of("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data").toAbsolutePath().normalize().equals(Path.of(r.getString(3)).toAbsolutePath().normalize())&&"jnpf".equals(r.getString(4)),"EXACT_LIVE_OWN_G");}
   Map<String,Object>e=get(c,"base_user",120002);need("own_statistics_reader_e".equals(e.get("f_account"))&&"0".equals(Objects.toString(e.get("f_is_administrator")))&&id(120000).equals(e.get("f_role_id"))&&id(14).equals(e.get("f_system_id")),"EXISTING_OWN_NONADMIN_E_ONLY");
   zero(c,"SELECT COUNT(*) FROM tj_endanger.hazard_source WHERE id=?",id(120199));
   Properties audit=new Properties();
   for(String table:TABLES){int present=0;for(String key:NEW){try(PreparedStatement p=c.prepareStatement("SELECT COUNT(*) FROM jnpf."+table+" WHERE f_id=?")){p.setString(1,key);try(ResultSet r=p.executeQuery()){need(r.next(),"AUDIT_COUNT");present+=r.getInt(1);}}}audit.setProperty("reservedIdsPresent."+table,Integer.toString(present));}
   for(String code:List.of("functionArea","hazardousSourcesRiskLevel")){int count=0;boolean own=true;try(PreparedStatement p=c.prepareStatement("SELECT f_id FROM jnpf.base_dictionary_type WHERE f_parent_id=? AND f_en_code=?")){p.setString(1,id(1000));p.setString(2,code);try(ResultSet r=p.executeQuery()){while(r.next()){need(++count<20,"BOUNDED_DICT_TYPE_AUDIT");own&=r.getString(1).matches("a531[0-9a-f]{28}");}}}audit.setProperty("existingDictionaryTypes."+code,Integer.toString(count));audit.setProperty("existingDictionaryTypesOwned."+code,Boolean.toString(own));}
   store(ROOT.resolve("scope-audit-"+mode+".private.properties"),audit);

   Properties old=new Properties();try(InputStream in=Files.newInputStream(Path.of("D:/Project/Zhumadian/work/hazard-statistics-probe-r1143/fixture-menu-journal.private.properties"))){old.load(in);}need("committed".equals(old.getProperty("phase"))&&"true".equals(old.getProperty("systemCorrectedToSafety")),"ORIGINAL_READER_COMMITTED_ONCE");
   // Explicit extension only for these twelve new IDs; original users/grants are
   // still projected by the previous verifier. New rows verified independently.
   OwnHazardStatisticsMenuFixtureR1172.NEW_IDS.addAll(NEW);
   need(old.getProperty("oldMetadataSHA256").equals(OwnHazardStatisticsMenuFixtureR1172.oldDigest(c)),"ORIGINAL_METADATA_MUST_REMAIN_UNCHANGED");
   Map<String,Object>page=get(c,"base_module",120011),grant=get(c,"base_authorize",120022),button=get(c,"base_module_button",800),buttonGrant=get(c,"base_authorize",900);
   need(id(14).equals(page.get("f_system_id"))&&id(120010).equals(page.get("f_parent_id"))&&id(120001).equals(grant.get("f_object_id"))&&"module".equals(grant.get("f_item_type"))&&"button".equals(buttonGrant.get("f_item_type")),"OWN_EXISTING_MENU_AND_GRANT_DONORS");
   Map<String,Object>type=get(c,"base_dictionary_type",1001),data=get(c,"base_dictionary_data",1002),root=get(c,"base_dictionary_type",1000);
   need("safetycode".equals(root.get("f_en_code"))&&"Own safety codes".equals(root.get("f_full_name"))&&id(1000).equals(type.get("f_parent_id"))&&"specialHomework".equals(type.get("f_en_code"))&&id(1001).equals(data.get("f_dictionary_type_id")),"OWN_ORIGINAL_DICTIONARY_DONORS");
   LinkedHashMap<String,List<Map<String,Object>>>rows=new LinkedHashMap<>();for(String t:TABLES)rows.put(t,new ArrayList<>());
   rows.get("base_module").add(copy(page,"f_id",id(120100),"f_full_name","重大危险源","f_en_code","OWN_HAZARD_SOURCE","f_path","/majorHazard/hazardSource","f_url_address","/majorHazard/hazardSource","f_is_button_authorize",1,"f_sort_code",120100));
   String[]paths={"add","edit","detail"};String[]labels={"新增","编辑","详情"};
   for(int i=0;i<3;i++)rows.get("base_module_button").add(copy(button,"f_id",id(120101+i),"f_module_id",id(120100),"f_full_name",labels[i],"f_en_code","OWN_HAZARD_"+paths[i],"f_path","/majorHazard/hazardSource/"+paths[i],"f_url_address","/majorHazard/hazardSource/info/index","f_sort_code",120101+i));
   rows.get("base_authorize").add(copy(grant,"f_id",id(120110),"f_item_id",id(120100),"f_sort_code",120110));
   for(int i=0;i<3;i++)rows.get("base_authorize").add(copy(buttonGrant,"f_id",id(120111+i),"f_object_id",id(120001),"f_item_id",id(120101+i),"f_sort_code",120111+i));
   String[]codes={"functionArea","hazardousSourcesRiskLevel"},dictLabels={"Own isolated zone","四级"};
   int reusedTypes=0,reusedValues=0;
   for(int i=0;i<2;i++){
    String typeId=null;try(PreparedStatement p=c.prepareStatement("SELECT f_id,f_is_tree,f_enabled_mark FROM jnpf.base_dictionary_type WHERE f_parent_id=? AND f_en_code=?")){p.setString(1,id(1000));p.setString(2,codes[i]);try(ResultSet r=p.executeQuery()){if(r.next()){typeId=r.getString(1);need(typeId.matches("a531[0-9a-f]{28}")&&r.getInt(2)==0&&r.getInt(3)==1&&!r.next(),"EXISTING_DICT_TYPE_REQUIRES_EXACT_OWN_REVIEW");}}}
    if(typeId==null){typeId=id(120120+i);rows.get("base_dictionary_type").add(copy(type,"f_id",typeId,"f_full_name",i==0?"Own hazard zone":"Own hazard level","f_en_code",codes[i],"f_sort_code",120120+i));}else if(!NEW.contains(typeId)){reusedTypes++;}
    else rows.get("base_dictionary_type").add(copy(type,"f_id",typeId,"f_full_name",i==0?"Own hazard zone":"Own hazard level","f_en_code",codes[i],"f_sort_code",120120+i));
    String valueId=null;try(PreparedStatement p=c.prepareStatement("SELECT f_id,f_full_name,f_enabled_mark,f_parent_id FROM jnpf.base_dictionary_data WHERE f_dictionary_type_id=? AND f_en_code=?")){p.setString(1,typeId);p.setString(2,dictLabels[i]);try(ResultSet r=p.executeQuery()){if(r.next()){valueId=r.getString(1);need(valueId.matches("a531[0-9a-f]{28}")&&dictLabels[i].equals(r.getString(2))&&r.getInt(3)==1&&"-1".equals(r.getString(4))&&!r.next(),"EXISTING_DICT_VALUE_REQUIRES_EXACT_OWN_REVIEW");}}}
    if(valueId==null||NEW.contains(valueId))rows.get("base_dictionary_data").add(copy(data,"f_id",id(120122+i),"f_dictionary_type_id",typeId,"f_full_name",dictLabels[i],"f_en_code",dictLabels[i],"f_sort_code",120122+i));else reusedValues++;
   }
   int expectedNew=rows.values().stream().mapToInt(List::size).sum();need(expectedNew>=8&&expectedNew<=12,"CLOSED_EIGHT_TO_TWELVE_NEW_METADATA_ROWS");
   Path journal=Path.of("D:/Project/Zhumadian/work/hazard-form-probe-r1188/hazard-form-metadata-journal.private.properties");Properties state=new Properties();
   if(mode.equals("prepare")){
    need(!Files.exists(journal),"NEVER_REISSUE_METADATA_PREPARE");
    for(String t:TABLES)for(String key:NEW)zero(c,"SELECT COUNT(*) FROM jnpf."+t+" WHERE f_id=?",key);
    zero(c,"SELECT COUNT(*) FROM jnpf.base_module WHERE f_system_id=? AND f_path=?",id(14),"/majorHazard/hazardSource");
    // Existing dictionary types/values were independently scoped above; exact own rows are reused unchanged.
    state.setProperty("oldMetadataSHA256",digest(c));state.setProperty("phase","before-transaction");store(journal,state);
   }else{
    try(InputStream in=Files.newInputStream(journal)){state.load(in);}need("committed".equals(state.getProperty("phase")),"COMMITTED_METADATA_ONLY_NO_AUTOMATIC_RETRY");need(state.getProperty("oldMetadataSHA256").equals(digest(c)),"EXISTING_METADATA_DRIFT");c.setReadOnly(true);
   }
   c.setAutoCommit(false);int count=0;try{
    for(var table:rows.entrySet())for(var expected:table.getValue()){
     if(mode.equals("prepare"))insert(c,table.getKey(),expected);
     Map<String,Object>actual=get(c,table.getKey(),Integer.parseInt(((String)expected.get("f_id")).substring(4),16));for(String key:expected.keySet())need(Objects.equals(Objects.toString(expected.get(key),null),Objects.toString(actual.get(key),null)),"EXACT_NEW_METADATA_ROW_REQUIRED");count++;
    }
    need(count==expectedNew&&state.getProperty("oldMetadataSHA256").equals(digest(c)),"ONLY_TWELVE_DECLARED_ROWS");c.commit();
   }catch(Exception error){c.rollback();if(mode.equals("prepare")){state.setProperty("phase","rolled-back");store(journal,state);}throw error;}
   if(mode.equals("prepare")){state.setProperty("phase","committed");state.setProperty("newMetadataRows",Integer.toString(expectedNew));store(journal,state);}
   Properties result=new Properties();result.setProperty("passed","true");result.setProperty("newSyntheticMetadataRows",Integer.toString(expectedNew));result.setProperty("reusedDictionaryTypes",Integer.toString(reusedTypes));result.setProperty("reusedDictionaryValues",Integer.toString(reusedValues));result.setProperty("existingStableIdentityRolesGrantsAndDictionariesPreserved","true");result.setProperty("businessWritesOrSchemaChanges","false");store(out,result);
  }finally{secret=null;}
  System.out.println("OWN_HAZARD_FORM_TWELVE_METADATA_ROWS_"+mode.toUpperCase(Locale.ROOT)+"_VERIFIED");
 }
 public static void main(String[]args)throws Exception{try{run(args);}catch(Exception e){System.out.println("OWN_HAZARD_FORM_METADATA_REJECTED:"+e.getClass().getSimpleName()+":"+(e instanceof SQLException?((SQLException)e).getSQLState()+":"+((SQLException)e).getErrorCode():e.getMessage()));System.exit(2);}}
}
