package xnby.platform;

import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import java.util.zip.ZipFile;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

/** Offline contract probe. Never prints keys, credentials, payloads or ciphertext. */
public final class OriginalLoginKeyContract {
    private static Properties properties(Path path) throws Exception {
        Properties p = new Properties();
        try (var in = Files.newInputStream(path)) { p.load(in); }
        return p;
    }
    public static void main(String[] args) throws Exception {
        String text = Files.readString(Paths.get(args[0]), StandardCharsets.UTF_8);
        Matcher m = Pattern.compile("if\\s*\\(!cipherKey\\)\\s*cipherKey\\s*=\\s*(['\"])([^'\"\\\\]+)\\1;").matcher(text);
        if (!m.find()) throw new IllegalArgumentException("FRONTEND_KEY_DECLARATION_UNRECOGNIZED");
        String frontend = m.group(2);
        Map<String,String> source = new LinkedHashMap<>();
        try (ZipFile z = new ZipFile(args[1])) {
            OriginalPlatformConfigBuilder.yaml(z,"BOOT-INF/classes/application.yml",source);
            String profile = source.get("spring.profiles.active");
            if (!Set.of("pro","test").contains(profile)) throw new IllegalArgumentException("PROFILE_UNRECOGNIZED");
            OriginalPlatformConfigBuilder.yaml(z,"BOOT-INF/classes/application-"+profile+".yml",source);
        }
        Properties candidate = properties(Paths.get(args[2]));
        Properties own = properties(Paths.get(args[3]));
        String candidateKey = candidate.getProperty("security.SecurityKey");
        if (candidateKey == null || source.get("security.SecurityKey") == null) throw new IllegalArgumentException("KEY_MISSING");
        byte[] probe = "own-offline-md5-shaped-canary-0001".getBytes(StandardCharsets.US_ASCII);
        Cipher encrypt = Cipher.getInstance("AES/ECB/PKCS5Padding");
        encrypt.init(Cipher.ENCRYPT_MODE,new SecretKeySpec(frontend.getBytes(StandardCharsets.UTF_8),"AES"));
        byte[] ciphertext = encrypt.doFinal(probe);
        boolean candidateDecrypts = false;
        String candidateFailure = "none";
        try {
            Cipher decrypt = Cipher.getInstance("AES/ECB/PKCS5Padding");
            decrypt.init(Cipher.DECRYPT_MODE,new SecretKeySpec(candidateKey.getBytes(StandardCharsets.UTF_8),"AES"));
            candidateDecrypts = Arrays.equals(probe,decrypt.doFinal(ciphertext));
        } catch (java.security.GeneralSecurityException ex) { candidateFailure = ex.getClass().getSimpleName(); }
        System.out.println("frontendMatchesOriginalBackend="+frontend.equals(source.get("security.SecurityKey")));
        System.out.println("frontendMatchesCandidateBackend="+frontend.equals(candidateKey));
        System.out.println("candidateMatchesOwnSecret="+candidateKey.equals(own.getProperty("ownSecret")));
        System.out.println("frontendAESKeyLengthValid="+Set.of(16,24,32).contains(frontend.getBytes(StandardCharsets.UTF_8).length));
        System.out.println("candidateAESKeyLengthValid="+Set.of(16,24,32).contains(candidateKey.getBytes(StandardCharsets.UTF_8).length));
        System.out.println("candidateDecryptsSyntheticFrontendCiphertext="+candidateDecrypts);
        System.out.println("candidateFailureType="+candidateFailure);
        System.out.println("preAuthEnabledMatchesOriginal="+Objects.equals(source.get("security.EnablePreAuth"),candidate.getProperty("security.EnablePreAuth")));
        System.out.println("originalAuthExecuted=false");
    }
}
