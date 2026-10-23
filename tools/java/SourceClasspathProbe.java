package xnby.audit;

import java.io.*;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Hash and resolve classes without initializing or invoking application code. */
public final class SourceClasspathProbe {
    private static String hash(InputStream stream) throws Exception {
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        byte[] buffer=new byte[65536];int count;
        while((count=stream.read(buffer))!=-1)digest.update(buffer,0,count);
        StringBuilder out=new StringBuilder();
        for(byte b:digest.digest())out.append(String.format("%02x",b&255));
        return out.toString();
    }
    private static String safeError(Throwable error) {
        String message=error.getMessage();
        return error.getClass().getName()+(message!=null&&message.matches("[A-Za-z0-9_/$.;]+")?":"+message:"");
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=2)throw new IllegalArgumentException("Expected specification and new result paths");
        Path result=Paths.get(args[1]);
        if(Files.exists(result))throw new IllegalArgumentException("Existing result must not be overwritten");
        ClassLoader loader=Thread.currentThread().getContextClassLoader();
        int passed=0,failed=0;
        try(BufferedReader input=Files.newBufferedReader(Paths.get(args[0]),StandardCharsets.UTF_8);
            BufferedWriter output=Files.newBufferedWriter(result,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW)) {
            String line;
            while((line=input.readLine())!=null) {
                String[] fields=line.split("\\t",-1);
                if(fields.length!=3||!fields[0].matches("[CR]")||!fields[2].matches("[a-f0-9]{64}"))throw new IllegalArgumentException("Invalid specification");
                String name=fields[1];String status="PASS",detail="";
                URL url=loader.getResource(name);
                if(url==null)status="RESOURCE_MISSING";
                else {
                    try(InputStream bytes=url.openStream()) {
                        if(!hash(bytes).equals(fields[2]))status="SHA_MISMATCH";
                    }
                    if(status.equals("PASS")&&fields[0].equals("C")) {
                        try {
                            String type=name.substring(0,name.length()-6).replace('/','.');
                            Class<?> cls=Class.forName(type,false,loader);
                            int methods=cls.getDeclaredMethods().length;
                            int constructors=cls.getDeclaredConstructors().length;
                            int members=cls.getDeclaredFields().length;
                            detail="methods="+methods+",constructors="+constructors+",fields="+members;
                        } catch(LinkageError|TypeNotPresentException error) {
                            status="LINKAGE_ERROR";detail=safeError(error);
                        }
                    }
                }
                if(status.equals("PASS"))passed++;else failed++;
                output.write(fields[0]+"\t"+name+"\t"+status+"\t"+detail+"\n");
            }
        }
        if(Boolean.getBoolean("xnby.sourceProbe.sentinel"))throw new IllegalStateException("Application class initialized unexpectedly");
        System.out.println("SOURCE_CLASSPATH_PROBE passed="+passed+" failed="+failed+" applicationMainInvoked=false");
        if(failed!=0)System.exit(4);
    }
}
