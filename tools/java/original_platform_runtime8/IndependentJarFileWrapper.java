package org.springframework.boot.loader.jar;
import xnby.compat.Java8IO;
import java.io.*;
import java.nio.file.*;
import java.util.*;

/** Give resource consumers their own closeable ZIP handle, preserving the loader-owned wrapper. */
public final class IndependentJarFileWrapper extends JarFileWrapper{
 private static final Map<JarFile,IndependentJarFileWrapper> handles=new IdentityHashMap<>();
 private boolean closed;
 private IndependentJarFileWrapper(JarFile original)throws IOException{super(original);}
 public static synchronized java.util.jar.JarFile forResource(java.util.jar.JarFile original)throws IOException{
  if(!(original instanceof AbstractJarFile))return original;
  JarFile parent=JarFileWrapper.unwrap(original);
  IndependentJarFileWrapper result=handles.get(parent);
  if(result==null||result.closed){result=new IndependentJarFileWrapper(parent);handles.put(parent,result);}
  return result;
 }
 @Override public synchronized void close()throws IOException{
  if(closed)return;
  closed=true;
  try{
   Path log=Paths.get(System.getProperty("own.platform.root")).resolve("resource-wrapper-close.private.log");
   if(!Files.exists(log)||Files.size(log)<65536){
    StringWriter text=new StringWriter();new Exception("Independent resource wrapper closed; original loader wrapper retained").printStackTrace(new PrintWriter(text));
    Java8IO.writeString(log,text.toString(),StandardOpenOption.CREATE,StandardOpenOption.APPEND);
   }
  }finally{super.close();}
 }
}
