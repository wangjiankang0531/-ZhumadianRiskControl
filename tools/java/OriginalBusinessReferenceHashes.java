package xnby.replica;
import java.io.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
/** Emit only hashes for the eleven explicitly selected business references, never credentials. */
public final class OriginalBusinessReferenceHashes {
 static final String[] KEYS={"safety.roleId","safety.auditRoleId","safety.env-role-id","safety.hiddenDangerFormCode","safety.checkLedgerFormCode","flow.workCode","flow.inspectionHandle","flow.workReservation","flow.workProgramme","flow.eventInfoHandle","flow.eventTaskHandle"};
 static String sha(byte[] raw)throws Exception{StringBuilder s=new StringBuilder();for(byte b:MessageDigest.getInstance("SHA-256").digest(raw))s.append(String.format("%02x",b&255));return s.toString();}
 public static void main(String[] args)throws Exception{
  if(args.length!=3||!args[1].matches("[0-9a-f]{64}"))throw new IllegalArgumentException("PINNED_PRIVATE_INPUT_REQUIRED");Path input=Paths.get(args[0]),output=Paths.get(args[2]);if(Files.size(input)>256*1024||Files.exists(output))throw new IllegalArgumentException("INPUT_SIZE_OR_OUTPUT_EXISTS");byte[] raw=Files.readAllBytes(input);if(!sha(raw).equals(args[1]))throw new IllegalArgumentException("PRIVATE_INPUT_PIN_MISMATCH");Properties source=new Properties();source.load(new ByteArrayInputStream(raw));Properties hashes=new Properties();
  for(String key:KEYS){String value=source.getProperty(key);hashes.setProperty(key,value==null||value.isEmpty()?"EMPTY":sha(value.getBytes("UTF-8")));}
  try(OutputStream stream=Files.newOutputStream(output,StandardOpenOption.CREATE_NEW)){hashes.store(stream,"Only business reference hashes; no credentials selected");}System.out.println("BUSINESS_REFERENCE_HASHES=11");
 }
}
