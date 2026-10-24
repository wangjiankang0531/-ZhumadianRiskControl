package xnby.replica;

import com.iemp.endanger.minio.MinioConfig;
import com.iemp.endanger.server.file.service.impl.SysFileServiceImpl;
import com.cqweh.cloud.common.model.Response;
import com.sun.net.httpserver.HttpServer;
import io.minio.MinioClient;
import jakarta.servlet.http.HttpServletResponse;
import okhttp3.OkHttpClient;
import org.springframework.web.multipart.MultipartFile;
import java.io.*;
import java.lang.reflect.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** A deliberately failing local HTTP transport, never a replacement object store. */
@SuppressWarnings({"removal", "rawtypes"})
public final class OriginalFileFailureFixture {
    static int checks;
    static void check(boolean value) { if (!value) throw new AssertionError("FILE_FAILURE_OBSERVATION_MISMATCH"); checks++; }
    static final class OwnPart implements MultipartFile {
        private final byte[] bytes = "own synthetic attachment fixture".getBytes(StandardCharsets.US_ASCII);
        public String getName() { return "file"; }
        public String getOriginalFilename() { return "own-fixture.txt"; }
        public String getContentType() { return "text/plain"; }
        public boolean isEmpty() { return false; }
        public long getSize() { return bytes.length; }
        public byte[] getBytes() { return bytes.clone(); }
        public InputStream getInputStream() { return new ByteArrayInputStream(bytes); }
        public void transferTo(File destination) { throw new UnsupportedOperationException("NO_FIXTURE_FILE_WRITES"); }
    }
    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args[0]).toRealPath();
        Path sentinel = root.resolve("sentinel.txt");
        Files.write(sentinel, "unchanged".getBytes(StandardCharsets.US_ASCII));
        AtomicInteger requests = new AtomicInteger(), puts = new AtomicInteger(), statusesSet = new AtomicInteger(), outputRequested = new AtomicInteger();
        HttpServer server = HttpServer.create(new InetSocketAddress(InetAddress.getByAddress(new byte[]{127,0,0,1}), 0), 8);
        server.createContext("/", exchange -> {
            requests.incrementAndGet();
            if (exchange.getRequestMethod().equals("PUT")) puts.incrementAndGet();
            byte[] failure = "<Error><Code>ServiceUnavailable</Code><Message>Owned negative fixture only</Message><RequestId>own</RequestId></Error>".getBytes(StandardCharsets.US_ASCII);
            exchange.getResponseHeaders().set("Content-Type", "application/xml");
            if (exchange.getRequestMethod().equals("HEAD")) exchange.sendResponseHeaders(503, -1);
            else { exchange.sendResponseHeaders(503, failure.length); exchange.getResponseBody().write(failure); }
            exchange.close();
        });
        int port = server.getAddress().getPort();
        OriginalProcessBoundary guard = new OriginalProcessBoundary(root, Collections.singleton(port), true);
        System.setSecurityManager(guard);
        server.start();
        OkHttpClient http = null;
        try {
            http = new OkHttpClient.Builder().connectTimeout(1, TimeUnit.SECONDS).readTimeout(1, TimeUnit.SECONDS)
                .callTimeout(2, TimeUnit.SECONDS).retryOnConnectionFailure(false).build();
            MinioClient client = MinioClient.builder().endpoint("http://127.0.0.1:" + port)
                .credentials("own-fixture-only", UUID.randomUUID().toString()).httpClient(http).build();
            MinioConfig config = new MinioConfig();
            Field bucket = MinioConfig.class.getDeclaredField("bucketName"); bucket.setAccessible(true); bucket.set(config, "own-fixture-bucket");
            SysFileServiceImpl service = new SysFileServiceImpl(client, config);
            Response upload = service.uploadFile(new OwnPart());
            check(requests.get() > 0); check(puts.get() == 0);
            check(upload.getCode() == Response.SUCCESS);
            check(upload.getData() instanceof Map);
            Map data = (Map) upload.getData();
            check(data.get("url") instanceof String && ((String) data.get("url")).startsWith("/sys-file/own-fixture-bucket/"));
            check(data.containsKey("fileName") && data.containsKey("bucketName"));
            int afterUpload = requests.get();
            Response pdf = service.uploadPdf(new ByteArrayInputStream(new byte[]{37,80,68,70}));
            check(pdf.getCode() == Response.SUCCESS); check(requests.get() > afterUpload); check(puts.get() == 0);
            int afterPdf = requests.get();
            check(service.getFileBase64("own-fixture-bucket", "missing.txt") == null);
            check(requests.get() > afterPdf);
            HttpServletResponse response = (HttpServletResponse) java.lang.reflect.Proxy.newProxyInstance(OriginalFileFailureFixture.class.getClassLoader(), new Class<?>[]{HttpServletResponse.class}, (proxy, method, values) -> {
                if (method.getName().equals("setStatus") || method.getName().equals("sendError")) statusesSet.incrementAndGet();
                if (method.getName().equals("getOutputStream")) { outputRequested.incrementAndGet(); throw new AssertionError("FAILED_OBJECT_MUST_NOT_RETURN_BYTES"); }
                if (method.getReturnType() == boolean.class) return false;
                if (method.getReturnType() == int.class) return 200;
                if (method.getReturnType() == long.class) return 0L;
                return null;
            });
            int afterBase64 = requests.get();
            service.getFile("own-fixture-bucket", "missing.txt", response);
            check(requests.get() > afterBase64); check(statusesSet.get() == 0); check(outputRequested.get() == 0);
            check(System.getSecurityManager() == guard);
            check(Arrays.equals(Files.readAllBytes(sentinel), "unchanged".getBytes(StandardCharsets.US_ASCII)));
            for (Class<?> type : new Class<?>[]{SysFileServiceImpl.class, MinioConfig.class, Class.forName("com.iemp.endanger.minio.MinioUtil")}) {
                check(Paths.get(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath().equals(Paths.get(args[1]).toRealPath()));
            }
            String result = "{\"passedChecks\":" + checks + ",\"ownedFailureHTTPRequests\":" + requests.get()
                + ",\"objectPUTRequests\":" + puts.get() + ",\"uploadResponseSuccessDespiteNoObjectPUT\":true"
                + ",\"pdfResponseSuccessDespiteNoObjectPUT\":true,\"failedDownloadStatusNotSet\":true,\"failedDownloadBodyNotOpened\":true"
                + ",\"base64FailureReturnsNull\":true,\"originalServiceClassesFromPinnedFlatJar\":true"
                + ",\"originalSpringApplicationStarted\":false,\"databaseConnected\":false,\"sourceObjectStoreConnected\":false"
                + ",\"originalClassesModified\":false,\"isReplacementObjectStore\":false,\"fileServiceSuccessVerified\":false}";
            Files.write(root.resolve("result.json"), result.getBytes(StandardCharsets.US_ASCII));
            System.out.println("ORIGINAL_FILE_FAILURE_OBSERVATION " + result);
        } finally {
            server.stop(0);
            if (http != null) { http.dispatcher().executorService().shutdown(); http.connectionPool().evictAll(); }
        }
    }
}
