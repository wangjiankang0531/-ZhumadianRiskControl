package xnby.replica;
import java.lang.reflect.InvocationTargetException;
import java.net.URI;
import java.nio.file.*;
import java.util.*;

/** Direct original-business launch with exactly the owned MySQL, Redis and verified platform ports. */
@SuppressWarnings("removal")
public final class OriginalBusinessLaunch {
 static int port(String value) {
  if(value==null||!value.matches("[0-9]{4,5}"))throw new IllegalArgumentException("OWN_COMPONENT_PORT_REQUIRED");int p=Integer.parseInt(value);if(p<1024||p>65535)throw new IllegalArgumentException("OWN_COMPONENT_PORT_RANGE");return p;
 }
 static Set<Integer> scope(String configured,String mysql,String redis,String platformBase)throws Exception {
  int db=port(mysql),cache=port(redis);if(db==cache||platformBase==null)throw new IllegalArgumentException("OWN_THREE_COMPONENTS_REQUIRED");URI uri=new URI(platformBase);
  if(!"http".equals(uri.getScheme())||!"127.0.0.1".equals(uri.getHost())||uri.getRawUserInfo()!=null||uri.getRawQuery()!=null||uri.getRawFragment()!=null||!(uri.getRawPath()==null||uri.getRawPath().isEmpty()))throw new IllegalArgumentException("OWN_VERIFIED_PLATFORM_BASE_REQUIRED");int platform=port(Integer.toString(uri.getPort()));if(platform==db||platform==cache)throw new IllegalArgumentException("OWN_DISTINCT_PLATFORM_PORT_REQUIRED");
  if(configured==null)throw new IllegalArgumentException("OWN_EXACT_PORT_LIST_REQUIRED");String[] values=configured.split(",",-1);if(values.length!=3)throw new IllegalArgumentException("OWN_EXACTLY_THREE_PORTS_REQUIRED");Set<Integer> found=new HashSet<Integer>();for(String v:values)if(!found.add(port(v)))throw new IllegalArgumentException("OWN_DUPLICATE_PORT_REJECTED");Set<Integer> expected=new HashSet<Integer>(Arrays.asList(db,cache,platform));if(!found.equals(expected))throw new IllegalArgumentException("OWN_COMPONENT_PORT_IDENTITY_MISMATCH");return Collections.unmodifiableSet(found);
 }
 public static void main(String[] args)throws Exception {
  if(args.length!=1||!Boolean.getBoolean("own.direct.main"))throw new IllegalArgumentException("OWN_DIRECT_ORIGINAL_BUSINESS_ONLY");final Path root=Paths.get(args[0]).toRealPath();Set<Integer> ports=scope(System.getProperty("own.allowed.loopback.ports"),System.getProperty("own.expected.database.port"),System.getProperty("own.expected.redis.port"),System.getProperty("own.internal.platform.base"));
  final OriginalProcessBoundary guard=new OriginalProcessBoundary(root,ports,true);Runtime.getRuntime().addShutdownHook(new Thread(()->{try{Files.write(root.resolve("process-boundary-result.txt"),("guardStillInstalled="+(System.getSecurityManager()==guard)+"\n"+guard.deniedCounts()+"\n").getBytes("UTF-8"));}catch(Exception e){System.err.println("OWN_BOUNDARY_RECEIPT_FAILED");}},"own-business-boundary-receipt"));System.setSecurityManager(guard);System.out.println("OWN_BOUNDARY_INSTALLED_WITH_EXACT_THREE_COMPONENT_PORTS");
  try {Files.write(root.resolve("own-main-invocation-requested.txt"),"com.iemp.endanger.Application.main\n".getBytes("US-ASCII"));Class.forName("com.iemp.endanger.Application").getMethod("main",String[].class).invoke(null,(Object)new String[0]);Files.write(root.resolve("own-main-returned.txt"),"original-main-returned\n".getBytes("US-ASCII"));}
  catch(InvocationTargetException e){Throwable cause=e.getCause();System.err.println("OWN_ORIGINAL_LAUNCH_FAILED "+cause.getClass().getName());cause.printStackTrace(System.err);throw new IllegalStateException("ORIGINAL_STARTUP_NOT_READY",cause);}
 }
}
