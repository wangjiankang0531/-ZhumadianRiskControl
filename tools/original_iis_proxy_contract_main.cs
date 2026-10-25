using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
public sealed class OriginalProxyCase {
 public string name,path,method,host,body;public bool secure;public Dictionary<string,string> headers;
}
public static class OriginalProxyContractMain {
 public static int Main(string[] args){
  try { Run(args); return 0; }
  catch(Exception error) { Console.Error.WriteLine("FIXTURE_FAILED: "+error.ToString()); return 1; }
 }
 private static void Run(string[] args){
  if(args.Length!=1)throw new ArgumentException("One synthetic case file required");
  JavaScriptSerializer json=new JavaScriptSerializer();
  OriginalProxyCase[] cases=json.Deserialize<OriginalProxyCase[]>(File.ReadAllText(args[0],Encoding.UTF8));
  List<object> results=new List<object>();
  foreach(OriginalProxyCase item in cases){
   File.AppendAllText(args[0]+".progress","BEGIN "+item.name+"\n");
   XnbyProxyContractResult response=XnbyProxyWorker.Invoke(item.path,item.method,item.secure,item.host,item.body,new Dictionary<string,string>(item.headers,StringComparer.OrdinalIgnoreCase),new string('1',64));
   File.AppendAllText(args[0]+".progress","END "+item.name+" "+response.Status+"\n");
   byte[] body=Encoding.UTF8.GetBytes(response.Body);string hash;
   using(SHA256 sha=SHA256.Create())hash=BitConverter.ToString(sha.ComputeHash(body)).Replace("-","").ToLowerInvariant();
   results.Add(new {name=item.name,status=response.Status,bytes=body.Length,sha256=hash,headers=response.Headers});
  }
  Console.WriteLine(json.Serialize(results));
 }
}
