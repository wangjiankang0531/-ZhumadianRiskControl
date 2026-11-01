package xnby.replica;

import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.sql.*;import java.util.*;import java.security.MessageDigest;import javax.crypto.Cipher;import javax.crypto.spec.SecretKeySpec;import com.fasterxml.jackson.databind.ObjectMapper;

/** Exact fresh owned JNPF dataset; no admin account and no token/session seeding. */

public final class OriginalPublishedWorkflowLoginDataFixture {

 public static final String WIRE_KEY=clientWireKey();

 static String clientWireKey(){try {String text=Files.readString(Path.of("D:/Project/Zhumadian/Application/work/tianjin_native_20261023/emergency_pc/src/utils/common.ts"));var m=java.util.regex.Pattern.compile("if\\s*\\(!cipherKey\\)\\s*cipherKey\\s*=\\s*(['\"])([^'\"\\\\]+)\\1;").matcher(text);need(m.find(),"PUBLIC_CLIENT_WIRE_KEY_DECLARATION");String key=m.group(2);need(Set.of(16,24,32).contains(key.getBytes(StandardCharsets.UTF_8).length),"PUBLIC_CLIENT_WIRE_KEY_LENGTH");return key;}catch(Exception e){throw new IllegalStateException("PUBLIC_CLIENT_WIRE_KEY_CONTRACT_FAILED");}}

 static void portal(Connection c)throws Exception {
  insert(c,"base_system",row(14,"f_full_name","Own safety workflow portal","f_en_code","safety","f_is_main",0,"f_property_json","{}","f_enabled_mark",1,"f_sort_code",5,"f_tenant_id","","f_workflow_enabled",1,"f_icon","","f_navigation_icon","","f_work_logo_icon",""));
  String[][] workflowMenus={{"1200","-1","审批管理","/workflow",""},{"1201",id(1200),"我的发起","/workflow/startWithMeTwo","/workflow/startWithMeTwo"},{"1202",id(1200),"待办事宜","/workflow/flowTodo","/workflow/flowTodo"},{"1203",id(1200),"我已处理","/workflow/completedMatters","/workflow/completedMatters"}};
  for(int ownRole=0;ownRole<2;ownRole++)insert(c,"base_authorize",row(1400+ownRole,"f_item_type","system","f_item_id",id(14),"f_object_type","Role","f_object_id",id(30+ownRole),"f_sort_code",30,"f_tenant_id",""));
  for(String[] menu:workflowMenus){
   int n=Integer.parseInt(menu[0]);insert(c,"base_module",row(n,"f_parent_id",menu[1],"f_type",n==1200?1:2,"f_full_name",menu[2],"f_en_code","OWN_WORKFLOW_"+n,"f_category","Web","f_path",menu[3],"f_url_address",menu[4],"f_system_id",id(14),"f_property_json","{}","f_enabled_mark",1,"f_sort_code",n,"f_visible","1","f_is_button_authorize",0,"f_is_column_authorize",0,"f_is_data_authorize",0,"f_is_form_authorize",0,"f_tenant_id",""));
   for(int ownRole=0;ownRole<2;ownRole++)insert(c,"base_authorize",row(5000+n*2+ownRole,"f_item_type","module","f_item_id",id(n),"f_object_type","Role","f_object_id",id(30+ownRole),"f_sort_code",n,"f_tenant_id",""));
  }


  insert(c,"base_system",row(13,"f_full_name","Own emergency portal","f_en_code","emergency","f_is_main",0,"f_property_json","{}","f_enabled_mark",1,"f_sort_code",4,"f_tenant_id","","f_workflow_enabled",1,"f_icon","","f_navigation_icon","","f_work_logo_icon",""));

  String[][] menus={{"600","-1","应急处置","/emergencyResponse",""},{"601","-1","首页","/home/index","/home/index"},{"602",id(600),"事件接报","/emergencyResponse/response","/emergencyResponse/response"},{"603",id(600),"任务派发","/emergencyResponse/taskSend","/emergencyResponse/taskSend"}};

  insert(c,"base_authorize",row(650,"f_item_type","system","f_item_id",id(13),"f_object_type","Role","f_object_id",id(30),"f_sort_code",20,"f_tenant_id",""));

  for(String[] m:menus){int n=Integer.parseInt(m[0]);insert(c,"base_module",row(n,"f_parent_id",m[1],"f_type",n==600?1:2,"f_full_name",m[2],"f_en_code","OWN_PORTAL_"+n,"f_category","Web","f_path",m[3],"f_url_address",m[4],"f_system_id",id(13),"f_property_json","{}","f_enabled_mark",1,"f_sort_code",n,"f_visible","1","f_is_button_authorize",n==603?1:0,"f_is_column_authorize",0,"f_is_data_authorize",0,"f_is_form_authorize",0,"f_tenant_id",""));insert(c,"base_authorize",row(n+100,"f_item_type","module","f_item_id",id(n),"f_object_type","Role","f_object_id",id(30),"f_sort_code",n,"f_tenant_id",""));}

  for(int i=0;i<2;i++){String path=i==0?"detail":"edit";insert(c,"base_module_button",row(800+i,"f_parent_id","-1","f_full_name",i==0?"任务详情":"任务编辑","f_path","/emergencyResponse/taskSend/"+path,"f_en_code","OWN_TASK_"+path,"f_url_address","/emergencyResponse/taskSend/info/index","f_module_id",id(603),"f_property_json","{}","f_enabled_mark",1,"f_sort_code",i+1,"f_tenant_id","","f_visible","1"));insert(c,"base_authorize",row(900+i,"f_item_type","button","f_item_id",id(800+i),"f_object_type","Role","f_object_id",id(30),"f_sort_code",i+1,"f_tenant_id",""));}

  insert(c,"base_dictionary_type",row(1000,"f_parent_id","-1","f_full_name","Own safety codes","f_en_code","safetycode","f_is_tree",1,"f_type",0,"f_enabled_mark",1,"f_sort_code",1,"f_tenant_id",""));

  insert(c,"base_dictionary_type",row(1001,"f_parent_id",id(1000),"f_full_name","Own special homework","f_en_code","specialHomework","f_is_tree",0,"f_type",0,"f_enabled_mark",1,"f_sort_code",1,"f_tenant_id",""));

  insert(c,"base_dictionary_data",row(1002,"f_parent_id","-1","f_full_name","Own task category","f_en_code","1","f_is_default",0,"f_enabled_mark",1,"f_dictionary_type_id",id(1001),"f_sort_code",2,"f_tenant_id",""));



 }



 static void need(boolean value,String code){if(!value)throw new IllegalStateException(code);}

 static String id(int value){if(value==1){String root=System.getProperty("own.fixture.production.organization.id");need(root!=null&&root.matches("[A-Za-z0-9-]{1,64}"),"ACTUAL_PRODUCTION_ORGANIZATION_ID_REQUIRED_IN_OWN_DATASET");return root;}return String.format(Locale.ROOT,"a531%028x",value);}

 static String hex(byte[] bytes){StringBuilder out=new StringBuilder();for(byte value:bytes)out.append(String.format(Locale.ROOT,"%02x",value&255));return out.toString();}

 static String md5(String value)throws Exception{return hex(MessageDigest.getInstance("MD5").digest(value.getBytes(StandardCharsets.UTF_8)));}

 static String wire(String value)throws Exception {Cipher cipher=Cipher.getInstance("AES/ECB/PKCS5Padding");cipher.init(Cipher.ENCRYPT_MODE,new SecretKeySpec(WIRE_KEY.getBytes(StandardCharsets.US_ASCII),"AES"));return hex(cipher.doFinal(md5(value).getBytes(StandardCharsets.US_ASCII)));}

 static Map<String,Object> row(int key,Object...values){Map<String,Object> row=new LinkedHashMap<>();row.put("f_id",id(key));for(int i=0;i<values.length;i+=2)row.put((String)values[i],values[i+1]);return row;}

 static void insert(Connection c,String table,Map<String,Object> row)throws Exception {Set<String> allowed=Set.of("base_organize","base_system","base_module","base_role","base_permission_group","base_user","base_user_relation","base_authorize","base_sys_config","base_module_button","base_dictionary_type","base_dictionary_data");need(allowed.contains(table),"CLOSED_OWN_LOGIN_TABLES");String columns=String.join(",",row.keySet().stream().map(k->"`"+k+"`").toList());String marks=String.join(",",Collections.nCopies(row.size(),"?"));try(var p=c.prepareStatement("INSERT INTO `"+table+"`("+columns+") VALUES("+marks+")")){int i=1;for(Object value:row.values())p.setObject(i++,value);need(p.executeUpdate()==1,"OWN_LOGIN_INSERT_COUNT");}}

 static long count(Connection c,String table)throws Exception{try(var s=c.createStatement();var r=s.executeQuery("SELECT COUNT(*) FROM `"+table+"`")){need(r.next(),"OWN_LOGIN_COUNT");return r.getLong(1);}}

 public static void main(String[] a)throws Exception {

  need(a.length==4,"OWN_LOGIN_DATA_ARGS");Path root=Path.of(a[0]).toRealPath();need(root.getFileName().toString().matches("full-business-main-r[1-9][0-9]*"),"OWN_LOGIN_DATA_ROOT");int port=Integer.parseInt(a[1]);String uuid=a[2],mode=a[3];need(Set.of("seed","snapshot-negative","snapshot-positive","snapshot-final").contains(mode),"OWN_LOGIN_DATA_MODE");byte[] raw=System.in.readNBytes(4097);need(raw.length==32,"OWN_LOGIN_DATA_SECRET_STDIN");String secret=new String(raw,StandardCharsets.US_ASCII);Arrays.fill(raw,(byte)0);var mapper=new ObjectMapper();var manifest=mapper.readTree(Files.readString(root.resolve("short-runtime.json")));String owner=manifest.path("owner").asText();UUID.fromString(owner);var guard=new OriginalSocketProcessBoundary(root,Set.of(port),false);System.setSecurityManager(guard);

  Properties props=new Properties();props.putAll(Map.of("user","xnby_whole_main","password",secret,"useSSL","false","allowPublicKeyRetrieval","true","serverTimezone","UTC","connectTimeout","5000","socketTimeout","15000"));

  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+port+"/jnpf",props)){

   try(var s=c.createStatement();var r=s.executeQuery("SELECT @@server_uuid,@@port,@@datadir,DATABASE()")){need(r.next()&&uuid.equals(r.getString(1))&&port==r.getInt(2)&&Path.of(r.getString(3)).toRealPath().equals(root.resolve("data").toRealPath())&&"jnpf".equals(r.getString(4)),"EXACT_OWN_LOGIN_SERVER_IDENTITY");}

   List<String> tables=List.of("base_organize","base_system","base_module","base_role","base_permission_group","base_user","base_user_relation","base_authorize","base_sys_config");

   if(mode.equals("seed")){

    for(String table:tables)need(count(c,table)==0,"FRESH_EMPTY_LOGIN_TABLES_REQUIRED");c.setAutoCommit(false);try {

     insert(c,"base_organize",row(1,"f_parent_id","-1","f_category","company","f_en_code","OWN_COMPANY","f_full_name","Own isolated test organization","f_organize_id_tree",id(1),"f_enabled_mark",1,"f_sort_code",1,"f_tenant_id",""));

     insert(c,"base_organize",row(220,"f_parent_id",id(1),"f_category","department","f_en_code","OWN_WORKFLOW_DEPT","f_full_name","Own workflow child department","f_organize_id_tree",id(1)+","+id(220),"f_enabled_mark",1,"f_sort_code",1,"f_tenant_id",""));

     for(int i=0;i<3;i++){String code=List.of("mainSystem","workSystem","cqweh-endanger").get(i);insert(c,"base_system",row(10+i,"f_full_name","Own "+code,"f_en_code",code,"f_is_main",i==0?1:0,"f_property_json","{}","f_enabled_mark",1,"f_sort_code",i+1,"f_tenant_id","","f_workflow_enabled",1,"f_icon","","f_navigation_icon","","f_work_logo_icon",""));}

     Map<String,Object> accounts=new TreeMap<>();

     for(int i=0;i<2;i++){

      int role=20+i,group=30+i,module=40+i;String code=i==0?"OWN_OPERATOR_ROLE":"OWN_REVIEWER_ROLE";

      insert(c,"base_role",row(role,"f_full_name",code,"f_en_code",code,"f_type","0","f_global_mark",1,"f_property_json","{}","f_enabled_mark",1,"f_sort_code",i+1,"f_tenant_id",""));

      insert(c,"base_permission_group",row(group,"f_full_name","Own permission group "+i,"f_en_code","OWN_GROUP_"+i,"f_permission_member","[\""+id(role)+"--role\"]","f_enabled_mark",1,"f_sort_code",i+1,"f_tenant_id",""));

      insert(c,"base_module",row(module,"f_parent_id","-1","f_type",2,"f_full_name","Own module "+i,"f_en_code","OWN_MODULE_"+i,"f_category","Web","f_path","own-module-"+i,"f_url_address","own/module/"+i,"f_system_id",id(12),"f_property_json","{}","f_enabled_mark",1,"f_sort_code",i+1,"f_visible","1","f_is_button_authorize",0,"f_is_column_authorize",0,"f_is_data_authorize",0,"f_is_form_authorize",0,"f_tenant_id",""));

      insert(c,"base_authorize",row(50+i*2,"f_item_type","system","f_item_id",id(12),"f_object_type","Role","f_object_id",id(group),"f_sort_code",1,"f_tenant_id",""));

      insert(c,"base_authorize",row(51+i*2,"f_item_type","module","f_item_id",id(module),"f_object_type","Role","f_object_id",id(group),"f_sort_code",2,"f_tenant_id",""));

     }

     List<String> names=List.of("own_operator_a","own_reviewer_b","own_no_permission_c","own_disabled_d");

     for(int i=0;i<4;i++){

      int user=100+i;String salt=md5(owner+":"+user),name=names.get(i);Integer role=i==2?null:(i==1?21:20);

      insert(c,"base_user",row(user,"f_account",name,"f_real_name",name,"f_password",md5(md5(secret)+salt.toLowerCase(Locale.ROOT)),"f_secretkey",salt,"f_is_administrator",0,"f_organize_id",id(220),"f_position_id","","f_role_id",role==null?"":id(role),"f_system_id",id(12),"f_app_system_id",id(12),"f_theme","classic","f_language","zh-CN","f_portal_id","","f_group_id","","f_manager_id","","f_gender","1","f_head_icon","","f_log_success_count",0,"f_log_error_count",0,"f_enabled_mark",i==3?0:1,"f_sort_code",i+1,"f_tenant_id","","f_change_password_date",new Timestamp(System.currentTimeMillis())));

      insert(c,"base_user_relation",row(200+i,"f_user_id",id(user),"f_object_type","Organize","f_object_id",id(220),"f_sort_code",i+1,"f_tenant_id",""));

      if(role!=null)insert(c,"base_user_relation",row(210+i,"f_user_id",id(user),"f_object_type","Role","f_object_id",id(role),"f_sort_code",i+1,"f_tenant_id",""));

      accounts.put(name,Map.of("id",id(user),"roleId",role==null?"":id(role),"moduleId",i==1?id(41):i==2?"":id(40),"isAdministrator",false));

     }

     Map<String,String> settings=new TreeMap<>(Map.of("singleLogin","0","passwordErrorsNumber","5","lockType","2","lockTime","5","enableVerificationCode","0","verificationCodeNumber","4","tokenTimeout","30","lastLoginTimeSwitch","0","whitelistSwitch","0","isLog","0"));settings.putAll(Map.of("sysName","Own isolated login test","companyName","Own test organization","companyCode","OWN_TEST","sysVersion","OWN","passwordIsUpdatedRegularly","0","updateCycle","30","updateInAdvance","1","isClick","0","unClickNum","0"));int key=300;for(var setting:settings.entrySet())insert(c,"base_sys_config",row(key++,"f_full_name",setting.getKey(),"f_key",setting.getKey(),"f_value",setting.getValue(),"f_category","SysConfig","f_sort_code",key,"f_tenant_id",""));

     portal(c);c.commit();Map<String,Object> privateRequest=new TreeMap<>();privateRequest.put("schema","xnby.own-normal-login-request.v1");privateRequest.put("credentialsSynthetic",true);privateRequest.put("wirePassword",wire(secret));privateRequest.put("wrongWirePassword",wire("WRONG_"+secret));privateRequest.put("accounts",accounts);privateRequest.put("systemCode","cqweh-endanger");mapper.writeValue(root.resolve("own-normal-login.private.json").toFile(),privateRequest);

    }catch(Exception error){c.rollback();throw error;}finally{c.setAutoCommit(true);}

    Map<String,Long> counts=new TreeMap<>();for(String table:tables)counts.put(table,count(c,table));mapper.writeValue(root.resolve("normal-login-seed-result.json").toFile(),Map.of("tables",counts,"syntheticAccounts",4,"administratorAccounts",0,"realAccountsImported",false,"tokenOrSessionCreatedBySeed",false,"ownCaptchaPolicyEnabled",false,"captchaBranchAccepted",false));

   }else {

    Map<String,Object> users=new TreeMap<>();try(var p=c.prepareStatement("SELECT f_id,f_account,f_is_administrator,f_enabled_mark,f_log_error_count,f_log_success_count FROM base_user WHERE f_id IN (?,?,?,?) ORDER BY f_id")){for(int i=0;i<4;i++)p.setString(i+1,id(100+i));try(var r=p.executeQuery()){while(r.next())users.put(r.getString(2),Map.of("id",r.getString(1),"isAdministrator",r.getInt(3),"enabledMark",r.getInt(4),"errorCount",r.getInt(5),"successCount",r.getInt(6)));}}need(users.size()==4,"EXACT_OWN_LOGIN_USERS");mapper.writeValue(root.resolve("normal-login-"+mode+".json").toFile(),users);

   }

  }finally{props.remove("password");secret=null;}

  need(guard.deniedCounts().isEmpty(),"NO_LOGIN_SEED_BOUNDARY_DENIALS");System.out.println("OWN_NORMAL_LOGIN_DATA_"+mode.toUpperCase(Locale.ROOT)+"_OK");

 }

}

