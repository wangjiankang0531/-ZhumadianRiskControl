package xnby.replica;
import xnby.compat.Java8IO;

import java.io.FileDescriptor;
import java.net.*;
import java.nio.file.*;
import java.security.Permission;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** Java-8-compatible, process-local integration constraint, not an OS sandbox for hostile code. */
@SuppressWarnings("removal")
public final class OriginalProcessBoundary extends SecurityManager {
    private final Path writeRoot;
    private final Set<Integer> loopbackPorts;
    private final boolean ephemeralListen;
    private final Map<String,AtomicInteger> denied = new ConcurrentHashMap<>();

    public OriginalProcessBoundary(Path root, Set<Integer> ports, boolean listen) throws Exception {
        writeRoot = root.toRealPath();
        loopbackPorts = Collections.unmodifiableSet(new HashSet<Integer>(ports));
        ephemeralListen = listen;
        // Load helper implementations before installing this manager.
        new SecurityException("BOUNDARY"); denied.put("warmup",new AtomicInteger()); denied.remove("warmup");
    }
    private void deny(String kind) {
        if(Boolean.getBoolean("own.boundary.trace")) {
            try {
                Path trace=writeRoot.resolve("boundary-denial-trace.txt");
                if(!Files.exists(trace) || Files.size(trace)<65536) {
                    StringBuilder observation=new StringBuilder("denial\t"+kind+"\n");
                    for(StackTraceElement frame:Thread.currentThread().getStackTrace()) observation.append(frame.getClassName()).append('.').append(frame.getMethodName()).append('\n');
                    Java8IO.writeString(trace,observation.toString(),StandardOpenOption.CREATE,StandardOpenOption.APPEND);
                }
            }catch(java.io.IOException error){System.err.println("OWN_BOUNDARY_TRACE_WRITE_FAILED");}
        }
        denied.computeIfAbsent(kind,k->new AtomicInteger()).incrementAndGet();
        throw new SecurityException("OWN_PROCESS_BOUNDARY_"+kind);
    }
    public Map<String,Integer> deniedCounts() {
        Map<String,Integer> result = new TreeMap<>(); denied.forEach((k,v)->result.put(k,v.get())); return result;
    }
    private void fileAllowed(String file) {
        try {
            Path target=Paths.get(file).toAbsolutePath().normalize();
            if (!target.startsWith(writeRoot)) { deny("FILE_OUTSIDE_ROOT"); return; }
            Path existing=target;
            while(existing!=null && !Files.exists(existing,LinkOption.NOFOLLOW_LINKS)) existing=existing.getParent();
            if(existing==null || !existing.toRealPath().startsWith(writeRoot)) deny("FILE_REDIRECT_OUTSIDE_ROOT");
        } catch(SecurityException e) { throw e; }
        catch(Exception e) { deny("FILE_PATH_UNPROVEN"); }
    }
    @Override public void checkWrite(String file) { fileAllowed(file); }
    @Override public void checkDelete(String file) { fileAllowed(file); }
    @Override public void checkWrite(FileDescriptor fd) {
        if(fd==FileDescriptor.out || fd==FileDescriptor.err)return;
        // Java 8's bootstrap SocketOutputStream invokes the descriptor constructor.
        // Socket connect/accept still pass the unchanged numeric-loopback/port checks.
        Class<?>[] callers=getClassContext();
        if(callers.length>=3 && callers[1]==java.io.FileOutputStream.class
                && callers[2].getName().equals("java.net.SocketOutputStream")
                && callers[2].getClassLoader()==null)return;
        deny("RAW_FILE_DESCRIPTOR");
    }
    private boolean allowedHost(String host) {
        return "127.0.0.1".equals(host) || "::1".equals(host) || "[::1]".equals(host);
    }
    @Override public void checkConnect(String host,int port) {
        if(!allowedHost(host)) { deny(port==-1?"NON_LOOPBACK_DNS":"NON_LOOPBACK_CONNECT"); return; }
        if(port!=-1 && !loopbackPorts.contains(port)) {
            // Windows Java 8 builds a Selector wakeup pipe using its own local socket.
            // Recognize only the bootstrap JDK connector immediately above SocketChannel.
            Class<?>[] callers=getClassContext();int first=0;
            while(first<callers.length && callers[first]==OriginalProcessBoundary.class)first++;
            if(ephemeralListen && callers.length>first+2
                    && callers[first].getName().equals("sun.nio.ch.SocketChannelImpl")
                    && callers[first+1]==java.nio.channels.SocketChannel.class
                    && callers[first+2].getName().equals("sun.nio.ch.PipeImpl$Initializer$LoopbackConnector")
                    && callers[first].getClassLoader()==null && callers[first+2].getClassLoader()==null)return;
            deny("UNLISTED_LOOPBACK_CONNECT");
        }
    }
    @Override public void checkConnect(String host,int port,Object context) { checkConnect(host,port); }
    @Override public void checkListen(int port) { if(!ephemeralListen || port!=0) deny("LISTEN"); }
    @Override public void checkAccept(String host,int port) { if(!allowedHost(host)) deny("NON_LOOPBACK_ACCEPT"); }
    @Override public void checkMulticast(InetAddress address) { deny("MULTICAST"); }
    @Override public void checkExec(String command) { deny("SUBPROCESS"); }
    @Override public void checkLink(String library) {
        // Only JDK's own shipped libraries may be loaded. No project/JNA/Netty native binaries.
        String jdk=System.getProperty("java.home");
        Path p;
        try { p=Paths.get(library); }
        catch(Exception e) { deny("NON_JDK_NATIVE_LIBRARY"); return; }
        if(p.isAbsolute() && p.normalize().startsWith(Paths.get(jdk).resolve("bin"))) return;
        if(new HashSet<String>(Arrays.asList("net","nio","extnet","zip","jimage","management","management_ext","sunec","sunmscapi","verify","java","awt","fontmanager","lcms","freetype","jpeg")).contains(library)) return;
        deny("NON_JDK_NATIVE_LIBRARY");
    }
    @Override public void checkPermission(Permission permission) {
        if(permission instanceof RuntimePermission) {
            String n=permission.getName();
            if(n.equals("setSecurityManager") || n.equals("setIO")) deny("BOUNDARY_OR_RUNTIME_REPLACEMENT");
        }
        if(permission instanceof java.security.SecurityPermission && permission.getName().equals("setPolicy")) deny("POLICY_REPLACEMENT");
        // Direct permission checks by clients must not sidestep the socket methods above.
        if(permission instanceof SocketPermission) deny("DIRECT_SOCKET_PERMISSION");
        if(permission instanceof URLPermission) {
            try { URL u=new URL(permission.getName()); checkConnect(u.getHost(),u.getPort()==-1?u.getDefaultPort():u.getPort()); }
            catch(SecurityException e) { throw e; }
            catch(Exception e) { deny("URL_PERMISSION_UNPROVEN"); }
        }
    }
    @Override public void checkPermission(Permission permission,Object context) { checkPermission(permission); }
}
