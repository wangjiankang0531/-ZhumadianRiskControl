import java.nio.file.*;
import java.util.*;
import java.lang.reflect.*;
import java.security.Permission;
import org.springframework.boot.loader.JarLauncher;
import org.springframework.boot.loader.archive.JarFileArchive;

@SuppressWarnings("removal")
public final class OwnOriginalPoolLayoutBinding extends JarLauncher {
  private OwnOriginalPoolLayoutBinding(Path jar)throws Exception{super(new JarFileArchive(jar.toFile()));}
  static ClassLoader loader;
  static int networkAttempts, processAttempts;
  static Class<?> cls(String n)throws Exception{return Class.forName(n,true,loader);}
  static Object call(Object target,String name,Object...args)throws Exception{
    for(Method m:target.getClass().getMethods())if(m.getName().equals(name)&&m.getParameterCount()==args.length){
      try{return m.invoke(target,args);}catch(IllegalArgumentException e){}
    }
    throw new NoSuchMethodException(name);
  }
  static void need(boolean b,String message){if(!b)throw new IllegalStateException(message);}
  static Properties read(Path p)throws Exception{Properties v=new Properties();try(var in=Files.newInputStream(p)){v.load(in);}return v;}
  static Object bind(Properties p)throws Exception{
    Map<String,Object> map=new LinkedHashMap<>();for(String k:p.stringPropertyNames())map.put(k,p.getProperty(k));
    Object source=cls("org.springframework.boot.context.properties.source.MapConfigurationPropertySource").getConstructor(Map.class).newInstance(map);
    Class<?> kind=cls("org.springframework.boot.context.properties.source.ConfigurationPropertySource");Object sources=Array.newInstance(kind,1);Array.set(sources,0,source);
    Object binder=cls("org.springframework.boot.context.properties.bind.Binder").getConstructor(sources.getClass()).newInstance(sources);
    Object result=call(binder,"bind","spring.datasource.dynamic",cls("com.baomidou.dynamic.datasource.spring.boot.autoconfigure.DynamicDataSourceProperties"));return call(result,"get");
  }
  static Object generated(Object properties)throws Exception{
    Class<?> util=cls("jnpf.database.util.DynamicDataSourceUtil");Field global=util.getDeclaredField("dynamicDataSourceProperties");global.setAccessible(true);global.set(null,properties);
    Object data=cls("jnpf.database.util.DataSourceUtil").getConstructor().newInstance();
    call(data,"setDbType","MySQL");call(data,"setHost","127.0.0.1");call(data,"setPort",9);call(data,"setDbName","own_layout");call(data,"setUserName","own-layout");call(data,"setPassword",UUID.randomUUID().toString());
    return util.getMethod("createDataSourceProperty",cls("jnpf.database.util.DataSourceUtil"),String.class).invoke(null,data,"jdbc:mysql://127.0.0.1:9/own_layout");
  }
  public static void main(String[] a)throws Exception{
    need(a.length==3,"EXACT_PROGRAM_FIXTURES_OUTPUT_REQUIRED");Path jar=Path.of(a[0]).toRealPath(),root=Path.of(a[1]).toRealPath(),output=Path.of(a[2]).toAbsolutePath();need(!Files.exists(output),"FRESH_PROOF_REQUIRED");
    Path log=root.resolve("own-logback.xml");Files.writeString(log,"<configuration><root level=\"OFF\"/></configuration>");System.setProperty("logback.configurationFile",log.toString());
    System.setSecurityManager(new SecurityManager(){
      public void checkPermission(Permission p){}
      public void checkConnect(String h,int p){networkAttempts++;throw new SecurityException("NO_NETWORK_IN_BINDING_PROBE");}
      public void checkConnect(String h,int p,Object c){checkConnect(h,p);}
      public void checkListen(int p){networkAttempts++;throw new SecurityException("NO_LISTEN_IN_BINDING_PROBE");}
      public void checkExec(String p){processAttempts++;throw new SecurityException("NO_PROCESS_IN_BINDING_PROBE");}
    });
    org.springframework.boot.loader.jar.JarFile.registerUrlProtocolHandler();OwnOriginalPoolLayoutBinding probe=new OwnOriginalPoolLayoutBinding(jar);loader=probe.createClassLoader(probe.getClassPathArchivesIterator());Thread.currentThread().setContextClassLoader(loader);
    Class<?> propertyClass=cls("com.baomidou.dynamic.datasource.creator.DataSourceProperty"),propertiesClass=cls("com.baomidou.dynamic.datasource.spring.boot.autoconfigure.DynamicDataSourceProperties");
    need("master".equals(call(propertiesClass.getConstructor().newInstance(),"getPrimary")),"ORIGINAL_DEFAULT_PRIMARY_CHANGED");
    Method predicate=cls("jnpf.database.config.MybatisPlusConfig").getDeclaredMethod("lambda$initDynamicDataSource$1",propertiesClass,Map.Entry.class);predicate.setAccessible(true);
    int cases=0,pools=0;List<String> passed=new ArrayList<>();
    for(String name:List.of("generated","extra","group","alias","native-override","declared-override")){
      Object properties=bind(read(root.resolve(name+".properties")));Properties expected=read(root.resolve(name+".expected.properties"));
      Map<?,?> declared=(Map<?,?>)call(properties,"getDatasource");boolean covered=false;for(Map.Entry<?,?>entry:declared.entrySet())covered|=(Boolean)predicate.invoke(null,properties,entry);
      boolean implicit=Boolean.parseBoolean(expected.getProperty("generated"));need(covered!=implicit,"ORIGINAL_PRIMARY_SELECTION_DIFFERS");
      Map<String,Object> actual=new LinkedHashMap<>();for(var entry:declared.entrySet())actual.put(String.valueOf(entry.getKey()),entry.getValue());
      if(implicit)actual.put((String)call(properties,"getPrimary"),generated(properties));
      need(actual.size()==Integer.parseInt(expected.getProperty("count")),"ORIGINAL_POOL_COUNT_DIFFERS");
      Object global=call(properties,"getHikari");Object creator=cls("com.baomidou.dynamic.datasource.creator.hikaricp.HikariDataSourceCreator").getConstructor(global.getClass()).newInstance(global);
      for(var entry:actual.entrySet()){
        String n=entry.getKey();Object property=entry.getValue();call(property,"setLazy",true);call(property,"setPoolName","OWN_LAYOUT_"+name.replace('-','_')+"_"+n);
        Object pool=creator.getClass().getMethod("createDataSource",propertyClass).invoke(creator,property);
        try{
          need(!(Boolean)call(pool,"isRunning")&&call(pool,"getHikariPoolMXBean")==null,"UNEXPECTED_POOL_STARTED");
          need(((Number)call(pool,"getMaximumPoolSize")).intValue()==Integer.parseInt(expected.getProperty(n+".maximum")),"ACTUAL_MAXIMUM_DIFFERS");
          need(((Number)call(pool,"getMinimumIdle")).intValue()==Integer.parseInt(expected.getProperty(n+".minimum")),"ACTUAL_MINIMUM_DIFFERS");
          need(((Number)call(pool,"getConnectionTimeout")).intValue()==Integer.parseInt(expected.getProperty(n+".timeout")),"ACTUAL_TIMEOUT_DIFFERS");pools++;
        }finally{call(pool,"close");}
      }
      cases++;passed.add(name);
    }
    need(networkAttempts==0&&processAttempts==0,"UNEXPECTED_EXTERNAL_ACTIVITY");
    Files.writeString(output,"{\"allPassed\":true,\"originalLayoutCases\":"+cases+",\"actualLazyPools\":"+pools+",\"originalJNPFPrimaryPredicateUsed\":true,\"originalGeneratedDataSourcePropertyUsed\":true,\"originalSpringBinderAndHikariCreatorUsed\":true,\"networkAttempts\":"+networkAttempts+",\"processAttempts\":"+processAttempts+",\"noDatabaseConnections\":true}\n");
    System.out.println("ORIGINAL_POOL_LAYOUT_BINDING_PASSED:"+cases+":"+pools);
  }
}
