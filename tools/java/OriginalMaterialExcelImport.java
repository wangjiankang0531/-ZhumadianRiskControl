package xnby.replica;

import com.alibaba.excel.context.AnalysisContext;
import com.alibaba.excel.metadata.data.ReadCellData;
import com.alibaba.excel.read.listener.ReadListener;
import com.iemp.endanger.server.materials.entity.Materials;
import com.iemp.endanger.server.materials.service.MaterialsService;
import com.iemp.endanger.util.export.excel.ExcelUtil;
import com.iemp.endanger.util.response.ServiceException;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.multipart.MultipartFile;
import java.io.BufferedInputStream;
import java.io.IOException;
import java.util.*;

/** Material import only: existing XLS/XLSX layout and append semantics, one file transaction. */
public final class OriginalMaterialExcelImport {
 private OriginalMaterialExcelImport(){}
 private static final Set<String> REQUIRED_HEADERS=Set.of("物资名称","物资类型","所属部门","坐标");
 private static ServiceException invalid(String message){return new ServiceException(message);}
 public static void importFile(MultipartFile file,MaterialsService service,PlatformTransactionManager manager){
  if(file==null||file.isEmpty())throw invalid("请选择非空的 xls / xlsx 文件。");
  Objects.requireNonNull(service,"material service");Objects.requireNonNull(manager,"material transaction manager");
  try{
   new TransactionTemplate(manager).execute(status->{
    try(var input=new BufferedInputStream(file.getInputStream())){
     input.mark(8);byte[] magic=input.readNBytes(8);input.reset();
     boolean xlsx=magic.length>=4&&magic[0]==0x50&&magic[1]==0x4b&&magic[2]==3&&magic[3]==4;
     boolean xls=Arrays.equals(magic,new byte[]{(byte)0xd0,(byte)0xcf,0x11,(byte)0xe0,(byte)0xa1,(byte)0xb1,0x1a,(byte)0xe1});
     if(!xlsx&&!xls)throw invalid("文件内容不是有效的 xls / xlsx，请使用物资模板。");
     ExcelUtil.readFirst(input,Materials.class,new ReadListener<Materials>(){
      final List<Materials> batch=new ArrayList<>(3000); boolean headerChecked;
      @Override public void invokeHead(Map<Integer,ReadCellData<?>> header,AnalysisContext context){
       var seen=new HashSet<String>();
       for(var cell:header.values()){
        String text=Objects.toString(cell.getStringValue(),"").trim();
        if(REQUIRED_HEADERS.contains(text)&&!seen.add(text))throw invalid("物资模板必填列重复，请重新下载模板。");
       }
       if(!seen.containsAll(REQUIRED_HEADERS))throw invalid("缺少物资名称、物资类型、所属部门或坐标列，请使用物资模板。");
       headerChecked=true;
      }
      @Override public void invoke(Materials entity,AnalysisContext context){
       if(!headerChecked)throw invalid("缺少物资模板表头。");
       if(blank(entity.getMaterialName())||blank(entity.getMaterialType())||blank(entity.getDepartment())||blank(entity.getCoordinate()))throw invalid("第 "+(context.readRowHolder().getRowIndex()+1)+" 行缺少必填物资信息，请核对模板。");
       batch.add(entity);if(batch.size()==3000)flush();
      }
      void flush(){if(batch.isEmpty())return;if(!service.saveBatch(new ArrayList<>(batch)))throw invalid("物资保存未完成，请核对导入结果后重试。");batch.clear();}
      @Override public void doAfterAllAnalysed(AnalysisContext context){if(!headerChecked)throw invalid("缺少物资模板表头。");flush();}
     });
    }catch(IOException error){throw invalid("文件读取失败，请核对文件后重试。");}
    return null;
   });
  }catch(ServiceException error){throw error;}catch(RuntimeException error){throw invalid("文件导入未完成，请核对模板及导入结果后重试。");}
 }
 private static boolean blank(String text){return text==null||text.isBlank();}
}
