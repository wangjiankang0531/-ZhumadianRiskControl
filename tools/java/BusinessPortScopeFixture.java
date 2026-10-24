package xnby.replica;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Actual sockets/HTTP under the existing guard; no original application or database classes. */
@SuppressWarnings("removal")
public final class BusinessPortScopeFixture {
 interface Action {void run()throws Exception;}
 static int checks;
 static void check(boolean value){if(!value)throw new AssertionError("BUSINESS_PORT_SCOPE_CHECK_FAILED");checks++;}
 static void rejectScope(Action action)throws Exception{try{action.run();throw new AssertionError("BAD_SCOPE_ACCEPTED");}catch(IllegalArgumentException expected){checks++;}}
 static void denied(Action action)throws Exception{try{action.run();throw new AssertionError("BOUNDARY_ACTION_ACCEPTED");}catch(SecurityException e){if(!e.getMessage().startsWith("OWN_PROCESS_BOUNDARY_"))throw e;checks++;}}
 static void exchange(ServerSocket server)throws Exception{try(Socket client=new Socket("127.0.0.1",server.getLocalPort());Socket peer=server.accept()){client.getOutputStream().write(7);peer.setSoTimeout(1000);if(peer.getInputStream().read()!=7)throw new AssertionError("OWN_TCP_EXCHANGE_FAILED");}checks++;}
 public static void main(String[] args)throws Exception {
  Path root=Paths.get(args[0]).toRealPath(),allowed=root.resolve("allowed"),sibling=root.resolve("sibling");Files.createDirectory(allowed);Files.createDirectory(sibling);Path sentinel=sibling.resolve("sentinel.txt");Files.write(sentinel,"unchanged".getBytes("US-ASCII"));InetAddress loop=InetAddress.getByAddress(new byte[]{127,0,0,1});
  try(ServerSocket db=new ServerSocket(0,8,loop);ServerSocket redis=new ServerSocket(0,8,loop);ServerSocket platform=new ServerSocket(0,8,loop);ServerSocket other=new ServerSocket(0,8,loop)){
   String d=Integer.toString(db.getLocalPort()),r=Integer.toString(redis.getLocalPort()),p=Integer.toString(platform.getLocalPort()),list=d+","+r+","+p,base="http://127.0.0.1:"+p;Set<Integer> ports=OriginalBusinessLaunch.scope(list,d,r,base);check(ports.size()==3&&ports.contains(platform.getLocalPort()));
   rejectScope(()->OriginalBusinessLaunch.scope(list,d,r,null));rejectScope(()->OriginalBusinessLaunch.scope(d+","+r,d,r,base));rejectScope(()->OriginalBusinessLaunch.scope(list+","+other.getLocalPort(),d,r,base));rejectScope(()->OriginalBusinessLaunch.scope(d+","+r+","+d,d,r,base));rejectScope(()->OriginalBusinessLaunch.scope(d+","+r+","+other.getLocalPort(),d,r,base));rejectScope(()->OriginalBusinessLaunch.scope(list,d,d,base));
   for(String invalid:new String[]{"http://other.invalid:"+p,base+"/path",base+"?x=1",base+"#fragment","http://user@127.0.0.1:"+p})rejectScope(()->OriginalBusinessLaunch.scope(list,d,r,invalid));rejectScope(()->OriginalBusinessLaunch.scope(list,"9",r,base));
   OriginalProcessBoundary guard=new OriginalProcessBoundary(allowed,ports,true);System.setSecurityManager(guard);Files.write(allowed.resolve("own.txt"),"owned".getBytes("US-ASCII"));checks++;exchange(db);exchange(redis);exchange(platform);
   AtomicInteger httpAccepted=new AtomicInteger();Thread server=new Thread(()->{try(Socket peer=platform.accept()){peer.setSoTimeout(2000);BufferedReader reader=new BufferedReader(new InputStreamReader(peer.getInputStream(),"US-ASCII"));String line;while((line=reader.readLine())!=null&&!line.isEmpty()){}byte[] body="fixture-ok".getBytes("US-ASCII");peer.getOutputStream().write(("HTTP/1.1 200 OK\r\nContent-Length: "+body.length+"\r\nConnection: close\r\n\r\n").getBytes("US-ASCII"));peer.getOutputStream().write(body);peer.getOutputStream().flush();httpAccepted.incrementAndGet();}catch(Exception e){throw new RuntimeException("OWN_HTTP_FIXTURE_FAILED",e);}},"own-third-port-http-fixture");server.setDaemon(true);server.start();HttpURLConnection connection=(HttpURLConnection)new URL(base+"/own-fixture").openConnection();connection.setConnectTimeout(2000);connection.setReadTimeout(2000);try{check(connection.getResponseCode()==200);try(InputStream input=connection.getInputStream()){check(input.read()=='f');}}finally{connection.disconnect();}server.join(3000);check(!server.isAlive()&&httpAccepted.get()==1);
   denied(()->{try(Socket s=new Socket("127.0.0.1",other.getLocalPort())){}});denied(()->{try(Socket s=new Socket("192.0.2.1",9)){}});denied(()->Files.write(sentinel,"bad".getBytes("US-ASCII")));denied(()->new ProcessBuilder(Paths.get(System.getProperty("java.home"),"bin","java.exe").toString(),"-version").start());denied(()->System.setSecurityManager(null));check(Arrays.equals(Files.readAllBytes(sentinel),"unchanged".getBytes("US-ASCII"))&&System.getSecurityManager()==guard);other.setSoTimeout(100);try(Socket s=other.accept()){throw new AssertionError("UNLISTED_SERVER_RECEIVED_CONNECTION");}catch(SocketTimeoutException expected){checks++;}
   String result="{\"passedCases\":"+checks+",\"exactOwnedPorts\":3,\"ownTCPExchanges\":3,\"thirdPortHTTPExchanges\":"+httpAccepted.get()+",\"outsideSentinelUnchanged\":true,\"originalApplicationLoaded\":false,\"databaseConnected\":false,\"operatingSystemSettingsChanged\":false}";Files.write(allowed.resolve("result.json"),result.getBytes("US-ASCII"));System.out.println("BUSINESS_PORT_SCOPE_FIXTURE_RESULT "+result);
  }
 }
}
