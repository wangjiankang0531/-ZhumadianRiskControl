package xnby.replica;
import xnby.compat.Java8IO;

import java.io.*;
import java.net.*;
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

@SuppressWarnings("removal")
public final class OriginalProcessBoundaryFixture {
    interface Action { void run() throws Exception; }
    private static final List<String> passed=new ArrayList<>();
    private static void denied(String label,Action action) throws Exception {
        try { action.run(); }
        catch(SecurityException e) {
            if(!e.getMessage().startsWith("OWN_PROCESS_BOUNDARY_")) throw e;
            passed.add(label);return;
        }
        throw new IllegalStateException("ACTION_NOT_DENIED_"+label);
    }
    public static void main(String[] args) throws Exception {
        Path out=Paths.get(args[0]).toRealPath(), allowed=out.resolve("allowed"), sibling=out.resolve("sibling");
        Files.createDirectory(allowed);Files.createDirectory(sibling);
        Path canary=sibling.resolve("canary.txt");Java8IO.writeString(canary,"unchanged");
        try(ServerSocket yes=new ServerSocket(0,5,InetAddress.getByName("127.0.0.1"));
            ServerSocket no=new ServerSocket(0,5,InetAddress.getByName("127.0.0.1"))) {
            int yesPort=yes.getLocalPort(),noPort=no.getLocalPort();
            // Initialize JDK networking in the fixture, not by contacting external services.
            AtomicInteger accepted=new AtomicInteger();
            Thread server=new Thread(()->{try(Socket s=yes.accept()){
                s.setSoTimeout(2000);accepted.incrementAndGet();s.getInputStream().read();s.getOutputStream().write(7);
            }catch(Exception e){throw new RuntimeException(e);}});
            FileOutputStream outsideDescriptor=new FileOutputStream(sibling.resolve("raw-canary.txt").toFile());
            OriginalProcessBoundary guard=new OriginalProcessBoundary(allowed,Collections.singleton(yesPort),true);
            System.setSecurityManager(guard);
            try(Selector selector=Selector.open()){selector.wakeup();selector.selectNow();if(!selector.isOpen())throw new IllegalStateException("SELECTOR_NOT_OPEN");}passed.add("jdk-windows-selector-owned-loopback-pipe");
            Java8IO.writeString(allowed.resolve("own.txt"),"owned");passed.add("own-file-write");
            Class.forName("jdk.net.ExtendedSocketOptions");passed.add("jdk-extended-socket-options");
            try(Socket s=new Socket("127.0.0.1",yesPort)) {
                server.start();s.setSoTimeout(2000);s.getOutputStream().write(1);
                if(s.getInputStream().read()!=7)throw new IllegalStateException("OWN_SOCKET_FAILED");
            }
            server.join(3000);if(server.isAlive()||accepted.get()!=1)throw new IllegalStateException("OWN_SERVER_NOT_FINISHED");
            passed.add("explicit-own-loopback-port");
            if(System.getProperty("own.canary.jar")!=null) {
                try(URLClassLoader loader=new URLClassLoader(new URL[]{Paths.get(System.getProperty("own.canary.jar")).toUri().toURL()},null)) {
                    Class<?> c=Class.forName("xnby.replica.BoundaryClassLoadingCanary",false,loader);
                    if(c.getClassLoader()!=loader)throw new IllegalStateException("CANARY_NOT_LOADED_BY_OWN_URL_LOADER");
                    passed.add("fresh-url-class-loader");
                }
            }
            denied("sibling-write",()->Java8IO.writeString(canary,"bad"));
            denied("sibling-delete",()->Files.delete(canary));
            denied("parent-traversal",()->Java8IO.writeString(allowed.resolve("../sibling/new.txt"),"bad"));
            denied("prefix-is-not-child",()->Java8IO.writeString(out.resolve("allowed-extra.txt"),"bad"));
            denied("raw-descriptor",()->new FileOutputStream(FileDescriptor.in));
            denied("outside-raw-file-descriptor",()->new FileOutputStream(outsideDescriptor.getFD()));
            denied("unlisted-loopback-port",()->{try(Socket s=new Socket("127.0.0.1",noPort)) {}});
            denied("non-loopback-classic-socket",()->{try(Socket s=new Socket("192.0.2.1",9)) {}});
            denied("non-loopback-nio-socket",()->{try(SocketChannel s=SocketChannel.open()) {s.connect(new InetSocketAddress("192.0.2.1",9));}});
            denied("non-loopback-datagram",()->{try(DatagramSocket s=new DatagramSocket(null)) {s.send(new DatagramPacket(new byte[]{1},1,InetAddress.getByName("192.0.2.1"),9));}});
            denied("non-loopback-dns",()->InetAddress.getByName("own-fixture.invalid"));
            denied("url-connection",()->new URL("http://192.0.2.1:9/own-fixture").openConnection().getInputStream());
            denied("direct-socket-permission",()->guard.checkPermission(new SocketPermission("127.0.0.1:"+yesPort,"connect")));
            denied("direct-external-url-permission",()->guard.checkPermission(new URLPermission("http://192.0.2.1:9/own-fixture")));
            guard.checkPermission(new URLPermission("http://127.0.0.1:"+yesPort+"/own-fixture"));passed.add("explicit-own-url-permission");
            denied("subprocess",()->new ProcessBuilder(Paths.get(System.getProperty("java.home"),"bin","java.exe").toString(),"-version").start());
            denied("native-library",()->System.loadLibrary("own-fixture-non-jdk-library"));
            denied("remove-boundary",()->System.setSecurityManager(null));
            denied("listen-fixed-port",()->{try(ServerSocket s=new ServerSocket(noPort)) {}});
            if(!Java8IO.readString(canary).equals("unchanged")||Files.exists(sibling.resolve("new.txt")))throw new IllegalStateException("CANARY_CHANGED");
            if(System.getSecurityManager()!=guard)throw new IllegalStateException("BOUNDARY_REMOVED");
            no.setSoTimeout(100);try(Socket s=no.accept()){throw new IllegalStateException("DENIED_SERVER_RECEIVED_CONNECTION");}catch(SocketTimeoutException expected){}
            passed.add("outside-canary-unchanged");passed.add("denied-server-no-connection");
            System.out.println("BOUNDARY_FIXTURE_RESULT {\"passedCases\":"+passed.size()+",\"ownLoopbackConnections\":"+accepted.get()+",\"outsideCanaryUnchanged\":true,\"originalBusinessLoaded\":false,\"operatingSystemSettingsChanged\":false}");
            Java8IO.writeString(allowed.resolve("results.txt"),String.join("\n",passed)+"\n"+guard.deniedCounts()+"\n");
        }
    }
}
