import java.io.*;import java.nio.charset.StandardCharsets;import java.nio.file.*;import java.nio.*;import java.sql.*;import java.util.*;import java.security.MessageDigest;
/** Own G only. One new nonadmin reader and ten absent fixture metadata rows.
 * Existing users, groups, grants, business rows and authentication are never updated. */
public final class OwnHazardStatisticsMenuFixtureR1172 {
 static final Path ROOT=Path.of("D:/Project/Zhumadian/work/hazard-statistics-probe-r1172");
 static final List<String>TABLES=List.of("base_role","base_permission_group","base_user","base_user_relation","base_module","base_authorize");
 static final int ROLE=120000,GROUP=120001,USER=120002,ORGREL=120003,ROLEREL=120004,PARENT=120010,PAGE=120011,SYS=120020,PG=120021,MG=120022;
 static final Set<String>NEW_IDS=new HashSet<>();static{for(int n:new int[]{ROLE,GROUP,USER,ORGREL,ROLEREL,PARENT,PAGE,SYS,PG,MG})NEW_IDS.add(id(n));}
 static void need(boolean b,String m){if(!b)throw new IllegalStateException(m);}
 static String id(int n){return "a531"+String.format("%028x",n);}
 static String md5(String s)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("MD5").digest(s.getBytes(StandardCharsets.UTF_8)));}
 static Map<String,Object>get(Connection c,String t,int n)throws Exception{
  need(TABLES.contains(t),"CLOSED_FIXTURE_TABLES");try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+t+" WHERE f_id=?")){p.setString(1,id(n));try(ResultSet r=p.executeQuery()){need(r.next(),"OWN_METADATA_DONOR_REQUIRED");Map<String,Object>v=new LinkedHashMap<>();for(int i=1;i<=r.getMetaData().getColumnCount();i++)v.put(r.getMetaData().getColumnName(i).toLowerCase(),r.getObject(i));need(!r.next(),"UNIQUE_OWN_DONOR");return v;}}
 }
 static Map<String,Object>copy(Map<String,Object>v,Object...args){Map<String,Object>x=new LinkedHashMap<>(v);for(int i=0;i<args.length;i+=2){need(x.containsKey(args[i]),"EXISTING_ORIGINAL_COLUMN_REQUIRED");x.put((String)args[i],args[i+1]);}return x;}
 static void part(MessageDigest d,String s){byte[]b=s==null?new byte[0]:s.getBytes(StandardCharsets.UTF_8);d.update((byte)(s==null?0:1));d.update(ByteBuffer.allocate(4).putInt(b.length).array());d.update(b);}
 static String oldDigest(Connection c)throws Exception{
  Set<String>identity=Set.of("f_id","f_account","f_real_name","f_password","f_secretkey","f_is_administrator","f_role_id","f_system_id","f_app_system_id","f_manager_id","f_organize_id","f_enabled_mark","f_group_id","f_position_id");
  MessageDigest d=MessageDigest.getInstance("SHA-256");for(String t:TABLES){part(d,t);try(Statement s=c.createStatement()){s.setQueryTimeout(15);try(ResultSet r=s.executeQuery("SELECT * FROM jnpf."+t+" ORDER BY f_id")){int count=0;while(r.next()){need(++count<20000,"BOUNDED_SYNTHETIC_METADATA");if(NEW_IDS.contains(r.getString("f_id")))continue;for(int i=1;i<=r.getMetaData().getColumnCount();i++)if(!t.equals("base_user")||identity.contains(r.getMetaData().getColumnName(i).toLowerCase()))part(d,r.getString(i));}}}}return HexFormat.of().formatHex(d.digest());
 }
 static void insert(Connection c,String t,Map<String,Object>v)throws Exception{
  need(TABLES.contains(t)&&NEW_IDS.contains(v.get("f_id")),"ONLY_NEW_DECLARED_FIXTURE_ROWS");String marks=String.join(",",Collections.nCopies(v.size(),"?"));String cols=String.join(",",v.keySet().stream().map(k->"`"+k+"`").toList());try(PreparedStatement p=c.prepareStatement("INSERT INTO jnpf."+t+"("+cols+") VALUES("+marks+")")){int i=1;for(Object x:v.values())p.setObject(i++,x);need(p.executeUpdate()==1,"EXACT_ONE_INSERT");}
 }
 static void store(Path p,Properties v)throws Exception{
  Path tmp=p.resolveSibling(p.getFileName()+".own.tmp");need(!Files.exists(tmp),"NO_FOREIGN_JOURNAL_TEMP");try(OutputStream o=Files.newOutputStream(tmp,StandardOpenOption.CREATE_NEW)){v.store(o,"owned synthetic statistics menu only; no password, salt, raw row or runtime UUID");}Files.move(tmp,p,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
 }
 static boolean existsAny(Connection c,String t,String key)throws Exception{try(PreparedStatement p=c.prepareStatement("SELECT f_id FROM jnpf."+t+" WHERE f_id=?")){p.setString(1,key);try(ResultSet r=p.executeQuery()){return r.next();}}}
 public static void main(String[]a)throws Exception{
  need(a.length==4,"EXACT_OWN_MENU_ARGS");int port=Integer.parseInt(a[0]);need(port>1024&&port<65536&&port!=3306,"OWN_DYNAMIC_DATABASE");need(a[1].matches("[0-9a-f-]{36}"),"OWN_DATABASE_IDENTITY");
  String mode=a[2];need(Set.of("verify").contains(mode),"CLOSED_MODES");Path out=Path.of(a[3]).toAbsolutePath().normalize();need(out.startsWith(ROOT)&&!Files.exists(out),"FRESH_OWN_RESULT");Path journal=Path.of("D:/Project/Zhumadian/work/hazard-statistics-probe-r1143/fixture-menu-journal.private.properties");
  need(Files.readString(ROOT.resolve("own-normal-manager-test.marker")).equals("own-original-manager-full-lifecycle-r609\n"),"OWN_FIXTURE_MARKER");
  String secret=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(secret!=null&&secret.matches("[0-9a-f]{32}"),"OWN_STDIN_SECRET_ONLY");Properties result=new Properties();
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=20000","root",secret)){
   try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){Path data=Path.of("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data").toAbsolutePath().normalize();need(r.next()&&a[1].equals(r.getString(1))&&port==r.getInt(2)&&data.equals(Path.of(r.getString(3)).toAbsolutePath().normalize())&&"jnpf".equals(r.getString(4)),"ONLY_EXACT_LIVE_OWN_G");}
   Map<String,Object>donor=get(c,"base_user",100);need("own_operator_a".equals(donor.get("f_account"))&&"0".equals(Objects.toString(donor.get("f_is_administrator")))&&id(20).equals(donor.get("f_role_id")),"EXACT_SYNTHETIC_NONADMIN_DONOR");
   Map<String,Object>role=get(c,"base_role",20),group=get(c,"base_permission_group",30),page=get(c,"base_module",40),grant=get(c,"base_authorize",50),moduleGrant=get(c,"base_authorize",51),org=get(c,"base_user_relation",200),roleRel=get(c,"base_user_relation",210);
   need(id(12).equals(page.get("f_system_id"))&&id(30).equals(grant.get("f_object_id"))&&"system".equals(grant.get("f_item_type")),"ORIGINAL_OWN_SECURITY_ROLE_GROUP_CONTRACT");
   Properties journalData=new Properties();String salt;
   if(mode.equals("prepare")){
    need(!Files.exists(journal),"DO_NOT_REISSUE_EXISTING_FIXTURE");
    Set<String>known=new HashSet<>(List.of(id(100),id(101),id(102),id(103)));int inspected=0,extra=0;boolean synthetic=true;
    try(Statement s=c.createStatement()){s.setQueryTimeout(15);try(ResultSet r=s.executeQuery("SELECT f_id,f_account,f_is_administrator FROM jnpf.base_user ORDER BY f_id")){while(r.next()){
     need(++inspected<=20000,"BOUNDED_EXISTING_USER_NAMESPACE_AUDIT");String key=r.getString(1),account=r.getString(2);boolean own=key!=null&&key.matches("a531[0-9a-f]{28}")&&account!=null&&account.startsWith("own_")&&r.getInt(3)==0;synthetic&=own;if(!known.remove(key))extra++;
    }}}
    Properties audit=new Properties();audit.setProperty("originalFourIdsPresent",Boolean.toString(known.isEmpty()));audit.setProperty("allExistingAccountsInOwnSyntheticNamespaceAndNonadmin",Boolean.toString(synthetic));audit.setProperty("additionalUsersObserved",Boolean.toString(extra>0));audit.setProperty("rawAccountRowsExported","false");store(out.resolveSibling("existing-user-scope-audit.private.properties"),audit);
    need(known.isEmpty()&&synthetic,"UNKNOWN_OR_ADMIN_USER_NAMESPACE_REFUSE_BEFORE_WRITES");
    for(String t:TABLES)for(String key:NEW_IDS)need(!existsAny(c,t,key),"FOREIGN_FIXTURE_ID_REFUSED");
    try(PreparedStatement p=c.prepareStatement("SELECT COUNT(*) FROM jnpf.base_module WHERE f_system_id=? AND f_path=?")){p.setString(1,id(12));p.setString(2,"/majorHazard/statistics");try(ResultSet r=p.executeQuery()){need(r.next()&&r.getInt(1)==0,"EXISTING_STATISTICS_MENU_REQUIRES_RECONCILIATION");}}
    try(PreparedStatement p=c.prepareStatement("SELECT COUNT(*) FROM jnpf.base_user WHERE f_account=?")){p.setString(1,"own_statistics_reader_e");try(ResultSet r=p.executeQuery()){need(r.next()&&r.getInt(1)==0,"NO_FOREIGN_ACCOUNT_COLLISION");}}
    salt=md5(UUID.randomUUID().toString());journalData.setProperty("oldMetadataSHA256",oldDigest(c));journalData.setProperty("phase","before-transaction");journalData.setProperty("statisticsMenuPreviouslyAbsent","true");store(journal,journalData);
   }else{
    need(Files.isRegularFile(journal),"PREVIOUS_FIXTURE_JOURNAL_REQUIRED");try(InputStream in=Files.newInputStream(journal)){journalData.load(in);}need("committed".equals(journalData.getProperty("phase")),"EXACT_COMMITTED_FIXTURE");salt=Objects.toString(get(c,"base_user",USER).get("f_secretkey"));
    need(journalData.getProperty("oldMetadataSHA256").equals(oldDigest(c)),"PREEXISTING_USERS_ROLES_OR_GRANTS_CHANGED");c.setReadOnly(true);
   }
   LinkedHashMap<String,List<Map<String,Object>>>rows=new LinkedHashMap<>();for(String t:TABLES)rows.put(t,new ArrayList<>());
   rows.get("base_role").add(copy(role,"f_id",id(ROLE),"f_full_name","Own statistics reader role","f_en_code","OWN_STAT_READER_ROLE","f_sort_code",120000));
   rows.get("base_permission_group").add(copy(group,"f_id",id(GROUP),"f_full_name","Own statistics reader group","f_en_code","OWN_STAT_READER_GROUP","f_permission_member","[\""+id(ROLE)+"--role\"]","f_sort_code",120001));
   rows.get("base_user").add(copy(donor,"f_id",id(USER),"f_account","own_statistics_reader_e","f_real_name","Own statistics reader E","f_password",md5(md5(secret)+salt.toLowerCase(Locale.ROOT)),"f_secretkey",salt,"f_is_administrator",0,"f_role_id",id(ROLE),"f_system_id",id(14),"f_app_system_id",id(14),"f_manager_id","","f_log_success_count",0,"f_log_error_count",0,"f_sort_code",120002));
   secret=null;
   rows.get("base_user_relation").add(copy(org,"f_id",id(ORGREL),"f_user_id",id(USER),"f_object_id",id(1),"f_sort_code",120003));
   rows.get("base_user_relation").add(copy(roleRel,"f_id",id(ROLEREL),"f_user_id",id(USER),"f_object_id",id(ROLE),"f_sort_code",120004));
   rows.get("base_module").add(copy(page,"f_id",id(PARENT),"f_system_id",id(14),"f_parent_id","-1","f_type",1,"f_full_name","重大危险源管理","f_en_code","OWN_HAZARD_PARENT","f_path","/majorHazard","f_url_address","","f_sort_code",120010));
   rows.get("base_module").add(copy(page,"f_id",id(PAGE),"f_system_id",id(14),"f_parent_id",id(PARENT),"f_type",2,"f_full_name","重大危险源统计","f_en_code","OWN_HAZARD_STATISTICS","f_path","/majorHazard/statistics","f_url_address","/majorHazard/statistics","f_sort_code",120011));
   rows.get("base_authorize").add(copy(grant,"f_id",id(SYS),"f_object_id",id(GROUP),"f_item_id",id(14),"f_sort_code",120020));
   rows.get("base_authorize").add(copy(moduleGrant,"f_id",id(PG),"f_object_id",id(GROUP),"f_item_id",id(PARENT),"f_sort_code",120021));
   rows.get("base_authorize").add(copy(moduleGrant,"f_id",id(MG),"f_object_id",id(GROUP),"f_item_id",id(PAGE),"f_sort_code",120022));
   c.setAutoCommit(false);int checked=0;
   try{
    for(var table:rows.entrySet())for(var expected:table.getValue()){
     if(mode.equals("prepare"))insert(c,table.getKey(),expected);
     Map<String,Object>actual=get(c,table.getKey(),Integer.parseInt(((String)expected.get("f_id")).substring(4),16));
     Set<String>fields=table.getKey().equals("base_user")?Set.of("f_id","f_account","f_real_name","f_password","f_secretkey","f_is_administrator","f_role_id","f_system_id","f_app_system_id","f_manager_id","f_organize_id","f_enabled_mark"):expected.keySet();
     for(String key:fields)need((table.getKey().equals("base_user")&&key.equals("f_organize_id")&&Set.of("",id(1)).contains(Objects.toString(actual.get(key),"")))||Objects.equals(Objects.toString(expected.get(key),null),Objects.toString(actual.get(key),null)),"EXACT_NEW_FIXTURE_READBACK_REQUIRED");checked++;
    }
    need(checked==10&&journalData.getProperty("oldMetadataSHA256").equals(oldDigest(c)),"ONLY_TEN_NEW_ROWS_ALLOWED");c.commit();
   }catch(Exception e){c.rollback();if(mode.equals("prepare")){journalData.setProperty("phase","rolled-back");store(journal,journalData);}throw e;}
   if(mode.equals("prepare")){journalData.setProperty("phase","committed");journalData.setProperty("newSyntheticMetadataRows","10");store(journal,journalData);}
   result.setProperty("passed","true");result.setProperty("phase",mode);result.setProperty("statisticsMenuPreviouslyAbsent","true");result.setProperty("preExistingIdentityCredentialsAndPermissionMetadataUnchanged","true");result.setProperty("ordinaryLoginTelemetryNotIncludedInIdentityProjection","true");result.setProperty("newStatisticsReaderIsNonAdministrator","true");result.setProperty("newFixtureRowsVerified","10");result.setProperty("businessRowsOrSchemaOrExistingPermissionsChanged","false");
   try(OutputStream o=Files.newOutputStream(out,StandardOpenOption.CREATE_NEW)){result.store(o,"owned fixture verification booleans only");}
  }finally{secret=null;}
  System.out.println("OWN_STATISTICS_MENU_FIXTURE_"+mode.toUpperCase(Locale.ROOT)+"_VERIFIED");
 }
}
