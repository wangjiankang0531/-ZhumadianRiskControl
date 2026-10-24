package xnby.platform;
import xnby.compat.Java8IO;
import java.nio.file.*;
import java.io.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.SpringApplicationRunListener;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.Ordered;

/** Preserve the original failure before an unavailable logging class can mask it. */
public final class PlatformFailureObservation implements SpringApplicationRunListener,Ordered{
 public PlatformFailureObservation(SpringApplication application,String[] arguments){}
 public int getOrder(){return Ordered.HIGHEST_PRECEDENCE;}
 public void failed(ConfigurableApplicationContext context,Throwable error){
  try{
   Path root=Paths.get(System.getProperty("own.platform.root"));
   StringWriter text=new StringWriter();error.printStackTrace(new PrintWriter(text));
   Java8IO.writeString(root.resolve("original-failure-before-reporting.private.log"),text.toString(),StandardOpenOption.CREATE_NEW);
  }catch(Exception observationError){System.err.println("OWN_PLATFORM_ORIGINAL_FAILURE_OBSERVATION_FAILED");}
 }
}
