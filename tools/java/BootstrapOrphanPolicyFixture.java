package xnby.platform;
import java.util.*;
public final class BootstrapOrphanPolicyFixture {
 static int checks;
 static final class Row{final String id,instance;Row(String id,String instance){this.id=id;this.instance=instance;}}
 static class Lookup implements OriginalBootstrapOrphanGuard.Lookup {
  int definitions;long runtime,historical,runtimeInstance,historicalInstance;boolean broken;
  public boolean definitionExists(String id)throws Exception{definitions++;if(broken)throw new Exception("OWN_SYNTHETIC_LOOKUP_FAILURE");return id.equals("valid");}
  public long runtimeDefinitionReferences(String id){return runtime;}
  public long historicalDefinitionReferences(String id){return historical;}
  public long runtimeInstanceReferences(String id){return runtimeInstance;}
  public long historicalInstanceReferences(String id){return historicalInstance;}
 }
 static List<Row> select(List<Row> rows,Lookup lookup,OriginalBootstrapOrphanGuard.Scope scope)throws Exception{return OriginalBootstrapOrphanGuard.select(rows,r->r.id,r->r.instance,lookup,scope);}
 static void check(boolean yes){if(!yes)throw new AssertionError();checks++;}
 public static void main(String[]args)throws Exception {
  Row valid=new Row("valid","v"),orphan1=new Row("private-orphan","a"),orphan2=new Row("private-orphan","b");
  List<Row> originals=Arrays.asList(valid);check(select(originals,new Lookup(),new OriginalBootstrapOrphanGuard.Scope())==originals);
  List<Row> mixed=Arrays.asList(orphan1,valid,orphan2);Lookup lookup=new Lookup();OriginalBootstrapOrphanGuard.Scope scope=new OriginalBootstrapOrphanGuard.Scope();List<Row> result=select(mixed,lookup,scope);
  check(result.size()==1&&result.get(0)==valid&&mixed.size()==3&&mixed.get(0)==orphan1);check(lookup.definitions==2&&scope.orphanGroups.size()==1&&scope.inputRows==3&&scope.keptRows==1);
  for(int mode=0;mode<5;mode++) {
   Lookup bad=new Lookup();if(mode==0)bad.runtime=1;if(mode==1)bad.historical=1;if(mode==2)bad.runtimeInstance=1;if(mode==3)bad.historicalInstance=1;if(mode==4)bad.broken=true;
   boolean rejected=false;try{select(mixed,bad,new OriginalBootstrapOrphanGuard.Scope());}catch(Exception expected){rejected=true;}check(rejected&&mixed.size()==3);
  }
  boolean invalid=false;try{select(Arrays.asList(new Row(null,"a")),new Lookup(),new OriginalBootstrapOrphanGuard.Scope());}catch(IllegalStateException expected){invalid=true;}check(invalid);
  check(!scope.orphanGroups.toString().contains("private-orphan"));
  System.out.println("ORPHAN_POLICY_FIXTURE_CHECKS="+checks);
 }
}
