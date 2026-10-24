package xnby.bigscreen;
import java.nio.file.*;
import java.util.*;
import org.springframework.boot.loader.JarLauncher;
import org.springframework.boot.loader.archive.*;

/** Original bigscreen archive/boot loader and dependency order, with owned observations appended. */
@SuppressWarnings("removal")
public final class OriginalBigscreenLaunch extends JarLauncher {
 private final Archive own;
 private OriginalBigscreenLaunch(Archive original,Archive observation){super(original);own=observation;}
 @Override protected Iterator<Archive> getClassPathArchivesIterator()throws Exception {List<Archive> paths=new ArrayList<>();super.getClassPathArchivesIterator().forEachRemaining(paths::add);paths.add(own);return paths.iterator();}
 public static void main(String[] args)throws Exception {
  if(args.length!=2)throw new IllegalArgumentException("EXPLICIT_ORIGINAL_BIGSCREEN_AND_OWN_ROOT_REQUIRED");
  final Path root=Paths.get(args[1]).toRealPath();
  final OriginalBigscreenProcessBoundary guard=new OriginalBigscreenProcessBoundary(root,Collections.<Integer>emptySet(),true);
  Runtime.getRuntime().addShutdownHook(new Thread(()->{try{Files.write(root.resolve("boundary-result.properties"),("guardStillInstalled="+(System.getSecurityManager()==guard)+"\nsqliteNativeLoads="+guard.allowedSqliteLoads()+"\ndenied="+guard.deniedCounts()+"\n").getBytes("US-ASCII"));}catch(Exception e){System.err.println("OWN_BIGSCREEN_BOUNDARY_RECEIPT_FAILED");}},"own-bigscreen-boundary-receipt"));System.setSecurityManager(guard);
  JarFileArchive original=new JarFileArchive(Paths.get(args[0]).toFile()),observation=new JarFileArchive(root.resolve("own-observation.jar").toFile());
  Files.write(root.resolve("original-main-requested.txt"),"Original HikspBaseApplication.main\n".getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);
  new OriginalBigscreenLaunch(original,observation).launch(new String[0]);
  Files.write(root.resolve("original-main-returned.txt"),"original-main-returned\n".getBytes("US-ASCII"),StandardOpenOption.CREATE_NEW);
 }
}
