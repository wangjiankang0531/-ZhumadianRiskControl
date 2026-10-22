// ASP.NET 4 fixed-destination adapter. Never serves disk files or arbitrary upstreams.
using System;
using System.Configuration;
using System.IO;
using System.Net;
using System.Web;

public sealed class XnbyReferenceProxy : IHttpHandler
{
    private const string Prefix = "/zhumadian/";
    private const string Origin = "https://www.joinlinksmart.com";
    private const string Upstream = "http://127.0.0.1:18874";
    public bool IsReusable { get { return true; } }
    private static void Error(HttpContext context, int status)
    {
        context.Response.Clear(); context.Response.StatusCode = status;
        context.Response.TrySkipIisCustomErrors = true;
        context.Response.ContentType = "text/plain; charset=utf-8";
        context.Response.Cache.SetCacheability(HttpCacheability.NoCache);
        context.Response.Write("XNBY test ingress: " + status);
    }
    public void ProcessRequest(HttpContext context)
    {
        ProcessConfiguredRequest(context, ConfigurationManager.AppSettings["XnbyIngressKey"]);
    }
    internal static void ProcessConfiguredRequest(HttpContext context, string key)
    {
        HttpRequest input = context.Request;
        if (!input.IsSecureConnection || !String.Equals(input.Url.Authority, "www.joinlinksmart.com", StringComparison.OrdinalIgnoreCase))
        { Error(context, 403); return; }
        string raw = input.RawUrl, route = raw.Split('?')[0];
        if (!route.StartsWith(Prefix, StringComparison.Ordinal) || raw.Length > 4096 || route.IndexOf('%') >= 0 || route.IndexOf('\\') >= 0 || route.IndexOf("..", StringComparison.Ordinal) >= 0)
        { Error(context, 404); return; }
        if (input.HttpMethod != "GET" && input.HttpMethod != "POST") { Error(context, 405); return; }
        if (key == null || !System.Text.RegularExpressions.Regex.IsMatch(key, "^[0-9a-f]{64}$") || key == new string('0',64)) { Error(context, 503); return; }
        int bodyLimit = (route == Prefix + "api/demo/workflow-material" || route == Prefix + "api/demo/plan-material") ? 2828972 : 131072;
        if (input.ContentLength < 0 || input.ContentLength > bodyLimit || !String.IsNullOrEmpty(input.Headers["Transfer-Encoding"])) { Error(context, 413); return; }
        try
        {
            // This handler owns the entity body. Keep the framework size limit,
            // bound our allocation, and reject truncation before forwarding.
            byte[] postBody = null;
            if (input.HttpMethod == "POST")
            {
                postBody = new byte[input.ContentLength];
                Stream incoming = input.GetBufferlessInputStream();
                int offset = 0;
                while (offset < postBody.Length)
                {
                    int n = incoming.Read(postBody, offset, Math.Min(8192, postBody.Length-offset));
                    if (n <= 0) { Error(context,400); return; }
                    offset += n;
                }
            }
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(Upstream + raw);
            request.Method = input.HttpMethod; request.AllowAutoRedirect = false; request.Proxy = null;
            request.UseDefaultCredentials = false; request.KeepAlive = false;
            request.Timeout = 15000; request.ReadWriteTimeout = 15000; request.MaximumResponseHeadersLength = 32;
            request.Headers["X-XNBY-Ingress"] = key; request.Headers["X-XNBY-Public-Origin"] = Origin;
            foreach (string name in new string[] { "Cookie", "Origin", "X-XNBY-Demo", "X-XNBY-CSRF" })
            {
                string value = input.Headers[name];
                if (value != null) { if (value.Length > 4096) { Error(context,400); return; } request.Headers[name] = value; }
            }
            if (input.HttpMethod == "POST")
            {
                request.ContentType = input.ContentType; request.ContentLength = input.ContentLength;
                using (Stream target = request.GetRequestStream())
                {
                    target.Write(postBody,0,postBody.Length);
                }
            }
            HttpWebResponse response;
            try { response = (HttpWebResponse)request.GetResponse(); }
            catch (WebException e) { response = e.Response as HttpWebResponse; if (response == null) throw; }
            using (response)
            using (Stream stream = response.GetResponseStream())
            using (MemoryStream body = new MemoryStream())
            {
                byte[] buffer = new byte[8192]; int n;
                while ((n = stream.Read(buffer,0,buffer.Length)) > 0) { if (body.Length+n > 2097152) throw new IOException(); body.Write(buffer,0,n); }
                context.Response.Clear(); context.Response.StatusCode = (int)response.StatusCode;
                context.Response.TrySkipIisCustomErrors = true; context.Response.ContentType = response.ContentType;
                foreach (string name in new string[] { "Content-Disposition", "Cache-Control", "X-Content-Type-Options", "Content-Security-Policy", "X-Frame-Options", "Permissions-Policy" })
                    if (response.Headers[name] != null) context.Response.AppendHeader(name,response.Headers[name]);
                // Native same-origin form POSTs must retain Origin; no-referrer makes it null.
                context.Response.AppendHeader("Referrer-Policy", "same-origin");
                string[] cookies = response.Headers.GetValues("Set-Cookie");
                if (cookies != null) foreach (string cookie in cookies) context.Response.AppendHeader("Set-Cookie",cookie);
                string location = response.Headers["Location"];
                if (location != null) { if (!location.StartsWith(Prefix,StringComparison.Ordinal) || location.IndexOf('\\') >= 0) throw new IOException(); context.Response.AppendHeader("Location",location); }
                context.Response.OutputStream.Write(body.GetBuffer(),0,(int)body.Length);
            }
        }
        catch (HttpException) { Error(context,400); }
        catch (WebException) { Error(context,502); }
        catch (IOException) { Error(context,502); }
        catch (ArgumentException) { Error(context,400); }
    }
}
