package xnby.platform;

import java.nio.file.*;
import java.util.*;
import org.springframework.boot.loader.JarLauncher;
import org.springframework.boot.loader.archive.*;
import xnby.replica.OriginalProcessBoundary;

/** Original nested dependencies, own fixture main, no Spring application startup. */
@SuppressWarnings("removal")
public final class OriginalRedisWireLaunch extends JarLauncher {
    private final Archive source;
    private OriginalRedisWireLaunch(Archive source){super(source);this.source=source;}
    protected String getMainClass(){return "xnby.replica.OriginalRedisWireProbe";}
    protected ClassLoader createClassLoader(Iterator<Archive> archives)throws Exception{
        java.net.URLClassLoader original=(java.net.URLClassLoader)super.createClassLoader(archives);
        ClassLoader replacement=new OriginalResourceCachedClassLoader(source,original.getURLs(),original.getParent(),System.getProperty("own.platform.source.path"));
        original.close();return replacement;
    }
    public static void main(String[] args)throws Exception {
        if(args.length!=3)throw new IllegalArgumentException("SOURCE_ROOT_MODE_REQUIRED");
        final Path root=Paths.get(args[1]).toRealPath();
        final OriginalProcessBoundary boundary=new OriginalProcessBoundary(root,Collections.<Integer>emptySet(),false);
        Runtime.getRuntime().addShutdownHook(new Thread(new Runnable(){public void run(){try{
            Files.write(root.resolve(args[2]+"-boundary.txt"),Arrays.asList("guardInstalled="+(System.getSecurityManager()==boundary),boundary.deniedCounts().toString()),java.nio.charset.StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW);
        }catch(Exception error){throw new IllegalStateException("BOUNDARY_RECEIPT_FAILED",error);}}}));
        System.setSecurityManager(boundary);
        if(args[2].equals("business-read")){
            xnby.replica.OriginalRedisWireProbe.main(new String[]{args[2],root.toString()});return;
        }
        if(!args[2].equals("platform-write"))throw new IllegalArgumentException("UNKNOWN_MODE");
        new OriginalRedisWireLaunch(new JarFileArchive(Paths.get(args[0]).toFile())).launch(new String[]{args[2],root.toString()});
    }
}
