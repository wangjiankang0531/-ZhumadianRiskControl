import java.io.*;import java.nio.file.*;import java.sql.*;import java.util.*;
/** Temporarily hide three exact synthetic menu modules, without changing accounts or roles. */
public final class OwnPersonalWorkflowMenuVisibilityR206 {
 static String id(int n){return "a531"+String.format("%028x",n);}
 static void need(boolean v)throws Exception{if(!v)throw new Exception("OWN_PERSONAL_MENU_VISIBILITY_SCOPE_REJECTED");}
 public static void main(String[]a)throws Exception{
  need(a.length==5&&Set.of("hide","restore").contains(a[3]));Path data=Path.of(a[2]).toRealPath(),root=Path.of(a[4]).toRealPath();need(data.toString().replace('\\','/').equals("D:/Project/Zhumadian/_g/Application/UserData/OriginalServer/database/data")&&!Files.exists(data.getParent().getParent().getParent().getParent().getParent().resolve("user-manual-protected.json")));
  need(root.getParent().toString().replace('\\','/').equals("D:/Project/Zhumadian/work/event_delivery_consistency_20261030/full-controller-r163")&&root.getFileName().toString().matches("r103"));Path scope=root.resolve("own-menu-visibility-scope.private.txt");String password=new BufferedReader(new InputStreamReader(System.in)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"));
  try(Connection c=DriverManager.getConnection("jdbc:mysql://127.0.0.1:"+Integer.parseInt(a[0])+"/jnpf?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=15000","root",password)){
   password=null;try(Statement s=c.createStatement();ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir")){need(r.next()&&a[1].equals(r.getString(1))&&data.equals(Path.of(r.getString(2)).toRealPath()));}
   c.setAutoCommit(false);int[] modules={1600,1601,1602};
   for(int n:modules)try(PreparedStatement p=c.prepareStatement("SELECT f_en_code,f_path,f_enabled_mark FROM base_module WHERE f_id=? FOR UPDATE")){p.setString(1,id(n));try(ResultSet r=p.executeQuery()){need(r.next());need((n==1600?"OWN_WORKFLOW_ROOT":"OWN_WORKFLOW_"+n).equals(r.getString(1)));need((n==1600?"/workflow":n==1601?"/workflow/flowTodo":"/workflow/startWithMeTwo").equals(r.getString(2)));int value=r.getInt(3);need(!r.wasNull()&&(a[3].equals("hide")?value==1:value==0||value==1));need(!r.next());}}
   String expected="own.synthetic.menu.visibility.v1\n1600=1\n1601=1\n1602=1\n";
   if(a[3].equals("hide")){need(!Files.exists(scope));Files.writeString(scope,expected,StandardOpenOption.CREATE_NEW);}else need(Files.readString(scope).equals(expected));
   try(PreparedStatement p=c.prepareStatement("UPDATE base_module SET f_enabled_mark=? WHERE f_id=?")){for(int n:modules){p.setInt(1,a[3].equals("hide")?0:1);p.setString(2,id(n));need(p.executeUpdate()==1);}}
   c.commit();String result="{\"passed\":true,\"mode\":\""+a[3]+"\",\"exactSyntheticModules\":3,\"accountRoleOrGrantRowsChanged\":false}";Files.writeString(root.resolve("own-menu-visibility-"+a[3]+".json"),result+"\n");System.out.println(result);
  }
 }
}
