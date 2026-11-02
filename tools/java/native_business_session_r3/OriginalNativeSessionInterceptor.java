package xnby.replica;

import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import java.net.SocketTimeoutException;
import java.net.HttpURLConnection;
import java.net.Proxy;
import java.net.URI;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.core.JsonParser;
import com.cqweh.cloud.security.annotation.IgnoreAuth;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;

/** Ask the unchanged native platform about the current session after original SDK validation. */
public final class OriginalNativeSessionInterceptor implements HandlerInterceptor {
  private static final int MAX_RESPONSE_BYTES = 1048576;
  private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
      .enable(JsonParser.Feature.STRICT_DUPLICATE_DETECTION);
  private final URI currentUser;

  public OriginalNativeSessionInterceptor(String platformBase) {
    URI base = URI.create(platformBase);
    if (!"http".equals(base.getScheme()) || !"127.0.0.1".equals(base.getHost())
        || base.getPort() < 1024 || base.getPort() > 65535 || base.getRawUserInfo() != null
        || base.getRawQuery() != null || base.getRawFragment() != null
        || !(base.getRawPath() == null || base.getRawPath().isEmpty())) {
      throw new IllegalArgumentException("EXPLICIT_LOOPBACK_NATIVE_PLATFORM_BASE_REQUIRED");
    }
    currentUser = URI.create(platformBase + "/api/oauth/CurrentUser");
  }

  private static boolean blank(String value) {
    return jodd.util.StringUtil.isBlank(value);
  }

  private static boolean deny(HttpServletResponse response, boolean unavailable) throws Exception {
    response.setStatus(unavailable ? 503 : 200);
    response.setCharacterEncoding("UTF-8");
    response.setContentType("application/json;charset=UTF-8");
    response.setHeader("Cache-Control", "no-store");
    response.getWriter().write(unavailable
        ? "{\"code\":503,\"msg\":\"登录验证暂不可用，请稍后重试\",\"message\":\"登录验证暂不可用，请稍后重试\",\"data\":null}"
        : OriginalMissingAuthInterceptor.BODY);
    return false;
  }

  @Override
  public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)
      throws Exception {
    if (!(handler instanceof HandlerMethod)) return true;
    HandlerMethod method = (HandlerMethod) handler;
    String type = method.getBeanType().getName();
    if (!type.startsWith("com.iemp.endanger.") || type.contains(".rpc.")
        || method.getMethod().isAnnotationPresent(IgnoreAuth.class)) return true;
    String authorization = request.getHeader("X-TOKEN");
    if (blank(authorization)) authorization = request.getHeader("Authorization");
    // The retained missing-credentials interceptor owns this response.
    if (blank(authorization)) return true;
    if (authorization.length() > 16384 || authorization.indexOf('\r') >= 0
        || authorization.indexOf('\n') >= 0) return deny(response, false);

    HttpURLConnection connection = null;
    try {
      connection = (HttpURLConnection) currentUser.toURL().openConnection(Proxy.NO_PROXY);
      connection.setRequestMethod("GET");
      connection.setInstanceFollowRedirects(false);
      connection.setConnectTimeout(2000);
      connection.setReadTimeout(3000);
      connection.setRequestProperty("Authorization", authorization);
      connection.setRequestProperty("Accept", "application/json");
      connection.setRequestProperty("Cache-Control", "no-store");
      long deadline = System.nanoTime() + 5_000_000_000L;
      int status = connection.getResponseCode();
      if (status == 401 || status == 403) return deny(response, false);
      if (status != 200) return deny(response, true);
      byte[] body;
      if (connection.getContentLengthLong() > MAX_RESPONSE_BYTES) return deny(response, true);
      try (InputStream input = connection.getInputStream();
           ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
        byte[] buffer = new byte[8192];
        while (bytes.size() <= MAX_RESPONSE_BYTES) {
          if (System.nanoTime() >= deadline) throw new SocketTimeoutException("NATIVE_SESSION_DEADLINE");
          int count = input.read(buffer, 0, Math.min(buffer.length, MAX_RESPONSE_BYTES + 1 - bytes.size()));
          if (count < 0) break;
          bytes.write(buffer, 0, count);
        }
        body = bytes.toByteArray();
      }
      if (body.length == 0 || body.length > MAX_RESPONSE_BYTES) return deny(response, true);
      JsonNode reply = JSON.readTree(body);
      if (reply == null || !reply.isObject() || !reply.path("code").isIntegralNumber()
          || !reply.path("code").canConvertToInt())
        return deny(response, true);
      int code = reply.path("code").asInt();
      if (code == 600 || code == 401 || code == 200001) return deny(response, false);
      if (code != 200) return deny(response, true);
      JsonNode userId = reply.path("data").path("userInfo").path("userId");
      if (!userId.isTextual() || blank(userId.textValue())) return deny(response, true);
      return true;
    } catch (java.io.IOException | IllegalArgumentException error) {
      return deny(response, true);
    } finally {
      if (connection != null) connection.disconnect();
    }
  }
}
