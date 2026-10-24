package xnby.replica;
import java.io.*;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import com.cqweh.cloud.common.model.Response;
import com.iemp.endanger.minio.MinioConfig;
import com.iemp.endanger.server.file.service.SysFileService;
import io.minio.*;
import org.springframework.context.*;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.web.multipart.MultipartFile;

/** Observe the real Spring-owned original file beans, never an HTTP authentication substitute. */
@SuppressWarnings("rawtypes")
public final class OriginalObjectStoreObservation implements ApplicationContextInitializer<ConfigurableApplicationContext> {
 static void require(boolean value,String code){if(!value)throw new IllegalStateException(code);}
 static String sha(byte[] bytes)throws Exception{StringBuilder out=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(bytes))out.append(String.format("%02x",b&255));return out.toString();}
 static final class OwnPart implements MultipartFile {
  final byte[] bytes;OwnPart(byte[] bytes){this.bytes=bytes;}
  public String getName(){return "file";}public String getOriginalFilename(){return "own-spring-probe.txt";}public String getContentType(){return "text/plain";}public boolean isEmpty(){return false;}public long getSize(){return bytes.length;}public byte[] getBytes(){return bytes.clone();}public InputStream getInputStream(){return new ByteArrayInputStream(bytes);}public void transferTo(File file){throw new UnsupportedOperationException();}
 }
 public void initialize(final ConfigurableApplicationContext context){
  boolean servlet=false;for(java.lang.reflect.Method method:context.getClass().getMethods())if(method.getName().equals("getServletContext")&&method.getParameterCount()==0)servlet=true;if(!servlet)return;
  final Path root=Paths.get(System.getProperty("own.candidate.root"));
  context.addApplicationListener(event->{if(!(event instanceof ApplicationReadyEvent)||((ApplicationReadyEvent)event).getApplicationContext()!=context)return;
   Thread worker=new Thread(()->{Properties result=new Properties();
    try {
     String owner=System.getProperty("own.object-store.probe.owner","");require(owner.matches("[a-f0-9-]{36}"),"OWN_STORE_PROBE_OWNER_REQUIRED");
     Properties expected=new Properties();try(InputStream input=Files.newInputStream(root.resolve("application.properties"))){expected.load(input);}
     MinioConfig config=context.getBean(MinioConfig.class);
     for(String name:new String[]{"url","port","secure","accessKey","secretKey","bucketName"}){Field field=MinioConfig.class.getDeclaredField(name);field.setAccessible(true);require(String.valueOf(field.get(config)).equals(expected.getProperty("minio."+name)),"OWN_STORE_ORIGINAL_BEAN_BINDING_MISMATCH");}
     result.setProperty("originalBeanBindingsMatched","6");
     byte[] payload=("owned-original-spring-file-probe:"+owner).getBytes(StandardCharsets.US_ASCII);
     SysFileService service=context.getBean(SysFileService.class);MinioClient client=context.getBean(MinioClient.class);
     Response response=service.uploadFile(new OwnPart(payload));require(response.getCode()==Response.SUCCESS&&response.getData() instanceof Map,"OWN_ORIGINAL_BEAN_UPLOAD_RESPONSE");
     Map data=(Map)response.getData();String bucket=(String)data.get("bucketName"),object=(String)data.get("fileName"),url=(String)data.get("url");
     require(config.getBucketName().equals(bucket)&&object!=null&&object.matches("[a-fA-F0-9-]{36}\\.txt")&&("/sys-file/"+bucket+"/"+object).equals(url),"OWN_SYNTHETIC_OBJECT_IDENTITY_MISMATCH");
     require(client.statObject(StatObjectArgs.builder().bucket(bucket).object(object).build()).size()==payload.length,"OWN_ORIGINAL_CLIENT_OBJECT_STAT_MISMATCH");
     String encoded=service.getFileBase64(bucket,object);require(encoded!=null&&Arrays.equals(Base64.getDecoder().decode(encoded),payload),"OWN_ORIGINAL_SPRING_READBACK_MISMATCH");
     result.setProperty("bucket",bucket);result.setProperty("object",object);result.setProperty("url",url);result.setProperty("probeOwner",owner);result.setProperty("payloadBytes",Integer.toString(payload.length));result.setProperty("payloadSHA256",sha(payload));result.setProperty("originalBeanUploadAndBase64ReadbackExact","true");result.setProperty("passed","true");
    }catch(Exception error){result.setProperty("passed","false");result.setProperty("failureClass",error.getClass().getName());try{StringWriter text=new StringWriter();error.printStackTrace(new PrintWriter(text));Files.write(root.resolve("object-store-failure.private.log"),text.toString().getBytes(StandardCharsets.UTF_8),StandardOpenOption.CREATE_NEW);}catch(Exception ignored){}}
    result.setProperty("authenticatedHTTPUploadVerified","false");result.setProperty("historicalObjectsRecovered","false");
    try{Path pending=root.resolve("object-store-observation.pending"),target=root.resolve("object-store-observation.private.properties");try(OutputStream output=Files.newOutputStream(pending,StandardOpenOption.CREATE_NEW)){result.store(output,"Owned synthetic object identity for bounded gateway readback and cleanup only");}Files.move(pending,target,StandardCopyOption.ATOMIC_MOVE);}catch(Exception error){throw new IllegalStateException("OWN_STORE_OBSERVATION_WRITE_FAILED",error);}
   },"own-original-object-store-observer");worker.setDaemon(true);worker.start();
  });
 }
}
