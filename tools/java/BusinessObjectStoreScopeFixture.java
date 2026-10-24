package xnby.replica;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Exact owned fourth-port scope; transport fixtures are not an object store. */
@SuppressWarnings("removal")
public final class BusinessObjectStoreScopeFixture {
 interface Action {void run()throws Exception;}
 static int checks;
 static void check(boolean value){if(!value)throw new AssertionError("OBJECT_STORE_SCOPE_CHECK_FAILED");checks++;}
 static void reject(Action action)throws Exception{try{action.run();throw new AssertionError("BAD_FOUR_PORT_SCOPE_ACCEPTED");}catch(IllegalArgumentException expected){checks++;}}
 static void denied(Action action)throws Exception{try{action.run();throw new AssertionError("UNLISTED_ACTION_ACCEPTED");}catch(SecurityException e){if(!e.getMessage().startsWith("OWN_PROCESS_BOUNDARY_"))throw e;checks++;}}
 static void exchange(ServerSocket server)throws Exception{try(Socket client=new Socket("127.0.0.1",server.getLocalPort());Socket peer=server.accept()){client.getOutputStream().write(5);peer.setSoTimeout(1000);check(peer.getInputStream().read()==5);}}
 public static void main(String[] args)throws Exception {
  Path root=Paths.get(args[0]).toRealPath(),allowed=root.resolve("allowed"),outside=root.resolve("outside");Files.createDirectory(allowed);Files.createDirectory(outside);Path sentinel=outside.resolve("sentinel");Files.write(sentinel,new byte[]{3});InetAddress loop=InetAddress.getByAddress(new byte[]{127,0,0,1});
  try(ServerSocket db=new ServerSocket(0,8,loop);ServerSocket redis=new ServerSocket(0,8,loop);ServerSocket platform=new ServerSocket(0,8,loop);ServerSocket store=new ServerSocket(0,8,loop);ServerSocket other=new ServerSocket(0,8,loop)){
   String d=""+db.getLocalPort(),r=""+redis.getLocalPort(),p=""+platform.getLocalPort(),s=""+store.getLocalPort(),three=d+","+r+","+p,list=three+","+s,base="http://127.0.0.1:"+p,object="http://127.0.0.1:"+s;
   Set<Integer> ports=OriginalBusinessLaunch.scopeWithObjectStore(list,d,r,base,object);check(ports.size()==4&&ports.contains(store.getLocalPort()));check(OriginalBusinessLaunch.scopeWithObjectStore(three,d,r,base,null).size()==3);
   reject(()->OriginalBusinessLaunch.scopeWithObjectStore(three,d,r,base,object));reject(()->OriginalBusinessLaunch.scopeWithObjectStore(list+","+other.getLocalPort(),d,r,base,object));reject(()->OriginalBusinessLaunch.scopeWithObjectStore(three+","+other.getLocalPort(),d,r,base,object));reject(()->OriginalBusinessLaunch.scopeWithObjectStore(three+","+s,d,r,base,base));reject(()->OriginalBusinessLaunch.scopeWithObjectStore(three+","+d,d,r,base,object));
   for(String invalid:new String[]{"http://other.invalid:"+s,object+"/path",object+"?x=1",object+"#f","http://user@127.0.0.1:"+s,"https://127.0.0.1:"+s})reject(()->OriginalBusinessLaunch.scopeWithObjectStore(list,d,r,base,invalid));
   OriginalProcessBoundary guard=new OriginalProcessBoundary(allowed,ports,true);System.setSecurityManager(guard);Files.write(allowed.resolve("own"),new byte[]{2});checks++;exchange(db);exchange(redis);exchange(platform);exchange(store);
   AtomicInteger accepted=new AtomicInteger();Thread service=new Thread(()->{try(Socket peer=store.accept()){peer.setSoTimeout(2000);BufferedReader reader=new BufferedReader(new InputStreamReader(peer.getInputStream(),"US-ASCII"));String line;while((line=reader.readLine())!=null&&!line.isEmpty()){}peer.getOutputStream().write("HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok".getBytes("US-ASCII"));peer.getOutputStream().flush();accepted.incrementAndGet();}catch(Exception e){throw new IllegalStateException("OWN_STORE_TRANSPORT_FAILED",e);}},"own-fourth-port-fixture");service.setDaemon(true);service.start();HttpURLConnection connection=(HttpURLConnection)new URL(object+"/owned-transport").openConnection();connection.setConnectTimeout(2000);connection.setReadTimeout(2000);try{check(connection.getResponseCode()==200);try(InputStream input=connection.getInputStream()){check(input.read()=='o');}}finally{connection.disconnect();}service.join(3000);check(!service.isAlive()&&accepted.get()==1);
   denied(()->{try(Socket ignored=new Socket("127.0.0.1",other.getLocalPort())){}});denied(()->{try(Socket ignored=new Socket("192.0.2.1",9)){}});denied(()->Files.write(sentinel,new byte[]{9}));denied(()->new ProcessBuilder("unlisted-process").start());denied(()->System.setSecurityManager(null));check(Arrays.equals(Files.readAllBytes(sentinel),new byte[]{3})&&System.getSecurityManager()==guard);
   String result="{\"passedChecks\":"+checks+",\"exactOwnedPorts\":4,\"actualTCPExchanges\":4,\"fourthPortHTTPExchanges\":"+accepted.get()+",\"originalApplicationOrDatabaseLoaded\":false,\"outsideSentinelUnchanged\":true}";Files.write(allowed.resolve("result.json"),result.getBytes("US-ASCII"));System.out.println("BUSINESS_OBJECT_STORE_SCOPE_RESULT "+result);
  }
 }
}
