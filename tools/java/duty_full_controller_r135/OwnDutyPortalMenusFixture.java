import java.io.*;import java.sql.*;import java.nio.file.*;import java.util.*;
/** Only standard menu/button/grant rows on the separately owned _g synthetic clone. */
public final class OwnDutyPortalMenusFixture{
 static String id(int n){return "a531"+String.format("%028x",n);}
 static void need(boolean b)throws Exception{if(!b)throw new Exception("OWN_WORKFLOW_MENU_SCOPE_REJECTED");}
 static Map<String,Object> row(Connection c,String table,String key)throws Exception{
  need(Set.of("base_user","base_module","base_module_button","base_authorize").contains(table));
  try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+table+" WHERE f_id=?")){p.setString(1,key);try(ResultSet r=p.executeQuery()){
   need(r.next());ResultSetMetaData m=r.getMetaData();Map<String,Object>v=new LinkedHashMap<>();for(int i=1;i<=m.getColumnCount();i++)v.put(m.getColumnName(i).toLowerCase(),r.getObject(i));need(!r.next());return v;}}
 }
 static void insert(Connection c,String table,Map<String,Object>v)throws Exception{
  need(Set.of("base_module","base_module_button","base_authorize").contains(table));
  try(PreparedStatement p=c.prepareStatement("SELECT * FROM jnpf."+table+" WHERE f_id=?")){p.setObject(1,v.get("f_id"));try(ResultSet r=p.executeQuery()){if(r.next()){for(var e:v.entrySet())need(Objects.equals(Objects.toString(e.getValue(),null),Objects.toString(r.getObject(e.getKey()),null)));need(!r.next());return;}}}
  try(PreparedStatement p=c.prepareStatement("INSERT INTO jnpf."+table+"("+String.join(",",v.keySet())+") VALUES("+String.join(",",Collections.nCopies(v.size(),"?"))+")")){int i=1;for(Object o:v.values())p.setObject(i++,o);need(p.executeUpdate()==1);}
 }
 static Map<String,Object> clone(Map<String,Object>v,Object...pairs){Map<String,Object>r=new LinkedHashMap<>(v);for(int i=0;i<pairs.length;i+=2)r.put((String)pairs[i],pairs[i+1]);return r;}
 public static void main(String[]a)throws Exception{
  need(a.length==3&&a[1].matches("[0-9a-f-]{36}")&&Path.of(a[2]).toAbsolutePath().normalize().toString().replace('\\','/').equals("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data"));
  need(!Files.exists(Path.of("D:/Project/Zhumadian/_g/user-manual-protected.json")));
  String password=new BufferedReader(new InputStreamReader(System.in)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"));
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+Integer.parseInt(a[0])+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=10000","root",password)){
   password=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&Path.of(r.getString(2)).toAbsolutePath().normalize().equals(Path.of(a[2]).toAbsolutePath().normalize()));}
   for(int n=0;n<2;n++){Map<String,Object>user=row(c,"base_user",id(100+n));need((n==0?"own_operator_a":"own_reviewer_b").equals(user.get("f_account"))&&((Number)user.get("f_is_administrator")).intValue()==0);}
   c.setAutoCommit(false);
   Map<String,Object>parent=row(c,"base_module",id(600)),page=row(c,"base_module",id(603)),button=row(c,"base_module_button",id(801));
   need("/emergencyResponse/taskSend".equals(page.get("f_path"))&&id(13).equals(page.get("f_system_id"))&&id(603).equals(button.get("f_module_id")));
   Map<String,Object>grant=row(c,"base_authorize",id(703)),buttonGrant=row(c,"base_authorize",id(901)),systemGrant=row(c,"base_authorize",id(650));need(id(30).equals(grant.get("f_object_id"))&&"module".equals(grant.get("f_item_type")));
   insert(c,"base_module",clone(parent,"f_id",id(3600),"f_full_name","值班管理","f_en_code","OWN_DUTY_R135_ROOT","f_path","/dutyManage","f_url_address","","f_sort_code",3600));
   String[][] pages={{"3601","值班人员","dutyPersonnel"},{"3602","值班排班","dutySchedule"},{"3603","值班日志","dutyLog"}};
   for(String[]v:pages)insert(c,"base_module",clone(page,"f_id",id(Integer.parseInt(v[0])),"f_parent_id",id(3600),"f_full_name",v[1],"f_en_code","OWN_DUTY_R135_"+v[2],"f_path","/dutyManage/"+v[2],"f_url_address","/dutyManage/"+v[2],"f_sort_code",Integer.parseInt(v[0])));
   String[][] buttons={{"3801","3601","新增","dutyPersonnel","add"},{"3802","3601","编辑","dutyPersonnel","edit"},{"3803","3601","详情","dutyPersonnel","detail"},{"3804","3602","新增","dutySchedule","add"},{"3805","3602","编辑","dutySchedule","edit"},{"3806","3602","详情","dutySchedule","detail"},{"3807","3603","新增","dutyLog","add"},{"3808","3603","编辑","dutyLog","edit"},{"3809","3603","详情","dutyLog","detail"}};
   for(String[]v:buttons)insert(c,"base_module_button",clone(button,"f_id",id(Integer.parseInt(v[0])),"f_module_id",id(Integer.parseInt(v[1])),"f_full_name",v[2],"f_en_code","OWN_DUTY_R135_BUTTON_"+v[0],"f_path","/dutyManage/"+v[3]+"/"+v[4],"f_url_address","/dutyManage/"+v[3]+"/info/index"));
   int next=5500;
   for(int group:new int[]{30,31}){
    for(int module:new int[]{3600,3601,3602,3603})insert(c,"base_authorize",clone(grant,"f_id",id(next++),"f_item_id",id(module),"f_object_id",id(group)));
    for(int n=3801;n<=3809;n++)insert(c,"base_authorize",clone(buttonGrant,"f_id",id(next++),"f_item_id",id(n),"f_object_id",id(group)));
   }
   c.commit();System.out.println("OWN_SYNTHETIC_DUTY_MENUS_AND_TWO_GROUPS_READY");
  }
 }
}
