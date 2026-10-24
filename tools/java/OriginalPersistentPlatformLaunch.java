package xnby.platform;
import java.nio.file.*;
import java.util.*;
import org.springframework.boot.loader.JarLauncher;
import org.springframework.boot.loader.archive.*;
import xnby.replica.OriginalProcessBoundary;

/** Original archive/dependency order and cached resources; explicit owned persistent storage scope. */
@SuppressWarnings("removal")
public final class OriginalPersistentPlatformLaunch extends JarLauncher {
 private final Archive source,observation;
 private OriginalPersistentPlatformLaunch(Archive source,Archive observation){super(source);this.source=source;this.observation=observation;}
 @Override protected Iterator<Archive> getClassPathArchivesIterator()throws Exception {List<Archive> paths=new ArrayList<>();super.getClassPathArchivesIterator().forEachRemaining(paths::add);paths.add(observation);return paths.iterator();}
 @Override protected ClassLoader createClassLoader(Iterator<Archive> archives)throws Exception {
  java.net.URLClassLoader original=(java.net.URLClassLoader)super.createClassLoader(archives);
  ClassLoader cached=new OriginalResourceCachedClassLoader(source,original.getURLs(),original.getParent(),System.getProperty("own.platform.source.path"));original.close();return cached;
 }
 public static void main(String[] args)throws Exception {
  if(args.length!=2)throw new IllegalArgumentException("EXPLICIT_ORIGINAL_ARCHIVE_AND_PLATFORM_RUNTIME_REQUIRED");
  final Path supplied=Paths.get(args[1]).toAbsolutePath().normalize();OriginalPlatformStorageScope.Scope scope=OriginalPlatformStorageScope.resolve(supplied,Paths.get(System.getProperty("own.platform.data.root")),System.getProperty("own.platform.data.owner"),System.getProperty("own.allowed.loopback.ports"),System.getProperty("own.expected.database.port"),System.getProperty("own.expected.redis.port"),System.getProperty("own.internal.object-store.base"));final Path root=supplied.toRealPath();
  final OriginalProcessBoundary guard=new OriginalProcessBoundary(scope.writeRoot,scope.ports,true);
  Runtime.getRuntime().addShutdownHook(new Thread(()->{try{Files.write(root.resolve("process-boundary-result.txt"),("guardStillInstalled="+(System.getSecurityManager()==guard)+"\n"+guard.deniedCounts()+"\n").getBytes("UTF-8"));}catch(Exception e){System.err.println("OWN_PERSISTENT_PLATFORM_BOUNDARY_RECEIPT_FAILED");}},"own-platform-boundary-receipt"));System.setSecurityManager(guard);
  JarFileArchive source=new JarFileArchive(Paths.get(args[0]).toFile()),observation=new JarFileArchive(root.resolve("own-platform-observation.jar").toFile());
  Files.write(root.resolve("original-platform-main-requested.txt"),"Original JnpfAdminApplication.main\n".getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);
  new OriginalPersistentPlatformLaunch(source,observation).launch(new String[0]);
  Files.write(root.resolve("original-platform-main-returned.txt"),"Original main returned\n".getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);
 }
}
