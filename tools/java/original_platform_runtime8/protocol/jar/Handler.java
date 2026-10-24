package xnby.platform.protocol.jar;
import java.io.*;
import java.net.*;
import xnby.platform.OriginalJarResourceCache;

/** JVM-local original Boot handler; retain connections only for the pinned source archive. */
public final class Handler extends org.springframework.boot.loader.jar.Handler{
 @Override protected URLConnection openConnection(URL url)throws IOException{
  URLConnection connection=super.openConnection(url);
  String source=System.getProperty("own.platform.source.path");
  return source==null?connection:new OriginalJarResourceCache(source).retain(url,connection);
 }
}
