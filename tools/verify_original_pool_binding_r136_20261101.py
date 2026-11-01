from pathlib import Path
import copy,hashlib,importlib.util,json,subprocess
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';A=R/'_g/Application';C=R/'work/event_delivery_consistency_20261030/full-controller-r136/pool-binding';D=R/'Document/Deployment/emergency_runtime_capacity_r136_20261101';assert not C.exists();C.mkdir()
spec=importlib.util.spec_from_file_location('new_pool_policy',T/'original_connection_pool_policy_r136_20261101.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def config():
    out={'configuration':{}}
    for side,names in [('platform',['master']),('business',['master','tow'])]:
        v={'spring.datasource.dynamic.datasource.'+n+'.url':'jdbc:mysql://127.0.0.1:9/own_pool_not_started'for n in names};v.update({'spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.min-idle':'0','spring.datasource.dynamic.druid.max-wait':'5000'});out['configuration'][side]=v
    return out
cases=[];c=config();before=copy.deepcopy(c);p=m.connection_pool_budget(c);assert c==before and p['maximumPoolConnections']==12 and p['mysqlMaxConnections']==24 and all(x['hikariMaximum']==4 and x['hikariMinimumIdle']==0 for x in p['datasources']);cases.append('existing-druid-budget-mapped-to-actual-hikari-without-input-mutation')
c2=config();c2['configuration']['business'].update({'spring.datasource.dynamic.hikari.maximum-pool-size':'6','spring.datasource.dynamic.hikari.minimum-idle':'2'});p=m.connection_pool_budget(c2);assert p['mysqlMaxConnections']==28 and all(x['hikariMaximum']==6 and x['hikariMinimumIdle']==2 for x in p['datasources']if x['side']=='business');cases.append('explicit-hikari-aliases-preserved-and-budget-expanded')
c3=config();c3['configuration']['business'].update({'spring.datasource.dynamic.datasource.master.hikari.max-pool-size':'7','spring.datasource.dynamic.datasource.master.hikari.min-idle':'2'});p=m.connection_pool_budget(c3);assert p['mysqlMaxConnections']==27 and next(x for x in p['datasources']if x['side']=='business'and x['name']=='master')['hikariMaximum']==7;cases.append('per-datasource-hikari-overrides-preserved')
for label,changes in [('conflicting-aliases',{'spring.datasource.dynamic.hikari.max-pool-size':'4','spring.datasource.dynamic.hikari.maximum-pool-size':'5'}),('idle-exceeds-max',{'spring.datasource.dynamic.hikari.min-idle':'5'}),('invalid-numeric-pool-limit',{'spring.datasource.dynamic.druid.max-active':'4;bad'}),('unbounded-total',{'spring.datasource.dynamic.druid.max-active':'128'})]:
    bad=config();bad['configuration']['business'].update(changes)
    try:m.connection_pool_budget(bad)
    except ValueError:cases.append(label+'-refused')
    else:raise AssertionError(label)
c4=config()
for side in c4['configuration']:c4['configuration'][side]={k:v for k,v in c4['configuration'][side].items()if '.druid.'not in k}
p=m.connection_pool_budget(c4);assert p['maximumPoolConnections']==30 and p['mysqlMaxConnections']==42;cases.append('undeclared-pool-defaults-budgeted-without-silent-downsize')
for name,values in [('old',c['configuration']['business']),('mapped',{**c['configuration']['business'],**m.runtime_pool_properties(c,'business')}),('explicit',{**c3['configuration']['business'],**m.runtime_pool_properties(c3,'business')})]:
    (C/(name+'.properties')).write_text(''.join(k+'='+v+'\n'for k,v in values.items()),encoding='ascii')
source='''import java.nio.file.*;import java.io.*;import java.util.*;
import org.springframework.boot.context.properties.bind.Binder;import org.springframework.boot.context.properties.source.MapConfigurationPropertySource;
import com.baomidou.dynamic.datasource.creator.DataSourceProperty;import com.baomidou.dynamic.datasource.creator.hikaricp.*;import com.zaxxer.hikari.HikariDataSource;
public final class OwnHikariBudgetBinding{
 static int[] check(String file)throws Exception{Properties p=new Properties();try(InputStream in=Files.newInputStream(Path.of(file))){p.load(in);}Map<String,Object>v=new LinkedHashMap<>();for(String k:p.stringPropertyNames())v.put(k,p.getProperty(k));Binder b=new Binder(new MapConfigurationPropertySource(v));HikariCpConfig global=b.bind("spring.datasource.dynamic.hikari",HikariCpConfig.class).orElseGet(HikariCpConfig::new);DataSourceProperty d=b.bind("spring.datasource.dynamic.datasource.master",DataSourceProperty.class).get();d.setLazy(true);d.setPoolName("OWN_NUMERIC_BINDING");try(HikariDataSource pool=(HikariDataSource)new HikariDataSourceCreator(global).createDataSource(d)){if(pool.isRunning()||pool.getHikariPoolMXBean()!=null)throw new IllegalStateException("UNEXPECTED_DATABASE_CONNECTION");return new int[]{pool.getMaximumPoolSize(),pool.getMinimumIdle(),(int)pool.getConnectionTimeout()};}}
 public static void main(String[]a)throws Exception{int[] old=check(a[0]),mapped=check(a[1]),explicit=check(a[2]);if(old[0]!=10||old[1]!=10||mapped[0]!=4||mapped[1]!=0||mapped[2]!=5000||explicit[0]!=7||explicit[1]!=2)throw new IllegalStateException("ACTUAL_BINDING_MISMATCH");Files.writeString(Path.of(a[3]),"{\\"oldHikariMaximum\\":10,\\"oldHikariMinimum\\":10,\\"mappedMaximum\\":4,\\"mappedMinimum\\":0,\\"mappedTimeoutMillis\\":5000,\\"perDatasourceOverrideMaximum\\":7,\\"actualSpringBinderAndOriginalCreatorUsed\\":true,\\"databaseConnectionsOpened\\":false}\\n");}
}'''
(C/'OwnHikariBudgetBinding.java').write_text(source,encoding='utf-8')
cp=str(A/'payload/business/lib/*');jdk=A/'runtime/jdk17/bin'
r=subprocess.run([str(jdk/'javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-cp',cp,'-d',str(C),str(C/'OwnHikariBudgetBinding.java')],capture_output=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
if r.returncode:raise RuntimeError('BINDING_COMPILE_FAILED:'+r.stderr.decode(errors='replace')[:1200])
r=subprocess.run([str(jdk/'java.exe'),'-Xmx128m','-cp',str(C)+';'+cp,'OwnHikariBudgetBinding',*[str(C/(n+'.properties'))for n in ['old','mapped','explicit']],str(C/'actual-binding.json')],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
if r.returncode:raise RuntimeError('ACTUAL_BINDING_FAILED:'+r.stderr.decode(errors='replace')[-1200:])
proof={'cases':cases,'policyBoundaryChecksPassed':len(cases),'actualBinding':json.loads((C/'actual-binding.json').read_bytes()),'sourceSHA256':hashlib.sha256((T/'original_connection_pool_policy_r136_20261101.py').read_bytes()).hexdigest(),'actualSixComponentRuntimePending':True};(D/'pool-policy-binding-verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
