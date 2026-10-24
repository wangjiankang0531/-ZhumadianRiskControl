package xnby.platform;
import xnby.compat.Java8IO;
import org.springframework.boot.loader.LaunchedURLClassLoader;
import org.springframework.boot.loader.archive.Archive;
import java.net.*;
import java.io.*;
import java.util.*;

/** Original class definition/delegation and URL order; only resource connection lifetime differs. */
public final class OriginalResourceCachedClassLoader extends LaunchedURLClassLoader{
 private final OriginalJarResourceCache cache;
 public OriginalResourceCachedClassLoader(Archive archive,URL[] urls,ClassLoader parent,String source)throws MalformedURLException{
  super(false,archive,urls,parent);cache=new OriginalJarResourceCache(source);
 }
 public URL getResource(String name){return cache.wrap(super.getResource(name));}
 public URL[] getURLs(){
  URL[] urls=super.getURLs();if(cache!=null)for(int i=0;i<urls.length;i++)urls[i]=cache.wrap(urls[i]);return urls;
 }
 public Enumeration<URL> getResources(String name)throws IOException{
  Enumeration<URL> original=super.getResources(name);
  return new Enumeration<URL>(){public boolean hasMoreElements(){return original.hasMoreElements();}public URL nextElement(){return cache.wrap(original.nextElement());}};
 }
 public void close()throws IOException{
  observe("classloader-close");super.close();
 }
 public void clearCache(){observe("classloader-clear-cache");super.clearCache();}
 private void observe(String operation){
  try{
   StringWriter text=new StringWriter();new Exception(operation).printStackTrace(new PrintWriter(text));
   xnby.compat.Java8IO.writeString(java.nio.file.Paths.get(System.getProperty("own.platform.root")).resolve("classloader-lifecycle.private.log"),text.toString(),java.nio.file.StandardOpenOption.CREATE,java.nio.file.StandardOpenOption.APPEND);
  }catch(IOException error){System.err.println("OWN_CLASSLOADER_LIFECYCLE_OBSERVATION_FAILED");}
 }
}
