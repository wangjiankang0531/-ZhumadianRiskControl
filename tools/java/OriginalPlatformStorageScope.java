package xnby.platform;
import java.io.*;
import java.net.URI;
import java.nio.file.*;
import java.util.*;

/** Exact persistent platform root and exactly its three owned infrastructure ports. */
public final class OriginalPlatformStorageScope {
 public static final class Scope {public final Path writeRoot;public final Set<Integer> ports;Scope(Path r,Set<Integer> p){writeRoot=r;ports=Collections.unmodifiableSet(p);}}
 static void require(boolean v,String code){if(!v)throw new IllegalArgumentException(code);}
 static int port(String text){require(text!=null&&text.matches("[0-9]{4,5}"),"OWN_COMPONENT_PORT_REQUIRED");int p=Integer.parseInt(text);require(p>=1024&&p<=65535,"OWN_COMPONENT_PORT_RANGE");return p;}
 public static Scope resolve(Path runtime,Path requested,String owner,String configured,String mysql,String redis,String endpoint)throws Exception {
  Path root=runtime.toRealPath(),data=requested.toRealPath();
  require(runtime.toAbsolutePath().normalize().equals(root)&&requested.toAbsolutePath().normalize().equals(data),"PLATFORM_ROOT_REDIRECTION_REJECTED");
  require(root.getFileName().toString().matches("j[1-9][0-9]{0,3}")&&root.getParent().getFileName().toString().equals("runs")&&root.getParent().getParent().equals(data),"EXACT_PLATFORM_RUNTIME_LAYOUT_REQUIRED");
  require(data.getFileName().toString().equals("TianjinOriginalPlatform")&&data.getParent().getFileName().toString().equals("UserData")&&data.getParent().getParent().getFileName().toString().equals("Application"),"EXACT_PLATFORM_USERDATA_ROOT_REQUIRED");
  require(owner!=null&&owner.matches("[0-9a-f-]{36}")&&UUID.fromString(owner).toString().equals(owner),"PLATFORM_OWNER_UUID_REQUIRED");
  Path identity=data.resolve("identity.properties"),files=data.resolve("files");require(Files.isRegularFile(identity)&&Files.size(identity)<=4096&&!Files.isSymbolicLink(identity)&&Files.isDirectory(files)&&files.toRealPath().equals(files),"PLATFORM_IDENTITY_AND_FILES_SCOPE_REQUIRED");
  Properties known=new Properties();try(InputStream in=Files.newInputStream(identity)){known.load(in);}
  require(known.size()==3&&"xnby.original.platform.local-data.v1".equals(known.getProperty("schema"))&&owner.equals(known.getProperty("ownerId"))&&"files/".equals(known.getProperty("filesRelativePath")),"PLATFORM_DATA_IDENTITY_MISMATCH");
  int db=port(mysql),cache=port(redis);URI object=new URI(endpoint);
  require("http".equals(object.getScheme())&&"127.0.0.1".equals(object.getHost())&&object.getRawUserInfo()==null&&object.getRawQuery()==null&&object.getRawFragment()==null&&object.getRawPath().isEmpty(),"OWN_VERIFIED_OBJECT_BASE_REQUIRED");int store=port(Integer.toString(object.getPort()));
  Set<Integer> expected=new HashSet<Integer>(Arrays.asList(db,cache,store));require(expected.size()==3,"DISTINCT_PLATFORM_COMPONENT_PORTS_REQUIRED");
  require(configured!=null&&configured.split(",",-1).length==3,"EXACT_THREE_PLATFORM_PORTS_REQUIRED");Set<Integer> found=new HashSet<Integer>();for(String v:configured.split(",",-1))require(found.add(port(v)),"PLATFORM_DUPLICATE_PORT_REJECTED");require(found.equals(expected),"PLATFORM_COMPONENT_PORT_IDENTITY_MISMATCH");
  return new Scope(data,found);
 }
}
