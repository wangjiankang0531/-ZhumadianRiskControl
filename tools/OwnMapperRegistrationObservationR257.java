package xnby.own;
import java.io.*;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.jar.*;
import javax.xml.parsers.DocumentBuilderFactory;
import org.w3c.dom.*;
import org.springframework.context.*;import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.apache.ibatis.session.SqlSessionFactory;
import com.fasterxml.jackson.databind.ObjectMapper;

/** Observe static mapped-statement identities in an owned container. No SQL or registration changes. */
public final class OwnMapperRegistrationObservationR257 implements ApplicationListener<ApplicationReadyEvent> {
 static void need(boolean v)throws Exception{if(!v)throw new Exception("OWN_MAPPER_OBSERVATION_SCOPE_REJECTED");}
 public void onApplicationEvent(final ApplicationReadyEvent event){
  final ConfigurableApplicationContext context=event.getApplicationContext();
  final Path app=Path.of("D:/Project/Zhumadian/_g/Application");
  final Path root=Path.of(System.getProperty("own.candidate.root")).toAbsolutePath().normalize();
  try{
   need(!Files.exists(app.getParent().resolve("user-manual-protected.json"))&&root.startsWith(app.resolve("UserData/OriginalServer/runs"))&&root.getFileName().toString().equals("b")&&root.getParent().getFileName().toString().matches("j[1-9][0-9]*")&&root.toRealPath().equals(root));
   Properties p=new Properties();try(InputStream in=Files.newInputStream(root.resolve("server-owner.properties"))){p.load(in);}
   need(p.size()==2&&p.getProperty("schema").equals("zhumadian.original.server.owner.v1")&&p.getProperty("ownerId").equals(System.getProperty("own.server.owner")));
  }catch(Exception e){throw new IllegalStateException("OWN_MAPPER_OBSERVATION_OWNER_REFUSED",e);}
   try{
    Path jar=app.resolve("payload/business/application.jar");byte[] bytes=Files.readAllBytes(jar);String pin=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));
    need(pin.equals("363330e27998fadbb780005ee760ee6b0d41fed08577dfb4f2ff58919aadd83a"));
    DocumentBuilderFactory xml=DocumentBuilderFactory.newInstance();xml.setValidating(false);xml.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd",false);xml.setFeature("http://xml.org/sax/features/external-general-entities",false);xml.setFeature("http://xml.org/sax/features/external-parameter-entities",false);xml.setXIncludeAware(false);xml.setExpandEntityReferences(false);
    Set<String> expected=new TreeSet<>();int resources=0;
    try(JarFile z=new JarFile(jar.toFile())){List<String> names=z.stream().map(e->e.getName()).filter(n->n.startsWith("xml/")&&n.endsWith(".xml")).sorted().toList();
     for(String name:names){Document d;try(InputStream in=z.getInputStream(z.getJarEntry(name))){d=xml.newDocumentBuilder().parse(in);}Element mapper=d.getDocumentElement();need(mapper.getTagName().equals("mapper"));resources++;String ns=mapper.getAttribute("namespace");need(!ns.isBlank());
      for(Node n=mapper.getFirstChild();n!=null;n=n.getNextSibling())if(n instanceof Element&&Set.of("select","insert","update","delete").contains(n.getNodeName())){String id=((Element)n).getAttribute("id");need(!id.isBlank()&&expected.add(ns+"."+id));}
     }
    }
    need(resources==96&&expected.size()>100);Map<String,SqlSessionFactory> factories=context.getBeansOfType(SqlSessionFactory.class,false,false);need(factories.size()>=1&&factories.size()<=4);
    List<Map<String,Object>> details=new ArrayList<>();boolean all=true;
    for(var f:factories.entrySet()){var c=f.getValue().getConfiguration();List<String> missing=new ArrayList<>();Map<String,Integer> sources=new TreeMap<>();int plan=0;
     for(String id:expected){if(!c.hasStatement(id,false))missing.add(id);else{String resource=c.getMappedStatement(id,false).getResource();sources.merge(resource==null?"unknown":resource,1,Integer::sum);if(id.contains(".EmergencyPlanMapper."))plan++;}}
     all&=missing.isEmpty();Map<String,Object> row=new LinkedHashMap<>();row.put("factory",f.getKey());row.put("registeredOriginalXMLStatements",expected.size()-missing.size());row.put("missingOriginalXMLStatements",missing.size());row.put("missingStaticStatementIdentities",missing);row.put("registeredResourceCounts",sources);row.put("registeredPlanStatements",plan);details.add(row);
    }
    Map<String,Object> report=new LinkedHashMap<>();report.put("schema","xnby.own.r255.actual-mapper-registration.v1");report.put("actualApplicationReadySpringFactoryObservation",true);report.put("originalXMLResources",resources);report.put("expectedOriginalXMLStatements",expected.size());report.put("factoryCount",factories.size());report.put("allFactoriesHaveEveryOriginalXMLStatement",all);report.put("factories",details);report.put("SQLExecutedOrConfigurationRegistrationMutatedByObserver",false);report.put("accountsBusinessRowsCredentialsOrRuntimeUUIDIncluded",false);
    byte[] raw=new ObjectMapper().writerWithDefaultPrettyPrinter().writeValueAsBytes(report);Files.write(root.resolve("own-mapper-observation.json"),raw,StandardOpenOption.CREATE_NEW);
   }catch(Exception e){throw new IllegalStateException("OWN_MAPPER_OBSERVATION_FAILED",e);}
 }
}
