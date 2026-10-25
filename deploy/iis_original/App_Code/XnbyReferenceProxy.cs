// Fixed-destination HTTPS ingress for the original project frontend and APIs.
using System;
using System.Configuration;
using System.IO;
using System.Net;
using System.Net.WebSockets;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Web;
using System.Web.WebSockets;

public sealed class XnbyReferenceProxy : IHttpHandler
{
    private const string Prefix = "/zhumadian/";
    private const string Origin = "https://www.joinlinksmart.com";
    private const string Upstream = "http://127.0.0.1:18892";
    private const int RequestLimit = 104857600;
    private const long ResponseLimit = 134217728;
    public bool IsReusable { get { return true; } }
    private static void Error(HttpContext context, int status)
    {
        context.Response.Clear(); context.Response.StatusCode = status;
        context.Response.TrySkipIisCustomErrors = true;
        context.Response.ContentType = "text/plain; charset=utf-8";
        context.Response.Cache.SetCacheability(HttpCacheability.NoCache);
        context.Response.Write("Zhumadian project ingress: " + status);
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
        string raw = input.RawUrl, route = raw.Split('?')[0], decoded;
        try { decoded = Uri.UnescapeDataString(route); }
        catch (UriFormatException) { Error(context,400); return; }
        if (!route.StartsWith(Prefix, StringComparison.Ordinal) || raw.Length > 8192 || decoded.IndexOf('\\') >= 0 ||
            decoded.IndexOf('\0') >= 0 || decoded.IndexOf('\r') >= 0 || decoded.IndexOf('\n') >= 0 ||
            Regex.IsMatch(decoded, @"(^|/)\.\.?(/|$)") || decoded.IndexOf('%') >= 0)
        { Error(context, 404); return; }
        if (key == null || !Regex.IsMatch(key, "^[0-9a-f]{64}$") || key == new string('0',64))
        { Error(context,503); return; }
        // IsWebSocketRequest itself throws outside the IIS integrated pipeline.
        // Ordinary HTTP must not call that IIS-only API, including in fixtures.
        bool wantsWebSocket = String.Equals(input.Headers["Upgrade"], "websocket", StringComparison.OrdinalIgnoreCase);
        if (wantsWebSocket)
        {
            if (input.HttpMethod != "GET") { Error(context,405); return; }
            string ws = Prefix + "api/serv/websocket";
            if (route != ws && !route.StartsWith(ws + "/",StringComparison.Ordinal)) { Error(context,404); return; }
            try { if (!context.IsWebSocketRequest) { Error(context,400); return; } }
            catch (PlatformNotSupportedException) { Error(context,503); return; }
            string protocol=input.Headers["Sec-WebSocket-Protocol"];
            if (protocol != null && (protocol.Length>128 || !Regex.IsMatch(protocol,@"^[A-Za-z0-9!#$%&'*+.^_`|~-]+$")))
            { Error(context,400); return; }
            string authorization=input.Headers["Authorization"], cookies=input.Headers["Cookie"];
            if (authorization != null && authorization.Length>16384 || cookies != null && cookies.Length>16384)
            { Error(context,400); return; }
            context.AcceptWebSocketRequest(async socketContext => {
                using (ClientWebSocket target = new ClientWebSocket())
                using (CancellationTokenSource cancel = new CancellationTokenSource())
                {
                    target.Options.Proxy=null;
                    target.Options.SetRequestHeader("Origin",Origin);
                    if (authorization!=null) target.Options.SetRequestHeader("Authorization",authorization);
                    if (cookies!=null) target.Options.SetRequestHeader("Cookie",cookies);
                    if (protocol!=null) target.Options.AddSubProtocol(protocol);
                    try {
                        await target.ConnectAsync(new Uri("ws://127.0.0.1:18892"+raw),cancel.Token);
                        Task outbound=Pump(socketContext.WebSocket,target,cancel.Token);
                        Task inbound=Pump(target,socketContext.WebSocket,cancel.Token);
                        await Task.WhenAny(outbound,inbound);
                    } catch (WebSocketException) { }
                      catch (OperationCanceledException) { }
                    finally { cancel.Cancel(); socketContext.WebSocket.Abort(); }
                }
            },new AspNetWebSocketOptions {SubProtocol=protocol});
            return;
        }
        if (!Array.Exists(new string[]{"GET","HEAD","POST","PUT","PATCH","DELETE","OPTIONS"}, m=>m==input.HttpMethod))
        { Error(context,405); return; }
        if (input.ContentLength < 0 || input.ContentLength > RequestLimit || !String.IsNullOrEmpty(input.Headers["Transfer-Encoding"]))
        { Error(context,413); return; }
        HttpWebRequest request = null;
        bool responseStarted = false;
        try
        {
            request=(HttpWebRequest)WebRequest.Create(Upstream+raw);
            request.Method=input.HttpMethod;request.AllowAutoRedirect=false;request.Proxy=null;
            request.UseDefaultCredentials=false;request.KeepAlive=false;
            request.Timeout=120000;request.ReadWriteTimeout=120000;request.MaximumResponseHeadersLength=64;
            request.Headers["X-XNBY-Ingress"]=key;
            request.Headers["X-XNBY-Public-Origin"]=Origin;
            foreach (string name in new string[]{"Authorization","Cookie","Origin","Accept-Language","If-None-Match","If-Modified-Since","If-Range","Range","X-Requested-With","X-XNBY-CSRF","X-CSRF-Token"})
            {
                string value=input.Headers[name];
                if(value==null)continue;
                if(value.Length>16384){Error(context,400);return;}
                if(name=="If-Modified-Since") {DateTime date;if(DateTime.TryParse(value,out date))request.IfModifiedSince=date;}
                else if(name=="Range") {
                    Match range=Regex.Match(value,@"^bytes=(\d+)-(\d*)$");
                    if(!range.Success){Error(context,416);return;}
                    long first,last;if(!Int64.TryParse(range.Groups[1].Value,out first)){Error(context,416);return;}
                    if(range.Groups[2].Value.Length==0)request.AddRange(first);
                    else {if(!Int64.TryParse(range.Groups[2].Value,out last)||last<first){Error(context,416);return;}request.AddRange(first,last);}
                }
                else request.Headers[name]=value;
            }
            if(input.AcceptTypes!=null)request.Accept=String.Join(",",input.AcceptTypes);
            if(!String.IsNullOrEmpty(input.ContentType))request.ContentType=input.ContentType;
            if(input.ContentLength>0 || input.HttpMethod=="POST" || input.HttpMethod=="PUT" || input.HttpMethod=="PATCH")
            {
                request.ContentLength=input.ContentLength;
                using(Stream target=request.GetRequestStream())
                {
                    Stream source=input.GetBufferlessInputStream();byte[] buffer=new byte[65536];int left=input.ContentLength;
                    while(left>0){int count=source.Read(buffer,0,Math.Min(buffer.Length,left));if(count<=0)throw new IOException("Truncated request");target.Write(buffer,0,count);left-=count;}
                }
            }
            HttpWebResponse response;
            try {response=(HttpWebResponse)request.GetResponse();}
            catch(WebException error){response=error.Response as HttpWebResponse;if(response==null)throw;}
            using(response)
            {
                if(response.ContentLength>ResponseLimit)throw new IOException("Response bound exceeded");
                context.Response.Clear();context.Response.StatusCode=(int)response.StatusCode;
                context.Response.TrySkipIisCustomErrors=true;context.Response.ContentType=response.ContentType;
                foreach(string name in new string[]{"Content-Disposition","Cache-Control","ETag","Last-Modified","Accept-Ranges","Content-Range","Content-Encoding","X-Content-Type-Options","Content-Security-Policy","X-Frame-Options","Permissions-Policy"})
                    if(response.Headers[name]!=null)context.Response.AppendHeader(name,response.Headers[name]);
                context.Response.AppendHeader("Referrer-Policy","same-origin");
                string[] setCookies=response.Headers.GetValues("Set-Cookie");if(setCookies!=null)foreach(string cookie in setCookies)context.Response.AppendHeader("Set-Cookie",cookie);
                string location=response.Headers["Location"];
                if(location!=null){if(!location.StartsWith(Prefix,StringComparison.Ordinal)||location.IndexOf('\\')>=0||location.IndexOf('\r')>=0||location.IndexOf('\n')>=0)throw new IOException("Unexpected redirect");context.Response.AppendHeader("Location",location);}
                if(input.HttpMethod=="HEAD")return;
                context.Response.BufferOutput=false;long total=0;
                using(Stream source=response.GetResponseStream())
                {byte[] buffer=new byte[65536];int count;while(source!=null&&(count=source.Read(buffer,0,buffer.Length))>0){total+=count;if(total>ResponseLimit)throw new IOException("Response bound exceeded");responseStarted=true;context.Response.OutputStream.Write(buffer,0,count);}}
            }
        }
        catch(HttpException){if(responseStarted)context.Response.Close();else Error(context,400);}
        catch(WebException){if(responseStarted)context.Response.Close();else Error(context,502);}
        catch(IOException){if(responseStarted)context.Response.Close();else Error(context,502);}
        catch(ArgumentException){if(responseStarted)context.Response.Close();else Error(context,400);}
        finally { if(request!=null)request.Abort(); }
    }
    private static async Task Pump(WebSocket source,WebSocket target,CancellationToken cancel)
    {
        byte[] buffer=new byte[65536];long messageBytes=0;
        while(!cancel.IsCancellationRequested)
        {
            WebSocketReceiveResult received=await source.ReceiveAsync(new ArraySegment<byte>(buffer),cancel);
            if(received.MessageType==WebSocketMessageType.Close){if(target.State==WebSocketState.Open)await target.CloseOutputAsync(WebSocketCloseStatus.NormalClosure,"",cancel);return;}
            messageBytes+=received.Count;if(messageBytes>1048576)throw new WebSocketException("Message bound exceeded");
            await target.SendAsync(new ArraySegment<byte>(buffer,0,received.Count),received.MessageType,received.EndOfMessage,cancel);
            if(received.EndOfMessage)messageBytes=0;
        }
    }
}
