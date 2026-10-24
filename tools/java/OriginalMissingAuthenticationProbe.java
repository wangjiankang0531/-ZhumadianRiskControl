package xnby.replica;
import java.lang.reflect.*;import java.util.*;
import jakarta.servlet.http.*;
import org.springframework.web.method.HandlerMethod;
import com.cqweh.cloud.security.core.SecurityInterceptor;
public final class OriginalMissingAuthenticationProbe {
 public static void main(String[] args)throws Exception {
  Class<?> controller=Class.forName("com.iemp.endanger.server.emergencyResponse.controller.EventDisposalRecordController",false,OriginalMissingAuthenticationProbe.class.getClassLoader());
  Method method=controller.getDeclaredMethod("getListByEventId",String.class);
  HandlerMethod handler=new HandlerMethod(new Object(),method);
  List<String> headers=new ArrayList<>();
  HttpServletRequest request=(HttpServletRequest)Proxy.newProxyInstance(HttpServletRequest.class.getClassLoader(),new Class[]{HttpServletRequest.class},(proxy,m,values)->{
   if(m.getName().equals("getHeader")){headers.add((String)values[0]);return null;}
   if(m.getReturnType()==boolean.class)return false;
   if(m.getReturnType()==int.class)return 0;
   return null;
  });
  HttpServletResponse response=(HttpServletResponse)Proxy.newProxyInstance(HttpServletResponse.class.getClassLoader(),new Class[]{HttpServletResponse.class},(proxy,m,values)->null);
  try{new SecurityInterceptor().preHandle(request,response,handler);throw new AssertionError("ORIGINAL_MISSING_AUTH_FAILURE_NOT_REPRODUCED");}
  catch(NullPointerException error){
   if(!headers.equals(Arrays.asList("X-TOKEN","Authorization")))throw new AssertionError("UNEXPECTED_HEADER_READS");
   StackTraceElement top=error.getStackTrace()[0];if(!top.getClassName().equals(SecurityInterceptor.class.getName())||!top.getMethodName().equals("preHandle"))throw new AssertionError("UNEXPECTED_FAILURE_LOCATION");
   System.out.println("originalInterceptorMissingAuthNullPointerReproduced=true headersRead=X-TOKEN,Authorization controllerMethodInvoked=false databaseConnected=false realTokenReadOrCreated=false");
   System.out.println("failureMessage="+error.getMessage());
  }
 }
}
