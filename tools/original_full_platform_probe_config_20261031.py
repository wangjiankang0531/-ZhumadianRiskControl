"""Construct only synthetic whole-platform configuration; retain original source feature flags."""
from pathlib import Path
import hashlib,re,uuid,zipfile
import original_server_release_parameters as p

SAFE_SOURCE_KEYS={'flowable.app.enabled','flowable.cmmn.enabled','flowable.content.enabled','flowable.dmn.enabled','flowable.eventregistry.enabled','flowable.idm.enabled','flowable.async-executor-activate','flowable.async-history-executor-activate','flowable.check-process-definitions','spring.mvc.pathmatch.matching-strategy','spring.main.allow-bean-definition-overriding','spring.main.allow-circular-references'}

def safe_defaults(jar):
 values={};stack=[]
 with zipfile.ZipFile(jar) as archive:
  for line in archive.read('BOOT-INF/classes/application.yml').decode('utf8').splitlines():
   m=re.match(r'^( *)([A-Za-z0-9_.-]+)\s*:\s*(.*)$',line)
   if not m:continue
   indent=len(m[1])
   while stack and stack[-1][0]>=indent:stack.pop()
   stack.append((indent,m[2]));key='.'.join(x[1] for x in stack)
   if key in SAFE_SOURCE_KEYS:
    value=m[3].split('#',1)[0].strip().strip('"\x27');assert re.fullmatch('[A-Za-z0-9_-]+',value);values[key]=value
 return values

def build(platform,original_jar,database_port,redis_port,object_port,password,access,owner):
 platform=Path(platform);data=platform.parents[1];assert data.name=='TianjinOriginalPlatform';(data/'files').mkdir(exist_ok=True)
 (data/'identity.properties').write_bytes(p.properties_ascii({'schema':'xnby.original.platform.local-data.v1','ownerId':owner,'filesRelativePath':'files/'}))
 for name in ['tmp','home','logs']:(platform/name).mkdir(exist_ok=True)
 values=safe_defaults(original_jar);values.update({'spring.application.name':'jnpf-admin','spring.profiles.active':'own-full-platform-probe','server.address':'127.0.0.1','server.port':'0','server.servlet.context-path':'/','spring.main.banner-mode':'off','spring.main.allow-circular-references':'true','spring.cloud.bootstrap.enabled':'false','spring.cloud.discovery.enabled':'false','spring.cloud.nacos.discovery.enabled':'false','spring.cloud.nacos.config.enabled':'false','spring.jmx.enabled':'false','management.endpoints.enabled-by-default':'false','spring.mvc.pathmatch.matching-strategy':'ant_path_matcher','spring.datasource.db-type':'MySQL','spring.datasource.db-name':'jnpf','spring.datasource.db-schema':'','spring.datasource.host':'127.0.0.1','spring.datasource.port':str(database_port),'spring.datasource.username':'xnby_whole_main','spring.datasource.password':password,'spring.datasource.prepare-url':'jdbc:mysql://127.0.0.1:'+str(database_port)+'/jnpf?useUnicode=true&characterEncoding=UTF-8&useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=UTC&connectTimeout=5000&socketTimeout=15000','spring.datasource.dynamic.primary':'master','spring.datasource.dynamic.strict':'true','spring.datasource.dynamic.druid.initial-size':'0','spring.datasource.dynamic.druid.min-idle':'0','spring.datasource.dynamic.druid.max-active':'4','spring.datasource.dynamic.druid.max-wait':'5000','spring.redis.host':'127.0.0.1','spring.redis.port':str(redis_port),'spring.redis.password':password,'spring.redis.database':'0','spring.redis.timeout':'5000','sa-token.jwt-secret-key':uuid.uuid4().hex,'context.initializer.classes':'xnby.replica.ServerLifecycleObservation,xnby.platform.PlatformWritableObservation,xnby.platform.OriginalIdGeneratorShutdown,xnby.platform.OriginalTaskTokenBridgeSpringRegistration','logging.level.root':'INFO','logging.file.name':str(platform/'logs/platform.log')})
 url=values['spring.datasource.prepare-url']
 for key,value in {'url':url,'username':'xnby_whole_main','password':password,'driver-class-name':'com.mysql.cj.jdbc.Driver'}.items():values['spring.datasource.dynamic.datasource.master.'+key]=value
 for key in ['ErrorReport','RecordLog','TestVersion','IgexinEnabled']:values['config.'+key]='false'
 for key in ['SoftVersion','AppVersion','AppUpdateContent','CodeAreasName']:values['config.'+key]='OWN_FULL_PLATFORM'
 for key in ['IgexinAppid','IgexinAppkey','IgexinMastersecret','YozoAppId','YozoAppKey','YozoDomainKey']:values['config.'+key]='OWN_'+uuid.uuid4().hex
 for key in ['AllowPreviewFileType','AllowUploadFileType','AllowUploadImageType','MPUploadFileType','WeChatUploadFileType']:values['config.'+key]='.txt,.png,.pdf'
 values['config.PreviewType']='1';values['config.ErrorReportTo']='own-probe@example.invalid'
 for key in ['ApiDomain','AppDomain','FrontDomain','MultiTenancyUrl','YozoCloudDomain','YozoDomain','YozoEditDomain','kkFileUrl']:values['config.'+key]='http://127.0.0.1:'+str(object_port)+'/own-dependency-unavailable'
 for key in ['BiVisualPath','DataBackupFilePath','DocumentFilePath','DocumentPreviewPath','EmailFilePath','IMContentFilePath','MPMaterialFilePath','SystemFilePath','TemplateCodePath','TemplateCodePathVue3','TemplateFilePath','TemporaryFilePath','UserAvatarFilePath','WebAnnexFilePath','WebDirectoryPath','ServiceDirectoryPath']:
  folder=data/'files'/key;folder.mkdir(exist_ok=True);values['config.'+key]=folder.as_posix()+'/'
 base='config.file-storage.minio[0].';endpoint='http://127.0.0.1:'+str(object_port);values['config.file-storage.default-platform']='minio-1'
 for key,value in {'platform':'minio-1','enable-storage':'true','end-point':endpoint,'access-key':access,'secret-key':password,'bucket-name':'own-full-main','base-path':'','domain':endpoint+'/own-full-main/'}.items():values[base+key]=value
 return values
