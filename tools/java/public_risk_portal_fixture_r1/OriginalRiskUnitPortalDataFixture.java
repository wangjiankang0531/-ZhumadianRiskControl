package xnby.replica;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.sql.*;import java.util.*;import com.fasterxml.jackson.databind.ObjectMapper;
import static xnby.replica.OriginalCompiledPortalLoginDataFixture.*;
/** Additional known synthetic risk menu, departments, contact, and grade in the fresh owned schema. */
public final class OriginalRiskUnitPortalDataFixture{
 public static void main(String[]a)throws Exception{
  need(a.length==3,"OWN_RISK_PORTAL_ARGS");Path root=Path.of(a[0]).toRealPath();
  need(root.getFileName().toString().matches("full-business-main-r[1-9][0-9]*"),"OWN_RISK_PORTAL_ROOT");
  int port=Integer.parseInt(a[1]);byte[] raw=System.in.readNBytes(4097);need(raw.length==32,"OWN_RISK_PORTAL_SECRET_BOUND");
  String secret=new String(raw,StandardCharsets.US_ASCII);Arrays.fill(raw,(byte)0);
  Properties props=new Properties();props.putAll(Map.of("user","xnby_whole_main","password",secret,"useSSL","false","allowPublicKeyRetrieval","true","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000"));
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf",props)){
   try(var s=c.createStatement();var r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){
    need(r.next()&&a[2].equals(r.getString(1))&&port==r.getInt(2)&&root.resolve("data").toRealPath().equals(Path.of(r.getString(3)).toRealPath())&&"jnpf".equals(r.getString(4)),"EXACT_OWN_RISK_PORTAL_SERVER");
   }
   try(var p=c.prepareStatement("SELECT f_en_code FROM base_organize WHERE f_id=?")){p.setString(1,id(1));try(var r=p.executeQuery()){need(r.next()&&"OWN_COMPANY".equals(r.getString(1)),"OWN_COMPANY_ALREADY_SEEDED");}}
   try(var p=c.prepareStatement("SELECT f_en_code FROM base_system WHERE f_id=?")){p.setString(1,id(14));try(var r=p.executeQuery()){need(r.next()&&"safety".equals(r.getString(1)),"OWN_SAFETY_SYSTEM_ALREADY_SEEDED");}}
   c.setAutoCommit(false);try{
    for(int i=0;i<2;i++)insert(c,"base_organize",row(1800+i,"f_parent_id",id(1),"f_category","department","f_en_code","OWN_RISK_DEPT_"+i,"f_full_name","Own risk department "+(i==0?"A":"B"),"f_organize_id_tree",id(1)+","+id(1800+i),"f_enabled_mark",1,"f_sort_code",i+1,"f_tenant_id",""));
    String salt=md5("OWN_RISK_CONTACT_"+root.getFileName());
    insert(c,"base_user",row(150,"f_account","own_risk_contact","f_real_name","Own risk contact A","f_password",md5(md5(secret)+salt.toLowerCase(Locale.ROOT)),"f_secretkey",salt,"f_is_administrator",0,"f_organize_id",id(1800),"f_position_id","","f_role_id","","f_system_id",id(14),"f_app_system_id",id(14),"f_theme","classic","f_language","zh-CN","f_portal_id","","f_group_id","","f_manager_id","","f_gender","1","f_head_icon","","f_log_success_count",0,"f_log_error_count",0,"f_enabled_mark",1,"f_sort_code",5,"f_tenant_id","","f_change_password_date",new Timestamp(System.currentTimeMillis())));
    insert(c,"base_user_relation",row(2150,"f_user_id",id(150),"f_object_type","Organize","f_object_id",id(1800),"f_sort_code",1,"f_tenant_id",""));
    insert(c,"base_dictionary_type",row(1100,"f_parent_id",id(1000),"f_full_name","Own risk grades","f_en_code","riskLevel","f_is_tree",0,"f_type",0,"f_enabled_mark",1,"f_sort_code",2,"f_tenant_id",""));
    insert(c,"base_dictionary_data",row(1101,"f_parent_id","-1","f_full_name","Own risk grade 1","f_en_code","1","f_is_default",0,"f_enabled_mark",1,"f_dictionary_type_id",id(1100),"f_sort_code",1,"f_tenant_id",""));
    String[][] menus={{"1300","-1","双重预防","/hiddenInvestigate",""},{"1301",id(1300),"风险分析单元","/hiddenInvestigate/riskAnalysisUnit","/hiddenInvestigate/riskAnalysisUnit/index"}};
    for(String[]m:menus){int n=Integer.parseInt(m[0]);insert(c,"base_module",row(n,"f_parent_id",m[1],"f_type",n==1300?1:2,"f_full_name",m[2],"f_en_code","OWN_RISK_"+n,"f_category","Web","f_path",m[3],"f_url_address",m[4],"f_system_id",id(14),"f_property_json","{}","f_enabled_mark",1,"f_sort_code",n,"f_visible","1","f_is_button_authorize",n==1301?1:0,"f_is_column_authorize",0,"f_is_data_authorize",0,"f_is_form_authorize",0,"f_tenant_id",""));insert(c,"base_authorize",row(19000+n,"f_item_type","module","f_item_id",id(n),"f_object_type","Role","f_object_id",id(30),"f_sort_code",n,"f_tenant_id",""));}
    for(int i=0;i<3;i++){String path=List.of("add","edit","detail").get(i);insert(c,"base_module_button",row(1310+i,"f_parent_id","-1","f_full_name",List.of("新增","编辑","查看").get(i),"f_path","/hiddenInvestigate/riskAnalysisUnit/"+path,"f_en_code","OWN_RISK_"+path,"f_url_address","/hiddenInvestigate/riskAnalysisUnit/info/index","f_module_id",id(1301),"f_property_json","{}","f_enabled_mark",1,"f_sort_code",i+1,"f_tenant_id","","f_visible","1"));insert(c,"base_authorize",row(22000+i,"f_item_type","button","f_item_id",id(1310+i),"f_object_type","Role","f_object_id",id(30),"f_sort_code",i+1,"f_tenant_id",""));}
    c.commit();
   }catch(Exception e){c.rollback();throw e;}finally{c.setAutoCommit(true);}
  }finally{props.remove("password");secret=null;}
  new ObjectMapper().writeValue(root.resolve("risk-portal-seed-result.json").toFile(),Map.of("syntheticDepartments",2,"syntheticNonLoginContact",1,"syntheticGradeOptions",1,"nativeRiskMenusAndRoutes",true,"originalAccountOrBusinessRowsImported",false));
 }
}
