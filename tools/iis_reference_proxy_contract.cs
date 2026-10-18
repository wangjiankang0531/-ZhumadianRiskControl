// In-process HTTP worker fixture: exercises the exact production handler source.
// Not an IIS deployment test. No Win32 UI, registry or machine configuration.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Web;
using System.Web.Hosting;

public sealed class XnbyProxyContractResult
{
    public int Status;
    public string Body;
    public string[] Headers;
}

public sealed class XnbyProxyWorker : SimpleWorkerRequest
{
    private string raw, method, authority;
    private bool secure;
    private byte[] body;
    private Dictionary<string,string> headers;
    private MemoryStream output = new MemoryStream();
    private List<string> responseHeaders = new List<string>();
    private int status = 200;
    public XnbyProxyWorker(string path,string verb,bool tls,string host,string content,Dictionary<string,string> input)
        : base("/zhumadian/",Path.GetTempPath(),"index.html","",new StringWriter())
    { raw=path; method=verb; secure=tls; authority=host; body=Encoding.UTF8.GetBytes(content ?? ""); headers=input; }
    public override string GetRawUrl() { return raw; }
    public override string GetHttpVerbName() { return method; }
    public override bool IsSecure() { return secure; }
    public override string GetServerName() { return authority; }
    public override int GetLocalPort() { return secure ? 443 : 80; }
    public override string GetKnownRequestHeader(int index)
    {
        string name=GetKnownRequestHeaderName(index);
        if (name=="Host") return authority;
        if (name=="Content-Length") return body.Length.ToString();
        string value; return headers.TryGetValue(name,out value) ? value : null;
    }
    public override string[][] GetUnknownRequestHeaders()
    {
        List<string[]> result=new List<string[]>();
        foreach(var entry in headers) if(GetKnownRequestHeaderIndex(entry.Key)<0) result.Add(new string[]{entry.Key,entry.Value});
        return result.ToArray();
    }
    public override byte[] GetPreloadedEntityBody() { return body; }
    public override bool IsEntireEntityBodyIsPreloaded() { return true; }
    public override int GetTotalEntityBodyLength() { return body.Length; }
    public override void SendStatus(int code,string description) { status=code; }
    public override void SendKnownResponseHeader(int index,string value) { responseHeaders.Add(GetKnownResponseHeaderName(index)+": "+value); }
    public override void SendUnknownResponseHeader(string name,string value) { responseHeaders.Add(name+": "+value); }
    public override void SendResponseFromMemory(byte[] data,int length) { output.Write(data,0,length); }
    public override void FlushResponse(bool finalFlush) { }
    public override void EndOfRequest() { }
    public XnbyProxyContractResult Result() { return new XnbyProxyContractResult{Status=status,Body=Encoding.UTF8.GetString(output.ToArray()),Headers=responseHeaders.ToArray()}; }
    public static XnbyProxyContractResult Invoke(string path,string verb,bool tls,string host,string body,Dictionary<string,string> headers,string key)
    {
        XnbyProxyWorker worker=new XnbyProxyWorker(path,verb,tls,host,body,headers);
        HttpContext context=new HttpContext(worker);
        HttpContext.Current=context;
        try { XnbyReferenceProxy.ProcessConfiguredRequest(context,key); context.Response.Flush(); return worker.Result(); }
        finally { HttpContext.Current=null; }
    }
}
