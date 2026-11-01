package xnby.replica;
import java.nio.file.*;import java.util.*;import java.io.*;import java.lang.reflect.Proxy;import java.security.MessageDigest;
import org.springframework.context.*;import org.springframework.context.event.ContextRefreshedEvent;import org.springframework.aop.support.AopUtils;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;
import jakarta.servlet.*;import jakarta.servlet.http.HttpServletResponse;import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import com.iemp.endanger.server.hidden.controller.RiskLevelController;
public final class OriginalPublicRiskObservation implements ApplicationListener<ContextRefreshedEvent>{
 static ConfigurableApplicationContext captured;
 public void onApplicationEvent(ContextRefreshedEvent event){if(event.getApplicationContext() instanceof ConfigurableApplicationContext candidate&&candidate.getBeanFactory().containsLocalBean("requestMappingHandlerMapping")){captured=candidate;OwnReadOnlyLoginSnapshot.register(candidate);}}
 static String sha(Class<?> type)throws Exception{try(var in=type.getResourceAsStream('/'+type.getName().replace('.','/')+".class")){return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(in.readAllBytes()));}}
 static void need(boolean value,String message){if(!value)throw new IllegalStateException(message);}
 public static void main(String[] args)throws Exception{
  try{inspect(args);}catch(Exception failure){Files.writeString(Path.of(args[0]).resolve("public-risk-chain-observation-failed.json"),new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(Map.of("exceptionType",failure.getClass().getName(),"additionalObserverRejected",true)));throw failure;}
 }
 static void inspect(String[] args)throws Exception{
  OriginalBusinessLaunch.main(args);var context=captured;Path root=Path.of(args[0]);need(context!=null&&context.isActive(),"ACTUAL_PUBLIC_BUSINESS_MAIN_CONTEXT_REQUIRED");
  need(sha(OriginalBusinessLaunch.class).equals("64d03e5bdbcf149dba8424bd0b6ea0467845feb371b87121319bf3d068871307"),"EXACT_PUBLISHED_LAUNCHER_REQUIRED");
  need(sha(System.getSecurityManager().getClass()).equals("9523d118575d9191961f8d7ad50ddd528e756536875d69e7023dbcc2aead561a"),"EXACT_PUBLISHED_LISTEN_BOUNDARY_REQUIRED");
  need(context.getClassLoader().getResource("xnby/replica/OriginalTaskIdentityBusinessLaunch.class")==null,"R10_TASK_LAYER_MUST_BE_ABSENT");
  int original=0,missing=0;for(var i:context.getBean("requestMappingHandlerMapping",RequestMappingHandlerMapping.class).getAdaptedInterceptors()){if(i.getClass().getName().equals("com.cqweh.cloud.security.core.SecurityInterceptor"))original++;if(i.getClass().getName().equals("xnby.replica.OriginalMissingAuthInterceptor"))missing++;}need(original==1&&missing==1,"PUBLISHED_ORIGINAL_AND_MISSING_AUTH_GUARDS_REQUIRED");
  int sdkPosition=-1,sessionPosition=-1,sessionCount=0;var interceptors=context.getBean("requestMappingHandlerMapping",RequestMappingHandlerMapping.class).getAdaptedInterceptors();for(int i=0;i<interceptors.length;i++){if(interceptors[i].getClass().getName().equals("com.cqweh.cloud.security.core.SecurityInterceptor"))sdkPosition=i;if(interceptors[i].getClass()==OriginalNativeSessionInterceptor.class){sessionPosition=i;sessionCount++;}}need(sessionCount==1&&sessionPosition>sdkPosition,"DECLARED_SESSION_GUARD_AFTER_ORIGINAL_SDK_REQUIRED");need(Files.isRegularFile(root.resolve("native-session-guard-ready.properties")),"NATIVE_SESSION_READY_RECEIPT_REQUIRED");
  OriginalRiskBatchTimeFixture.verify(context,root);OriginalRiskWholeImportFixture.verify(context,root);
  var bytes=new ByteArrayOutputStream();var stream=new ServletOutputStream(){public boolean isReady(){return true;}public void setWriteListener(WriteListener l){}public void write(int b){bytes.write(b);}};
  var response=(HttpServletResponse)Proxy.newProxyInstance(HttpServletResponse.class.getClassLoader(),new Class<?>[]{HttpServletResponse.class},(p,m,a)->{if(m.getName().equals("getOutputStream"))return stream;if(m.getName().equals("getWriter"))return new PrintWriter(bytes);if(m.getReturnType()==boolean.class)return false;if(m.getReturnType()==int.class)return 0;return null;});
  context.getBean(RiskLevelController.class).importExcel(response);Files.write(root.resolve("public-chain-native-risk-template.xlsx"),bytes.toByteArray());
  try(var workbook=new XSSFWorkbook(new ByteArrayInputStream(bytes.toByteArray()))){need(workbook.getNumberOfSheets()==1&&workbook.getSheetAt(0).getLastRowNum()==0&&workbook.getSheetAt(0).getRow(0).getPhysicalNumberOfCells()==6,"ACTUAL_NATIVE_EMPTY_TEMPLATE_SIX_COLUMNS_REQUIRED");}
  var result=new TreeMap<String,Object>();result.put("actualPublishedBusinessLaunchAndBoundary",true);result.put("additionalNativeSessionGuardDeclaredAndAfterOriginalSDK",true);result.put("additionalObservationListenerDeclared",true);result.put("R10TaskAndFontCacheAuthLifecyclePrototypesAbsent",true);result.put("originalSecurityInterceptors",original);result.put("originalMissingAuthInterceptors",missing);result.put("nativeTemplateSixColumnsAndNoDataRows",true);result.put("riskControllerClassSHA256",sha(AopUtils.getTargetClass(context.getBean(RiskLevelController.class))));result.put("formalOrPublicChanged",false);Files.writeString(root.resolve("public-risk-chain-result.json"),new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(result));
 }
}
