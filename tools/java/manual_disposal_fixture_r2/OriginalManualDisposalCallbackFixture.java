package xnby.replica;
import com.fasterxml.jackson.databind.*;
import jakarta.servlet.*;import jakarta.servlet.http.*;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.security.*;import java.util.*;
import org.springframework.boot.context.event.ApplicationPreparedEvent;import org.springframework.beans.factory.support.*;import org.springframework.boot.web.servlet.FilterRegistrationBean;import org.springframework.context.*;
import org.springframework.web.filter.OncePerRequestFilter;import org.springframework.web.util.ContentCachingResponseWrapper;
/** Observe callback status/code only in the exact owned short fixture. No production entries are replaced. */
public final class OriginalManualDisposalCallbackFixture implements ApplicationListener<ApplicationPreparedEvent> {
 static final ObjectMapper JSON=new ObjectMapper();static final List<Map<String,Object>> CALLS=new ArrayList<>();static boolean closed;
 static Path root()throws Exception {Path p=Path.of(System.getProperty("own.fixture.manual.callback.root")).toRealPath();if(!p.startsWith(Path.of("D:/Project/Zhumadian/_b/Application/UserData/OriginalServer/runs/j1").toRealPath())||!p.getFileName().toString().equals("b"))throw new IllegalStateException("OWN_CALLBACK_OBSERVATION_ROOT_REQUIRED");return p;}
 static synchronized void save()throws Exception {Path p=root().resolve("manual-disposal-callback-observation.json"),next=p.resolveSibling(p.getFileName()+".next");Files.write(next,JSON.writeValueAsBytes(Map.of("callbacks",CALLS,"closed",closed,"headersTokensOrResponseBodiesRecorded",false)));Files.move(next,p,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);}
 @Override public void onApplicationEvent(ApplicationPreparedEvent event){ConfigurableApplicationContext context=event.getApplicationContext();((BeanDefinitionRegistry)context.getBeanFactory()).registerBeanDefinition("ownManualDisposalCallbackFixture",new RootBeanDefinition(Registration.class));}
 public static final class Registration extends FilterRegistrationBean<OncePerRequestFilter> {
  public Registration(){setName("ownManualDisposalCallbackFixture");addUrlPatterns("/*");setOrder(-100);setFilter(new OncePerRequestFilter(){
   @Override protected void doFilterInternal(HttpServletRequest request,HttpServletResponse response,FilterChain chain)throws java.io.IOException,ServletException {
    if(!request.getRequestURI().equals("/serv/eventTask/callback")||!request.getMethod().equals("GET")){chain.doFilter(request,response);return;}
    var cached=new ContentCachingResponseWrapper(response);
    try{chain.doFilter(request,cached);}finally{
     try{byte[] raw=cached.getContentAsByteArray();if(raw.length>32768)throw new IllegalStateException("BOUNDED_OWN_CALLBACK_RESPONSE_REQUIRED");JsonNode body=JSON.readTree(raw);Map<String,Object> row=new LinkedHashMap<>();row.put("httpStatus",cached.getStatus());row.put("businessCode",body.path("code").asInt(-1));row.put("instanceIdSHA256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(request.getParameter("id").getBytes(StandardCharsets.UTF_8))));row.put("result","1".equals(request.getParameter("result")));synchronized(OriginalManualDisposalCallbackFixture.class){if(CALLS.size()>=16)throw new IllegalStateException("BOUNDED_OWN_CALLBACK_OBSERVATIONS_REQUIRED");CALLS.add(row);save();}}
     catch(Exception e){throw new ServletException("OWN_CALLBACK_STATUS_OBSERVATION_FAILED",e);}finally{cached.copyBodyToResponse();}
    }
   }
   @Override public void destroy(){synchronized(OriginalManualDisposalCallbackFixture.class){closed=true;try{save();}catch(Exception e){throw new IllegalStateException("OWN_CALLBACK_OBSERVER_CLOSE_FAILED",e);}}super.destroy();}
  });}
 }
}
