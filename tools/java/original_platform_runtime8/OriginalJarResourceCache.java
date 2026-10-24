package xnby.platform;
import java.io.*;
import java.net.*;
import java.security.Permission;
import java.security.cert.Certificate;
import java.util.jar.*;

/** Only original immutable runtime archive URLs retain loader-owned connections. */
public final class OriginalJarResourceCache{
 private final String prefix;
 public OriginalJarResourceCache(String source)throws MalformedURLException{prefix="jar:"+new File(source).toURI().toURL().toExternalForm()+"!/";}
 public URL wrap(URL original){
  if(original==null||!original.toExternalForm().startsWith(prefix))return original;
  try{return new URL(null,original.toExternalForm(),new URLStreamHandler(){
   protected URLConnection openConnection(URL requested)throws IOException{
    URL target=requested.toExternalForm().equals(original.toExternalForm())?original:new URL(original,requested.toExternalForm());
    return retain(requested,target.openConnection());
   }
  });}catch(MalformedURLException failure){throw new IllegalArgumentException("OWN_SOURCE_ARCHIVE_URL_INVALID",failure);}
 }
 public URLConnection retain(URL requested,URLConnection raw)throws IOException{
    if(!requested.toExternalForm().startsWith(prefix)||!(raw instanceof JarURLConnection))return raw;
    final JarURLConnection delegate=(JarURLConnection)raw;
    delegate.setUseCaches(true);
    return new JarURLConnection(requested){
     public void connect()throws IOException{delegate.connect();}
     public JarFile getJarFile()throws IOException{
      JarFile file=delegate.getJarFile();
      return Boolean.getBoolean("own.platform.independent.jar.wrappers")?org.springframework.boot.loader.jar.IndependentJarFileWrapper.forResource(file):file;
     }
     public URL getJarFileURL(){return delegate.getJarFileURL();}
     public String getEntryName(){return delegate.getEntryName();}
     public JarEntry getJarEntry()throws IOException{return delegate.getJarEntry();}
     public Manifest getManifest()throws IOException{return delegate.getManifest();}
     public Attributes getAttributes()throws IOException{return delegate.getAttributes();}
     public Attributes getMainAttributes()throws IOException{return delegate.getMainAttributes();}
     public Certificate[] getCertificates()throws IOException{return delegate.getCertificates();}
     public InputStream getInputStream()throws IOException{return delegate.getInputStream();}
     public int getContentLength(){return delegate.getContentLength();}
     public long getContentLengthLong(){return delegate.getContentLengthLong();}
     public long getLastModified(){return delegate.getLastModified();}
     public String getContentType(){return delegate.getContentType();}
     public Permission getPermission()throws IOException{return delegate.getPermission();}
     public void setUseCaches(boolean requested){delegate.setUseCaches(true);}
     public boolean getUseCaches(){return true;}
    };
 }
}
