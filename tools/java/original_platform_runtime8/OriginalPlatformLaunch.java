package xnby.platform;
import xnby.compat.Java8IO;
import org.springframework.boot.loader.JarLauncher;
import org.springframework.boot.loader.archive.*;
import java.nio.file.*;
import java.util.*;
import xnby.replica.OriginalProcessBoundary;

/** Preserve original archive and nested dependency order; append only own observation classes. */
@SuppressWarnings("removal")
public final class OriginalPlatformLaunch extends JarLauncher{
 private final Archive observation;
 private final Archive sourceArchive;
 private OriginalPlatformLaunch(Archive source,Archive observation){super(source);this.sourceArchive=source;this.observation=observation;}
 @Override protected Iterator<Archive> getClassPathArchivesIterator()throws Exception{
  List<Archive> paths=new ArrayList<>();super.getClassPathArchivesIterator().forEachRemaining(paths::add);paths.add(observation);return paths.iterator();
 }
 @Override protected ClassLoader createClassLoader(Iterator<Archive> archives)throws Exception{
  ClassLoader loader=super.createClassLoader(archives);
  if(Boolean.getBoolean("own.platform.cached.resources")){
   java.net.URLClassLoader original=(java.net.URLClassLoader)loader;
   loader=new OriginalResourceCachedClassLoader(sourceArchive,original.getURLs(),original.getParent(),System.getProperty("own.platform.source.path"));
   original.close();
  }
  if(Boolean.getBoolean("own.platform.preflight")){
   ClassLoader previous=Thread.currentThread().getContextClassLoader();Thread.currentThread().setContextClassLoader(loader);
   try{
    loader.loadClass("xnby.audit.SourceClasspathProbe").getMethod("main",String[].class).invoke(null,(Object)new String[]{System.getProperty("own.platform.preflight.spec"),Paths.get(System.getProperty("own.platform.root")).resolve("pre-main-classpath-result.tsv").toString()});
   }finally{Thread.currentThread().setContextClassLoader(previous);}
  }
  return loader;
 }
 private void probeOnly(Path root)throws Exception{
  org.springframework.boot.loader.jar.JarFile.registerUrlProtocolHandler();
  List<Archive> archives=new ArrayList<>();getClassPathArchivesIterator().forEachRemaining(archives::add);
  ClassLoader loader=createClassLoader(archives.iterator());List<String> rows=new ArrayList<>();
  if(Boolean.getBoolean("own.platform.metadata.probe"))loader.loadClass("xnby.platform.PlatformJava8MetadataProbe").getMethod("run",Path.class).invoke(null,root);
  rows.add("loader\t"+loader.getClass().getName());rows.add("archiveCount\t"+archives.size());
  for(String spec:Files.readAllLines(root.resolve("class-probe-expected.tsv"))){
   String[] parts=spec.split("\\t");String name=parts[0];java.net.URL resource=loader.getResource(name);
   String status="RESOURCE_MISSING";
   if(resource!=null){
    byte[] bytes;try(java.io.InputStream input=resource.openStream()){bytes=xnby.compat.Java8IO.readAllBytes(input);}
    String hash=xnby.compat.Java8IO.hex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));
    if(!hash.equals(parts[1]))status="HASH_MISMATCH";
    else try{Class<?> type=Class.forName(name.substring(0,name.length()-6).replace('/','.'),false,loader);type.getDeclaredMethods();type.getDeclaredConstructors();type.getDeclaredFields();status="PASS";}
    catch(Throwable error){status=error.getClass().getName();}
   }
   rows.add(name+"\t"+status+"\t"+(resource==null?"":resource.toExternalForm()));
  }
  Files.write(root.resolve("actual-launcher-class-probe.tsv"),rows,StandardOpenOption.CREATE_NEW);
 }
 public static void main(String[] args)throws Exception{
  Path root=Paths.get(args[1]).toRealPath();Set<Integer> ports=new HashSet<>();for(String value:System.getProperty("own.allowed.loopback.ports").split(","))ports.add(Integer.parseInt(value));
  if(ports.size()!=2||ports.stream().anyMatch(p->p<1024||p>65535))throw new IllegalArgumentException("OWN_PORT_SCOPE");
  OriginalProcessBoundary guard=new OriginalProcessBoundary(root,ports,true);
  Runtime.getRuntime().addShutdownHook(new Thread(()->{try{Java8IO.writeString(root.resolve("process-boundary-result.txt"),guard.deniedCounts().toString()+"\n");}catch(Exception e){System.err.println("OWN_BOUNDARY_RECEIPT_FAILED");}}));
  System.setSecurityManager(guard);
  JarFileArchive source=new JarFileArchive(Paths.get(args[0]).toFile());JarFileArchive observation=new JarFileArchive(root.resolve("own-platform-observation.jar").toFile());
  // Archive lifetime follows the JVM, as in the original launcher. Closing from a
  // parallel shutdown hook can race Spring's shutdown-time class loading.
  if(Boolean.getBoolean("own.platform.probe.only")){new OriginalPlatformLaunch(source,observation).probeOnly(root);return;}
  Java8IO.writeString(root.resolve("original-platform-main-requested.txt"),"Original JarLauncher and original JnpfAdminApplication.main\n",StandardOpenOption.CREATE_NEW);
  new OriginalPlatformLaunch(source,observation).launch(new String[0]);
  Java8IO.writeString(root.resolve("original-platform-main-returned.txt"),"Original main returned\n",StandardOpenOption.CREATE_NEW);
 }
}
