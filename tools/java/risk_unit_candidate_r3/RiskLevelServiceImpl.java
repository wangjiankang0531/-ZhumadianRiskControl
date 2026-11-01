package com.iemp.endanger.server.hidden.service.impl;





import com.alibaba.fastjson.JSON;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;

import com.iemp.endanger.base.entity.SendDock;

import com.iemp.endanger.common.dataDocking.enums.TableNameEnums;

import com.iemp.endanger.server.hidden.entity.RiskLevel;

import com.iemp.endanger.server.hidden.entity.RiskLevelApiDock;

import com.iemp.endanger.server.hidden.entity.query.RiskLevelQuery;

import com.iemp.endanger.server.hidden.entity.vo.Dock1;

import com.iemp.endanger.server.hidden.entity.vo.OtherDock1;

import com.iemp.endanger.server.hidden.entity.vo.OtherDock2;

import com.iemp.endanger.server.hidden.mapper.RiskLevelMapper;

import com.iemp.endanger.server.hidden.service.RiskLevelService;

import com.iemp.endanger.server.work.entity.DockLog;

import com.iemp.endanger.server.work.mapper.DockLogMapper;

import com.iemp.endanger.util.CommonUtil;

import com.iemp.endanger.util.http.DockUtil;

import lombok.extern.slf4j.Slf4j;

import org.slf4j.helpers.MessageFormatter;

import org.springframework.beans.factory.annotation.Autowired;

import org.springframework.stereotype.Service;



import java.util.List;



/**

 * @author rachel

 * @date 2025-07-04

 * 作用描述: 区域原始风险分级清单 业务实现类

 */

@Slf4j

@Service

public class RiskLevelServiceImpl extends ServiceImpl<RiskLevelMapper,RiskLevel> implements RiskLevelService{



    @Autowired

    private DockUtil dockUtil;



    @Autowired

    private DockLogMapper logMapper;



    @Override

    public Page<RiskLevel> getPage(Page<RiskLevel> page,RiskLevelQuery query){

        return getBaseMapper().selectPage(page,createQueryWrapper(query));

    }



    @Override

    public List<RiskLevel> getList(RiskLevelQuery query){

        return getBaseMapper().selectList(createQueryWrapper(query));

    }



    @Override

    public boolean save(RiskLevel entity){

        // 创建时间为空时在服务端补齐，保证原表的新增时间与列表排序一致。
        if(entity.getCreateTime()==null){
            entity.setCreateTime(java.time.LocalDateTime.now());
        }
        getBaseMapper().insert(entity);

        dock("c",entity);

        return true;

    }



    @Override
    @org.springframework.transaction.annotation.Transactional(rollbackFor=Exception.class)
    public boolean saveBatch(java.util.Collection<RiskLevel> entities,int batchSize){
        if(entities==null||entities.isEmpty()||batchSize<=0)return super.saveBatch(entities,batchSize);
        java.time.LocalDateTime created=java.time.LocalDateTime.now();
        for(RiskLevel entity:entities){
            if(entity.getCreateTime()==null)entity.setCreateTime(created);
        }
        return super.saveBatch(entities,batchSize);
    }

    @Override

    public boolean updateById(RiskLevel entity){

        getBaseMapper().updateById(entity);

        dock("u",entity);

        return true;

    }



    @Override

    public void dockAll(){

        List<RiskLevel> list=getBaseMapper().selectList(null);

        for(RiskLevel entity:list){

           dock("c",entity);

        }

    }



    /**

     * 发送风险分析单元数据到市或区的数据局

     * @param id 数据id

     */

    @Override

    public void sendMessage(String id){

        dock("c",getBaseMapper().selectById(id));

    }



    /**

     * 发送风险分析单元数据到市或区的数据局

     * @param type 发送方式

     * @param entity 数据实体

     */

    private void dock(String type,RiskLevel entity){

        new Thread(()->{

            try{

                dockUtil.sendDockMessage1(new SendDock(type,new RiskLevelApiDock(entity),"hidden_danger_area_coordinate"));

                dockUtil.sendDockMessage2(new SendDock(type,new Dock1(entity),TableNameEnums.RRU.getValue()));



                OtherDock1 dock1=new OtherDock1(entity);

                String result1=dockUtil.sendDockMessage5(new SendDock(type,dock1,TableNameEnums.DRO.getValue()));

                logMapper.insert(new DockLog(entity.getId(),"风险对象上报市局",JSON.toJSONString(dock1),result1));

                OtherDock2 dock2=new OtherDock2(entity);

                String result2=dockUtil.sendDockMessage5(new SendDock(type,dock2,TableNameEnums.DRRU.getValue()));

                logMapper.insert(new DockLog(entity.getId(),"风险单元上报市局",JSON.toJSONString(dock2),result2));

            }catch(Exception e){

                log.info(MessageFormatter.arrayFormat(log.getName()+"-"+e.getMessage(), e.getStackTrace()).getMessage());

            }

        }).start();

    }





    //这个方法用于创建查询条件QueryWrapper并返回 当没有查询条件时可以直接返回null

    private QueryWrapper<RiskLevel> createQueryWrapper(RiskLevelQuery query){



        QueryWrapper<RiskLevel> wrapper=new QueryWrapper<>();

        // 原筛选条件保持；无条件查询和导出也使用一致的稳定时间顺序。
        if(query!=null){

        if(CommonUtil.isExist(query.getRiskLevel()))wrapper.eq("risk_level",query.getRiskLevel());

        if(CommonUtil.isExist(query.getAnalysisObject()))wrapper.like("analysis_object",query.getAnalysisObject());

        if(CommonUtil.isExist(query.getDepartment()))wrapper.like("department",query.getDepartment());

        if(CommonUtil.isExist(query.getAnalysisUnit()))wrapper.like("analysis_unit",query.getAnalysisUnit());

        }
        return wrapper.orderByDesc("create_time","id");

    }

}

