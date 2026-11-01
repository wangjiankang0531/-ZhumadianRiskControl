package com.iemp.endanger.server.hidden.controller;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.cqweh.cloud.common.model.Response;
import com.iemp.endanger.server.hidden.entity.RiskLevel;
import com.iemp.endanger.server.hidden.entity.query.RiskLevelQuery;
import com.iemp.endanger.server.hidden.service.RiskLevelService;
import com.iemp.endanger.util.export.excel.ExcelUtil;
import com.iemp.endanger.util.response.ServiceException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.ArrayList;

/**
 * @author rachel
 * @date 2025-07-04
 * 作用描述: 区域原始风险分级清单 控制层
 */
@Tag(name="RiskLevelController",description="区域原始风险分级清单管理")
@RestController
@RequestMapping("/riskLevel")
public class RiskLevelController{

    @Autowired
    private RiskLevelService service;

    @Operation(summary="区域原始风险分级清单详情")
    @GetMapping("/getById")
    public Response getById(String id){
        return Response.success(service.getById(id));
    }

    @Operation(summary="区域原始风险分级清单新增")
    @PostMapping("/save")
    public Response save(@RequestBody RiskLevel entity){
        return Response.success(service.save(entity));
    }

    @Operation(summary="区域原始风险分级清单修改")
    @PostMapping("/updateById")
    public Response updateById(@RequestBody RiskLevel entity){
        return Response.success(service.updateById(entity));
    }

    @Operation(summary="区域原始风险分级清单删除")
    @GetMapping("/removeById")
    public Response removeById(String id){
        return Response.success(service.removeById(id));
    }

    @Operation(summary="分页查询")
    @GetMapping("/getPage")
    public Response getPage(int current,int size,RiskLevelQuery query){
        return Response.success(service.getPage(new Page<>(current,size),query));
    }

    @Operation(summary="导出")
    @GetMapping("/export")
    public void export(RiskLevelQuery query,HttpServletResponse response){
        try{
            ExcelUtil.fastWrite(response.getOutputStream(),RiskLevel.class,service.getList(query),null);
        }catch(IOException e){
            e.printStackTrace();
        }
    }

    @Operation(summary="导入")
    @PostMapping("/importExcel")
    @org.springframework.transaction.annotation.Transactional(rollbackFor=Exception.class)
    public void importExcel(MultipartFile file){
        try{
            try(java.io.InputStream input=org.apache.poi.poifs.filesystem.FileMagic.prepareToCheckMagic(file.getInputStream())){
                var magic=org.apache.poi.poifs.filesystem.FileMagic.valueOf(input);
                if(magic!=org.apache.poi.poifs.filesystem.FileMagic.OLE2&&magic!=org.apache.poi.poifs.filesystem.FileMagic.OOXML)throw new ServiceException("请上传有效的Excel文件");
                ExcelUtil.readFirst(input,RiskLevel.class,service);
            }
        }catch(Exception e){
            e.printStackTrace();
            throw new ServiceException("文件导入失败");
        }
    }

    @Operation(summary="下载模板")
    @GetMapping("/getModel")
    public void importExcel(HttpServletResponse response){
        try{
            ExcelUtil.fastWrite(response.getOutputStream(),RiskLevel.class,new ArrayList<>(),"sheet");
        }catch(Exception e){
            e.printStackTrace();
            throw new ServiceException("文件导入失败");
        }
    }

    @Operation(summary="全部对接")
    @GetMapping("/dockAll")
    public void dockAll(){
        service.dockAll();
    }

    @Operation(summary="对接测试")
    @GetMapping("/sendMessage")
    public void sendMessage(String id){
        service.sendMessage(id);
    }

}
