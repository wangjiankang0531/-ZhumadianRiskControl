package xnby.replica;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;
import cn.xuyanwu.spring.file.storage.*;
import cn.xuyanwu.spring.file.storage.platform.*;
import cn.xuyanwu.spring.file.storage.recorder.DefaultFileRecorder;

/** Run unchanged original storage classes in separate JVMs; only synthetic owned files. */
public final class OriginalPlatformLocalStorageFixture {
 static int checks;
 static void require(boolean v,String code){if(!v)throw new IllegalStateException(code);checks++;}
 static String sha(byte[] raw)throws Exception{StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))s.append(String.format("%02x",b&255));return s.toString();}
 static byte[] payload(int i){if(i==0)return new byte[0];if(i==1)return "original-platform-local-probe-\u4e2d\u6587".getBytes(StandardCharsets.UTF_8);byte[] b=new byte[262145];for(int n=0;n<b.length;n++)b[n]=(byte)(n*31);return b;}
 static FileInfo info(int i){FileInfo f=new FileInfo();f.setBasePath("files/");f.setPath("synthetic/");f.setFilename("owned-"+i+".txt");f.setPlatform("own-local");return f;}
 public static void main(String[] args)throws Exception {
  if(args.length!=2||!Arrays.asList("write","read-delete").contains(args[1]))throw new IllegalArgumentException("OWN_ROOT_AND_PHASE_REQUIRED");
  Path root=Paths.get(args[0]).toRealPath();require(Files.isRegularFile(root.resolve("owner.json")),"OWN_IDENTITY_REQUIRED");
  OriginalProcessBoundary guard=new OriginalProcessBoundary(root,Collections.<Integer>emptySet(),false);System.setSecurityManager(guard);
  LocalPlusFileStorage local=new LocalPlusFileStorage();local.setPlatform("own-local");local.setBasePath("files/");local.setStoragePath(root.toString()+"/");local.setDomain("");
  FileStorageProperties props=new FileStorageProperties();props.setDefaultPlatform("own-local");
  FileStorageService service=new FileStorageService();service.setSelf(service);service.setProperties(props);service.setFileRecorder(new DefaultFileRecorder());service.setFileStorageList(new CopyOnWriteArrayList<FileStorage>(Arrays.<FileStorage>asList(local)));service.setAspectList(new CopyOnWriteArrayList<cn.xuyanwu.spring.file.storage.aspect.FileStorageAspect>());
  require(service.getFileStorage()==local,"ORIGINAL_DEFAULT_PROVIDER_SELECTION");
  for(int i=0;i<3;i++) {
   byte[] bytes=payload(i);FileInfo f=info(i);Path path=root.resolve("files/synthetic/owned-"+i+".txt");
   if(args[1].equals("write")) {
    require(!Files.exists(path),"FRESH_OWN_FILE_REQUIRED");
    FileInfo uploaded=service.of(bytes).setOriginalFilename("\u9644\u4ef6-"+i+".txt").setPath("synthetic/").setSaveFilename("owned-"+i+".txt").upload();
    require(uploaded!=null,"ORIGINAL_SERVICE_UPLOAD_RESULT");require(uploaded.getUrl().equals("files/synthetic/owned-"+i+".txt"),"ORIGINAL_LOCAL_URL_SHAPE");
    require(Files.size(path)==bytes.length,"REAL_DISK_SIZE");require(Arrays.equals(Files.readAllBytes(path),bytes),"REAL_DISK_BYTES");
   }
   require(service.exists(f),"ORIGINAL_EXISTS");
   final ByteArrayOutputStream actual=new ByteArrayOutputStream();local.download(f,in->{try{byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1)actual.write(buffer,0,n);}catch(IOException e){throw new UncheckedIOException(e);}});
   require(Arrays.equals(actual.toByteArray(),bytes),"ORIGINAL_DOWNLOAD_BYTES");require(sha(actual.toByteArray()).equals(sha(bytes)),"ORIGINAL_DOWNLOAD_SHA");
   if(args[1].equals("read-delete")){require(service.delete(f),"ORIGINAL_DELETE");require(!Files.exists(path),"REAL_FILE_GONE");require(!service.exists(f),"ORIGINAL_EXISTS_FALSE");}
  }
  service.destroy();require(System.getSecurityManager()==guard,"ORIGINAL_BOUNDARY_STILL_INSTALLED");require(guard.deniedCounts().isEmpty(),"NO_UNEXPECTED_BOUNDARY_DENIAL");System.out.println("ORIGINAL_LOCAL_STORAGE_CHECKS="+checks);
 }
}
