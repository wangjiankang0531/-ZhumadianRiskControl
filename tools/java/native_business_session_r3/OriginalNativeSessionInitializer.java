package xnby.replica;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Properties;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.ApplicationContextInitializer;
import org.springframework.context.ApplicationListener;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.core.Ordered;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.mvc.method.annotation.RequestMappingHandlerMapping;
import com.cqweh.cloud.security.core.SecurityInterceptor;

/** Retain original token validation and then enforce the original platform's current session state. */
public final class OriginalNativeSessionInitializer
    implements ApplicationContextInitializer<ConfigurableApplicationContext>, WebMvcConfigurer {
  private OriginalNativeSessionInterceptor guard;

  @Override
  public void addInterceptors(InterceptorRegistry registry) {
    if (guard == null) throw new IllegalStateException("NATIVE_SESSION_GUARD_NOT_PREPARED");
    registry.addInterceptor(guard).order(Ordered.LOWEST_PRECEDENCE);
  }

  @Override
  public void initialize(ConfigurableApplicationContext context) {
    if (!(context instanceof org.springframework.web.context.ConfigurableWebApplicationContext)) return;
    Path root = Path.of(System.getProperty("own.candidate.root")).toAbsolutePath().normalize();
    try {
      if (!root.toRealPath().equals(root) || !root.getFileName().toString().equals("b")
          || !root.getParent().getFileName().toString().matches("j[1-9][0-9]{0,3}")
          || !root.getParent().getParent().getFileName().toString().equals("runs")
          || !root.getParent().getParent().getParent().getFileName().toString().equals("OriginalServer"))
        throw new IllegalStateException("OWN_BUSINESS_SESSION_ROOT_REQUIRED");
      Properties owner = new Properties();
      try (var input = Files.newInputStream(root.resolve("server-owner.properties"))) { owner.load(input); }
      if (!"zhumadian.original.server.owner.v1".equals(owner.getProperty("schema"))
          || !owner.getProperty("ownerId", "").equals(System.getProperty("own.server.owner")))
        throw new IllegalStateException("OWN_BUSINESS_SESSION_OWNER_REQUIRED");
    } catch (Exception error) { throw new IllegalStateException("NATIVE_SESSION_SCOPE_REJECTED", error); }
    guard = new OriginalNativeSessionInterceptor(System.getProperty("own.internal.platform.base"));
    context.addBeanFactoryPostProcessor(factory -> {
      if (factory.containsBean("ownNativeSessionConfigurer"))
        throw new IllegalStateException("FRESH_NATIVE_SESSION_BEAN_REQUIRED");
      factory.registerSingleton("ownNativeSessionConfigurer", this);
    });
    context.addApplicationListener((ApplicationListener<ApplicationReadyEvent>) event -> {
      if (event.getApplicationContext() != context) return;
      HandlerInterceptor[] all = context.getBean("requestMappingHandlerMapping",
          RequestMappingHandlerMapping.class).getAdaptedInterceptors();
      int sdk = -1, session = -1, sdkCount = 0, sessionCount = 0;
      for (int i = 0; i < all.length; i++) {
        if (all[i].getClass() == SecurityInterceptor.class) { sdk = i; sdkCount++; }
        if (all[i].getClass() == OriginalNativeSessionInterceptor.class) { session = i; sessionCount++; }
      }
      if (sdkCount != 1 || sessionCount != 1 || session <= sdk)
        throw new IllegalStateException("ONE_SESSION_GUARD_AFTER_RETAINED_SDK_REQUIRED");
      try {
        Files.write(root.resolve("native-session-guard-ready.properties"), List.of(
            "schema=xnby.original-native-session-guard.v1", "guardCount=1",
            "originalSDKCount=1", "guardAfterOriginalSDK=true", "originalSigningAndPermissionsRetained=true",
            "nativeCurrentSessionChecked=true", "localPositiveCache=false", "unavailableFailsClosed=true"),
            StandardOpenOption.CREATE_NEW);
      } catch (Exception error) { throw new IllegalStateException("NATIVE_SESSION_RECEIPT_FAILED", error); }
    });
  }
}
