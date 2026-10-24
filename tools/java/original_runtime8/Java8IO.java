package xnby.compat;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
/** UTF-8 equivalents for the observer's Java 11 convenience methods. */
public final class Java8IO {
 private Java8IO(){}
 public static Path writeString(Path path,CharSequence text,OpenOption... options)throws IOException{
  return Files.write(path,text.toString().getBytes(StandardCharsets.UTF_8),options);
 }
 public static String readString(Path path)throws IOException{return new String(Files.readAllBytes(path),StandardCharsets.UTF_8);}
 public static byte[] readAllBytes(InputStream input)throws IOException{
  ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[65536];int count;
  while((count=input.read(buffer))!=-1)out.write(buffer,0,count);return out.toByteArray();
 }
 public static String hex(byte[] data){StringBuilder out=new StringBuilder();for(byte b:data)out.append(String.format("%02x",b&255));return out.toString();}
}
