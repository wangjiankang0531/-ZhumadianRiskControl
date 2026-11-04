import java.io.*;
import java.lang.reflect.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.sql.*;
import java.util.*;
import org.springframework.boot.loader.JarLauncher;
import org.springframework.boot.loader.archive.JarFileArchive;

/** Existing owned G only. No service launch, adoption, account/permission write,
 * DDL, public host, raw configuration output or retry of an issued mutation.
 */
@SuppressWarnings({"unchecked","removal"})
public final class OwnOriginalCallbackRuntimeR770 extends JarLauncher{
    static final Path APP=Path.of("D:/Project/Zhumadian/_g/Application");
    static final Path ROOT=Path.of("D:/Project/Zhumadian/work/original-manager-full-lifecycle-r609");
    static final Path ATTEMPT=stagePath();
    static Path stagePath(){String s=System.getProperty("xnby.owned.manager.stage","");if(!Set.of("first-start","normal-restart","after-submit-r889").contains(s))throw new IllegalStateException("EXACT_MANAGER_STAGE_REQUIRED");return ROOT.resolve("feedback-r880").resolve(s);}
    static final Path DATA=APP.resolve("UserData/OriginalServer/database/data");
    static final Path DEFINITIONS=Path.of("D:/Project/Zhumadian/work/original-manager-http-definitions-r615/native-definitions.private.json");
    static final Path GRAPHS=Path.of("D:/Project/Zhumadian/work/original-manager-graph-r466/clone-graphs.private.json");
    static final Path SNAPSHOT=Path.of("D:/Project/Zhumadian/work/callback-config-read-r654/original-callback-configs.private.json");
    static Class<?> json;
    OwnOriginalCallbackRuntimeR770(File f)throws Exception{super(new JarFileArchive(f));}
    ClassLoader loader()throws Exception{return createClassLoader(getClassPathArchivesIterator());}
    static void need(boolean b,String s){if(!b)throw new IllegalStateException(s);}
    static boolean hash(String s){return s!=null&&s.matches("[0-9a-f]{64}");}
    static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    static String sha(Path p)throws Exception{
        MessageDigest d=MessageDigest.getInstance("SHA-256");try(InputStream in=Files.newInputStream(p)){byte[] b=new byte[65536];for(int n;(n=in.read(b))!=-1;)d.update(b,0,n);}return HexFormat.of().formatHex(d.digest());
    }
    static Path plain(Path p)throws Exception{
        need(p.isAbsolute()&&p.normalize().equals(p),"NORMAL_ABSOLUTE_OWN_RUNTIME_PATH_REQUIRED");
        for(Path q=p;q!=null;q=q.getParent())if(Files.exists(q))need(!Files.isSymbolicLink(q)&&q.toRealPath().equals(q),"OWN_RUNTIME_LINK_REFUSED");return p;
    }
    static void marker()throws Exception{
        plain(APP);plain(ATTEMPT);need(Files.readString(ROOT.resolve("own-normal-manager-test.marker")).equals("own-original-manager-full-lifecycle-r609\n"),"ORIGINAL_FULL_PARENT_MARKER_REQUIRED");need(Files.isDirectory(ATTEMPT),"FULL_MANAGER_ATTEMPT_MARKER_REQUIRED");
        Path p=plain(ATTEMPT.resolve("own-normal-manager-test.marker"));
        need(Files.isRegularFile(p)&&Files.readString(p,StandardCharsets.US_ASCII).equals("own-original-manager-full-lifecycle-r609\n"),"FULL_MANAGER_ATTEMPT_MARKER_REQUIRED");
        need(!Files.exists(APP.getParent().resolve("user-manual-protected.json")),"PROTECTED_G_FIXTURE_REFUSED");
    }
    static Object parse(String s)throws Exception{return json.getMethod("parse",String.class).invoke(null,s);}
    static Map<String,Object> object(Object v){need(v instanceof Map<?,?>,"EXPLICIT_RUNTIME_OBJECT_REQUIRED");return (Map<String,Object>)v;}
    static Map<String,Object> file(Path p)throws Exception{plain(p);need(Files.isRegularFile(p)&&Files.size(p)<1048576,"BOUNDED_RUNTIME_JSON_FILE_REQUIRED");return object(parse(Files.readString(p,StandardCharsets.UTF_8)));}
    static String text(Map<String,Object>m,String k){Object v=m.get(k);need(v instanceof String,"EXPLICIT_RUNTIME_STRING_REQUIRED");return (String)v;}
    static long number(Map<String,Object>m,String k){Object v=m.get(k);need(v instanceof Number,"EXPLICIT_RUNTIME_NUMBER_REQUIRED");long n=((Number)v).longValue();need(((Number)v).doubleValue()==n,"INTEGER_RUNTIME_VALUE_REQUIRED");return n;}
    static int port(Map<String,Object>m,String k){long n=number(m,k);need(n>1024&&n<65536&&!Set.of(8767L,18891L,18892L).contains(n),"NONRESERVED_OWN_RUNTIME_PORT_REQUIRED");return (int)n;}
    static final class Boundary extends SecurityManager{
        final int port;Boundary(int p){port=p;}
        public void checkPermission(Permission p){}
        public void checkConnect(String h,int p){if("127.0.0.1".equals(h)&&(p==port||p==-1))return;throw new SecurityException("ONLY_DECLARED_OWN_JDBC_PORT");}
        public void checkConnect(String h,int p,Object c){checkConnect(h,p);}
        public void checkListen(int p){throw new SecurityException("NO_CALLBACK_RUNTIME_LISTEN");}
        public void checkExec(String s){throw new SecurityException("NO_CALLBACK_RUNTIME_EXEC");}
    }
    static ProcessHandle process(long pid,Path image,long parent)throws Exception{
        ProcessHandle h=ProcessHandle.of(pid).orElseThrow(()->new IllegalStateException("DECLARED_OWN_PROCESS_MISSING"));
        need(h.isAlive()&&h.info().command().isPresent()&&Path.of(h.info().command().get()).toRealPath().equals(image.toRealPath()),"DECLARED_OWN_PROCESS_IMAGE_MISMATCH");
        if(parent>0)need(h.parent().isPresent()&&h.parent().get().pid()==parent,"OWN_CHILD_PARENT_MISMATCH");return h;
    }
    static void runtime(Map<String,Object>p,Path plan,String pin)throws Exception{
        marker();need(sha(plan).equals(pin),"RUNTIME_PLAN_DRIFT");
        need(text(p,"schema").equals("xnby.owned-original-callback-plan.r662.v1")&&text(p,"application").equals(APP.toString())&&text(p,"attempt").equals(ATTEMPT.toString())&&Boolean.TRUE.equals(p.get("onlyOwnedRuntimeFixture")),"EXACT_OWN_CALLBACK_PLAN_REQUIRED");
        need(Boolean.TRUE.equals(file(APP.getParent().resolve("own-fixture.json")).get("ownedSyntheticFixtureOnly")),"ONLY_SYNTHETIC_G_FIXTURE");
        String release=text(p,"releaseSHA256");need(hash(release)&&sha(APP.resolve("release-manifest.json")).equals(release),"OWN_CANDIDATE_RELEASE_DRIFT");
        Path pointer=plain(APP.resolve("UserData/OriginalServer/current-run.json"));need(sha(pointer).equals(text(p,"currentRunSHA256")),"OWN_READY_POINTER_DRIFT");
        Map<String,Object>row=file(pointer);long pid=number(p,"controllerPID");need(number(row,"controllerPID")==pid&&Boolean.TRUE.equals(row.get("ready"))&&Boolean.TRUE.equals(row.get("persistent"))&&Boolean.TRUE.equals(row.get("callbackProjectionEnabled")),"EXACT_READY_CALLBACK_CONTROLLER_REQUIRED");
        for(String k:List.of("databasePort","businessPort","gatewayPort"))need(port(p,k)==port(row,k),"OWN_READY_PORT_DRIFT");
        need(port(p,"databasePort")!=port(p,"businessPort")&&port(p,"gatewayPort")!=port(p,"businessPort"),"DISTINCT_OWN_COMPONENT_PORTS_REQUIRED");
        String uuid=text(p,"databaseUUID");need(UUID.fromString(uuid).toString().equals(uuid)&&uuid.equals(text(row,"databaseUUID"))&&uuid.equals(text(file(APP.resolve("UserData/OriginalServer/installation.json")),"databaseUUID")),"OWN_DATABASE_UUID_DRIFT");
        Path run=plain(Path.of(text(row,"run")));need(run.getParent().equals(APP.resolve("UserData/OriginalServer/runs"))&&run.getFileName().toString().matches("j[1-9][0-9]{0,3}"),"EXACT_G_RUNTIME_DIRECTORY_REQUIRED");
        ProcessHandle owner=process(pid,APP.resolve("runtime/python/python.exe"),0);List<String>args=OwnedWindowsProcessArgumentsR747.verified(owner,object(p.get("controllerWindowsIdentity")));
        int releaseArg=args.indexOf("--release-manifest-sha256"),appArg=args.indexOf("--application");
        need(args.contains(APP.resolve("tools/serve_original_server_release.py").toString())&&Collections.frequency(args,"--release-manifest-sha256")==1&&releaseArg>=0&&releaseArg+1<args.size()&&release.equals(args.get(releaseArg+1))
             &&Collections.frequency(args,"--application")==1&&appArg>=0&&appArg+1<args.size()&&Path.of(args.get(appArg+1)).equals(APP),"EXACT_G_CONTROLLER_ARGUMENTS_REQUIRED");
        Map<String,Object>children=object(row.get("children"));process(number(children,"mysql"),APP.resolve("runtime/mysql/bin/mysqld.exe"),pid);process(number(children,"business"),APP.resolve("runtime/jdk17/bin/java.exe"),pid);
    }
    static List<OwnedOriginalCallbacksR648.Row> rows(Object value)throws Exception{
        need(value instanceof List<?> && ((List<?>)value).size()==2,"EXACT_TWO_RUNTIME_CALLBACK_ROWS_REQUIRED");List<OwnedOriginalCallbacksR648.Row>out=new ArrayList<>();
        for(Object row:(List<?>)value){need(row instanceof List<?> && ((List<?>)row).size()==17,"EXACT_SEVENTEEN_CALLBACK_FIELDS_REQUIRED");List<String>v=new ArrayList<>();for(Object x:(List<?>)row){need(x==null||x instanceof String,"ONLY_PINNED_CALLBACK_STRING_OR_NULL_VALUES");v.add((String)x);}out.add(new OwnedOriginalCallbacksR648.Row(v));}
        OwnedOriginalCallbacksR648.checked(out);return out;
    }
    static void originalRows(List<OwnedOriginalCallbacksR648.Row>rows,int businessPort)throws Exception{
        need(sha(DEFINITIONS).equals("539b57deffd8710dc633cd401f81898440d82ff5e7b7f8f1cbfe86cc55595660")&&sha(GRAPHS).equals("14854a91ca1541548b5a3dde89ee6d128a81151451bb8417fbed223070a2948f")&&sha(SNAPSHOT).equals("232fb979bcf834c4c596adc297a328b0f251e875b54527be9a7eddb1df760d9f"),"PINNED_ORIGINAL_CALLBACK_INPUT_DRIFT");
        Map<String,Object>defs=file(DEFINITIONS),graphs=file(GRAPHS),snapshot=file(SNAPSHOT);Set<String> matched=new HashSet<>();
        for(var row:rows){
            Map<String,Object>d=null,g=null,source=null;
            for(Object x:(List<?>)defs.get("definitions"))if(row.id().equals(object(x).get("interfaceId")))d=object(x);
            need(d!=null,"CALLBACK_ID_NOT_FROM_ORIGINAL_TWO_DEFINITIONS");String code=text(d,"code");need(Set.of("tj_eventInfo","tj_eventTask").contains(code)&&matched.add(code),"TWO_DISTINCT_ORIGINAL_CALLBACK_CODES_REQUIRED");
            for(Object x:(List<?>)graphs.get("graphs"))if(code.equals(object(x).get("code")))g=object(x);need(g!=null,"ORIGINAL_CALLBACK_GRAPH_REQUIRED");
            Map<String,Object>graph=object(g.get("originalGraph"));String originalId=text(object(object(object(graph.get("childNode")).get("properties")).get("approveFuncConfig")),"interfaceId");
            for(Object x:(List<?>)snapshot.get("sourceCallbackRows"))if(originalId.equals(object(x).get("f_id")))source=object(x);need(source!=null,"EXACT_ORIGINAL_CALLBACK_SOURCE_REQUIRED");
            for(int i=0;i<17;i++)if(i!=0&&i!=1&&i!=5)need(Objects.equals(row.values().get(i),source.get(OwnedOriginalCallbacksR648.COLUMNS.get(i))),"ORIGINAL_CALLBACK_FIELD_CHANGED");
            Map<String,Object>expected=object(parse(text(source,"f_data_config_json")));Map<String,Object>api=object(expected.get("apiData"));String path="/"+(code.equals("tj_eventTask")?"eventTask":"eventInfo")+"/callback";
            need(api.get("url").equals("http://risk-server:20111"+path),"EXACT_ORIGINAL_CALLBACK_PATH_REQUIRED");api.put("url","http://127.0.0.1:"+businessPort+path);
            need(expected.equals(object(parse(row.config()))),"ONLY_CALLBACK_RUNTIME_ORIGIN_MAY_CHANGE");
        }need(matched.size()==2,"BOTH_ORIGINAL_CALLBACKS_REQUIRED");
    }
    static void database(Connection c,Map<String,Object>p)throws Exception{
        try(Statement s=c.createStatement()){
            s.setQueryTimeout(10);try(ResultSet r=s.executeQuery("SELECT @@server_uuid,@@datadir,@@port,DATABASE()")){
                need(r.next()&&text(p,"databaseUUID").equals(r.getString(1))&&Path.of(r.getString(2)).toRealPath().equals(DATA.toRealPath())&&port(p,"databasePort")==r.getInt(3)&&"jnpf".equals(r.getString(4)),"EXACT_LIVE_G_DATABASE_REQUIRED");
            }
            try(ResultSet r=s.executeQuery("SHOW CREATE TABLE base_data_interface")){need(r.next()&&sha(r.getString(2).getBytes(StandardCharsets.UTF_8)).equals("2017fb45f8b05f298501dd2a6f8b9f7b483bbc2f8fee0132e83890f5c7b26d10"),"ORIGINAL_PERSISTENT_CALLBACK_DDL_REQUIRED");}
        }
    }
    public static void main(String[]args)throws Exception{
        need(args.length==4&&Set.of("inspect","apply","verify-only").contains(args[0])&&Set.of("first-start","normal-restart").contains(args[1])&&hash(args[3]),"EXACT_CALLBACK_RUNTIME_ARGUMENTS_REQUIRED");
        marker();Path plan=plain(Path.of(args[2]));need(plan.equals(ATTEMPT.resolve("callback-"+args[1]+"-plan.private.json"))&&sha(plan).equals(args[3]),"EXACT_STAGE_CALLBACK_PLAN_REQUIRED");
        int dbport=Integer.getInteger("xnby.own.callback.port",-1);need(dbport>1024&&dbport<65536&&!Set.of(8767,18891,18892).contains(dbport),"DECLARED_OWN_CALLBACK_DB_PORT_REQUIRED");System.setSecurityManager(new Boundary(dbport));
        Path platform=APP.resolve("payload/platform/original-platform.jar");need(sha(platform).equals("294f809b830374656f8100b3fb6091387d619ff8d7ecf8685e7c61788843eda8"),"ORIGINAL_PLATFORM_PARSER_PIN_REQUIRED");
        org.springframework.boot.loader.jar.JarFile.registerUrlProtocolHandler();ClassLoader loader=new OwnOriginalCallbackRuntimeR770(platform.toFile()).loader();Thread.currentThread().setContextClassLoader(loader);
        Class<?> pc=loader.loadClass("com.alibaba.fastjson.parser.ParserConfig");pc.getMethod("setSafeMode",boolean.class).invoke(pc.getMethod("getGlobalInstance").invoke(null),true);json=loader.loadClass("com.alibaba.fastjson.JSON");
        Map<String,Object>p=file(plan);need(args[1].equals(text(p,"stage"))&&port(p,"databasePort")==dbport,"CALLBACK_PLAN_STAGE_AND_PORT_REQUIRED");runtime(p,plan,args[3]);
        var after=rows(p.get("afterRows"));List<OwnedOriginalCallbacksR648.Row>before=p.get("beforeRows")==null?null:rows(p.get("beforeRows"));originalRows(after,port(p,"businessPort"));
        if(before!=null)originalRows(before,port(p,"previousBusinessPort"));
        var binding=new OwnedCallbackProvisioningJournalR658.Binding(text(p,"attemptId"),text(p,"databaseUUID"),DATA.toString(),text(p,"releaseSHA256"),number(p,"controllerPID"),args[3],before==null?null:OwnedOriginalCallbackProvisioningR659.rowsSHA256(before),OwnedOriginalCallbackProvisioningR659.rowsSHA256(after),args[1]);
        var journal=new OwnedCallbackProvisioningJournalR658(ATTEMPT.resolve("callback-"+args[1]+"-journal.private.properties"),binding);
        String password=new BufferedReader(new InputStreamReader(System.in,StandardCharsets.US_ASCII)).readLine();need(password!=null&&password.matches("[0-9a-f]{32}"),"ONLY_OWN_STDIN_DATABASE_CREDENTIAL");
        Properties properties=new Properties();properties.setProperty("user","root");properties.setProperty("password",password);properties.setProperty("useSSL","false");properties.setProperty("allowPublicKeyRetrieval","true");properties.setProperty("allowMultiQueries","false");properties.setProperty("autoReconnect","false");properties.setProperty("connectTimeout","5000");properties.setProperty("socketTimeout","15000");password=null;
        Driver driver=(Driver)loader.loadClass("com.mysql.cj.jdbc.Driver").getDeclaredConstructor().newInstance();
        try(Connection c=driver.connect("jdbc:mysql://127.0.0.1:"+dbport+"/jnpf",properties)){
            properties.remove("password");need(c!=null,"OWN_JDBC_CONNECTION_REQUIRED");c.setAutoCommit(false);
            OwnedOriginalCallbackProvisioningR659.IdentityCheck identity=()->{runtime(p,plan,args[3]);database(c,p);};
            try{
                if(args[0].equals("inspect")){identity.requireActualOwnedIdentity();journal.requireUnused();if(before==null)OwnedOriginalCallbacksR648.requireAbsent(c,after);else OwnedOriginalCallbacksR648.requireMatched(c,before);c.rollback();}
                else if(args[0].equals("apply"))OwnedOriginalCallbackProvisioningR659.apply(c,before,after,journal,identity);
                else OwnedOriginalCallbackProvisioningR659.verifyOnly(c,after,journal,identity);
            }catch(Exception e){c.rollback();throw e;}
        }finally{properties.remove("password");}
        System.out.println("OWN_G_CALLBACK_"+args[0].toUpperCase(Locale.ROOT).replace('-','_')+"_MATCHED");
    }
}
