package xnby.replica;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import cn.xuyanwu.spring.file.storage.*;
import cn.xuyanwu.spring.file.storage.platform.*;
import cn.xuyanwu.spring.file.storage.recorder.DefaultFileRecorder;
import org.springframework.boot.context.properties.bind.*;
import org.springframework.core.env.*;

/** Original Spring Binder and original local-provider bean factory; no full application or database. */
public final class PlatformStorageBindingFixture {
 static int checks;static void require(boolean v){if(!v)throw new IllegalStateException("ORIGINAL_PLATFORM_STORAGE_BINDING_FAILED");checks++;}
 public static void main(String[] args)throws Exception {
  Properties expected=new Properties();try(InputStream in=Files.newInputStream(Paths.get(args[0]))){expected.load(in);}
  Map<String,Object> values=new HashMap<>();for(String key:expected.stringPropertyNames())values.put(key,expected.getProperty(key));
  StandardEnvironment environment=new StandardEnvironment();environment.getPropertySources().remove(StandardEnvironment.SYSTEM_ENVIRONMENT_PROPERTY_SOURCE_NAME);environment.getPropertySources().remove(StandardEnvironment.SYSTEM_PROPERTIES_PROPERTY_SOURCE_NAME);environment.getPropertySources().addFirst(new MapPropertySource("owned-prepared-file-config",values));
  FileStorageProperties props=Binder.get(environment).bind("config.file-storage",Bindable.of(FileStorageProperties.class)).get();
  String local="config.file-storage.local-plus[0].",minio="config.file-storage.minio[0].";
  require(props.getDefaultPlatform().equals(expected.getProperty("config.file-storage.default-platform")));require(props.getLocalPlus().size()==1);require(props.getMinio().size()==1);
  FileStorageProperties.LocalPlus localProps=props.getLocalPlus().get(0);require(Boolean.TRUE.equals(localProps.getEnableStorage()));require(localProps.getBasePath().equals(expected.getProperty(local+"base-path")));require(localProps.getStoragePath().equals(""));
  FileStorageProperties.MinIO object=props.getMinio().get(0);require(Boolean.TRUE.equals(object.getEnableStorage()));require(object.getEndPoint().equals(expected.getProperty(minio+"end-point")));require(object.getAccessKey().equals(expected.getProperty(minio+"access-key")));require(object.getSecretKey().equals(expected.getProperty(minio+"secret-key")));require(object.getBucketName().equals(expected.getProperty(minio+"bucket-name")));
  FileStorageAutoConfiguration factory=new FileStorageAutoConfiguration();java.lang.reflect.Field field=FileStorageAutoConfiguration.class.getDeclaredField("properties");field.setAccessible(true);field.set(factory,props);
  List<LocalPlusFileStorage> providers=factory.localPlusFileStorageList();require(providers.size()==1);LocalPlusFileStorage provider=providers.get(0);require(provider.getPlatform().equals(props.getDefaultPlatform()));require(provider.getBasePath().equals(localProps.getBasePath()));
  Path root=Paths.get(provider.getBasePath()).toRealPath();OriginalProcessBoundary guard=new OriginalProcessBoundary(root,Collections.<Integer>emptySet(),false);System.setSecurityManager(guard);
  List<List<? extends FileStorage>> selected=new ArrayList<>();selected.add(providers);
  FileStorageService service=factory.fileStorageService(new DefaultFileRecorder(),selected,Collections.<cn.xuyanwu.spring.file.storage.aspect.FileStorageAspect>emptyList());service.setSelf(service);require(service.getFileStorage()==provider);
  byte[] payload="owned-original-platform-bound-config-probe".getBytes(StandardCharsets.US_ASCII);
  FileInfo file=service.of(payload).setPath("own-probe/").setSaveFilename("owned-binding.txt").setOriginalFilename("owned-binding.txt").upload();require(file!=null);require(service.exists(file));
  Path actual=root.resolve("own-probe/owned-binding.txt");require(Arrays.equals(Files.readAllBytes(actual),payload));ByteArrayOutputStream bytes=new ByteArrayOutputStream();provider.download(file,in->{try{byte[] buffer=new byte[4096];int n;while((n=in.read(buffer))!=-1)bytes.write(buffer,0,n);}catch(IOException e){throw new UncheckedIOException(e);}});require(Arrays.equals(bytes.toByteArray(),payload));require(service.delete(file));require(!Files.exists(actual));
  service.destroy();require(System.getSecurityManager()==guard);System.out.println("ORIGINAL_BINDING_BOUNDARY_DENIALS="+guard.deniedCounts());require(guard.deniedCounts().isEmpty());System.out.println("PLATFORM_STORAGE_BINDING_CHECKS="+checks);
 }
}
