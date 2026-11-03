from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');A=R/'Application';T=A/'tools'
old=json.loads((R/'work/user_feedback_20261031/r36-native-history-candidate-r2/bundle/payload/release-manifest.json').read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a[:70],s.count(a));return s.replace(a,b)
source=A/'deploy/iis_original/App_Code/XnbyReferenceProxy.cs';raw=source.read_bytes()
assert sha(raw)==old['controllerFiles']['deploy/iis_original/App_Code/XnbyReferenceProxy.cs']
s=raw.decode('utf-8')
helper='''    internal static bool AcceptsGzip(string header)
    {
        if (String.IsNullOrEmpty(header) || header.Length > 1024) return false;
        string[] tokens = header.Split(',');
        if (tokens.Length > 32) return false;
        bool explicitGzip = false;
        decimal gzipWeight = 0, wildcardWeight = 0;
        foreach (string token in tokens)
        {
            Match item = Regex.Match(token.Trim(), @"^(gzip|\\*)\\s*(?:;\\s*q\\s*=\\s*(0(?:\\.[0-9]{0,3})?|1(?:\\.0{0,3})?))?$", RegexOptions.IgnoreCase);
            if (!item.Success) continue;
            decimal weight = 1;
            if (item.Groups[2].Success && !Decimal.TryParse(item.Groups[2].Value, System.Globalization.NumberStyles.AllowDecimalPoint, System.Globalization.CultureInfo.InvariantCulture, out weight)) continue;
            if (String.Equals(item.Groups[1].Value, "gzip", StringComparison.OrdinalIgnoreCase))
            { explicitGzip = true; gzipWeight = Math.Max(gzipWeight, weight); }
            else wildcardWeight = Math.Max(wildcardWeight, weight);
        }
        return explicitGzip ? gzipWeight > 0 : wildcardWeight > 0;
    }
    internal static bool PublicStaticResource(string route, string method)
    {
        return (method == "GET" || method == "HEAD") && Regex.IsMatch(route,
            @"^/zhumadian/(?:(?:emergency|h5)/)?(?:branding-20261025/)?assets/[A-Za-z0-9_./-]+\\.(?:js|css|svg|woff2?|png|jpe?g|webp|gif|ico)$", RegexOptions.IgnoreCase);
    }
'''
s=once(s,'    public void ProcessRequest(HttpContext context)',helper+'    public void ProcessRequest(HttpContext context)')
s=once(s,'            request.UseDefaultCredentials=false;request.KeepAlive=false;', '''            request.UseDefaultCredentials=false;request.KeepAlive=false;
            request.AutomaticDecompression=DecompressionMethods.None;
            if (PublicStaticResource(route, input.HttpMethod))
                request.Headers["Accept-Encoding"] = AcceptsGzip(input.Headers["Accept-Encoding"]) ? "gzip" : "identity";''')
s=once(s,'"Content-Range","Content-Encoding","X-Content-Type-Options"','"Content-Range","Content-Encoding","Vary","X-Content-Type-Options"')
out=T/'frontend/static_performance_r229/XnbyReferenceProxy.cs';assert not out.exists();out.parent.mkdir(parents=True);out.write_text(s,encoding='utf-8')
source=T/'original_project_branding.py';raw=source.read_bytes();assert sha(raw)==old['controllerFiles']['tools/original_project_branding.py']
s=raw.decode('utf-8')
mapping='''
STATIC_PERFORMANCE_MARKER = '# zhumadian-static-performance-v1'
def static_cache_map():
    # A versioned filename identifies a fixed representation; HTML and API responses never match.
    hashed = r'/zhumadian/(?:(?:emergency|h5)/)?(?:branding-20261025/)?assets/[A-Za-z0-9_./-]+-[A-Za-z0-9_-]{8,}\\.(?:js|css|svg|woff2?|png|jpe?g|webp|gif|ico)(?:[?].*)?$'
    return [STATIC_PERFORMANCE_MARKER,
            ' map "$status:$request_uri" $xnby_static_cache_control {',
            '  default "no-store";',
            '  "~^(?:200|304):' + hashed + '" "public, max-age=31536000, immutable";',
            ' }']

'''
s=once(s,'def static_directives(project_name):',mapping+'def static_directives(project_name):')
s=once(s,"'add_header Cache-Control \"no-store\" always;']", "'add_header Cache-Control $xnby_static_cache_control always;',\n             'gzip on;', 'gzip_vary on;', 'gzip_proxied any;', 'gzip_comp_level 5;',\n             'gzip_min_length 1024;',\n             'gzip_types text/css application/javascript text/javascript image/svg+xml application/wasm;']")
s=once(s,'    for line in config.splitlines():\n        result.append(line)', '''    for line in config.splitlines():
        if line.strip() == 'server {': result.extend(static_cache_map())
        result.append(line)''')
s=once(s,"'staticAssetVersion': ASSET_VERSION,", "'staticAssetVersion': ASSET_VERSION, 'staticPerformanceRevision': 'gzip-and-versioned-assets-v1',\n             'HTMLAndBusinessAPICachePolicyUnchanged': True,")
ast.parse(s);out2=T/'original_project_branding_r229.py';assert not out2.exists();out2.write_text(s,encoding='utf-8')
D=R/'Document/Deployment/static_performance_candidate_r229_20261103';D.mkdir(exist_ok=False)
proof={'generated':True,'proxySourceSHA256':sha(out.read_bytes()),'brandingSourceSHA256':sha(out2.read_bytes()),
       'exactR36SourcePinsChecked':True,'onlyPublicStaticGETHEADNegotiatesGzip':True,
       'encodedBytesPreservedWithoutProxyDecompression':True,'contentEncodingAndVaryForwarded':True,
       'onlySuccessfulHashNamedAssetsCacheable':True,'htmlBusinessErrorsAndNonHashedResourcesNotCacheable':True,
       'originalBrandingAndSourceFilesKept':True,'actualNginxAspNetTransportBrowserOrPublicAccepted':False}
(D/'source-preparation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps(proof))
