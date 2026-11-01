"""Adapt only original MaterialsController.importExcel; preserve all other endpoints."""
from hashlib import sha256
PIN='98832f3ab1fd8d36948e1cb4d94f0c13ced9da547055b9d1c1a9b9588083c0d1'
REL='com/iemp/endanger/server/materials/controller/MaterialsController.java'
def transform(raw):
 if sha256(raw).hexdigest()!=PIN:raise ValueError('PINNED_ORIGINAL_MATERIAL_CONTROLLER_REQUIRED')
 nl='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf8').replace('\r\n','\n')
 field='    private MaterialsService service;\n'
 injected=field+'\n    @Autowired\n    private org.springframework.transaction.PlatformTransactionManager xnbyMaterialImportTransactionManager;\n'
 old='''    public void importExcel(MultipartFile file){
        try{
            ExcelUtil.readFirst(file.getInputStream(),Materials.class,service);
        }catch(Exception e){
            e.printStackTrace();
            throw new ServiceException("文件导入失败");
        }
    }'''
 new='''    public void importExcel(MultipartFile file){
        xnby.replica.OriginalMaterialExcelImport.importFile(file,service,xnbyMaterialImportTransactionManager);
    }'''
 if text.count(field)!=1 or text.count(old)!=1:raise ValueError('EXACT_IMPORT_AND_SERVICE_FIELD_REQUIRED')
 adapted=text.replace(field,injected,1).replace(old,new,1)
 if adapted.replace(injected,field,1).replace(new,old,1)!=text:raise ValueError('NON_IMPORT_METHOD_CHANGED')
 out=adapted.replace('\n',nl).encode('utf8')
 return out,{'originalSHA256':PIN,'adaptedSHA256':sha256(out).hexdigest(),'onlyImportMethodAndTransactionManagerInjectionChanged':True,'allOtherControllerMethodsBytePreserved':True,'newEndpointOrDatabaseModelAdded':False}
