package xnby.export;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
/** Configuration validation only: no GUI, JDBC connection, or credential output. */
public final class ReadOnlyExportPreflight {
    public static void main(String[] args) {
        try {
            var path=Paths.get(args[0]);
            var config=ReadOnlyDatabaseExport.Config.parse(Files.readString(path,StandardCharsets.UTF_8),args[1]);
            System.out.println("PREFLIGHT_CONFIG_VALID schemas=jnpf,tj_endanger sharedIdentity=true databaseConnections=0 sourceConfigSHA256="+ReadOnlyDatabaseExport.sha(path));
        } catch(Throwable error) {
            System.err.println("PREFLIGHT_FAILED "+ReadOnlyDatabaseExport.safeFailure(error));
            System.exit(2);
        }
    }
}
