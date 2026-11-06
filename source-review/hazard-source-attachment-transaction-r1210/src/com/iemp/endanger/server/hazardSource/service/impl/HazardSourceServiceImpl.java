package com.iemp.endanger.server.hazardSource.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.iemp.endanger.base.entity.SendDock;
import com.iemp.endanger.base.service.BaseFileService;
import com.iemp.endanger.server.hazardSource.entity.HazardSource;
import com.iemp.endanger.server.hazardSource.entity.query.HazardSourceAnalysisQuery;
import com.iemp.endanger.server.hazardSource.entity.query.HazardSourceQuery;
import com.iemp.endanger.server.hazardSource.entity.vo.HazardSourceApiDock;
import com.iemp.endanger.server.hazardSource.entity.vo.HazardSourceSumApiDock;
import com.iemp.endanger.server.hazardSource.entity.vo.HazardSourceVo;
import com.iemp.endanger.server.hazardSource.mapper.HazardSourceMapper;
import com.iemp.endanger.server.hazardSource.service.HazardSourceService;
import com.iemp.endanger.server.websocket.SocketEntity;
import com.iemp.endanger.server.websocket.WebSocket;
import com.iemp.endanger.util.CommonUtil;
import com.iemp.endanger.util.analysis.AnalysisUtil;
import com.iemp.endanger.util.analysis.entity.AnalysisValue;
import com.iemp.endanger.util.analysis.entity.vo.AnalysisValueVo;
import com.iemp.endanger.util.http.DockUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * @author rachel
 * @date 2025-04-12
 * 作用描述:  业务实现类
 */
@Service
public class HazardSourceServiceImpl extends ServiceImpl<HazardSourceMapper, HazardSource> implements HazardSourceService{

    @Autowired
    private WebSocket webSocket;

    @Autowired
    private DockUtil dockUtil;

    @Autowired
    private BaseFileService baseFileService;

    @Override
    public Page<HazardSource> getPage(Page<HazardSource> page,HazardSourceQuery query){
        return getBaseMapper().selectPage(page,createQueryWrapper(query));
    }

    @Override
    public List<HazardSource> getList(HazardSourceQuery query){
        return getBaseMapper().selectList(createQueryWrapper(query));
    }

    @Override
    public HazardSourceVo getById(String id){
        HazardSourceVo vo=new HazardSourceVo();
        vo.setHazardSource(getBaseMapper().selectById(id));
        vo.setBaseFileList(baseFileService.getFileList(id));
        return vo;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean save(HazardSourceVo vo){
        if (getBaseMapper().insert(vo.getHazardSource()) != 1) return false;
        if(CommonUtil.isExist(vo.getBaseFileList())){
            baseFileService.insertFile(vo.getBaseFileList(),vo.getHazardSource().getId());
        }
        webSocket.sendMessageAll(SocketEntity.getMessage(vo.getHazardSource().getId(),"新增","危险源"));
        dockUtil.sendDockMessage1(new SendDock("c",new HazardSourceApiDock(vo.getHazardSource()),"hazard_source_infor_list"));
        return true;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean updateById(HazardSourceVo vo){
        // Acquire/update the live business row before touching its attachments.
        // A missing or concurrently deleted row returns false with no link writes.
        if (getBaseMapper().updateById(vo.getHazardSource()) != 1) return false;
        baseFileService.deleteFile(vo.getHazardSource().getId());
        if(CommonUtil.isExist(vo.getBaseFileList())){
            baseFileService.insertFile(vo.getBaseFileList(),vo.getHazardSource().getId());
        }
        return true;
    }

    @Override
    public List<AnalysisValue<Integer>> getAnalysis1(HazardSourceAnalysisQuery query){
        return getBaseMapper().selectAnalysis1(query);
    }

    @Override
    public AnalysisValueVo<Integer> getAnalysis2(HazardSourceAnalysisQuery query){
        return AnalysisUtil.getValueVo(getBaseMapper().selectAnalysis2(query));
    }

    @Override
    public List<AnalysisValue<Integer>> getAnalysis3(HazardSourceAnalysisQuery query){
        return getBaseMapper().selectAnalysis3(query);
    }

    @Override
    public List<AnalysisValue<Integer>> getAnalysis4(HazardSourceAnalysisQuery query){
        return getBaseMapper().selectAnalysis4(query);
    }

    @Override
    public AnalysisValueVo<Integer> getAnalysis5(HazardSourceAnalysisQuery query){
        return AnalysisUtil.getValueVo(getBaseMapper().selectAnalysis5(query));
    }

    @Override
    public void dock(String type){
        List<AnalysisValue<Integer>> list=getAnalysis1(new HazardSourceAnalysisQuery());
        Map<String,Integer> map=list.stream().collect(Collectors.toMap(AnalysisValue::getName,AnalysisValue::getValue));
        HazardSourceSumApiDock dock=new HazardSourceSumApiDock();
        dock.setId("1");
        dock.setRisk_quantity_1(map.get("一级")==null?0:map.get("一级"));
        dock.setRisk_quantity_2(map.get("二级")==null?0:map.get("二级"));
        dock.setRisk_quantity_3(map.get("三级")==null?0:map.get("三级"));
        dock.setRisk_quantity_4(map.get("四级")==null?0:map.get("四级"));
        dock.setRisk_quantity_sum(map.values().stream().reduce(Integer::sum).get());
        dockUtil.sendDockMessage1(new SendDock(type,dock,"risk_danger"));
    }

    @Override
    @Scheduled(cron="0 0 0/1 * * *")
    public void dockScheduled(){
       dock("u");
    }

    //这个方法用于创建查询条件QueryWrapper并返回 当没有查询条件时可以直接返回null
    private QueryWrapper<HazardSource> createQueryWrapper(HazardSourceQuery query){
        if(query==null)return null;
        QueryWrapper<HazardSource> wrapper=new QueryWrapper<>();
        //这里写query条件相关判断
        if(CommonUtil.isExist(query.getSourceName()))wrapper.like("source_name",query.getSourceName());
        if(CommonUtil.isExist(query.getMaterialType()))wrapper.like("material_type",query.getMaterialType());
        wrapper.orderByDesc("created_at");
        return wrapper;
    }
}
