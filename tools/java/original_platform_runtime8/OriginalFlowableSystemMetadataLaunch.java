package xnby.platform;
import java.nio.file.*;import java.util.*;import java.net.*;import org.springframework.boot.loader.JarLauncher;import org.springframework.boot.loader.archive.*;import xnby.replica.OriginalProcessBoundary;
/** Use the exact original nested library order for an isolated native-engine system preparation, without starting Jnpf main. */
public final class OriginalFlowableSystemMetadataLaunch extends JarLauncher {
 final Archive source,helper;OriginalFlowableSystemMetadataLaunch(Archive source,Archive helper){super(source);this.source=source;this.helper=helper;}
 @Override protected Iterator<Archive> getClassPathArchivesIterator()throws Exception {List<Archive> a=new ArrayList<>();super.getClassPathArchivesIterator().forEachRemaining(a::add);a.add(helper);return a.iterator();}
 @Override protected ClassLoader createClassLoader(Iterator<Archive> archives)throws Exception {URLClassLoader original=(URLClassLoader)super.createClassLoader(archives);ClassLoader cached=new OriginalResourceCachedClassLoader(source,original.getURLs(),original.getParent(),System.getProperty("own.platform.source.path"));original.close();return cached;}
 @Override protected String getMainClass(){return "xnby.platform.OriginalFlowableSystemMetadataFixture";}
 public static void main(String[] a)throws Exception {if(a.length!=6)throw new IllegalArgumentException("OWN_NATIVE_LAUNCH_ARGS");Path root=Paths.get(a[2]).toRealPath();System.setSecurityManager(new OriginalProcessBoundary(root,Collections.singleton(Integer.parseInt(a[3])),false));new OriginalFlowableSystemMetadataLaunch(new JarFileArchive(Paths.get(a[0]).toFile()),new JarFileArchive(Paths.get(a[1]).toFile())).launch(Arrays.copyOfRange(a,2,6));}
}
