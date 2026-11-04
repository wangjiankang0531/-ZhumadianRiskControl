import java.util.*;
public final class CallbackRowsGoldenR878 {
 public static void main(String[]args)throws Exception {
  List<OwnedOriginalCallbacksR648.Row> rows=new ArrayList<>();
  for(int n:new int[]{1,2}) {List<String> v=new ArrayList<>(Collections.nCopies(17,null));
   v.set(0,"a546"+String.format("%028x",n));v.set(1,"OWN_MANAGER_CALLBACK_"+v.get(0));
   v.set(2,"合成回调"+n);v.set(3,"3");v.set(4,"3");v.set(5,"{\"url\":\"http://127.0.0.1:50123/synthetic\"}");v.set(8,"1");
   rows.add(new OwnedOriginalCallbacksR648.Row(v));}
  System.out.println(OwnedOriginalCallbackProvisioningR659.rowsSHA256(rows));
 }
}