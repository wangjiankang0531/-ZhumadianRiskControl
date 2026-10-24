package xnby.platform;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import xnby.replica.OriginalProcessBoundary;
public final class PlatformPersistentScopeFixture {
 static int checks;interface Checked {void run()throws Exception;}
 static void require(boolean v){if(!v)throw new IllegalStateException("PERSISTENT_PLATFORM_SCOPE_FIXTURE_FAILED");checks++;}
 static void rejected(Checked c)throws Exception {try{c.run();}catch(IllegalArgumentException e){checks++;return;}throw new IllegalStateException("INVALID_PLATFORM_SCOPE_ACCEPTED");}
 static void denied(Checked c)throws Exception {try{c.run();}catch(SecurityException e){checks++;return;}throw new IllegalStateException("FORBIDDEN_PLATFORM_ACTION_ACCEPTED");}
 public static void main(String[] args)throws Exception {
  final Path runtime=Paths.get(args[0]).toRealPath(),data=runtime.getParent().getParent(),outside=Paths.get(args[2]).toAbsolutePath();final String owner=args[1];
  List<ServerSocket> servers=new ArrayList<>();for(int i=0;i<4;i++)servers.add(new ServerSocket(0,1,InetAddress.getByName("127.0.0.1")));
  try {
   final String db=""+servers.get(0).getLocalPort(),cache=""+servers.get(1).getLocalPort(),store=""+servers.get(2).getLocalPort(),extra=""+servers.get(3).getLocalPort(),ports=db+","+cache+","+store,endpoint="http://127.0.0.1:"+store;
   OriginalPlatformStorageScope.Scope scope=OriginalPlatformStorageScope.resolve(runtime,data,owner,ports,db,cache,endpoint);require(scope.writeRoot.equals(data));require(scope.ports.size()==3);require(OriginalPlatformStorageScope.resolve(runtime,data,owner,store+","+db+","+cache,db,cache,endpoint).ports.equals(scope.ports));
   for(String bad:new String[]{db+","+cache,ports+","+extra,db+","+cache+","+cache,db+","+cache+","+extra})rejected(()->OriginalPlatformStorageScope.resolve(runtime,data,owner,bad,db,cache,endpoint));
   for(String bad:new String[]{"https://127.0.0.1:"+store,"http://192.168.0.107:"+store,"http://user@127.0.0.1:"+store,endpoint+"/path",endpoint+"?q=1"})rejected(()->OriginalPlatformStorageScope.resolve(runtime,data,owner,ports,db,cache,bad));
   rejected(()->OriginalPlatformStorageScope.resolve(runtime,data,owner,ports,db,db,endpoint));
   rejected(()->OriginalPlatformStorageScope.resolve(runtime,data,"00000000-0000-0000-0000-000000000000",ports,db,cache,endpoint));
   rejected(()->OriginalPlatformStorageScope.resolve(data.resolve("files"),data,owner,ports,db,cache,endpoint));
   rejected(()->OriginalPlatformStorageScope.resolve(runtime,data.resolve("files"),owner,ports,db,cache,endpoint));
   rejected(()->OriginalPlatformStorageScope.resolve(runtime,data,null,ports,db,cache,endpoint));
   final OriginalProcessBoundary guard=new OriginalProcessBoundary(scope.writeRoot,scope.ports,true);System.setSecurityManager(guard);
   Path first=runtime.resolve("own-scope-probe.txt"),second=data.resolve("files/own-scope-probe.txt");Files.write(first,"runtime".getBytes("US-ASCII"));checks++;Files.write(second,"persistent".getBytes("US-ASCII"));checks++;require(Files.isRegularFile(first));require(Files.isRegularFile(second));
   for(int i=0;i<3;i++){try(Socket socket=new Socket("127.0.0.1",servers.get(i).getLocalPort())){require(socket.isConnected());}}
   denied(()->{try(Socket socket=new Socket("127.0.0.1",Integer.parseInt(extra))){};});
   denied(()->guard.checkConnect("example.invalid",-1));denied(()->Files.write(outside,"must-not-exist".getBytes("US-ASCII")));denied(()->System.setSecurityManager(null));
   require(System.getSecurityManager()==guard);require(guard.deniedCounts().size()==4);
   Files.delete(first);Files.delete(second);System.out.println("PERSISTENT_PLATFORM_SCOPE_CHECKS="+checks);
  }finally{for(ServerSocket server:servers)server.close();}
 }
}
