# Web满预算视口覆盖目标重平衡

日期2026-10-21，实验阶段。承接bff6aba，完整UE/EXE/Web业务/迁移目标active。

## 真实问题与策略

旧maintain在视口放大后直接coverageGuard.resize；该方法先释放旧目标再按新尺寸预留。当细层已接近512MiB，新目标更大而空间不足，预留抛错；maintain随后每次return，无法释放足够细层空间，持续没有覆盖目标，细节加载无法继续。

新maintain先计算held-oldCoverage+newCoverage。若超过原预算，独占pending.type=viewport，释放旧覆盖目标后调用resizeSourceViewport。根据实际ledger-held与当前完整前沿字节数计算其余固定开销，恢复期间capacity=limit-fixed；用真实目标字节作为最终reservedBytes。每个完整回退步骤都检查原始父页共存峰值，不能以最终能装下代替恢复过程能装下。最后在申请新目标前再次检查ledger的新鲜占用。

固定viewport缓冲是运行必需开销，不是有像素收益的新细节。source_recovery_plan新增显式resourceKind=viewport，只接受id0/parent null/score0/无新增驻留槽请求；所有普通detail请求仍默认原两倍收益迟滞。viewport路径按估计画质损失增量/释放字节排序，能恢复较小完整父层时先回退父层，恢复共存无法满足时可以退回已常驻的完整基础层。它是预算压力下的启发式选择，不保证全局最小画质损失；不会冒用Infinity细节收益。该强制固定开销策略与普通细节质量迟滞明确区分。

每次回退后仍是完整cut。取消、源页失败或视口再次变化时保留最近已提交完整cut；恢复失败沿既有restoreFailed记录排除失败父层，下一轮可以选择其它分支或基础层。viewport的epoch/尺寸/fine/photo及拥有者不符即取消，清空过期gain估计，下一轮重新采样。实际上传、SHA/租约/原始页验证、2px缺口保护及512MiB预算不放松。强制重平衡会在必要范围内降低局部细节，随后按新视口重新分配细节。

## 验证与可见控制

全Web469项通过（461+8）。针对测试使用真实SourcePageBudget和SourceFrontier：满账本放大、最低估计损失完整根退回、父A再父P两步恢复且每步共存峰值<=账本、缩小/有余量不回退、步间取消、父页读取失败后基础层回退、申请前出现新预留、非法尺寸/过期请求，以及普通细节不能调用固定开销策略。原普通细节九项恢复测试通过。

QA按钮仅qa=1&viewportQA=1开启：验收小视口768×344、验收大视口1280×573、恢复自适应视口。按钮修改真实viewport CSS尺寸，触发原ResizeObserver、renderer尺寸、投影矩阵和加载流程，未通过脚本直接改私有状态。它验证的是应用渲染视口改变，不等同已验证OS原生窗口拖动、多DPI、所有分辨率或8K。小/大视口比例接近，减少因相机宽高比差异导致的无关区块卸载。

性能明细新增viewportBudget累计请求/完成/取消/错误/步骤/根回退及最近结果，viewport显示实际宽高、guard宽高和字节；console独立记录viewport budget step。没有无界历史数组。源码冻结快照与最终重建证明将和实机事件归档。

## 包及尚未完成范围

W11=Application/work/web_viewport_budget_20261021，E11对应Deployment。manifest a8191c4d6011d6d8dcebac84449407b4e482f8e549ea9f3f23acbec5345979b2，viewerff8ec494eda8ca35751e7758b7194f926e374a0d0ab50b4295d50ec33110b0c2。从前版5840项声明文件复制，仅viewer变；同一外部只读Data，无GIS、旧UserData复制。

本次真实GPU压力与最终回收结果见下节；不能由这两次近景证明所有尺寸、相机或系统窗口行为。上传峰值、冷20秒/全区/外围合理层级、Web严格双轮、原始来源深度/8K，以及UE/EXE/Web业务/IAM/261013/252/迁移目标继续。旧25已同步ed5fafc；新14固定source5d→0925990仍等具体授权，后续ec1/bff及本轮候选不混入该载荷。

## 实机压力结果与终态

RTX5080/D3D11，同一近景相机，两次768×344→1280×573，均经可见按钮触发原ResizeObserver。

| 项目 | 第一次 | 第二次 |
| --- | ---: | ---: |
| 放大前held | 536396484 | 536570884 |
| 放大前空余bytes | 474428 | 300028 |
| 直接换目标将超额bytes | 3279556 | 3453956 |
| 新目标bytes | 5867520 | 5867520 |
| 完整父层恢复步骤 | 1 | 1 |
| 整根退回基础层 | 0 | 0 |
| 目标分配完成时held | 501653340 | 501827740 |

两次都恢复Tile221的Tile_221_L17_0uu.osgb完整父层；第一次indexed提交11→13、root请求32→41、family23→27；第二次indexed17→19、root63→71、family65→70，证明不只创建目标，后续细层加载继续推进。两次原始步骤及完成事件分别保存在first/second_growth_logs，计数和实际账目见actual_resize_validation.json。直接换目标超额是依据实测前状态和旧分配公式计算，并非在旧浏览器中额外注入/运行故障。

缩小后目标释放为2113536bytes且没有新增强制重平衡；恢复自适应为1280×573，完成数仍2，无多余强制回退。此次两次实际各一步父层恢复，无实机多步/整根回退/中途取消或失败注入；这些分支仅由明确单元测试覆盖，不冒称实机全部验证。固定开销策略可能降低必要分支细节，未锁定相同活动cut，不宣称画质与未resize版本逐像素一致。

继续道路近景约81.482s，仍拦截原始细层缺口并保留父层。道路source_upload最高70.80ms、帧间隔最高66.60ms，上传长帧仍未解决；viewport resize不是冷启动/完整加载性能测试。初始shader峰值仍保留在initial采样中，不能把近期P95当全阶段性能。

累计覆盖90、拒绝4、恢复8零错误。总览roots/active/retained/coverage均0，held1024，峰536788444bytes<536870912，仅细层账目不代表全部浏览器VRAM。服务51272/session87164已owner204/exit0，reader500 closed，保护写0，最终lease/job/waiter0、构建失败0。总运行364.032s含停留与机位/尺寸切换，不是加载时间。私有--check/原始样本SHA验证通过，冻结源重建viewer逐字节一致。

新入口Application/实验入口/地景加载优化_20261020/启动Web视口预算实验.cmd已生成未代运行，随机回环、独立manual_runs、owner/Job回收。公网/EXE/业务库/用户DLG未切换，数据库结构未变。应用视口这组近景重复放大问题已取得实机证据，OS原生拖动/多DPI/其它尺寸与相机仍未覆盖；全部长期与短期目标保持active。
