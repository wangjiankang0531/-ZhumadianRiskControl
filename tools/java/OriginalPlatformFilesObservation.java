package xnby.platform;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import cn.xuyanwu.spring.file.storage.*;
import cn.xuyanwu.spring.file.storage.platform.*;
import org.springframework.context.*;
import org.springframework.boot.context.event.ApplicationReadyEvent;

/** Real original Spring file beans and static helper, with an owned probe retained across two runs. */
public final class OriginalPlatformFilesObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static void require(boolean v,String code){if(!v)throw new IllegalStateException(code);}
 static Properties read(Path path)throws Exception {Properties p=new Properties();try(InputStream in=Files.newInputStream(path)){p.load(in);}return p;}
 static void publish(Path file,Properties value)throws Exception {Path pending=file.resolveSibling(file.getFileName()+".pending");try(OutputStream out=Files.newOutputStream(pending,StandardOpenOption.CREATE_NEW)){value.store(out,"Owned original-platform file observation; private path identity");}Files.move(pending,file,StandardCopyOption.ATOMIC_MOVE);}
 static String sha(byte[] b)throws Exception {StringBuilder out=new StringBuilder();for(byte x:MessageDigest.getInstance("SHA-256").digest(b))out.append(String.format("%02x",x&255));return out.toString();}
 public void initialize(final ConfigurableApplicationContext context) {
  boolean servlet=false;for(java.lang.reflect.Method method:context.getClass().getMethods())if(method.getName().equals("getServletContext")&&method.getParameterCount()==0)servlet=true;if(!servlet)return;
  context.addApplicationListener(event->{if(!(event instanceof ApplicationReadyEvent)||((ApplicationReadyEvent)event).getApplicationContext()!=context)return;
   Thread worker=new Thread(()->{Path run=Paths.get(System.getProperty("own.platform.root"));Properties result=new Properties();
    try {
     Path data=Paths.get(System.getProperty("own.platform.data.root")).toRealPath(),files=data.resolve("files").toRealPath(),marker=data.resolve("owned-restart-probe.private.properties");
     String dataOwner=System.getProperty("own.platform.data.owner"),runOwner=System.getProperty("own.platform.file-probe.owner");boolean recover=Boolean.getBoolean("own.platform.file-probe.recover");require(runOwner!=null&&UUID.fromString(runOwner).toString().equals(runOwner),"OWN_PLATFORM_PROBE_RUN_UUID_REQUIRED");
     Properties expected=read(run.resolve("application.properties"));FileStorageProperties props=context.getBean(FileStorageProperties.class);FileStorageService service=context.getBean(FileStorageService.class);
     String l="config.file-storage.local-plus[0].",m="config.file-storage.minio[0].";
     require(props.getDefaultPlatform().equals(expected.getProperty("config.file-storage.default-platform")),"ORIGINAL_DEFAULT_PROVIDER_BINDING");
     require(props.getLocalPlus().size()==1&&props.getMinio().size()==1,"ORIGINAL_TWO_PROVIDER_BINDINGS");
     FileStorageProperties.LocalPlus local=props.getLocalPlus().get(0);require(Boolean.TRUE.equals(local.getEnableStorage())&&local.getBasePath().equals(expected.getProperty(l+"base-path"))&&local.getStoragePath().equals(""),"ORIGINAL_LOCAL_STORAGE_BINDINGS");
     FileStorageProperties.MinIO object=props.getMinio().get(0);require(Boolean.TRUE.equals(object.getEnableStorage())&&object.getPlatform().equals(expected.getProperty(m+"platform"))&&object.getEndPoint().equals(expected.getProperty(m+"end-point"))&&object.getAccessKey().equals(expected.getProperty(m+"access-key"))&&object.getSecretKey().equals(expected.getProperty(m+"secret-key"))&&object.getBucketName().equals(expected.getProperty(m+"bucket-name")),"ORIGINAL_OBJECT_STORAGE_BINDINGS");
     require(service.getFileStorage() instanceof LocalPlusFileStorage&&service.getFileStorage().getPlatform().equals(props.getDefaultPlatform()),"ORIGINAL_LOCAL_PROVIDER_ACTUALLY_SELECTED");
     require(Paths.get(((LocalPlusFileStorage)service.getFileStorage()).getBasePath()).toRealPath().equals(files),"ORIGINAL_LOCAL_PHYSICAL_ROOT_BINDING");
     Class<?> configClass=Class.forName("jnpf.config.LocalPathConfig");Object config=context.getBean(configClass);int matched=0;
     for(String key:expected.stringPropertyNames())if(key.startsWith("config.")&&key.endsWith("Path")) {
      String wanted=key.substring(7).toLowerCase(Locale.ROOT);java.lang.reflect.Field found=null;for(java.lang.reflect.Field field:configClass.getDeclaredFields())if(field.getName().toLowerCase(Locale.ROOT).equals(wanted))found=field;
      require(found!=null,"ORIGINAL_LOGICAL_PATH_FIELD_REQUIRED");found.setAccessible(true);require(expected.getProperty(key).equals(found.get(config)),"ORIGINAL_LOGICAL_PATH_BINDING_MISMATCH");matched++;
     }
     require(matched==13,"ORIGINAL_THIRTEEN_LOGICAL_PATH_BINDINGS_REQUIRED");result.setProperty("originalLogicalPathBeanBindingsMatched","13");result.setProperty("originalLocalAndObjectProviderBindingsMatched","true");
     Class<?> helper=Class.forName("jnpf.util.FileUploadUtils");String path=(String)Class.forName("jnpf.util.FilePathUtil").getMethod("getFilePath",String.class).invoke(null,"annex");require(path!=null&&path.equals(expected.getProperty("config.WebAnnexFilePath")+"/")&&path.matches("[A-Za-z0-9_/-]+/")&&!path.contains(".."),"ORIGINAL_ANNEX_LOGICAL_PATH_HELPER_REQUIRED");
     Properties probe;boolean previous=Files.exists(marker);
     if(recover) {
      require(previous,"EXISTING_OWN_PLATFORM_RESTART_PROBE_REQUIRED");probe=read(marker);require(dataOwner.equals(probe.getProperty("dataOwnerId"))&&!runOwner.equals(probe.getProperty("runOwnerId"))&&path.equals(probe.getProperty("logicalPath")),"PREVIOUS_PROBE_OWNER_AND_PATH_REQUIRED");
     }else {
      require(!previous,"EXPLICIT_RECOVERY_REQUIRED_FOR_RETAINED_PLATFORM_PROBE");byte[] payload=("owned-original-platform-file-probe:"+dataOwner+":"+runOwner).getBytes(StandardCharsets.US_ASCII);
      FileInfo uploaded=(FileInfo)helper.getMethod("uploadFile",byte[].class,String.class,String.class).invoke(null,payload,path,"own-platform-probe.txt");require(uploaded!=null&&uploaded.getFilename()!=null&&uploaded.getFilename().matches("[A-Za-z0-9_-]{8,128}\\.txt"),"ORIGINAL_PLATFORM_UPLOAD_IDENTITY_REQUIRED");
      probe=new Properties();probe.setProperty("dataOwnerId",dataOwner);probe.setProperty("runOwnerId",runOwner);probe.setProperty("logicalPath",path);probe.setProperty("filename",uploaded.getFilename());probe.setProperty("payloadSHA256",sha(payload));probe.setProperty("payloadBytes",Integer.toString(payload.length));publish(marker,probe);
     }
     String filename=probe.getProperty("filename");require(filename!=null&&filename.matches("[A-Za-z0-9_-]{8,128}\\.txt"),"OWN_PLATFORM_FILE_IDENTITY_REQUIRED");
     byte[] payload=("owned-original-platform-file-probe:"+dataOwner+":"+probe.getProperty("runOwnerId")).getBytes(StandardCharsets.US_ASCII),actual=(byte[])helper.getMethod("downloadFileByte",String.class,String.class,boolean.class).invoke(null,path,filename,false);
     Path actualPath=files.resolve(path).resolve(filename).normalize();require(actualPath.startsWith(files)&&Arrays.equals(actual,payload)&&Arrays.equals(Files.readAllBytes(actualPath),payload)&&sha(actual).equals(probe.getProperty("payloadSHA256")),"ORIGINAL_PLATFORM_FILE_READBACK_MISMATCH");
     result.putAll(probe);result.setProperty("probeDataRetainedFromPreviousRun",Boolean.toString(recover));result.setProperty("originalSpringStaticHelperUploadOrRestartReadbackExact","true");result.setProperty("originalFileRecorderDatabasePersistenceVerified","false");result.setProperty("passed","true");publish(run.resolve("platform-files-observation.private.properties"),result);
     while(context.isActive()&&!Files.exists(run.resolve("cleanup-owned-file-probe")))Thread.sleep(200);
     if(context.isActive()&&Files.exists(run.resolve("cleanup-owned-file-probe"))) {
      Properties known=read(marker);require(known.equals(probe),"OWN_PLATFORM_PROBE_CHANGED_BEFORE_CLEANUP");byte[] current=(byte[])helper.getMethod("downloadFileByte",String.class,String.class,boolean.class).invoke(null,path,filename,false);require(Arrays.equals(current,payload),"OWN_PLATFORM_PROBE_PAYLOAD_BEFORE_CLEANUP");
      require(Boolean.TRUE.equals(helper.getMethod("deleteFileByPathAndFileName",String.class,String.class).invoke(null,path,filename))&&!Files.exists(actualPath),"ORIGINAL_PLATFORM_SYNTHETIC_DELETE_REQUIRED");Files.delete(marker);Properties cleaned=new Properties();cleaned.setProperty("onlyOwnedSyntheticProbeRemoved","true");cleaned.setProperty("dataOwnerId",dataOwner);cleaned.setProperty("originalHelperDeletePassed","true");publish(run.resolve("platform-file-probe-cleaned.properties"),cleaned);
     }
    }catch(Exception error) {
     try{StringWriter text=new StringWriter();error.printStackTrace(new PrintWriter(text));Files.write(run.resolve("platform-files-failure.private.log"),text.toString().getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);if(!Files.exists(run.resolve("platform-files-observation.private.properties"))){result.setProperty("passed","false");result.setProperty("failureClass",error.getClass().getName());publish(run.resolve("platform-files-observation.private.properties"),result);}}catch(Exception ignored){}
    }
   },"own-original-platform-files-observer");worker.setDaemon(true);worker.start();
  });
 }
}
