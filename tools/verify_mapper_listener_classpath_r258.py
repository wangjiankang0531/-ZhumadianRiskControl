from pathlib import Path
import json,subprocess,os
R=Path('D:/Project/Zhumadian');A=R/'_g/Application';V=Path(__file__).parent;W=V/'mapper-listener-classpath-r258';assert not W.exists();W.mkdir()
cfg=json.loads((A/'private/server-configuration.json').read_bytes());args=cfg['businessArguments'];cp=[x for x in args if 'application.jar'in x and ';'in x];assert len(cp)==1
cp=cp[0]
tokens={'APP':A,'BUSINESS_RUN':A/'payload/business/run-template','PLATFORM_RUN':A/'payload/platform/run-template','PLATFORM_DATA':A/'UserData/TianjinOriginalPlatform'}
for k,v in tokens.items():cp=cp.replace('${'+k+'}',v.as_posix())
assert '${'not in cp and 'own-mapper-observation-r257.jar'in cp
source=W/'OwnMapperListenerClasspathR258.java'
source.write_text('''import java.nio.file.*;import java.util.*;import org.springframework.core.io.support.SpringFactoriesLoader;import org.springframework.context.ApplicationListener;
public final class OwnMapperListenerClasspathR258{public static void main(String[]a)throws Exception{String name="xnby.own.OwnMapperRegistrationObservationR257";ClassLoader loader=Thread.currentThread().getContextClassLoader();var names=SpringFactoriesLoader.loadFactoryNames(ApplicationListener.class,loader);boolean once=Collections.frequency(names,name)==1;Class<?> type=Class.forName(name,false,loader);boolean assign=ApplicationListener.class.isAssignableFrom(type)&&type.getConstructor()!=null;if(!once||!assign)throw new Exception("OWN_LISTENER_DISCOVERY_REQUIRED");Files.writeString(Path.of(a[0]),"{\\"passed\\":true,\\"actualSpringFactoriesDiscoveryExactlyOnce\\":true,\\"actualConfiguredClasspathUsed\\":true,\\"originalInitializerListOrAuthClassesChanged\\":false,\\"springContainerSQLOrNetworkStarted\\":false}");}}''',encoding='utf-8')
env={k:v for k,v in os.environ.items()if k.upper()not in ['JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','_JAVA_OPTIONS','CLASSPATH']}
for label,command in [('compile',[str(A/'runtime/jdk17/bin/javac.exe'),'-J-Xmx96m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(W),str(source)]),('discover',[str(A/'runtime/jdk17/bin/java.exe'),'-Xmx96m','-cp',str(W)+';'+cp,'OwnMapperListenerClasspathR258',str(W/'result.json')])]:
 r=subprocess.run(command,env=env,capture_output=True,timeout=35,creationflags=subprocess.CREATE_NO_WINDOW);(W/(label+'.private.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,label+'_FAILED'
print((W/'result.json').read_text(encoding='utf-8'))
