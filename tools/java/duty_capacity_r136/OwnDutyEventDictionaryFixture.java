import java.io.*;import java.nio.file.*;import java.sql.*;import java.util.*;
/** Three narrowly scoped synthetic event dictionaries and exact reuse of the existing synthetic root1000 on never-user-delivered _g; no real data or schema changes. */
public final class OwnDutyEventDictionaryFixture{
 static String phase="start";
 static void need(boolean v)throws Exception{if(!v)throw new Exception("OWN_DUTY_DICTIONARY_SCOPE");}
 static String id(int n){return "a531"+String.format("%028x",n);}
 static String norm(String s){return s.toLowerCase(Locale.ROOT).replace("_","");}
 static Map<String,String> columns(Connection c,String table)throws Exception{
  phase="columns-"+table;
  need(Set.of("base_dictionary_type","base_dictionary_data").contains(table));Map<String,String>out=new LinkedHashMap<>();
  try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SHOW COLUMNS FROM jnpf."+table)){
   while(r.next()){String name=r.getString(1);need(name.matches("[A-Za-z0-9_]+"));out.put(norm(name),name);}}
  need(out.containsKey("fid")&&out.containsKey("fencode")&&out.containsKey("ffullname")&&out.containsKey("fparentid"));return out;
 }
 static void row(Connection c,String table,int n,String parent,String code,String name,Map<String,Object>extra)throws Exception{
  Map<String,String>cols=columns(c,table);phase="row-"+table+"-"+code;Map<String,Object>v=new LinkedHashMap<>();
  Map<String,Object> logical=new LinkedHashMap<>();logical.put("fid",id(n));logical.put("fparentid",parent);logical.put("fencode",code);logical.put("ffullname",name);logical.put("fenabledmark",1);logical.put("fdeletemark",0);logical.put("fsortcode",1);logical.put("fisdefault",1);logical.put("fistree",0);logical.put("fcategory",0);logical.put("ftype",0);logical.put("ftenantid","");logical.put("fdescription","OWN_SYNTHETIC_DUTY_DICTIONARY");logical.putAll(extra);
  for(var e:logical.entrySet())if(cols.containsKey(e.getKey()))v.put(cols.get(e.getKey()),e.getValue());
  String identifier=cols.get("fid");
  try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+table+" WHERE "+identifier+"=?")){
   p.setString(1,id(n));try(ResultSet r=p.executeQuery()){if(r.next()){for(var e:v.entrySet())need(Objects.equals(Objects.toString(e.getValue(),null),Objects.toString(r.getObject(e.getKey()),null)));need(!r.next());return;}}}
  String codeScope=cols.get("fencode")+"=?";
  boolean dataScope=table.equals("base_dictionary_data");
  if(dataScope){need(extra.containsKey("fdictionarytypeid")&&cols.containsKey("fdictionarytypeid"));codeScope+=" AND "+cols.get("fdictionarytypeid")+"=?";}
  try(PreparedStatement p=c.prepareStatement("SELECT COUNT(*) FROM jnpf."+table+" WHERE "+codeScope)){p.setString(1,code);if(dataScope)p.setObject(2,extra.get("fdictionarytypeid"));try(ResultSet r=p.executeQuery()){need(r.next()&&r.getLong(1)==0);}}
  try(PreparedStatement p=c.prepareStatement("INSERT INTO jnpf."+table+"("+String.join(",",v.keySet())+") VALUES("+String.join(",",Collections.nCopies(v.size(),"?"))+")")){int k=1;for(Object value:v.values())p.setObject(k++,value);need(p.executeUpdate()==1);}
 }
 static void exactOwnRoot(Connection c)throws Exception{
  Map<String,String>cols=columns(c,"base_dictionary_type");phase="exact-existing-own-root1000";
  try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf.base_dictionary_type WHERE "+cols.get("fid")+"=?")){
   p.setString(1,id(1000));try(ResultSet r=p.executeQuery()){
    need(r.next()&&"safetycode".equals(r.getString(cols.get("fencode")))&&"Own safety codes".equals(r.getString(cols.get("ffullname")))&&"-1".equals(r.getString(cols.get("fparentid")))&&r.getInt(cols.get("fistree"))==1&&r.getInt(cols.get("fenabledmark"))==1&&!r.next());}}
  try(PreparedStatement p=c.prepareStatement("SELECT COUNT(*) FROM jnpf.base_dictionary_type WHERE "+cols.get("fencode")+"=?")){
   p.setString(1,"safetycode");try(ResultSet r=p.executeQuery()){need(r.next()&&r.getLong(1)==1);}}
 }
 static int typesCreated=0,dataCreated=0,typesReused=0;
 static void ensureKind(Connection c,int n,String code,String label)throws Exception{
  Map<String,String>cols=columns(c,"base_dictionary_type");String typeId=null;phase="event-type-"+code;
  try(PreparedStatement p=c.prepareStatement("SELECT "+cols.get("fid")+","+cols.get("fparentid")+","+cols.get("fenabledmark")+" FROM jnpf.base_dictionary_type WHERE "+cols.get("fencode")+"=?")){p.setString(1,code);try(ResultSet r=p.executeQuery()){if(r.next()){typeId=r.getString(1);need(typeId.matches("a531[0-9a-f]{28}")&&id(1000).equals(r.getString(2))&&r.getInt(3)==1&&!r.next());typesReused++;}}}
  if(typeId==null){row(c,"base_dictionary_type",n,id(1000),code,label,Map.of());typeId=id(n);typesCreated++;}
  Map<String,String>data=columns(c,"base_dictionary_data");need(data.containsKey("fdictionarytypeid"));long count;
  try(PreparedStatement p=c.prepareStatement("SELECT COUNT(*) FROM jnpf.base_dictionary_data WHERE "+data.get("fdictionarytypeid")+"=?")){p.setString(1,typeId);try(ResultSet r=p.executeQuery()){need(r.next());count=r.getLong(1);}}
  if(count==0){row(c,"base_dictionary_data",n+10,"-1","1",label,Map.of("fdictionarytypeid",typeId));dataCreated++;}
 }
 public static void main(String[]a)throws Exception{
  try{run(a);}catch(Exception e){String state=e instanceof SQLException?((SQLException)e).getSQLState():"";int code=e instanceof SQLException?((SQLException)e).getErrorCode():0;System.out.println("OWN_DICTIONARY_DIAGNOSTIC:{\"phase\":\""+phase+"\",\"type\":\""+e.getClass().getSimpleName()+"\",\"SQLState\":\""+state+"\",\"vendorCode\":"+code+"}");System.exit(2);}
 }
 static void run(String[]a)throws Exception{
  need(a.length==3&&a[1].matches("[0-9a-f-]{36}")&&Path.of(a[2]).toAbsolutePath().normalize().equals(Path.of("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data").toAbsolutePath().normalize()));
  need(!Files.exists(Path.of("D:/Project/Zhumadian/_g/user-manual-protected.json")));
  String password=new BufferedReader(new InputStreamReader(System.in)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"));
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+Integer.parseInt(a[0])+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=10000","root",password)){
   password=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&Path.of(r.getString(2)).toAbsolutePath().normalize().equals(Path.of(a[2]).toAbsolutePath().normalize()));}
   c.setAutoCommit(false);
   exactOwnRoot(c);
   ensureKind(c,8501,"eventType","OWN_EVENT_TYPE_R136");
   ensureKind(c,8502,"eventLevel","OWN_EVENT_LEVEL_R136");
   ensureKind(c,8503,"researchStatus","OWN_RESEARCH_STATUS_R136");
   c.commit();System.out.println("OWN_EVENT_DICTIONARY_READY:{\"typesCreated\":"+typesCreated+",\"typesReused\":"+typesReused+",\"dataCreated\":"+dataCreated+"}");
  }
 }
}