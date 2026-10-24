package xnby.replica;

import com.iemp.endanger.minio.MinioConfig;
import com.iemp.endanger.server.file.service.impl.SysFileServiceImpl;
import com.cqweh.cloud.common.model.Response;
import io.minio.*;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.WriteListener;
import jakarta.servlet.http.HttpServletResponse;
import okhttp3.OkHttpClient;
import org.springframework.web.multipart.MultipartFile;
import java.io.*;
import java.lang.reflect.Field;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.TimeUnit;

/** Exercise original service bytes against a separately pinned real owned MinIO. */
@SuppressWarnings({"removal", "rawtypes"})
public final class OriginalFileRoundtripFixture {
    static int checks;
    static void check(boolean value) { if (!value) throw new AssertionError("ORIGINAL_FILE_ROUNDTRIP_FAILED"); checks++; }
    static String hex(byte[] bytes) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256").digest(bytes); StringBuilder b = new StringBuilder();
        for (byte v : digest) b.append(String.format("%02x", v & 255)); return b.toString();
    }
    static final class OwnPart implements MultipartFile {
        final byte[] bytes; final String name;
        OwnPart(String name, byte[] bytes) { this.name = name; this.bytes = bytes; }
        public String getName() { return "file"; }
        public String getOriginalFilename() { return name; }
        public String getContentType() { return "application/octet-stream"; }
        public boolean isEmpty() { return bytes.length == 0; }
        public long getSize() { return bytes.length; }
        public byte[] getBytes() { return bytes.clone(); }
        public InputStream getInputStream() { return new ByteArrayInputStream(bytes); }
        public void transferTo(File destination) { throw new UnsupportedOperationException("NO_DIRECT_FIXTURE_FILE_WRITE"); }
    }
    static byte[] download(SysFileServiceImpl service, String bucket, String file) {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        ServletOutputStream output = new ServletOutputStream() {
            public boolean isReady() { return true; }
            public void setWriteListener(WriteListener listener) { throw new UnsupportedOperationException(); }
            public void write(int b) { bytes.write(b); }
            public void write(byte[] b, int offset, int length) { bytes.write(b, offset, length); }
        };
        HttpServletResponse response = (HttpServletResponse) java.lang.reflect.Proxy.newProxyInstance(OriginalFileRoundtripFixture.class.getClassLoader(), new Class<?>[]{HttpServletResponse.class}, (proxy, method, args) -> {
            if (method.getName().equals("getOutputStream")) return output;
            if (method.getName().equals("setContentType")) check("application/octet-stream; charset=UTF-8".equals(args[0]));
            if (method.getName().equals("sendError")) throw new AssertionError("OWN_DOWNLOAD_HTTP_ERROR");
            if (method.getReturnType() == boolean.class) return false;
            if (method.getReturnType() == int.class) return 200;
            if (method.getReturnType() == long.class) return 0L;
            return null;
        });
        service.getFile(bucket, file, response); return bytes.toByteArray();
    }
    public static void main(String[] args) throws Exception {
        Path root = Paths.get(args[0]).toRealPath(), privateConfig = root.resolve("own-minio.private.properties");
        check(hex(Files.readAllBytes(privateConfig)).equals(args[1]));
        Properties p = new Properties(); try (Reader reader = Files.newBufferedReader(privateConfig, StandardCharsets.UTF_8)) { p.load(reader); }
        URI endpoint = new URI(p.getProperty("endpoint"));
        check("http".equals(endpoint.getScheme()) && "127.0.0.1".equals(endpoint.getHost()) && endpoint.getPort() >= 1024);
        check(endpoint.getRawUserInfo() == null && endpoint.getRawQuery() == null && endpoint.getRawFragment() == null && endpoint.getRawPath().isEmpty());
        String bucket = p.getProperty("bucket"); check(bucket.matches("own-attachment-[a-f0-9]{12}"));
        OriginalProcessBoundary guard = new OriginalProcessBoundary(root, Collections.singleton(endpoint.getPort()), true); System.setSecurityManager(guard);
        OkHttpClient http = new OkHttpClient.Builder().connectTimeout(3, TimeUnit.SECONDS).readTimeout(10, TimeUnit.SECONDS).callTimeout(20, TimeUnit.SECONDS).retryOnConnectionFailure(false).build();
        MinioClient client = MinioClient.builder().endpoint(endpoint.toString()).credentials(p.getProperty("accessKey"), p.getProperty("secretKey")).httpClient(http).build();
        List<String> objects = new ArrayList<>(); List<String> cases = new ArrayList<>();
        try {
            check(!client.bucketExists(BucketExistsArgs.builder().bucket(bucket).build()));
            MinioConfig config = new MinioConfig(); Field field = MinioConfig.class.getDeclaredField("bucketName"); field.setAccessible(true); field.set(config, bucket);
            SysFileServiceImpl service = new SysFileServiceImpl(client, config);
            byte[] multi = new byte[6 * 1024 * 1024 + 257]; for (int i = 0; i < multi.length; i++) multi[i] = (byte) (i * 31 + i / 257);
            byte[] pdf = "%PDF-1.4\n% own synthetic byte roundtrip only\n%%EOF\n".getBytes(StandardCharsets.US_ASCII);
            String[] names = {"original-file-unicode-name", "original-pdf-stream", "original-empty-file", "original-multipart-size"};
            byte[][] payloads = {"原附件流程\r\nUTF-8 byte preservation\n".getBytes(StandardCharsets.UTF_8), pdf, new byte[0], multi};
            for (int i = 0; i < names.length; i++) {
                Response result = i == 1 ? service.uploadPdf(new ByteArrayInputStream(payloads[i])) : service.uploadFile(new OwnPart(i == 0 ? "原文件名.txt" : "own-fixture.bin", payloads[i]));
                check(result.getCode() == Response.SUCCESS && result.getData() instanceof Map);
                Map data = (Map) result.getData(); check(bucket.equals(data.get("bucketName")));
                String object = (String) data.get("fileName"); if (object != null) objects.add(object);
                check(object != null && object.matches("[a-fA-F0-9-]{36}\\.[a-zA-Z0-9.]{1,32}"));
                check(("/sys-file/" + bucket + "/" + object).equals(data.get("url")));
                check(client.statObject(StatObjectArgs.builder().bucket(bucket).object(object).build()).size() == payloads[i].length);
                byte[] returned = download(service, bucket, object); check(Arrays.equals(returned, payloads[i])); check(hex(returned).equals(hex(payloads[i])));
                String encoded = service.getFileBase64(bucket, object); check(encoded != null && Arrays.equals(Base64.getDecoder().decode(encoded), payloads[i]));
                cases.add("{\"case\":\"" + names[i] + "\",\"bytes\":" + payloads[i].length + ",\"SHA256\":\"" + hex(payloads[i]) + "\",\"originalDownloadExact\":true,\"originalBase64Exact\":true}");
            }
            check(client.bucketExists(BucketExistsArgs.builder().bucket(bucket).build()));
            for (Class<?> type : new Class<?>[]{SysFileServiceImpl.class, MinioConfig.class, Class.forName("com.iemp.endanger.minio.MinioUtil")})
                check(Paths.get(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath().equals(Paths.get(args[2]).toRealPath()));
            for (String object : objects) client.removeObject(RemoveObjectArgs.builder().bucket(bucket).object(object).build()); objects.clear();
            check(!client.listObjects(ListObjectsArgs.builder().bucket(bucket).build()).iterator().hasNext());
            client.removeBucket(RemoveBucketArgs.builder().bucket(bucket).build()); check(!client.bucketExists(BucketExistsArgs.builder().bucket(bucket).build()));
            check(System.getSecurityManager() == guard);
            String result = "{\"passedChecks\":" + checks + ",\"cases\":[" + String.join(",", cases) + "]"
                + ",\"realOwnedObjectStoreUsed\":true,\"originalServiceClassesFromPinnedFlatJar\":true,\"ownedBucketAndObjectsRemoved\":true"
                + ",\"originalSpringApplicationStarted\":false,\"sourceObjectStoreConnected\":false,\"originalDataOrClassesModified\":false"
                + ",\"authenticationOrUIVerified\":false,\"historicalObjectsRecovered\":false,\"fullCloneReady\":false}";
            Files.write(root.resolve("roundtrip-result.json"), result.getBytes(StandardCharsets.US_ASCII)); System.out.println("ORIGINAL_FILE_ROUNDTRIP_RESULT " + result);
        } finally {
            for (String object : objects) { try { client.removeObject(RemoveObjectArgs.builder().bucket(bucket).object(object).build()); } catch (Exception ignored) {} }
            http.dispatcher().executorService().shutdown(); http.connectionPool().evictAll();
        }
    }
}
