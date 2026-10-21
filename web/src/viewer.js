import {captureSourceResidency} from './source_residency_audit.js';
import {FixedFrameWitness,visibilityWitnessGrid} from './startup_witness.js';
import {runStaticUploadJobs} from './static_upload_jobs.js';
import {uploadStaticTexture} from './static_texture_upload.js';
import {uploadStaticGeometry} from './static_geometry_upload.js';
import {StartupProfile} from './startup_profile.js';
import {AllocationFeasibilityMemo,allocationBudgetState,sameAllocationBudgetState} from './source_allocation_memo.js';
import {FrameProfile,SceneGpuTimer,webglDeviceInfo} from './frame_profile.js';
import {installOriginalImageQA} from './original_image_qa.js';
import {originalImageStats} from './original_image.js';
import {uploadSourceScene} from './source_upload.js';
import {sourceSurfaceHeight} from './source_surface_height.js';
import {loadSourceLevelIndex,initialIndexedCoverageDepth,indexedResidentCapacity} from './source_level_index.js';
import {isMemoryFamily,isIndexedMemoryFamily} from './source_page_format.js';
import {SourceCoverageGuard,coverageDimensions} from './source_coverage.js';
import {resizeSourceViewport} from './source_viewport_budget.js';
import {updateCommandDashboard} from './command_dashboard.js';
import {layoutLabels,readLabelOffsets} from './label_layout.js';
import {supportsSourcePlans,readSourcePlan,verifyPlannedSource,SourcePlanResponseError,SourcePlanCache,IndexedSourceQualityLimit,SourcePlanChanged} from './source_descriptor_plan.js';
import {OrbitActivity} from './orbit_activity.js';
import {chooseRefinementCandidate,chooseIndexedCoverageCandidate,chooseFeasibleSourceCandidate,SourceAllocationScan} from './source_allocation.js';
import {SourceVisibility,visiblePixelPriority,matchesVisibilityCamera} from './source_visibility.js';
import * as THREE from 'three';
import {readPortalConfiguration,OAuthLogin} from './oauth_login.js';
import {BusinessConnection} from './business_connection.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {drawLabel,drawSign,drawSignLeader,measureSign,labelWorldAnchor,labelFramingPositions,markerScreenPoint,signFootFeature} from './labels.js';
import {LayerLoading} from './layer_loading.js';
import {topics,categories,documentFingerprint,parseSpatialCatalog,spatialObject,catalogOrphans} from './spatial_catalog.js';
import {inSceneTopic as inTopic,scopedSceneObjects as scopedObjects,sceneTopicCounts as topicCounts} from './spatial_scene_scope.js';
import {opacityFromTransparency,annotationWithOpacity,applyModelOpacity} from './view_opacity.js';
import {businessDetailRows} from './business_binding.js';
import {validateLandscapeDocument as validate} from './landscape_document.js';
import {parseBusinessRecords,businessRecordRows,businessRecordSearchText,businessCoverage} from './business_records.js';
import {matchesFeature,featureTypeNames,buildHitTarget,pickAnnotation,ClickGesture} from './annotation_interaction.js';
import {selectDepth,prioritizeDetail,pickFocusRoot} from './lod_policy.js';
import {resolveBaseQuality} from './base_quality.js';
import {gasSceneRequest,rememberGasScene,resumeGasScene,gasSceneTarget} from './gas_scene_focus.js';
import {parseInspectionView} from './inspection_view.js';
import {LeasedDownloads} from './lod_downloads.js';
import {ensureSourceWanted,SourceLoadCancelled} from './lod_transaction.js';
import {withSourceRestorations,SourceRestoreUnavailable,sourceBundleIdentity} from './source_residency.js';
import {SourceFrontier,pickVisibleSource,visibleSourceCandidates,sourceViewPriority,sourceRefinementScore,rankSourceCandidates,planSourceBudget} from './source_frontier.js';
import {supportsPreparedBc7} from './prepared_bc7.js';
import {planPreparedSourceBundle,stagePreparedSourceBundle,originalSourceBundle,subsetPreparedSourcePlan,SourcePagePlanChanged,sourcePageTextureIdentity} from './prepared_source_page.js';
import {PreparedTextureIndex} from './prepared_texture_index.js';
import {SourcePageBudget,sourceRestorationFootprint} from './source_page_budget.js';
import {planSourceRecoverySequence,applySourceRecoverySequence,sourceRecoverySnapshot} from './source_recovery_plan.js';
import {SourceGeometryGainWorker,SourceGainUnavailable} from './source_gain_client.js';
const $=id=>document.getElementById(id), viewport=$('viewport');
const scene=new THREE.Scene();scene.background=new THREE.Color('#809ab0');
const camera=new THREE.PerspectiveCamera(52,1,.5,60000);camera.up.set(0,0,1);
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.NoToneMapping;
viewport.insertBefore(renderer.domElement,viewport.firstChild);
const frameProfile=new FrameProfile({enabled:new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('profile')==='1'}),sceneGpuTimer=new SceneGpuTimer(renderer.getContext(),frameProfile),frameDevice=frameProfile.enabled?webglDeviceInfo(renderer.getContext()):null;let profilePanel=null,lastProfilePublish=0;
if(frameProfile.enabled){const section=document.createElement('section'),title=document.createElement('h3'),summary=document.createElement('p'),details=document.createElement('details'),label=document.createElement('summary'),pre=document.createElement('pre');section.setAttribute('aria-label','本机性能验收采样');title.textContent='性能采样（验收模式）';summary.dataset.testid='frame-profile-summary';label.textContent='查看性能采样明细';pre.dataset.testid='frame-profile-json';pre.style.cssText='white-space:pre-wrap;font-size:10px;max-height:320px;overflow:auto';details.append(label,pre);section.append(title,summary,details);$('information').append(section);profilePanel={summary,pre};window.addEventListener('pagehide',()=>sceneGpuTimer.dispose());}
const startupProfile=new StartupProfile({enabled:frameProfile.enabled,record:(name,ms)=>frameProfile.record(name,ms)});
function publishFrameProfile(){if(!frameProfile.enabled)return;const r={...frameProfile.snapshot(),device:frameDevice,gpu:sceneGpuTimer.snapshot(),allocationFeasibility:allocationFeasibilityMemo.snapshot(),allocationScan:allocationScanStats,viewportBudget:viewportBudgetStats,uploadGL:uploadGLStats,originalImages:originalImageStats(),startup:startupProfile.snapshot(),staticUploads,staticTextureUploads,staticContextRedirects,staticOnlyQA,staticUploadConcurrency,sourcePreparationConcurrency,preserveWantedRoots,sourceBudgetEvents,balancedRegions,startupWitness:startupWitness.snapshot(),viewport:{width,height,coverageWidth:coverageGuard.width,coverageHeight:coverageGuard.height,coverageBytes:coverageGuard.bytes},scene:{drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,roots:resident.size,pending:pending?.type??null,pageBudget:pageBudget.snapshot()}};profilePanel.summary.textContent=`GPU: ${frameDevice.renderer??'不可读取'} · CPU帧P95 ${(r.stages.frame_cpu?.p95RecentMs??0).toFixed(2)}ms · GPU场景P95 ${r.stages.gpu_scene?(r.stages.gpu_scene.p95RecentMs.toFixed(2)+'ms'):'不可用'} · 调度最大 ${(r.stages.maintain?.maxMs??0).toFixed(2)}ms`;profilePanel.pre.textContent=JSON.stringify(r,null,2);console.info('[frame profile] '+JSON.stringify(r));}

const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.12;controls.maxDistance=40000;controls.minDistance=8;controls.maxPolarAngle=Math.PI*.49;
const orbitActivity=new OrbitActivity(controls);
const preserveWantedRoots=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('rootFloor')==='1',budgetAuditEnabled=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('budgetAudit')==='1',sourceBudgetEvents=[];
const sourcePreparationConcurrency=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('pageLoads')==='2'?2:1;
const staticUploadConcurrency=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('staticUpload')==='serial'?1:2;
const staticOnlyQA=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('staticOnly')==='1',verifyStaticGPU=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('geometryQA')==='1',staticUploads=[];
let staticContextRedirects=0;const staticTextureUploads=[];const staticManager=new THREE.LoadingManager();staticManager.setURLModifier(url=>{if(url==='assets/showcase/runtime/zhumadian/context/context.jpg'){staticContextRedirects++;return 'assets/showcase/runtime/zhumadian/context/context_colormatched.jpg';}return url;});
const loader=new GLTFLoader(staticManager),photoGroup=new THREE.Group(),contextGroup=new THREE.Group();scene.add(photoGroup,contextGroup);
const HUD=$('annotations'),ctx=HUD.getContext('2d');let layersDoc=null,businessCatalog=null,businessLoadGeneration=0,selected=null,base=null,catalog=null,width=1,height=1,lastRank=0;
let resident=new Map(),pending=null,epoch=0,lastError='',lastStation='',frames=0,fps=0,frameClock=performance.now();
const sourceVisibility=new SourceVisibility(renderer,scene,contextGroup);let visibilityReady=false;
const budget=512*1024*1024,uploadTargetBytes=16*16*4;let detailLimit=budget-uploadTargetBytes;
const pageBudget=new SourcePageBudget(budget);pageBudget.reserve({format:'upload_target',bytes:uploadTargetBytes});
let sourcePlansEnabled=false,sourceLevelIndex=null;
const sourcePlanCache=new SourcePlanCache();
const indexedRootsRequested=new URLSearchParams(location.search).get('levelIndex')==='1',indexedCutsRequested=new URLSearchParams(location.search).get('levelCut')==='1';
const residencyAuditEnabled=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('residencyAudit')==='1',residencyRejectedProbes=[];
const balancedRegions=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('regionBalance')==='1';
function sourceResidentLimit(){return sourceLevelIndex?indexedCutsRequested?indexedResidentCapacity(sourceLevelIndex.index.records.length):residentLimit:Infinity;}
const coverageGuard=new SourceCoverageGuard({renderer,scene,photoGroup,contextGroup,reserve:request=>pageBudget.reserve(request),measure:(name,fn)=>frameProfile.measure(name,fn),reference:new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('coverageReference')==='1'}),coverageRejected=new Set();
let preparedTextures=new PreparedTextureIndex({schema:'xnby.prepared_texture_index.v1',entries:[]},location.href);
const imageCache=new Map();let markerAtlas=null;
let baseEdges=new Map(),baseTexels=new Map(),focusId=0;const tierEdges=new Map(),tierTexels=new Map(),residentLimit=16;
const layerOpacities=new Map(),layerLoading=new LayerLoading();let userLayerLoad=false;
let activeTopic='all',spatialCatalog=null,spatialFingerprint='',spatialFingerprintPromise=Promise.resolve(''),spatialLoadGeneration=0,userSpatialLoad=false,userBusinessLoad=false;
let signOffsets=new Map(),signPrevious=new Map(),signPlacements=new Map(),signDrag=null,signPreferenceKey='',signLayoutKey='',signLayoutResult=null;
const signMetrics=new Map();
let dataMode='pending',apiBusinessState='unconfigured',businessConnection=null,oauthLogin=null;
const activeCatalog=()=>spatialFingerprint&&spatialCatalog?.layerFingerprint===spatialFingerprint?spatialCatalog:null;
const sceneOpacity=id=>opacityFromTransparency($(id+'-opacity').value);
function updateSceneOpacity(){applyModelOpacity(photoGroup,sceneOpacity('photo'),$('photo').checked);applyModelOpacity(contextGroup,sceneOpacity('satellite'),$('satellite').checked);}
const telemetry={lodRevision:'visible-pixel-geometry-worker-r1',baseRoots:0,nativeRoots:0,nativeBytes:0,stagingBytes:0,partialRootDrawn:false,requests:0,cancellations:0,context:false,photo:false,ready:false,errors:[]};
const geometryGainWorker=new SourceGeometryGainWorker({onStats:state=>{telemetry.sourceGainCpuBytes=state.bytes;telemetry.sourceGainCpuPeak=Math.max(telemetry.sourceGainCpuPeak??0,state.bytes);if(state.phase==='cancelled')telemetry.sourceGainCancelled=(telemetry.sourceGainCancelled??0)+1;if(state.phase==='failed')telemetry.sourceGainErrors=(telemetry.sourceGainErrors??0)+1;}});
function message(text){$('message').textContent=text;}
function fail(error){lastError=String(error.message||error);telemetry.errors.push(lastError);message(lastError);console.error(error);}
function sourceResponseError(response,operation,source){
 const status=response.status,notice=status===409?'此处更细地景暂不可用':status===404?'此处暂无更细地景':status===422?'此处地景资源未通过校验':status===401||status===403?'暂时无法读取此处地景':'更细地景加载暂时失败';
 const detail={operation,source,status};telemetry.lastSourceResponse=detail;console.info('[source response] '+JSON.stringify(detail));
 const error=Error(notice+'，继续显示已有地景。');error.httpStatus=status;return error;
}
function preset(name){visibilityReady=false;
  const damping=controls.enableDamping;controls.enableDamping=false;controls.update();
  if(name==='overview'){camera.position.set(-4300,-5200,6700);controls.target.set(650,200,20);}
  else if(name==='oblique'){camera.position.set(-2100,-3400,1900);controls.target.set(650,-300,35);}
  else {const r=catalog?.root_records.find(r=>r.tile_id===141);const x=r?(r.bounds_min[0]+r.bounds_max[0])/2:-286.5,y=r?(r.bounds_min[1]+r.bounds_max[1])/2:-1965,z=r?r.bounds_min[2]:35;camera.position.set(x,y-80,z+100);controls.target.set(x,y,z+8);}
  controls.update();controls.enableDamping=damping;epoch++;lastStation=name;
}
function photograph(group){group.traverse(node=>{if(node.isMesh){const old=node.material;const map=old.map;if(map){map.anisotropy=sourcePageTextureIdentity(map)?.samplingContract?1:Math.min(16,renderer.capabilities.getMaxAnisotropy());map.needsUpdate=true;}node.material=new THREE.MeshBasicMaterial({map,side:THREE.DoubleSide,color:0xffffff});old.dispose();}});return group;}
async function loadModel(url,group,label,keepParser=false){
  const gltf=await loader.loadAsync(url,event=>{$('progress').textContent=`${label} ${event.total?Math.round(event.loaded/event.total*100)+'%':Math.round(event.loaded/1048576)+' MiB'}`;});
  const meshes=[];gltf.scene.traverse(n=>{if(n.isMesh)meshes.push(n);});photograph(gltf.scene);
  if(url.endsWith('/context/context_fused.gltf'))for(const mesh of meshes){const t=mesh.material.map;t.anisotropy=1;t.wrapS=t.wrapT=THREE.ClampToEdgeWrapping;t.flipY=false;t.colorSpace=THREE.SRGBColorSpace;t.needsUpdate=true;}
  for(const mesh of meshes){const geometryState={label,status:'waiting'},textureState={label,status:'waiting'};staticUploads.push(geometryState);staticTextureUploads.push(textureState);
   await runStaticUploadJobs([
    async stillWanted=>{geometryState.status='uploading';try{const result=await frameProfile.measureAsync('startup_geometry_wait',()=>uploadStaticGeometry({geometry:mesh.geometry,gl:renderer.getContext(),stillWanted,verify:verifyStaticGPU,onProgress:stats=>Object.assign(geometryState,stats)}));geometryState.status='ready';mesh.geometry.addEventListener('dispose',()=>{geometryState.status='disposed';});return {dispose(){result.dispose();geometryState.status='disposed';}};}catch(error){geometryState.status='failed';geometryState.error=error.message;throw error;}},
    async stillWanted=>{textureState.status='uploading';const verify=new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('textureQA')==='1';let legacyReference;try{if(verify&&url.endsWith('/context/context_fused.gltf'))legacyReference=await new THREE.TextureLoader().loadAsync('assets/showcase/runtime/zhumadian/context/context_colormatched.jpg');await uploadStaticTexture({texture:mesh.material.map,renderer,stillWanted,verify,referenceImage:legacyReference?.image??null,onProgress:stats=>Object.assign(textureState,stats)});textureState.status='ready';return {dispose(){mesh.material.map.dispose();textureState.status='disposed';}};}catch(error){textureState.status='failed';textureState.error=error.message;throw error;}finally{legacyReference?.dispose();}}
   ],{concurrency:staticUploadConcurrency});
  }group.add(gltf.scene);updateSceneOpacity();return keepParser?gltf:gltf.scene;
}
function openDocument(doc,name){
  cancelSignDrag();signOffsets.clear();signPrevious.clear();signLayoutKey='';signMetrics.clear();signPlacements.clear();signLayoutResult=null;signPreferenceKey='';validate(doc);layersDoc=structuredClone(doc);layerOpacities.clear();selected=null;selectedLayer=null;hitTargets=[];
  tintedCache.clear();imageCache.clear();$('feature-search').value='';$('feature-type').value='all';
  $('file-name').textContent=name;clearSelection(false);spatialNotice('');spatialFingerprint='';const current=layersDoc;
  spatialFingerprintPromise=documentFingerprint(current).then(value=>{if(current===layersDoc){spatialFingerprint=value;loadSignPreferences();rebuildLayerUI();}return value;});
  spatialFingerprintPromise.catch(error=>spatialNotice(error.message));rebuildLayerUI();
  message('图层已打开，点击画面中的标注查看信息');
}
function text(tag,content){const e=document.createElement(tag);e.textContent=content;return e;}
function topicMatch(f){return inTopic(f,activeTopic,activeCatalog())&&($('object-category').value==='all'||spatialObject(f,activeCatalog()).category===$('object-category').value);}
function matches(f,l){return topicMatch(f)&&matchesFeature(f,l,$('feature-search').value,$('feature-type').value,businessRecordSearchText(f.business,businessCatalog));}
function visibleFeature(f,l){return l.visible&&matches(f,l);}
function detailRows(rows){
  $('details').replaceChildren();
  for(const [label,value] of rows)$('details').append(text('dt',label),text('dd',String(value)));
}
function revealDetails(title){$('details-title').textContent=title;document.body.classList.add('details-open');}
function clearSelection(rebuild=true){
  selected=null;selectedLayer=null;viewport.dataset.selectedFeature='';viewport.dataset.selectionSource='';
  $('details-title').textContent='标注信息';detailRows([['选择标注查看详情','可点击三维画面中的图标、线或区域']]);
  document.body.classList.remove('details-open');if(rebuild)rebuildLayerUI();
}
function selectFeature(f,l,source='list',details=true){
  if(!visibleFeature(f,l))return;
  selected=f;selectedLayer=null;viewport.dataset.selectedFeature=f.id;viewport.dataset.selectionSource=source;
  rebuildLayerUI();if(details)showDetails(f,l);message(`已选中${featureTypeNames[f.type]}标注：${f.name}`);
}
function rebuildLayerUI(){
  if(!layersDoc)return;
  if(selected&&!layersDoc.layers.some(l=>l.features.includes(selected)&&visibleFeature(selected,l)))clearSelection(false);
  $('layers').replaceChildren();$('features').replaceChildren();
  let total=0,count=0;
  const filtering=activeTopic!=='all'||$('object-category').value!=='all'||$('feature-search').value.trim()||$('feature-type').value!=='all';
  for(const l of layersDoc.layers){
    total+=l.features.length;const matched=l.features.filter(f=>matches(f,l));count+=matched.length;
    if(filtering&&!matched.length)continue;
    const card=text('div','');card.className='layer'+(selectedLayer===l?' selected-layer':'');
    const row=text('div','');row.className='layer-title';
    const check=document.createElement('input');check.type='checkbox';check.checked=l.visible;
    check.setAttribute('aria-label',l.name+'显隐');
    check.onchange=()=>{l.visible=check.checked;if(selectedLayer===l&&!l.visible)clearSelection(false);rebuildLayerUI();};
    const name=text('button',l.name);name.className='layer-name';name.title='双击定位整层';
    name.onclick=()=>{selected=null;selectedLayer=l;viewport.dataset.selectedFeature='';viewport.dataset.selectionSource='';rebuildLayerUI();showLayerDetails(l);};
    name.ondblclick=()=>locateLayer(l);
    const locateButton=text('button','定位');locateButton.className='layer-locate';
    locateButton.setAttribute('aria-label','定位图层 '+l.name);locateButton.onclick=()=>locateLayer(l);
    row.append(check,name,locateButton);card.append(row,text('small',`${l.features.length} 个标注${filtering?' · 匹配 '+matched.length:''}${l.locked?' · 已锁定':''}`));
    const opacityControl=text('label','');opacityControl.className='opacity-control';
    const opacityLabel=text('span','透明度');const opacityOutput=text('output',`${Math.round((1-(layerOpacities.get(l.id)??1))*100)}%`);
    const opacityInput=document.createElement('input');opacityInput.type='range';opacityInput.min='0';opacityInput.max='100';opacityInput.step='1';
    opacityInput.value=String(Math.round((1-(layerOpacities.get(l.id)??1))*100));opacityInput.setAttribute('aria-label',l.name+'透明度');
    opacityInput.oninput=()=>{layerOpacities.set(l.id,opacityFromTransparency(opacityInput.value));opacityOutput.value=opacityInput.value+'%';
      if(selectedLayer===l)showLayerDetails(l);else if(selected&&l.features.includes(selected))showDetails(selected,l);refreshPortal();};
    opacityControl.append(opacityLabel,opacityInput,opacityOutput);card.append(opacityControl);$('layers').append(card);
    for(const f of matched){
      for(const parent of [card,$('features')]){
        const b=text('button',`${featureTypeNames[f.type]} · ${f.name}`);
        b.className='feature'+(parent===card?' compact-feature':'')+(selected===f?' selected':'');
        b.disabled=!l.visible;b.onclick=()=>selectFeature(f,l);b.ondblclick=()=>{selectFeature(f,l);locate();};parent.append(b);
      }
    }
  }
  $('filter-status').textContent=`匹配 ${count} / ${total} 个标注`;
  if(!count){$('features').append(text('p',total?'没有匹配的标注，请调整名称或类型筛选。':dataMode==='authenticated'?'当前尚无授权空间对象，请核对登录与访问范围。':'此文件暂无标注，可在编辑器中新建。'));}
  refreshBusinessSummary();refreshPortal();
}
function showDetails(f,l){
  revealDetails('标注信息');
  detailRows([['所属图层',l.name],['空间类别',categories[spatialObject(f,activeCatalog()).category]??'未分类'],['分类来源',spatialObject(f,activeCatalog()).registration],['专题归属',spatialObject(f,activeCatalog()).themes.map(t=>topics[t].name).join('、')||'全部图层'],['图层浏览透明度',`${Math.round((1-(layerOpacities.get(l.id)??1))*100)}%`],['名称',f.name],['类型',featureTypeNames[f.type]],...(dataMode==='authenticated'&&!businessCatalog?[['业务数据状态',apiBusinessState==='forbidden'?'当前账号无业务详情权限':'业务服务尚未配置台账来源']]:businessRecordRows(f.business,businessCatalog)),...businessDetailRows(f).filter(([key])=>key!=='业务数据状态'&&key!=='业务关联'),
    ['坐标点数',f.positions.length],['图标',f.style.icon],['线型 / 宽度',`${f.style.pattern} / ${f.style.widthPx} px`],
    ['原始颜色 / 不透明度',`${f.style.color} / ${Math.round(f.style.opacity*100)}%`],['原始填色 / 不透明度',`${f.style.fillColor} / ${Math.round(f.style.fillOpacity*100)}%`],
    ['文字标牌',f.label?.visible?(f.label.text||f.name):'隐藏']]);
  const list=text('ol','');for(const p of f.positions)list.append(text('li',p.map(v=>v.toFixed(3)).join(' / ')));
  $('details').append(text('dt','顶点 XYZ（局部米制）'),list);
}
function refreshBusinessSummary(){
  if(!businessCatalog){$('business-status').textContent=dataMode==='authenticated'?(apiBusinessState==='forbidden'?'当前账号无业务详情权限':'业务服务尚未配置台账来源'):'未加载业务台账';return;}
  const counts=businessCoverage(layersDoc?.layers,businessCatalog);
  $('business-status').textContent=`${businessCatalog.filename} · ${businessCatalog.byKey.size} 条记录；${counts.matched}/${counts.bound} 个关联匹配${counts.missing?'，缺失 '+counts.missing:''}${counts.conflicts?'，需核对 '+counts.conflicts:''}`;
}
function businessNotice(message){$('business-note').hidden=!message;$('business-note').textContent=message;}
function adoptBusinessRecords(document,filename){
  const next=parseBusinessRecords(document,filename);
  businessCatalog=next;businessNotice('');rebuildLayerUI();refreshBusinessSummary();
  if(selected){const layer=layersDoc.layers.find(l=>l.features.includes(selected));if(layer)showDetails(selected,layer);}
  message(`业务台账已加载：${filename} · ${next.byKey.size} 条记录（文件快照，非实时）`);
}
async function reloadBusinessRecords(quiet=false){
  if(dataMode!=='local')return;
  if(quiet&&(businessCatalog||userBusinessLoad))return;
  const generation=++businessLoadGeneration;
  try{const response=await fetch('business/default.json',{cache:'no-store'});if(generation!==businessLoadGeneration)return;
    if(response.status===404&&quiet)return;
    if(!response.ok)throw Error(response.status===404?'尚未发布业务台账，可用“打开业务台账”读取本机文件':'读取业务台账失败');
    const bytes=new Uint8Array(await response.arrayBuffer());if(generation!==businessLoadGeneration)return;
    if(bytes.length>8*1048576)throw Error('业务台账超过 8 MiB');
    adoptBusinessRecords(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)),'发布业务台账');
  }catch(error){if(generation===businessLoadGeneration)throw error;}
}
function showLayerDetails(l){
  revealDetails('图层信息');
  detailRows([['图层名称',l.name],['标注总数',l.features.length],['当前专题对象',l.features.filter(topicMatch).length],['点 / 线 / 区域',
    ['point','line','region'].map(type=>l.features.filter(f=>f.type===type).length).join(' / ')],['显示状态',l.visible?'显示':'隐藏'],['浏览透明度',`${Math.round((1-(layerOpacities.get(l.id)??1))*100)}%`]]);
}
function fitPositions(positions){
  const box=new THREE.Box3();for(const p of positions)box.expandByPoint(new THREE.Vector3(...p));
  if(box.isEmpty())return false;
  const sphere=box.getBoundingSphere(new THREE.Sphere());
  const halfVertical=THREE.MathUtils.degToRad(camera.getEffectiveFOV())/2;
  const halfHorizontal=Math.atan(Math.tan(halfVertical)*camera.aspect);
  const distance=Math.max(160,sphere.radius*1.18/Math.sin(Math.min(halfVertical,halfHorizontal)));
  const damping=controls.enableDamping;controls.enableDamping=false;controls.update();
  controls.maxDistance=Math.max(40000,distance*1.25);camera.far=Math.max(60000,distance+sphere.radius*2);
  camera.updateProjectionMatrix();controls.target.copy(sphere.center);
  camera.position.copy(sphere.center).add(new THREE.Vector3(0,-1,.85).normalize().multiplyScalar(distance));
  controls.update();controls.enableDamping=damping;camera.updateMatrixWorld();epoch++;return true;
}
function locate(){
  if(!selected){message('先选择一个标注');return;}
  fitPositions(labelFramingPositions(selected));message(`已定位标注：${selected.name}`);
}
function locateLayer(l){
  const scoped=l.features.filter(f=>inTopic(f,activeTopic,activeCatalog())&&($('object-category').value==='all'||spatialObject(f,activeCatalog()).category===$('object-category').value));
  if(!scoped.length){selected=null;selectedLayer=l;viewport.dataset.selectedFeature='';viewport.dataset.selectionSource='';rebuildLayerUI();showLayerDetails(l);message(`图层“${l.name}”当前专题暂无对象，视角保持原位`);return;}
  l.visible=true;selected=null;selectedLayer=l;viewport.dataset.selectedFeature='';viewport.dataset.selectionSource='';
  $('feature-search').value='';$('feature-type').value='all';rebuildLayerUI();showLayerDetails(l);
  fitPositions(scoped.flatMap(labelFramingPositions));message(`已定位图层：${l.name} · 当前专题 ${scoped.length} 个对象`);
}
function project(p){
  const world=new THREE.Vector3(...p),cameraSpace=world.clone().applyMatrix4(camera.matrixWorldInverse);
  if(cameraSpace.z>=-camera.near||cameraSpace.z < -camera.far)return null;
  world.project(camera);return [(world.x+1)*width/2,(1-world.y)*height/2];
}
function iconImage(key){if(imageCache.has(key))return imageCache.get(key);const image=new Image();image.onload=()=>{if(image.width>2048||image.height>2048){imageCache.delete(key);fail(Error('自定义图标超过 2048×2048'));}};image.src=key;imageCache.set(key,image);return image;}
const tintedCache=new Map();
function tintedIcon(style){
  if(!markerAtlas?.complete||!markerAtlas.naturalWidth)return null;
  const key=style.icon+style.color;if(tintedCache.has(key))return tintedCache.get(key);
  const canvas=document.createElement('canvas');canvas.width=canvas.height=64;const tc=canvas.getContext('2d');
  const index=['pin','circle','square','star','warning'].indexOf(style.icon);
  tc.drawImage(markerAtlas,index*64,0,64,64,0,0,64,64);tc.globalCompositeOperation='source-in';
  tc.fillStyle=style.color;tc.fillRect(0,0,64,64);tintedCache.set(key,canvas);return canvas;
}
function drawSelection(f,p,labelBox,opacity=1){
  if(f!==selected)return;
  ctx.save();ctx.globalAlpha=opacity;ctx.strokeStyle='#FFFFFF';ctx.lineWidth=2;
  ctx.shadowColor='#43D6E7';ctx.shadowBlur=6;ctx.setLineDash([5,4]);
  if(p.every(Boolean)&&(f.style.opacity>0||(f.type==='region'&&f.style.fillOpacity>0))){
    ctx.beginPath();
    if(f.type==='point')ctx.arc(p[0][0],p[0][1],f.style.sizePx/2+6,0,Math.PI*2);
    else {p.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));if(f.type==='region')ctx.closePath();}
    ctx.stroke();
  }
  if(labelBox)ctx.strokeRect(labelBox[0]-2,labelBox[1]-2,labelBox[2]-labelBox[0]+4,labelBox[3]-labelBox[1]+4);
  ctx.restore();
}
let hitTargets=[],selectedLayer=null;
function loadSignPreferences(){
 signPreferenceKey=dataMode==='local'&&spatialFingerprint?`landscape.sign-layout.v1:${spatialFingerprint}`:'';signOffsets.clear();signPrevious.clear();
 if(signPreferenceKey)try{signOffsets=readLabelOffsets(localStorage.getItem(signPreferenceKey));}catch{}
}
function saveSignPreferences(){if(signPreferenceKey)try{localStorage.setItem(signPreferenceKey,JSON.stringify([...signOffsets].slice(0,1000)));}catch{message('标牌位置已调整，本次浏览器无法保存布局');}}
function labelObstacles(){const parent=viewport.getBoundingClientRect(),result=[],panels=[...document.querySelectorAll('.layout>aside')].map(n=>n.getBoundingClientRect()).filter(r=>r.width&&r.height);
 const left=panels.filter(r=>r.left<parent.left+parent.width/2).reduce((v,r)=>Math.max(v,r.right-parent.left+12),12),right=panels.filter(r=>r.left>=parent.left+parent.width/2).reduce((v,r)=>Math.max(v,parent.right-r.left+12),12);
 $('sign-tools').style.left=`${left}px`;$('sign-tools').style.right=`${right}px`;
 for(const node of document.querySelectorAll('.layout>aside,#tools,#sign-tools,#message')){const r=node.getBoundingClientRect();if(r.width&&r.height&&getComputedStyle(node).visibility!=='hidden')result.push([r.left-parent.left-6,r.top-parent.top-6,r.right-parent.left+6,r.bottom-parent.top+6]);}return result;
}
function signMetric(feature,compact){const key=JSON.stringify([feature.name,feature.label.text,feature.label.fontPx,compact]);if(!signMetrics.has(key)){if(signMetrics.size>2000)signMetrics.clear();signMetrics.set(key,measureSign(ctx,feature,compact));}return signMetrics.get(key);}
const surfaceAnchors=new WeakMap();let surfaceCutKey='',surfaceFrontiers=[];
function prepareSignSurface(){
 const entries=$('photo').checked&&sceneOpacity('photo')>0?[...resident.values()].filter(r=>r.frontier):[];
 surfaceCutKey=entries.map(r=>r.group.uuid+':'+r.frontier.cutVersion).join('|');
 surfaceFrontiers=entries.map(r=>r.frontier);
}
function displayedPoint(f){
 if(f.type!=='point'||f.label?.placement!=='billboard')return null;
 let cached=surfaceAnchors.get(f);
 if(!cached||cached.key!==surfaceCutKey){const original=f.positions[0],height=sourceSurfaceHeight(surfaceFrontiers,original[0],original[1]);cached={key:surfaceCutKey,point:[original[0],original[1],height??original[2]]};surfaceAnchors.set(f,cached);}
 return cached.point;
}
function displayedAnchor(f){const point=displayedPoint(f);return point?new THREE.Vector3(...point):labelWorldAnchor(f);}
function drawAnnotations(){
  ctx.clearRect(0,0,width,height);hitTargets=[];if(!layersDoc)return;const records=[],signs=[];prepareSignSurface();
  for(const l of layersDoc.layers)if(l.visible)for(const f of l.features){
    const opacity=layerOpacities.get(l.id)??1;if(!matches(f,l)||opacity<=0)continue;
    const rendered=annotationWithOpacity(f,opacity),s=rendered.style,p=(displayedPoint(f)?[displayedPoint(f)]:f.positions).map(project);let legacyLabelBox=null;ctx.save();ctx.strokeStyle=s.color;ctx.fillStyle=s.fillColor;
    ctx.lineWidth=s.widthPx;ctx.setLineDash(s.pattern==='dash'?[12,8]:s.pattern==='dot'?[2,6]:[]);ctx.globalAlpha=s.opacity;
    if(f.type==='point'&&p[0]){
      const [x,y]=markerScreenPoint(p[0],s),size=s.sizePx;ctx.setLineDash([]);
      const signFoot=f.label?.placement==='billboard';
      const image=signFoot?null:s.icon==='custom'?iconImage(s.iconData):tintedIcon(s);
      if(signFoot){ctx.beginPath();ctx.fillStyle=s.color;ctx.arc(p[0][0],p[0][1],3,0,Math.PI*2);ctx.fill();}
      else if(image&&(s.icon!=='custom'||image.complete&&image.naturalWidth))ctx.drawImage(image,x-size/2,y-size/2,size,size);
      ctx.globalAlpha=f.label?0:s.opacity;ctx.fillStyle='#f1f6fa';ctx.font='12px "Microsoft YaHei",sans-serif';
      ctx.shadowColor='#061521';ctx.shadowBlur=4;ctx.fillText(f.name,x+size*.6,y+4);
      if(!f.label&&s.opacity>0&&f.name)legacyLabelBox=[x+size*.6,y-12,x+size*.6+ctx.measureText(f.name).width,y+5];
    }else if(p.every(Boolean)){
      ctx.beginPath();p.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));
      if(f.type==='region'){ctx.closePath();ctx.globalAlpha=s.fillOpacity;ctx.fill();}
      ctx.globalAlpha=s.opacity;ctx.stroke();
    }
    ctx.restore();const billboard=rendered.label?.visible&&rendered.label.opacity>0&&rendered.label.placement==='billboard',anchor=billboard?project(displayedAnchor(f).toArray()):null;
    const record={f,l,rendered,s,p,opacity,legacyLabelBox,billboard};records.push(record);
    if(anchor&&anchor[0]>=0&&anchor[0]<=width&&anchor[1]>=0&&anchor[1]<=height)signs.push({id:f.id,anchor,full:signMetric(rendered,false),compact:signMetric(rendered,true),manual:signOffsets.get(f.id),offset:f.label.offset,selected:f===selected});
  }
  const obstacles=labelObstacles(),avoid=$('sign-avoid').checked,dragging=signDrag?.moved?signDrag.feature.id:null;
  const preferCompact=document.body.classList.contains('command-view');
  const key=JSON.stringify([width,height,obstacles,avoid,dragging,preferCompact,signs.map(i=>[i.id,i.anchor.map(v=>Math.round(v*2)/2),i.manual,i.offset,i.selected,i.full,i.compact])]);
  if(key!==signLayoutKey){signLayoutKey=key;signLayoutResult=layoutLabels(signs,{width,height,obstacles,previous:signPrevious,avoid,dragging,preferCompact});}
  const layout=signLayoutResult;
  signPlacements=layout.placements;signPrevious=signPlacements;
  viewport.dataset.signSurface=JSON.stringify(records.filter(r=>r.f.type==='point'&&r.billboard).map(r=>({id:r.f.id,source:r.f.positions[0],displayed:displayedPoint(r.f)})));
  viewport.dataset.signCount=String(signPlacements.size);viewport.dataset.signOmitted=String(layout.omitted);viewport.dataset.signCompact=String(layout.compact);
  $('sign-status').textContent=layout.omitted?`${layout.omitted} 块牌面暂被收起，请缩放或筛选图层`:layout.compact?'密集视图 · 点选展开详情':'拖动牌面调整位置 · 不改变点位';
  // Paint ordinary labels first; selected/manual cards are painted last and get matching picking order.
  records.sort((a,b)=>Number(!!signOffsets.get(a.f.id))-Number(!!signOffsets.get(b.f.id))||Number(a.f===selected)-Number(b.f===selected));
  for(const {f,rendered,p,opacity,billboard} of records)if(billboard){if(f.type!=='point')drawSelection(f,p,null,opacity);const placement=signPlacements.get(f.id);if(placement)drawSignLeader(ctx,rendered,placement.anchor,placement);}
  for(const {f,l,rendered,s,p,opacity,legacyLabelBox,billboard} of records){const placement=signPlacements.get(f.id);
    const labelBox=billboard?(placement?drawSign(ctx,rendered,placement.anchor,placement,{selected:f===selected,manual:signOffsets.has(f.id),leader:false}):null):drawLabel(ctx,rendered,project)||legacyLabelBox;
    if(!billboard)drawSelection(f,p,labelBox,opacity);
    const target=buildHitTarget(signFootFeature(rendered),l,f.type==='point'?[f.label?.placement==='billboard'?p[0]:markerScreenPoint(p[0],s)]:p,labelBox);if(target){target.feature=f;hitTargets.push(target);}
  }
}

const gesture=new ClickGesture(),canvas=renderer.domElement;
canvas.tabIndex=0;canvas.setAttribute('aria-label','驻马店三维场景');canvas.dataset.scene='zhumadian';
function eventPoint(event){const r=canvas.getBoundingClientRect();return [event.clientX-r.left,event.clientY-r.top];}
function cardAt(point){const target=pickAnnotation(hitTargets,point),b=target?.labelBox;return b&&target.feature.label?.placement==='billboard'&&point[0]>=b[0]&&point[0]<=b[2]&&point[1]>=b[1]&&point[1]<=b[3]?target:null;}
function cancelSignDrag(){if(!signDrag)return;const d=signDrag;signDrag=null;if(d.before)signOffsets.set(d.feature.id,d.before);else signOffsets.delete(d.feature.id);controls.enabled=d.controlsEnabled;try{canvas.releasePointerCapture(d.id);}catch{}canvas.style.cursor='';}
canvas.addEventListener('pointerdown',event=>{
 if(signDrag){if(event.pointerId!==signDrag.id)cancelSignDrag();return;}
 const target=event.button===0&&event.isPrimary&&event.pointerType!=='touch'?cardAt(eventPoint(event)):null;
 if(target){const placement=signPlacements.get(target.feature.id);if(!placement)return;
  signDrag={id:event.pointerId,feature:target.feature,layer:target.layer,start:eventPoint(event),box:[...placement.box],anchor:[...placement.anchor],before:signOffsets.get(target.feature.id),controlsEnabled:controls.enabled,moved:false};
  canvas.setPointerCapture(event.pointerId);event.preventDefault();event.stopImmediatePropagation();
 }else gesture.begin(event);
},true);
canvas.addEventListener('pointermove',event=>{
 if(signDrag?.id===event.pointerId){const p=eventPoint(event),d=signDrag,dx=p[0]-d.start[0],dy=p[1]-d.start[1];
  if(Math.hypot(dx,dy)>5)d.moved=true;
  if(d.moved){controls.enabled=false;signOffsets.set(d.feature.id,[d.box[0]+dx-d.anchor[0],d.box[1]+dy-d.anchor[1]]);canvas.style.cursor='grabbing';}
  event.preventDefault();event.stopImmediatePropagation();return;
 }
 gesture.move(event);if(!event.buttons)canvas.style.cursor=cardAt(eventPoint(event))?'grab':pickAnnotation(hitTargets,eventPoint(event))?'pointer':'';
},true);
canvas.addEventListener('pointercancel',event=>{if(signDrag?.id===event.pointerId)cancelSignDrag();gesture.cancel(event);},true);
canvas.addEventListener('pointerup',event=>{
 if(signDrag?.id===event.pointerId){const d=signDrag;signDrag=null;controls.enabled=d.controlsEnabled;try{canvas.releasePointerCapture(d.id);}catch{}
  if(d.moved){saveSignPreferences();selectFeature(d.feature,d.layer,'sign-drag',false);message('标牌位置已调整，企业地面坐标保持不变');}else selectFeature(d.feature,d.layer,'scene');
  canvas.style.cursor='grab';event.preventDefault();event.stopImmediatePropagation();return;
 }
 if(!gesture.end(event))return;camera.updateMatrixWorld();drawAnnotations();const target=pickAnnotation(hitTargets,eventPoint(event));
 if(target)selectFeature(target.feature,target.layer,'scene');else clearSelection();
},true);
canvas.addEventListener('lostpointercapture',event=>{if(signDrag?.id===event.pointerId)cancelSignDrag();});
canvas.addEventListener('dblclick',event=>{if(event.button!==0)return;const target=pickAnnotation(hitTargets,eventPoint(event));if(target){selectFeature(target.feature,target.layer,'scene');locate();}});
window.addEventListener('blur',()=>{gesture.cancel();cancelSignDrag();});
document.addEventListener('keydown',event=>{if(event.key==='Escape'){if(signDrag){cancelSignDrag();message('已取消本次标牌拖拽');}else clearSelection();}});
$('sign-reset').onclick=()=>{cancelSignDrag();signOffsets.clear();signPrevious.clear();signLayoutKey='';saveSignPreferences();message('已恢复标牌自动布局，企业点位未改变');};
$('command-panels').onclick=()=>{const collapsed=document.body.classList.toggle('command-panels-collapsed');$('command-panels').textContent=collapsed?'展开仪表盘':'收起仪表盘';$('command-panels').setAttribute('aria-pressed',String(collapsed));signPrevious.clear();signLayoutKey='';};
$('sign-avoid').onchange=()=>{signPrevious.clear();signLayoutKey='';};
for(const id of ['feature-search','feature-type','object-category'])$(id).addEventListener(id==='feature-search'?'input':'change',()=>rebuildLayerUI());
$('reset-filter').onclick=()=>{$('feature-search').value='';$('feature-type').value='all';$('object-category').value='all';rebuildLayerUI();};
$('details-close').onclick=()=>document.body.classList.remove('details-open');
$('business-file').onchange=async event=>{if(dataMode!=='local')return;
  const generation=++businessLoadGeneration;
  try{const file=event.target.files[0];if(!file)return;userBusinessLoad=true;if(file.size>8*1048576)throw Error('业务台账超过 8 MiB');
    const bytes=await file.arrayBuffer();const document=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));if(generation===businessLoadGeneration)adoptBusinessRecords(document,file.name);
  }catch(error){if(generation===businessLoadGeneration)businessNotice(`导入失败，保留当前台账：${error.message}`);}finally{event.target.value='';}
};
$('business-reload').onclick=()=>{userBusinessLoad=true;reloadBusinessRecords().catch(error=>businessNotice(`${error.message}；保留当前台账`));};
$('business-clear').onclick=()=>{userBusinessLoad=true;businessLoadGeneration++;businessCatalog=null;businessNotice('');rebuildLayerUI();refreshBusinessSummary();if(selected){const l=layersDoc.layers.find(l=>l.features.includes(selected));if(l)showDetails(selected,l);}message('业务台账已清除，空间标注及关联编号保留');};
$('business-template').onclick=()=>{
  const preview=$('business-template-preview');preview.hidden=!preview.hidden;
  $('business-template').textContent=preview.hidden?'查看空模板':'收起模板';
  if(!preview.hidden){preview.value=JSON.stringify({schema:'xnby.business.records.v1',scene:'zhumadian',exportedAt:new Date().toISOString(),ttlHours:24,records:[]},null,2);preview.focus();preview.select();}

};

function spatialNotice(value){$('spatial-note').hidden=!value;$('spatial-note').textContent=value;}
function refreshEmergencyResources(){
  const mapping={'hud-material-depot':'emergency-store','hud-rescue-team':'emergency-team','hud-medical':'medical','hud-expert':'emergency-expert','hud-shelter':'shelter','hud-fire':'firefighting'};
  const objects=(layersDoc?.layers??[]).flatMap(l=>l.features).map(f=>spatialObject(f,activeCatalog()));
  for(const [id,category] of Object.entries(mapping))$(id).textContent=layersDoc?objects.filter(o=>o.category===category).length:'—';
}
function refreshPortal(){
  refreshEmergencyResources();const command=activeTopic==='emergency',wasCommand=document.body.classList.contains('command-view');document.body.classList.toggle('command-view',command);if(command!==wasCommand)$('layer-settings').open=!command;document.querySelector('header>strong').textContent=command?'驻马店 · 敏捷应急指挥':'驻马店重大风险防控';updateCommandDashboard(layersDoc);
  const counts=topicCounts(layersDoc?.layers,activeCatalog());
  for(const button of $('topic-nav').querySelectorAll('button')){const key=button.dataset.topic;button.setAttribute('aria-pressed',String(activeTopic===key));button.querySelector('small').textContent=counts[key];}
  $('topic-title').textContent=topics[activeTopic]?.name??'全部图层';$('topic-description').textContent=activeTopic==='emergency'?'企业分布作为场景参照，叠加危险源、消防和应急资源':topics[activeTopic]?.description??(dataMode==='authenticated'?'浏览当前账号获准访问的空间对象和业务详情':'浏览编辑器保存的全部点线面与图层');
  const objects=scopedObjects(layersDoc?.layers,activeTopic,$('object-category').value,activeCatalog());
  const shown=objects.filter(({feature,layer})=>visibleFeature(feature,layer)&&(layerOpacities.get(layer.id)??1)>0).length;
  const bound=objects.filter(({feature})=>feature.business).length;
  const registered=objects.filter(({feature})=>spatialObject(feature,activeCatalog()).category!=='unregistered').length;
  $('scope-count').textContent=objects.length;$('shown-count').textContent=shown;$('bound-count').textContent=bound;$('classified-count').textContent=registered;
  $('portal-empty').hidden=objects.length>0||!layersDoc;$('portal-empty').textContent=activeTopic==='all'?'当前分类没有空间对象。':'此专题尚无匹配的空间对象，可打开空间对象目录或切回全部图层。';
  if(!spatialCatalog)$('spatial-status').textContent='未加载目录 · 使用已有业务关联分类';
  else if(!spatialFingerprint)$('spatial-status').textContent='正在核对图层与目录';
  else if(!activeCatalog())$('spatial-status').textContent='目录与当前图层不匹配，目录分类未应用';
  else $('spatial-status').textContent=`${spatialCatalog.filename} · ${spatialCatalog.byId.size} 条登记 · ${catalogOrphans(layersDoc.layers,spatialCatalog).length} 条编号不在当前图层`;
  $('spatial-template').disabled=!spatialFingerprint;
}
function switchTopic(key){activeTopic=key;$('feature-search').value='';$('feature-type').value='all';$('object-category').value='all';clearSelection(false);rebuildLayerUI();refreshPortal();message(`已切换：${topics[key]?.name??'全部图层'}`);}
for(const [key,definition] of [['all',{name:'全部图层'}],...Object.entries(topics)]){
  const button=text('button','');button.dataset.topic=key;button.append(text('span',definition.name),text('small','0'));button.onclick=()=>switchTopic(key);$('topic-nav').append(button);
}
for(const [key,name] of [['all','全部空间类别'],['unregistered','未分类标注'],...Object.entries(categories)]){
  const option=text('option',name);option.value=key;$('object-category').append(option);
}
const portalQuery=new URLSearchParams(location.search);
if(Object.hasOwn(topics,portalQuery.get('topic')))activeTopic=portalQuery.get('topic');
if(Object.hasOwn(categories,portalQuery.get('category')))$('object-category').value=portalQuery.get('category');
const portalSpatial=portalQuery.get('spatial');if(portalSpatial&&new TextEncoder().encode(portalSpatial).length<=256&&!/[\x00-\x1f\x7f]/.test(portalSpatial))$('feature-search').value=portalSpatial;
async function adoptSpatial(document,filename,generation){
  const next=parseSpatialCatalog(document,filename),current=layersDoc;if(!current)throw Error('请先打开图层文件');
  const fingerprint=await spatialFingerprintPromise;if(generation!==spatialLoadGeneration)return;
  if(current!==layersDoc)throw Error('图层已切换，请重新读取目录');
  if(next.layerFingerprint!==fingerprint)throw Error('目录与当前图层校验码不匹配，保留原目录');
  spatialCatalog=next;spatialNotice('');rebuildLayerUI();if(selected){const l=layersDoc.layers.find(l=>l.features.includes(selected));if(l)showDetails(selected,l);}message(`空间对象目录已加载：${filename}`);
}
$('spatial-file').onchange=async event=>{if(dataMode!=='local')return;const generation=++spatialLoadGeneration;try{const file=event.target.files[0];if(!file)return;userSpatialLoad=true;if(file.size>4*1048576)throw Error('空间目录超过4 MiB');await adoptSpatial(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(await file.arrayBuffer())),file.name,generation);}catch(error){if(generation===spatialLoadGeneration)spatialNotice(error.message);}finally{event.target.value='';}};
async function reloadSpatial(quiet=false){if(dataMode!=='local')return;if(quiet&&(spatialCatalog||userSpatialLoad))return;const generation=++spatialLoadGeneration;try{const response=await fetch('spatial/default.json',{cache:'no-store'});if(generation!==spatialLoadGeneration||quiet&&response.status===404)return;if(!response.ok)throw Error(response.status===404?'尚未发布空间对象目录':'读取空间对象目录失败');const raw=await response.arrayBuffer();if(generation!==spatialLoadGeneration)return;if(raw.byteLength>4*1048576)throw Error('空间目录超过4 MiB');await adoptSpatial(JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)),'发布空间对象目录',generation);}catch(error){if(generation===spatialLoadGeneration)throw error;}}
$('spatial-reload').onclick=()=>{userSpatialLoad=true;reloadSpatial().catch(error=>spatialNotice(error.message));};
$('spatial-clear').onclick=()=>{userSpatialLoad=true;spatialLoadGeneration++;spatialCatalog=null;spatialNotice('');rebuildLayerUI();if(selected){const l=layersDoc.layers.find(l=>l.features.includes(selected));if(l)showDetails(selected,l);}message('空间目录已清除，编辑器图层和业务关联保留');};
$('spatial-template').onclick=()=>{const preview=$('spatial-template-preview');preview.hidden=!preview.hidden;if(!preview.hidden){preview.value=JSON.stringify({schema:'xnby.spatial.catalog.v1',scene:'zhumadian',layerFingerprint:spatialFingerprint,exportedAt:new Date().toISOString(),objects:[]},null,2);preview.focus();preview.select();}};
refreshPortal();

function disposeGroup(group){const materials=new Set(),textures=new Set();group.traverse(n=>{if(n.isMesh){n.geometry.dispose();for(const m of Array.isArray(n.material)?n.material:[n.material]){materials.add(m);if(m.map)textures.add(m.map);}}});for(const texture of textures){texture.dispose();texture.source.data?.close?.();}for(const material of materials)material.dispose();}
function baseRanges(){if(!base||!catalog)return;const removed=[...resident.keys()].flatMap(id=>catalog.root_records.find(r=>r.tile_id===id).base_spans).sort((a,b)=>a[0]-b[0]);const geometry=base.geometry;geometry.clearGroups();let first=0;for(const [offset,count] of removed){if(offset>first)geometry.addGroup(first,offset-first,0);first=offset+count;}if(first<geometry.index.count)geometry.addGroup(first,geometry.index.count-first,0);base.material=[base.userData.photoMaterial];}
function visiblePriority(root,node,names=null){return sourceVisibility.priority(root,node,camera,height,names);}
function ranking(){if(!catalog||!baseEdges.size||!$('fine').checked||!$('photo').checked||sceneOpacity('photo')<=0)return[];camera.updateMatrixWorld();const frustum=new THREE.Frustum().setFromProjectionMatrix(new THREE.Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));const desired=[];const scale=height/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov)/2));
  const rootRecords=sourceLevelIndex?(()=>{const result=sourceLevelIndex.index.query(frustum.planes.map(p=>[p.normal.x,p.normal.y,p.normal.z,p.constant]));telemetry.levelIndexQuery=result.stats;return result.records.map(r=>({...catalog.root_records[r.tile-1],bounds_min:r.boundsMin,bounds_max:r.boundsMax,indexed:r}));})():catalog.root_records;
  for(const r of rootRecords){const box=new THREE.Box3(new THREE.Vector3(...r.bounds_min),new THREE.Vector3(...r.bounds_max));if(!frustum.intersectsBox(box))continue;const distance=Math.max(1,box.distanceToPoint(camera.position));const pixels=box.getSize(new THREE.Vector3()).length()*scale/distance;
    const prior=resident.get(r.tile_id),basePixels=baseEdges.get(r.tile_id)*scale/distance,edgePixels=(prior?.marker.longest_edge_p90_m??baseEdges.get(r.tile_id))*scale/distance;
    const parentPixels=(tierEdges.get(`${r.tile_id}/${(prior?.depth??0)-1}`)??0)*scale/distance;
    let depth=selectDepth(pixels,basePixels,edgePixels,prior?.depth??0,r.max_depth,parentPixels,(baseTexels.get(r.tile_id)??0)*scale/distance,(prior?.marker.texel_world_p90_m??baseTexels.get(r.tile_id)??0)*scale/distance,(tierTexels.get(`${r.tile_id}/${(prior?.depth??0)-1}`)??0)*scale/distance);if(prior?.frontier&&depth>=prior.depth)depth=prior.depth;if(indexedCutsRequested&&!prior&&depth>0)depth=initialIndexedCoverageDepth(r.indexed,depth,scale,distance);if(!depth)continue;
    const center=box.getCenter(new THREE.Vector3()).project(camera),coverage=Math.min(2,pixels/height)**2/(1+Math.hypot(center.x,center.y));
    desired.push({id:r.tile_id,depth,pixels,edgePixels,basePixels,distance,focusDistance:box.distanceToPoint(controls.target),score:coverage/Math.sqrt(Math.max(distance,40)),viewScore:sourceRefinementScore(Math.max(basePixels,(baseTexels.get(r.tile_id)??0)*scale/distance),pixels,height,Math.hypot(center.x,center.y))});}
  desired.sort((a,b)=>b.score-a.score);
  const forward=controls.target.clone().sub(camera.position).normalize();
  const centerScore=item=>{const record=catalog.root_records[item.id-1],delta=new THREE.Vector3(...record.bounds_min).add(new THREE.Vector3(...record.bounds_max)).multiplyScalar(.5).sub(camera.position),along=delta.dot(forward);return along>0?[Math.floor(Math.max(0,delta.lengthSq()/(along*along)-1)*100000),delta.length()]:[1e12,delta.length()];};
  const focus=pickFocusRoot(desired,catalog,base.geometry.attributes.position.array,base.geometry.index.array,new THREE.Ray(camera.position.clone(),forward))??[...desired].sort((a,b)=>{const x=centerScore(a),y=centerScore(b);return x[0]-y[0]||x[1]-y[1];})[0];
  if(focus){desired.splice(desired.indexOf(focus),1);desired.unshift(focus);}const result=sourceLevelIndex?desired:desired.slice(0,residentLimit);
  const nextFocus=result[0]?.id??0;if(nextFocus!==focusId){focusId=nextFocus;failed.clear();familyFailed.clear();}
  return result;}
function maintain(){const restorations=[],ranked=ranking();if(indexedCutsRequested){const view=JSON.stringify(indexedSourceView());if(telemetry.indexedView!==view){familyCosts.clear();coverageRejected.clear();telemetry.indexedView=view;}}const wanted=new Set(ranked.map(r=>r.id));for(const [id,r] of resident)if(!wanted.has(id)){photoGroup.remove(r.group);disposeGroup(r.group);resident.delete(id);}baseRanges();telemetry.nativeDesired=ranked.length;telemetry.nativeRoots=resident.size;telemetry.nativeBytes=[...resident.values()].reduce((sum,r)=>sum+r.bytes,0);
  for(const key of failed)if(!wanted.has(Number(key.split('/')[0])))failed.delete(key);
  for(const r of ranked){const ready=resident.get(r.id);if(!ready?.frontier)continue;
    const restore=rollbackWebFamilies(ready);if(restore)restorations.push({id:r.id,ready,parent:restore});
  }
  telemetry.nativeBytes=[...resident.values()].reduce((sum,r)=>sum+r.bytes,0);telemetry.pageBudget=pageBudget.snapshot();
  if(new URLSearchParams(location.search).get('lodDebug')==='1'){const stats={sourcePlanCache:sourcePlanCache.snapshot(),indexedFamilyCommits:telemetry.indexedFamilyCommits??0,indexedQualityLimits:telemetry.indexedQualityLimits??0,coverageReferenceChecks:coverageGuard.referenceChecks,coverageReferenceMismatches:coverageGuard.referenceMismatches,coverageRegionPixels:telemetry.coverageRegionPixels??0,coverageFullPixels:telemetry.coverageFullPixels??0,coverageChecks:telemetry.coverageChecks??0,coverageRejections:telemetry.coverageRejections??0,lastCoverage:telemetry.lastCoverage??null,coverageTargetBytes:coverageGuard.bytes,levelIndexMode:telemetry.levelIndexMode,sourceGainCancelReason:telemetry.sourceGainCancelReason??null,sourceGainJobs:telemetry.sourceGainJobs??0,sourceGainErrors:telemetry.sourceGainErrors??0,sourceGainCancelled:telemetry.sourceGainCancelled??0,sourceGainCpuBytes:telemetry.sourceGainCpuBytes??0,sourceGainCpuPeak:telemetry.sourceGainCpuPeak??0,sourceGainWorkerMs:telemetry.sourceGainWorkerMs??0,recoverySequencePlans:telemetry.recoverySequencePlans??0,recoverySequenceSteps:telemetry.recoverySequenceSteps??0,recoverySequencePeak:telemetry.recoverySequencePeak??0,lastGainEstimate:telemetry.lastGainEstimate??null,pageBudget:telemetry.pageBudget,preparedBc7Pages:telemetry.preparedBc7Pages??0,preparedReplans:telemetry.preparedReplans??0,preparedTextureCount:telemetry.preparedTextureCount??0,lodRevision:telemetry.lodRevision,width,height,camera:camera.position.toArray(),target:controls.target.toArray(),visibility:telemetry.visibility,requests:telemetry.requests,familyRequests:telemetry.familyRequests??0,cancellations:telemetry.cancellations,familyCommits:telemetry.familyCommits??0,retiredCpuPages:telemetry.retiredCpuPages??0,retiredCpuPayloadBytes:telemetry.retiredCpuPayloadBytes??0,restoredCpuPages:telemetry.restoredCpuPages??0,restoreRequests:telemetry.restoreRequests??0,restoreErrors:telemetry.restoreErrors??0,cpuRestoreStagingPayloadBytes:telemetry.cpuRestoreStagingPayloadBytes??0,peakBytes:telemetry.peakBytes??0,activeBytes:telemetry.nativeBytes,stagingBytes:telemetry.stagingBytes,retainedPayloadBytes:[...resident.values()].reduce((sum,r)=>sum+(r.frontier?.retainedPayloadBytes??r.bytes),0),textures:renderer.info.memory.textures,geometries:renderer.info.memory.geometries,roots:[...resident].map(([id,r])=>({id,screenWeight:sourceVisibility.weight(id)+[...r.frontier.visible].reduce((sum,name)=>sum+sourceVisibility.weight(id,name),0),depth:r.frontier?.maxDepth??r.depth,bytes:r.bytes,visible:r.frontier?[...r.frontier.visible]:[]}))};const signature=JSON.stringify(stats);if(signature!==telemetry.lastAudit){console.info('[LOD audit] '+signature);telemetry.lastAudit=signature;}}
  if(pending||!base)return;
  if(indexedCutsRequested){if(ranked.length){try{const required=coverageDimensions(width,height);if(pageBudget.held-coverageGuard.bytes+required.bytes>budget){rebalanceSourceViewport().catch(fail);return;}coverageGuard.resize(width,height);detailLimit=budget-uploadTargetBytes-coverageGuard.bytes;telemetry.coverageUnavailable=null;}catch(error){telemetry.coverageUnavailable=error.message;return;}}else{coverageGuard.release();detailLimit=budget-uploadTargetBytes;}}
  if(restorations.length){loadSourceCoarsen(restorations[0]).catch(fail);return;}
  if(!ranked.length){visibilityReady=false;return;}
  try{const obscured=sourceOcclusionRects();const visibilityStart=performance.now();const signature=JSON.stringify({width,height,obscured,photo:sceneOpacity('photo'),terrain:sceneOpacity('satellite'),terrainVisible:$('satellite').checked,cut:sourceRecoverySnapshot(resident)});
    if(signature!==telemetry.visibilitySignature||!matchesVisibilityCamera(sourceVisibility.visibleSnapshot,camera,width,height)){telemetry.visibility=sourceVisibility.sample({camera,width,height,base,catalog,residents:resident,obscured,balancedRegions,baseQuality:{edges:baseEdges,texels:baseTexels}});telemetry.visibility.milliseconds=performance.now()-visibilityStart;telemetry.visibilitySignature=signature;telemetry.visibilityCut=sourceRecoverySnapshot(resident);rootGainEstimates.clear();familyGainEstimates.clear();coverageRejected.clear();}visibilityReady=true;}catch(error){visibilityReady=false;console.info('[visibility] '+error.message);}
  if(visibilityReady)for(const r of ranked){const bounds=catalog.root_records[r.id-1];r.viewScore=rootGainEstimates.get(`${r.id}/${r.depth}`)??visiblePriority(r.id,{...bounds,longest_edge_p90_m:baseEdges.get(r.id),texel_world_p90_m:baseTexels.get(r.id)??0});}
  if(visibilityReady){if(indexedCutsRequested){startAllocationScan(ranked);return;}const chosen=chooseSourceCandidate(allocationCandidates(ranked));if(chosen){telemetry.allocationChoice={key:chosen.key,gain:chosen.score,bytes:chosen.cost};(chosen.kind==='family'?loadWebFamily({id:chosen.id,parent:chosen.node.name,ready:chosen.ready,score:chosen.score}):loadFine(chosen.request)).catch(fail);}return;}
  const local=wantedWebFamily(),seed=ranked.filter(r=>r.viewScore>0&&!resident.has(r.id)&&!failed.has(`${r.id}/${r.depth}`)&&(!rootCosts.has(`${r.id}/${r.depth}`)||canMakeFamilyRoom(r.id,null,r.viewScore,rootCosts.get(`${r.id}/${r.depth}`),false))).sort((a,b)=>b.viewScore-a.viewScore)[0];
  if(local&&(!seed||local.score>=seed.viewScore)){loadWebFamily({id:local.id,parent:local.node.name,ready:local.ready,score:local.score}).catch(fail);return;}
  if(seed){loadFine(seed).catch(fail);return;}
  ranked.splice(0,ranked.length,...prioritizeDetail(ranked,resident,focusId));
  for(const r of ranked){if(resident.get(r.id)?.depth===r.depth||visibilityReady&&!r.viewScore)continue;const key=`${r.id}/${r.depth}`;if(failed.has(key)||rootCosts.has(key)&&!canMakeFamilyRoom(r.id,null,r.viewScore,rootCosts.get(key),false))continue;loadFine(r).catch(fail);break;}}
const failed=new Set(),rootCosts=new Map(),rootGainEstimates=new Map(),familyGainEstimates=new Map();
function sourceGainContext({id,names,stillWanted}){
 if(!sourceVisibility.visibleSnapshot)throw new SourceGainUnavailable('可见像素尚未就绪，保留当前地景');
 camera.updateMatrixWorld();if(!matchesVisibilityCamera(sourceVisibility.visibleSnapshot,camera,width,height)||telemetry.visibilityCut!==sourceRecoverySnapshot(resident)){telemetry.sourceGainCancelReason={root:id,phase:'capture',camera:matchesVisibilityCamera(sourceVisibility.visibleSnapshot,camera,width,height),cut:telemetry.visibilityCut===sourceRecoverySnapshot(resident),worldDelta:Math.max(...sourceVisibility.visibleSnapshot.cameraWorld.map((n,i)=>Math.abs(n-camera.matrixWorld.elements[i]))),dimensions:[sourceVisibility.visibleSnapshot.width,sourceVisibility.visibleSnapshot.height,width,height]};throw new SourceLoadCancelled();}
 const snapshot=sourceVisibility.capture(id,names,camera,height),cut=sourceRecoverySnapshot(resident),version=epoch;
 const isCurrent=()=>{camera.updateMatrixWorld();const wanted=stillWanted(),sameCamera=matchesVisibilityCamera(snapshot,camera,width,height),sameCut=cut===sourceRecoverySnapshot(resident),valid=version===epoch&&wanted&&sameCamera&&sameCut;if(!valid)telemetry.sourceGainCancelReason={root:id,phase:'compute',epoch:version===epoch,wanted,camera:sameCamera,cut:sameCut,worldDelta:Math.max(...snapshot.cameraWorld.map((n,i)=>Math.abs(n-camera.matrixWorld.elements[i])))};return valid;};
 return {snapshot,isCurrent};
}
async function measureSourceGain({id,names,marker,downloads,folder,stillWanted}){
 const {snapshot,isCurrent}=sourceGainContext({id,names,stillWanted});
 const result=await geometryGainWorker.measure({marker,snapshot,loadFile:(part,name)=>downloads.read(`native/${folder}/${part.directory}/${name}`),isCurrent});
 ensureSourceWanted(isCurrent);if(result.memoHit)telemetry.sourceGainMemoHits=(telemetry.sourceGainMemoHits??0)+1;else telemetry.sourceGainJobs=(telemetry.sourceGainJobs??0)+1;telemetry.sourceGainWorkerMs=Math.max(telemetry.sourceGainWorkerMs??0,result.milliseconds);
 telemetry.lastGainEstimate={root:id,samples:result.samples,hits:result.hits,missing:result.missing,parentDeficit:result.beforeDeficit,childResidual:result.afterDeficit,gain:result.gain,model:result.model,memoHit:result.memoHit,milliseconds:result.milliseconds};
 console.info('[source gain] '+JSON.stringify(telemetry.lastGainEstimate));return result.gain;
}
function indexedSourceView(){return [...camera.position.toArray(),...controls.target.toArray(),camera.fov,camera.aspect,height,6].map(n=>Number(n.toPrecision(12)));}
async function prepareSourceAllocation({id,depth,parent,names,costs,key,choice,stillWanted}){
 if(!sourcePlansEnabled)return null;
 const topology=indexedCutsRequested?await sourceLevelIndex.tile(id):null;ensureSourceWanted(stillWanted);
 const context=indexedCutsRequested&&parent!==undefined?sourceGainContext({id,names,stillWanted}):null;
 const request=parent===undefined?{id,depth}:{id,parent,...(indexedCutsRequested?{view:indexedSourceView()}:{})};let plan;
 const current=context?.isCurrent??stillWanted;
 try{plan=await (sourceLevelIndex?sourcePlanCache.read({request,topology,stillWanted:current}):readSourcePlan({request,stillWanted:current}));}catch(error){if(error instanceof SourcePlanResponseError)throw sourceResponseError(error.response,'plan',{root:id,depth,parent});throw error;}
 telemetry.sourcePlanRequests=(telemetry.sourcePlanRequests??0)+1;telemetry.sourcePlanCache=sourcePlanCache.snapshot();
 await learnAllocationCost(plan.marker,costs,key,current);
 if(!allocationStillBest(choice))return {plan,request,topology,continue:false};
 const {snapshot,isCurrent}=context??sourceGainContext({id,names,stillWanted});
 const cached=await geometryGainWorker.peek({marker:plan.marker,snapshot,isCurrent});ensureSourceWanted(isCurrent);
 if(cached){telemetry.sourcePlanMemoHits=(telemetry.sourcePlanMemoHits??0)+1;const estimates=parent===undefined?rootGainEstimates:familyGainEstimates;estimates.set(key,cached.gain);if(cached.gain<=0||!allocationStillBest(choice))return {plan,request,topology,continue:false};}
 return {plan,request,topology,continue:true};
}
async function readIndexedBundle(allocation,stillWanted){
 let response=await fetch(allocation.plan.bundleURL,{cache:'no-store'});ensureSourceWanted(stillWanted);
 // An immutable plan can outlive the RAM server's bounded view-registration LRU.
 // Re-register only that exact view once; an altered marker is never accepted.
 if(response.status===422){await response.body?.cancel().catch(()=>{});const fresh=await readSourcePlan({request:allocation.request,topology:allocation.topology,stillWanted});if(fresh.markerSHA256!==allocation.plan.markerSHA256||sourceBundleIdentity(fresh.marker)!==sourceBundleIdentity(allocation.plan.marker)){sourcePlanCache.invalidate(allocation.plan);throw new SourcePlanChanged();}allocation.plan=fresh;response=await fetch(fresh.bundleURL,{cache:'no-store'});}
 while(response.status===202){await response.body?.cancel().catch(()=>{});await new Promise(resolve=>setTimeout(resolve,300));ensureSourceWanted(stillWanted);response=await fetch(allocation.plan.bundleURL,{cache:'no-store'});}
 ensureSourceWanted(stillWanted);return response;
}
function sourceParentSpans(id,parent,ready){
 const spans=new Map();if(ready){const names=parent===null?[...ready.frontier.visible]:[parent];for(const name of names){const source=ready.frontier.nodes.get(name);if(!source)throw Error('Coverage parent no longer belongs to source cut');for(const span of source.node.spans){const mesh=source.bundle.meshes.get(span.part);if(!mesh)throw Error('Visible coverage parent page missing');if(!spans.has(mesh))spans.set(mesh,[]);spans.get(mesh).push(span);}}}
 else spans.set(base,catalog.root_records[id-1].base_spans.map(([first,count])=>({first,count})));return spans;
}
function acceptsSourceCoverage({id,parent=null,ready,candidate,stillWanted}){
 if(!indexedCutsRequested)return true;ensureSourceWanted(stillWanted);
 const result=frameProfile.measure('coverage',()=>coverageGuard.check({camera,candidate,parentSpans:sourceParentSpans(id,parent,ready),stillWanted}));telemetry.coverageChecks=(telemetry.coverageChecks??0)+1;telemetry.coverageRegionPixels=(telemetry.coverageRegionPixels??0)+result.region.pixels;telemetry.coverageFullPixels=(telemetry.coverageFullPixels??0)+result.region.fullPixels;telemetry.lastCoverage={root:id,parent,...result};console.info('[source coverage] '+JSON.stringify(telemetry.lastCoverage));
 if(result.loss){const key=parent===null?`root/${id}`:`family/${id}/${parent}`;coverageRejected.add(key);telemetry.coverageRejections=(telemetry.coverageRejections??0)+1;message('原始细层存在可见几何缺口，保留完整父层');return false;}return true;
}
function verifySourceAllocation(allocation,response,marker){try{return verifyPlannedSource(allocation.plan,response,marker);}catch(error){sourcePlanCache.invalidate(allocation.plan);telemetry.sourcePlanCache=sourcePlanCache.snapshot();throw error;}}
const uploadGLStats={samples:0,slowSamples:0,instrumentationErrors:0,maxCalls:null,lastSlow:null};
function uploadSourceModel(model){
 frameProfile.measure('source_upload',()=>uploadSourceScene({scene:model.scene,renderer,camera,target:familyUploadTarget,diagnostics:{enabled:frameProfile.enabled,record:(name,ms)=>frameProfile.record(name,ms),onSample:sample=>{uploadGLStats.samples++;uploadGLStats.instrumentationErrors+=sample.instrumentationErrors.length;const total=Object.values(sample.methods).reduce((n,s)=>n+s.totalMs,0);if(!uploadGLStats.maxCalls||total>uploadGLStats.maxCalls.totalMs)uploadGLStats.maxCalls={totalMs:total,methods:sample.methods};if(total>16.67){const meshes=[];model.scene.traverse(m=>{if(m.isMesh)meshes.push(m);});const mesh=meshes[0],texture=mesh?.material?.map;uploadGLStats.slowSamples++;uploadGLStats.lastSlow={totalMs:total,methods:sample.methods,texture:{width:texture?.source?.data?.width,height:texture?.source?.data?.height,format:texture?.isCompressedTexture?'compressed':'rgba',sourceType:texture?.source?.data?.constructor?.name},geometry:{vertices:mesh?.geometry?.attributes?.position?.count,indices:mesh?.geometry?.index?.count}};console.info('[upload GL] '+JSON.stringify(uploadGLStats.lastSlow));}}}}));
}
async function stageManagedSource({marker,downloads,folder,stillWanted,admit,onReady,cancelAttempt}){
 const forceRgbaParts=new Set();
 for(let attempt=0;attempt<=marker.parts.length;attempt++){
  ensureSourceWanted(stillWanted);
  const plan=await planPreparedSourceBundle({marker,supported:part=>supportsPreparedBc7(renderer)&&preparedTextures.has(part),loadManifest:part=>preparedTextures.manifest(part),forceRgbaParts,stillWanted});
  if(!await admit(plan.marker))return null;
  try{
   const staged=await stagePreparedSourceBundle({THREE,renderer,metrics:frameProfile,loadConcurrency:sourcePreparationConcurrency,marker,plan,stillWanted,loadFile:(part,name)=>downloads.read(`native/${folder}/${part.directory}/${name}`),loadPayload:part=>preparedTextures.payload(part),reserve:request=>pageBudget.reserve(request),prepare:model=>photograph(model.scene),upload:uploadSourceModel,onReady,yieldFrame:()=>new Promise(resolve=>requestAnimationFrame(resolve))});
   telemetry.preparedBundleLoads=(telemetry.preparedBundleLoads??0)+1;telemetry.preparedBc7Pages=(telemetry.preparedBc7Pages??0)+staged.marker.parts.filter(p=>p.runtime_texture.format==='bc7').length;
   return staged;
  }catch(error){
   cancelAttempt?.();
   if(!(error instanceof SourcePagePlanChanged)||forceRgbaParts.has(error.directory))throw error;
   preparedTextures.reject(marker.parts.find(part=>part.directory===error.directory));forceRgbaParts.add(error.directory);telemetry.preparedReplans=(telemetry.preparedReplans??0)+1;
  }
 }
 throw Error('源页格式重新规划次数超限');
}
async function loadFine(request){const owner=resident.get(request.id),stillWanted=()=>resident.get(request.id)===owner&&ranking().some(r=>r.id===request.id&&r.depth===request.depth);pending=request;telemetry.requests++;let staged=new THREE.Group(),downloads=null,requestCancelled=false;try{
  const allocation=await prepareSourceAllocation({id:request.id,depth:request.depth,names:owner?[...owner.frontier.visible]:[''],costs:rootCosts,key:`${request.id}/${request.depth}`,choice:`root/${request.id}/${request.depth}`,stillWanted});if(allocation&&!allocation.continue)return;
  ensureSourceWanted(stillWanted);let response=await fetch(`api/lod/${request.id}/${request.depth}`);while(response.status===202){await new Promise(r=>setTimeout(r,300));ensureSourceWanted(stillWanted);response=await fetch(`api/lod/${request.id}/${request.depth}`);}if(!response.ok)throw sourceResponseError(response,'root',{root:request.id,depth:request.depth});const marker=await response.json();downloads=new LeasedDownloads(marker.cache_lease);if(allocation)verifySourceAllocation(allocation,response,marker);
  if(!marker.complete_frontier||!marker.parts?.length||marker.parts.length>64||marker.gpu_payload_bytes>384*1048576||marker.texture_policy!=='original_pixels_v1'||!Number.isFinite(marker.texel_world_p90_m)||marker.texel_world_p90_m<=0)throw Error('细层数据不完整，保留父层');
  tierEdges.set(`${request.id}/${request.depth}`,marker.longest_edge_p90_m);tierTexels.set(`${request.id}/${request.depth}`,marker.texel_world_p90_m??0);
  ensureSourceWanted(stillWanted);
  const previous=resident.get(request.id);
  if(!allocation)await learnAllocationCost(marker,rootCosts,`${request.id}/${request.depth}`,stillWanted);if(!allocationStillBest(`root/${request.id}/${request.depth}`))return;
  const gain=await measureSourceGain({id:request.id,names:previous?[...previous.frontier.visible]:[''],marker,downloads,folder:`tile_${request.id}_depth_${request.depth}`,stillWanted});rootGainEstimates.set(`${request.id}/${request.depth}`,gain);if(gain<=0||!allocationStillBest(`root/${request.id}/${request.depth}`))return;
  const loaded=await stageManagedSource({marker,downloads,folder:`tile_${request.id}_depth_${request.depth}`,stillWanted,admit:async runtime=>{
   rootCosts.set(`${request.id}/${request.depth}`,runtime.gpu_payload_bytes);if(!allocationStillBest(`root/${request.id}/${request.depth}`))return false;
   if(!await canMakeFamilyRoom(request.id,null,gain,runtime.gpu_payload_bytes,true,stillWanted)){telemetry.budgetFallbacks=(telemetry.budgetFallbacks??0)+1;return false;}
   const used=[...resident.values()].reduce((sum,r)=>sum+r.bytes,0);if(used+runtime.gpu_payload_bytes>detailLimit||sourceLevelIndex&&!resident.has(request.id)&&resident.size>=sourceResidentLimit())return false;
   telemetry.stagingBytes=runtime.gpu_payload_bytes;telemetry.peakBytes=Math.max(telemetry.peakBytes??0,used+runtime.gpu_payload_bytes+uploadTargetBytes+coverageGuard.bytes);message(`航拍细层加载中：瓦片 ${request.id} · 深度 ${request.depth}`);return true;
  }});if(!loaded)return;staged=loaded.group;const runtime=loaded.marker;
  ensureSourceWanted(stillWanted);
  if(!acceptsSourceCoverage({id:request.id,ready:previous,candidate:staged,stillWanted}))return;
  const frontier=new SourceFrontier(runtime,loaded.meshes,{topology:allocation?.topology??null});frontier.bundles.get('$root').group=staged;frontier.applyMasks();frontier.releaseHiddenPages();if(previous){if(request.depth<previous.depth)telemetry.coarsenings=(telemetry.coarsenings??0)+1;photoGroup.remove(previous.group);disposeGroup(previous.group);}photoGroup.add(staged);updateSceneOpacity();resident.set(request.id,{group:staged,depth:request.depth,bytes:runtime.gpu_payload_bytes,marker:runtime,frontier});staged=null;baseRanges();message(`倾斜摄影细层：瓦片 ${request.id} · 深度 ${request.depth} · ${runtime.parts.length} 批完整就绪`);
 }catch(error){if(error instanceof SourceLoadCancelled){requestCancelled=true;sourceCancelled();}else if(error instanceof SourceRestoreUnavailable)sourceRestoreFailed(error);else{failed.add(`${request.id}/${request.depth}`);lastError=String(error.message);message(lastError);}}finally{downloads?.release();if(staged)disposeGroup(staged);telemetry.stagingBytes=0;pending=null;lastRank=requestCancelled?performance.now():0;}}

function sourceCancelled(){telemetry.cancellations++;message($('fine').checked?'已取消本次细层加载':'细层加载已关闭，保留完整基础地景');}
const familyFailed=new Set(),familyCosts=new Map();
// Compare roots and local families in one queue. Cost is immutable per negotiated
// source layout, while actual geometry gains expire with the visible camera/cut.
const allocationFeasibilityMemo=new AllocationFeasibilityMemo();
const allocationScanStats={started:0,completed:0,cancelled:0,slices:0,yields:0,probes:0,maxCandidates:0,last:null};
function sourceOcclusionRects(){const viewportRect=viewport.getBoundingClientRect();return [...document.querySelectorAll('.layout>aside')].filter(n=>n.getClientRects().length).map(n=>{const r=n.getBoundingClientRect();return {left:r.left-viewportRect.left,right:r.right-viewportRect.left,top:r.top-viewportRect.top,bottom:r.bottom-viewportRect.top};});}
function allocationPresentationState(){return JSON.stringify([sourceOcclusionRects(),sceneOpacity('photo'),sceneOpacity('satellite'),$('satellite').checked]);}
function currentAllocationBudgetState(){return allocationBudgetState({residents:resident,visibility:sourceVisibility.visibleSnapshot,camera,width,height,limit:detailLimit,maxResidents:sourceResidentLimit(),held:pageBudget.held,stagingBytes:telemetry.stagingBytes,restoreFailed,visibilityReady});}
function probeSourceCandidate(c){const result=allocationFeasibilityMemo.resolve({id:c.id,parent:c.kind==='family'?c.node.name:null,score:c.score,cost:c.cost},()=>frameProfile.measure('budget_probe',()=>canMakeFamilyRoom(c.id,c.kind==='family'?c.node.name:null,c.score,c.cost,false)));if(residencyAuditEnabled&&!result){residencyRejectedProbes.push({key:c.key,cost:c.cost,score:c.score,held:pageBudget.held,limit:budget,detailLimit,stagingBytes:telemetry.stagingBytes,residentRoots:resident.size,reason:'no_feasible_fidelity_preserving_plan; not_a_unique_cause_classification'});if(residencyRejectedProbes.length>32)residencyRejectedProbes.shift();}return result;}
function startAllocationScan(ranked){
 const candidates=allocationCandidates(ranked),state=currentAllocationBudgetState();allocationFeasibilityMemo.setContext(state);
 const scan=new SourceAllocationScan(candidates,{indexed:true,hasRoot:id=>resident.has(id),feasible:probeSourceCandidate});
 pending={type:'planning',scan,state,epoch,presentation:allocationPresentationState()};allocationScanStats.started++;allocationScanStats.maxCandidates=Math.max(allocationScanStats.maxCandidates,candidates.length);
}
function continueAllocationScan(){
 const task=pending;if(task?.type!=='planning')return;
 try{
  const current=frameProfile.measure('allocation_state',()=>task.epoch===epoch&&$('fine').checked&&$('photo').checked&&sceneOpacity('photo')>0&&visibilityReady&&task.presentation===allocationPresentationState()&&sameAllocationBudgetState(task.state,currentAllocationBudgetState()));
  const beforeProbes=task.scan.probes,beforeSlices=task.scan.slices,beforeYields=task.scan.yields;
  const result=frameProfile.measure('allocation_slice',()=>task.scan.step({budgetMs:4,isCurrent:()=>current}));
  allocationScanStats.probes+=result.probes-beforeProbes;allocationScanStats.slices+=result.slices-beforeSlices;allocationScanStats.yields+=result.yields-beforeYields;
  allocationScanStats.last={...result,candidate:result.candidate?.key??null};
  if(!result.done)return;if(pending!==task)return;pending=null;
  if(result.cancelled){allocationScanStats.cancelled++;lastRank=0;return;}allocationScanStats.completed++;
  const chosen=result.candidate;if(chosen){telemetry.allocationChoice={key:chosen.key,gain:chosen.score,bytes:chosen.cost};(chosen.kind==='family'?loadWebFamily({id:chosen.id,parent:chosen.node.name,ready:chosen.ready,score:chosen.score}):loadFine(chosen.request)).catch(fail);}
 }catch(error){task.scan.cancel();if(pending===task)pending=null;lastRank=performance.now();fail(error);}
}

function allocationCandidates(ranked=ranking()){
 if(indexedCutsRequested)allocationFeasibilityMemo.setContext(currentAllocationBudgetState());
 const candidates=[];
 for(const r of ranked){
  if(resident.get(r.id)?.depth===r.depth||failed.has(`${r.id}/${r.depth}`)||coverageRejected.has(`root/${r.id}`))continue;
  const bounds=catalog.root_records[r.id-1],score=rootGainEstimates.get(`${r.id}/${r.depth}`)??visiblePriority(r.id,{...bounds,longest_edge_p90_m:baseEdges.get(r.id),texel_world_p90_m:baseTexels.get(r.id)??0}),cost=rootCosts.get(`${r.id}/${r.depth}`)??null;
  if(score>0&&(indexedCutsRequested||cost===null||canMakeFamilyRoom(r.id,null,score,cost,false)))candidates.push({key:`root/${r.id}/${r.depth}`,kind:'root',id:r.id,request:r,score,cost});
 }
 for(const [id,ready] of resident)if(ready.frontier)for(const c of visibleSourceCandidates(ready.frontier,camera,height)){
  const parent=c.node.name;if(familyFailed.has(`${id}/${parent}`)||coverageRejected.has(`family/${id}/${parent}`))continue;
  const score=familyGainEstimates.get(`${id}/${parent}`)??visiblePriority(id,c.node),cost=familyCosts.get(`${id}/${parent}`)??null;
  if(score>0&&(indexedCutsRequested||cost===null||canMakeFamilyRoom(id,parent,score,cost,false)))candidates.push({...c,key:`family/${id}/${parent}`,kind:'family',id,ready,score,cost});
 }
 return candidates;
}
function chooseSourceCandidate(candidates){return indexedCutsRequested?chooseFeasibleSourceCandidate(candidates,{indexed:true,hasRoot:id=>resident.has(id),feasible:probeSourceCandidate}):chooseRefinementCandidate(candidates);}
function allocationStillBest(key){if(!visibilityReady)return true;if(indexedCutsRequested&&pending){const active=pending.type==='family'?`family/${pending.id}/${pending.parent}`:`root/${pending.id}/${pending.depth}`;if(active===key)return true;}const best=chooseSourceCandidate(allocationCandidates());if(best?.key===key)return true;telemetry.allocationReorders=(telemetry.allocationReorders??0)+1;return false;}
async function learnAllocationCost(marker,costs,key,stillWanted){
 const plan=await planPreparedSourceBundle({marker,supported:part=>supportsPreparedBc7(renderer)&&preparedTextures.has(part),loadManifest:part=>preparedTextures.manifest(part),stillWanted});
 ensureSourceWanted(stillWanted);costs.set(key,plan.marker.gpu_payload_bytes);telemetry.allocationMetadata=(telemetry.allocationMetadata??0)+1;
}

const familyUploadTarget=new THREE.WebGLRenderTarget(16,16,{depthBuffer:false,stencilBuffer:false});
function wantedWebFamily(){
 if(!$('fine').checked||!$('photo').checked||sceneOpacity('photo')<=0)return null;
 const ray=new THREE.Ray(camera.position.clone(),controls.target.clone().sub(camera.position).normalize());let closest=null;
 for(const [id,ready] of resident)if(ready.frontier){const hit=pickVisibleSource(ready.frontier,ray);if(hit&&(!closest||hit.distance<closest.distance))closest={...hit,id};}
 const candidates=[];
 for(const [id,ready] of resident)if(ready.frontier)for(const candidate of visibleSourceCandidates(ready.frontier,camera,height,closest?.id===id?closest.node.name:''))if(!familyFailed.has(`${id}/${candidate.node.name}`)){if(visibilityReady){candidate.score=familyGainEstimates.get(`${id}/${candidate.node.name}`)??visiblePriority(id,candidate.node);if(!candidate.score)continue;}const cost=familyCosts.get(`${id}/${candidate.node.name}`);if(!cost||cost<=detailLimit-telemetry.nativeBytes||canMakeFamilyRoom(id,candidate.node.name,candidate.score,cost,false))candidates.push({...candidate,id,ready});}
 return rankSourceCandidates(candidates)[0]??null;
}
// Coarsen only clearly less valuable branches; a 2x margin avoids quality ping-pong.
function canMakeFamilyRoom(id,parent,score,cost,apply,stillWanted=()=>true){
 const priority=(root,node,names)=>restoreFailed.has(`${root}/${node.name}`)?Infinity:visibilityReady?sourceVisibility.retirementLoss(root,node,names,resident.get(root).frontier.nodes,camera,height):sourceViewPriority(node,camera,height);
 // QA floor keeps every currently wanted root at least at its complete source
 // cut. Normal ranking still removes roots after camera/LOD demand changes;
 // family rollback and mandatory viewport budget recovery remain available.
 const rootPriority=preserveWantedRoots?null:(root,names)=>priority(root,{...catalog.root_records[root-1],longest_edge_p90_m:baseEdges.get(root),texel_world_p90_m:baseTexels.get(root)??0},names);
 const actions=planSourceBudget(resident,{id,parent,score},cost,detailLimit,priority,rootPriority,{maxResidents:sourceResidentLimit()});
 if(actions===null){
  const sequence=planSourceRecoverySequence(resident,{id,parent,score},cost,detailLimit,priority,rootPriority,{maxResidents:sourceResidentLimit()});if(!sequence?.steps.length)return false;
  if(!apply)return true;
  telemetry.recoverySequencePlans=(telemetry.recoverySequencePlans??0)+1;telemetry.recoverySequencePeak=Math.max(telemetry.recoverySequencePeak??0,sequence.peakBytes+uploadTargetBytes+coverageGuard.bytes);
  return applySourceRecoverySequence({sequence,residents:resident,stillWanted,apply:async(...args)=>{const result=await applySourceBudget(...args);if(result)telemetry.recoverySequenceSteps=(telemetry.recoverySequenceSteps??0)+1;return result;}});
 }
 if(apply)return applySourceBudget(actions,stillWanted,cost);
 return true;
}
function retireWebBundles(ready,retired){for(const bundle of retired){ready.group.remove(bundle.group);disposeGroup(bundle.group);}applySourceMasks(ready);ready.bytes=ready.frontier.bytes;if(retired.length){telemetry.familyCoarsenings=(telemetry.familyCoarsenings??0)+1;familyFailed.clear();}}
function rollbackWebFamilies(ready){
 if(ready.frontier.bundles.size<2||pending?.restoring)return;
 const nodes=ready.frontier.nodes,parents=[...ready.frontier.bundles.keys()].filter(n=>n!=='$root');
 for(const parent of parents){if(!ready.frontier.bundles.has(parent))continue;const node=nodes.get(parent)?.node;if(!node?.bounds_min)continue;
   const distance=Math.max(1,new THREE.Box3(new THREE.Vector3(...node.bounds_min),new THREE.Vector3(...node.bounds_max)).distanceToPoint(camera.position)),quality=Math.max(node.longest_edge_p90_m,node.texel_world_p90_m*4)*height/(2*Math.tan(THREE.MathUtils.degToRad(camera.fov)/2)*distance);
   if(quality<2){const used=[...resident.values()].reduce((sum,r)=>sum+r.bytes,0),plan=ready.frontier.rollbackPlan(parent),extra=Math.max(0,detailLimit-used-telemetry.stagingBytes);if(plan.bytes>ready.bytes+extra)continue;if(plan.missingPages.length){if(sourceRestorationFootprint(resident,[{root:plan.missingPages[0].bundle.marker.tile_id,parent}])>detailLimit)continue;if(!restoreFailed.has(`${plan.missingPages[0].bundle.marker.tile_id}/${parent}`))return parent;continue;}retireWebBundles(ready,ready.frontier.rollback(parent,extra));}
 }
}
async function loadWebFamily(request){pending={...request,type:'family'};telemetry.familyRequests=(telemetry.familyRequests??0)+1;const requestEpoch=epoch;let staged=new THREE.Group(),ticket=null,downloads=null,requestCancelled=false;
 const stillWanted=()=>epoch===requestEpoch&&resident.get(request.id)===request.ready&&(ticket===null||request.ready.frontier.pending?.ticket===ticket)&&request.ready.frontier.visible.has(request.parent)&&visibleSourceCandidates(request.ready.frontier,camera,height).some(c=>c.node.name===request.parent)&&(!visibilityReady||sourceVisibility.weight(request.id,request.parent)>0);
 try{
  const allocation=await prepareSourceAllocation({id:request.id,parent:request.parent,names:[request.parent],costs:familyCosts,key:`${request.id}/${request.parent}`,choice:`family/${request.id}/${request.parent}`,stillWanted});if(allocation&&!allocation.continue)return;
  const route=`api/lod-family/${request.id}/${encodeURIComponent(request.parent)}`;let response=allocation?.plan.bundleURL?await readIndexedBundle(allocation,stillWanted):await fetch(route,{cache:'no-store'});while(response.status===202){await new Promise(resolve=>setTimeout(resolve,300));if(!stillWanted()){requestCancelled=true;sourceCancelled();return;}response=await fetch(route,{cache:'no-store'});}if(!response.ok)throw sourceResponseError(response,'family',{root:request.id,parent:request.parent});const marker=await response.json();downloads=new LeasedDownloads(marker.cache_lease);if(allocation)verifySourceAllocation(allocation,response,marker);if(!stillWanted()){requestCancelled=true;sourceCancelled();return;}
  if(!/^[0-9a-f]{16}$/.test(marker.family_key)||marker.tile_id!==request.id||marker.gpu_payload_bytes>256*1048576)throw Error('局部模型标记无效');
  if(!allocation)await learnAllocationCost(marker,familyCosts,`${request.id}/${request.parent}`,stillWanted);if(!allocationStillBest(`family/${request.id}/${request.parent}`))return;
  const gain=await measureSourceGain({id:request.id,names:[request.parent],marker,downloads,folder:`family_tile_${request.id}_${marker.family_key}`,stillWanted});familyGainEstimates.set(`${request.id}/${request.parent}`,gain);if(gain<=0||!allocationStillBest(`family/${request.id}/${request.parent}`))return;
  const loaded=await stageManagedSource({marker,downloads,folder:`family_tile_${request.id}_${marker.family_key}`,stillWanted,admit:async runtime=>{
   familyCosts.set(`${request.id}/${request.parent}`,runtime.gpu_payload_bytes);if(!allocationStillBest(`family/${request.id}/${request.parent}`))return false;
   if(!await canMakeFamilyRoom(request.id,request.parent,gain,runtime.gpu_payload_bytes,true,stillWanted)){telemetry.budgetFallbacks=(telemetry.budgetFallbacks??0)+1;message('当前视野已分配细节预算，部分外围保留较粗层');return false;}
   ensureSourceWanted(stillWanted);const used=[...resident.values()].reduce((sum,r)=>sum+r.bytes,0);
   ticket=request.ready.frontier.begin(runtime,detailLimit-used);telemetry.stagingBytes=runtime.gpu_payload_bytes;telemetry.peakBytes=Math.max(telemetry.peakBytes??0,used+runtime.gpu_payload_bytes+uploadTargetBytes+coverageGuard.bytes);message(`航拍局部细层加载中：深度 ${Math.max(...runtime.source_nodes.map(n=>n.depth))}`);return true;
  },onReady:i=>request.ready.frontier.markReady(ticket,i),cancelAttempt:()=>{if(ticket)request.ready.frontier.cancel(ticket);ticket=null;}});
  if(!loaded)return;staged=loaded.group;
  if(!stillWanted()){requestCancelled=true;sourceCancelled();return;}if(!acceptsSourceCoverage({id:request.id,parent:request.parent,ready:request.ready,candidate:staged,stillWanted}))return;if(!request.ready.frontier.commit(ticket,loaded.meshes))throw Error('局部细层事务已取消');request.ready.frontier.bundles.get(request.parent).group=staged;if(allocation?.plan.bundleURL){request.ready.frontier.bundles.get(request.parent).sourceRequest=allocation.request;telemetry.indexedFamilyCommits=(telemetry.indexedFamilyCommits??0)+1;}request.ready.group.add(staged);applySourceMasks(request.ready);request.ready.bytes=request.ready.frontier.bytes;updateSceneOpacity();telemetry.familyCommits=(telemetry.familyCommits??0)+1;message(`航拍局部细层 ${request.ready.frontier.maxDepth} · 完整父子替换`);staged=null;
 }catch(error){if(error instanceof SourceLoadCancelled){requestCancelled=true;sourceCancelled();}else if(error instanceof IndexedSourceQualityLimit){coverageRejected.add(`family/${request.id}/${request.parent}`);telemetry.indexedQualityLimits=(telemetry.indexedQualityLimits??0)+1;message(error.message);}else if(error instanceof SourceRestoreUnavailable)sourceRestoreFailed(error);else{familyFailed.add(`${request.id}/${request.parent}`);message(String(error.message));}}finally{downloads?.release();if(ticket)request.ready.frontier.cancel(ticket);if(staged)disposeGroup(staged);telemetry.stagingBytes=0;pending=null;lastRank=requestCancelled?performance.now():0;}}

const restoreFailed=new Set();
function applySourceMasks(ready){ready.frontier.applyMasks();const retired=ready.frontier.releaseHiddenPages();telemetry.retiredCpuPages=(telemetry.retiredCpuPages??0)+retired.pages;telemetry.retiredCpuPayloadBytes=(telemetry.retiredCpuPayloadBytes??0)+retired.bytes;}
function sourceRestoreFailed(error){telemetry.restoreErrors=(telemetry.restoreErrors??0)+1;message('回退源页读取失败，保留当前完整细层');console.info('[source restore] '+error.message);}
async function readSourcePages(need,stillWanted){
 const source=need.bundle.marker,indexed=isIndexedMemoryFamily(source),isFamily=source.schema==='xnby.osgb_native_family.v1'||isMemoryFamily(source);let route=isFamily?`api/lod-family/${need.root}/${encodeURIComponent(source.replacement_parent)}`:`api/lod/${need.root}/${need.ready.depth}`;let downloads=null,staged=null;
 try{
  telemetry.restoreRequests=(telemetry.restoreRequests??0)+1;ensureSourceWanted(stillWanted);let indexedPlan=null;if(indexed){if(!need.bundle.sourceRequest)throw Error('Indexed source restore request unavailable');indexedPlan=await readSourcePlan({request:need.bundle.sourceRequest,topology:need.ready.frontier.topology,stillWanted});if(sourceBundleIdentity(indexedPlan.marker)!==sourceBundleIdentity(originalSourceBundle(source)))throw Error('Indexed restore plan differs from complete parent');route=indexedPlan.bundleURL;}let response=await fetch(route,{cache:'no-store'});while(response.status===202){await new Promise(resolve=>setTimeout(resolve,300));ensureSourceWanted(stillWanted);response=await fetch(route,{cache:'no-store'});}if(!response.ok)throw sourceResponseError(response,'restore',{root:need.root,parent:source.replacement_parent??null});
  const marker=await response.json();downloads=new LeasedDownloads(marker.cache_lease);ensureSourceWanted(stillWanted);if(indexedPlan)verifyPlannedSource(indexedPlan,response,marker);if(sourceBundleIdentity(marker)!==sourceBundleIdentity(originalSourceBundle(source)))throw Error('回退源包与当前场景不一致');
  const plan=await planPreparedSourceBundle({marker,supported:part=>supportsPreparedBc7(renderer)&&preparedTextures.has(part),loadManifest:part=>preparedTextures.manifest(part),forceRgbaParts:new Set(source.parts.filter(p=>p.runtime_texture.format==='rgba8').map(p=>p.directory)),stillWanted});
  if(sourceBundleIdentity(plan.marker)!==sourceBundleIdentity(source))throw Error('回退源页格式或载荷身份已变化，保留当前细层');
  const subset=subsetPreparedSourcePlan(plan,need.parts.map(p=>p.directory));
  telemetry.cpuRestoreStagingPayloadBytes=(telemetry.cpuRestoreStagingPayloadBytes??0)+subset.plan.marker.gpu_payload_bytes;message('正在恢复回退源页，保留当前地景');
  const folder=isFamily?`family_tile_${need.root}_${marker.family_key}`:`tile_${need.root}_depth_${need.ready.depth}`;
  staged=await stagePreparedSourceBundle({THREE,renderer,metrics:frameProfile,loadConcurrency:sourcePreparationConcurrency,...subset,stillWanted,loadFile:(part,name)=>downloads.read(`native/${folder}/${part.directory}/${name}`),loadPayload:part=>preparedTextures.payload(part),reserve:request=>pageBudget.reserve(request),prepare:model=>photograph(model.scene),upload:uploadSourceModel,yieldFrame:()=>new Promise(resolve=>requestAnimationFrame(resolve))});
  return {marker:source,group:staged.group,meshes:staged.meshes,attached:false,dispose(){if(!this.attached)staged.dispose();}};
 }catch(error){staged?.dispose();throw error;}finally{downloads?.release();}
}
async function applySourceBudget(actions,stillWanted,reservedBytes=0){
 if(!actions.length)return true;const audit=budgetAuditEnabled?actions.map(action=>({elapsedMs:performance.now(),root:action.root,parent:action.parent,requestType:pending?.type??null,beforeBytes:resident.get(action.root)?.frontier.bytes??0,reservedBytes,detailLimit,held:pageBudget.held})):null;if(pending)pending.restoring=true;
 try{return await withSourceRestorations({actions,residents:resident,load:readSourcePages,stillWanted,reservedBytes,limit:detailLimit,apply:batches=>{
   for(const batch of batches){batch.ready.frontier.restorePages(batch.bundle,batch.meshes);batch.bundle.group.add(batch.group);batch.attached=true;telemetry.restoredCpuPages=(telemetry.restoredCpuPages??0)+batch.meshes.size;}
   const touched=new Set();for(const action of actions){const ready=resident.get(action.root);if(action.parent===null){photoGroup.remove(ready.group);disposeGroup(ready.group);resident.delete(action.root);}else{
    const retired=ready.frontier.rollback(action.parent);for(const bundle of retired){ready.group.remove(bundle.group);disposeGroup(bundle.group);}if(retired.length){telemetry.familyCoarsenings=(telemetry.familyCoarsenings??0)+1;familyFailed.clear();}touched.add(ready);
   }}
   for(const ready of touched){applySourceMasks(ready);ready.bytes=ready.frontier.bytes;}if(actions.some(a=>a.parent===null))baseRanges();updateSceneOpacity();if(audit){for(const event of audit)sourceBudgetEvents.push({...event,afterBytes:resident.get(event.root)?.frontier.bytes??0});if(sourceBudgetEvents.length>64)sourceBudgetEvents.splice(0,sourceBudgetEvents.length-64);}return true;
  }});
 }catch(error){if(error instanceof SourceRestoreUnavailable)for(const action of actions)if(action.parent!==null)restoreFailed.add(`${action.root}/${action.parent}`);throw error;
 }finally{telemetry.cpuRestoreStagingPayloadBytes=0;if(pending)pending.restoring=false;}
}
async function loadSourceCoarsen(request){const version=epoch;pending={...request,type:'coarsen'};const stillWanted=()=>epoch===version&&resident.get(request.id)===request.ready&&$('fine').checked&&$('photo').checked&&sceneOpacity('photo')>0;
 try{await applySourceBudget([{root:request.id,parent:request.parent}],stillWanted);message('航拍回退源页已恢复');}catch(error){if(error instanceof SourceLoadCancelled)sourceCancelled();else if(error instanceof SourceRestoreUnavailable)sourceRestoreFailed(error);else throw error;}finally{pending=null;}
}

const viewportBudgetStats={requests:0,completed:0,cancelled:0,errors:0,steps:0,rootFallbacks:0,last:null};
async function rebalanceSourceViewport(){
 const owner={type:'viewport'},version=epoch,w=width,h=height;pending=owner;viewportBudgetStats.requests++;viewportBudgetStats.last={width:w,height:h,status:'recovering',beforeHeld:pageBudget.held};
 const current=()=>pending===owner&&epoch===version&&width===w&&height===h&&$('fine').checked&&$('photo').checked&&sceneOpacity('photo')>0;
 const priority=(root,node)=>restoreFailed.has(`${root}/${node.name}`)?Infinity:sourceViewPriority(node,camera,height);
 const rootPriority=root=>sourceViewPriority({...catalog.root_records[root-1],longest_edge_p90_m:baseEdges.get(root),texel_world_p90_m:baseTexels.get(root)??0},camera,height);
 try{const result=await resizeSourceViewport({width:w,height:h,guard:coverageGuard,ledger:pageBudget,residents:resident,priority,rootPriority,stillWanted:current,onPlan:({capacity})=>{detailLimit=capacity;},apply:(actions,current,reserved)=>applySourceBudget(actions,current,reserved),onStep:step=>{viewportBudgetStats.steps++;viewportBudgetStats.rootFallbacks+=step.actions.filter(a=>a.parent===null).length;console.info('[viewport budget step] '+JSON.stringify(step));}});
  viewportBudgetStats.completed++;viewportBudgetStats.last={width:w,height:h,status:'ready',...result};telemetry.coverageUnavailable=null;message('视口预算已调整，继续加载地景');console.info('[viewport budget] '+JSON.stringify(viewportBudgetStats.last));
 }catch(error){if(error instanceof SourceLoadCancelled){viewportBudgetStats.cancelled++;viewportBudgetStats.last={width:w,height:h,status:'cancelled'};}else{viewportBudgetStats.errors++;viewportBudgetStats.last={width:w,height:h,status:'retry',reason:error.message};if(error instanceof SourceRestoreUnavailable)sourceRestoreFailed(error);else telemetry.coverageUnavailable=error.message;}}
 finally{if(pending===owner)pending=null;detailLimit=budget-uploadTargetBytes-coverageGuard.bytes;visibilityReady=false;rootGainEstimates.clear();familyGainEstimates.clear();lastRank=0;}
}
function resize(){visibilityReady=false;width=viewport.clientWidth;height=viewport.clientHeight;renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();HUD.width=width;HUD.height=height;}
new ResizeObserver(()=>{resize();epoch++;failed.clear();familyFailed.clear();restoreFailed.clear();}).observe(viewport);preset('overview');
function inspectionCamera(inspection){const damping=controls.enableDamping;controls.enableDamping=false;controls.target.set(...inspection.point);camera.position.copy(controls.target).add(new THREE.Vector3(-inspection.height*.55,-inspection.height*.6,inspection.height));controls.update();controls.enableDamping=damping;camera.updateMatrixWorld();epoch++;visibilityReady=false;failed.clear();familyFailed.clear();restoreFailed.clear();coverageRejected.clear();}
try{const inspection=parseInspectionView(location.search);if(inspection)inspectionCamera(inspection);}catch(error){message(error.message);}
// Explicit local acceptance mode offers repeatable views without reloading the
// renderer, changing annotations, or reading application internals via automation.
if(new URLSearchParams(location.search).get('qa')==='1'){
 const bar=document.createElement('div');bar.className='tools';bar.style.cssText='position:absolute;top:58px;left:50%;transform:translateX(-50%);z-index:8;display:flex;gap:8px;white-space:nowrap';bar.setAttribute('aria-label','场景验收机位');
 for(const [name,point,height] of [['园区近景100米',[-317,-1988,43],100],['园区中景350米',[-317,-1988,43],350],['园区远景1000米',[-317,-1988,43],1000],['园区道路近景',[494.65185546875,3184.25146484375,28.058813095092773],10]]){const button=document.createElement('button');button.textContent=name;button.onclick=()=>{if(frameProfile.enabled){frameProfile.reset(name);sceneGpuTimer.reset();}inspectionCamera({point,height});};bar.append(button);}viewport.append(bar);
}

if(new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('viewportQA')==='1'){
 const panel=document.createElement('div');panel.setAttribute('aria-label','视口预算验收');panel.style.cssText='position:fixed;bottom:34px;left:290px;z-index:30;display:flex;gap:5px';
 const setSize=(w,h)=>{viewport.style.width=w?`${w}px`:'';viewport.style.height=h?`${h}px`:'';viewport.style.minWidth='0';viewport.style.minHeight='0';};
 for(const [label,w,h] of [['验收小视口 768×344',768,344],['验收大视口 1280×573',1280,573],['恢复自适应视口',0,0]]){const button=document.createElement('button');button.textContent=label;button.onclick=()=>setSize(w,h);panel.append(button);}document.body.append(panel);
 if(new URLSearchParams(location.search).get('viewportSize')==='small')setSize(768,344);
}
controls.addEventListener('change',()=>{visibilityReady=false;});
controls.addEventListener('end',()=>{epoch++;familyFailed.clear();restoreFailed.clear();});
for(const name of ['overview','oblique','close'])$(name).onclick=()=>preset(name);$('locate').onclick=locate;
$('satellite').onchange=updateSceneOpacity;$('photo').onchange=()=>{updateSceneOpacity();epoch++;};
for(const id of ['photo','satellite'])$(id+'-opacity').oninput=()=>{$(id+'-opacity-value').value=$(id+'-opacity').value+'%';updateSceneOpacity();epoch++;};
$('restore-opacity').onclick=()=>{layerOpacities.clear();for(const id of ['photo','satellite']){$(id+'-opacity').value='0';$(id+'-opacity-value').value='0%';}updateSceneOpacity();epoch++;rebuildLayerUI();
  if(selected){const l=layersDoc.layers.find(l=>l.features.includes(selected));if(l)showDetails(selected,l);}else if(selectedLayer)showLayerDetails(selectedLayer);message('浏览透明度已恢复，标注原始样式保留');};$('fine').onchange=()=>{epoch++;failed.clear();familyFailed.clear();restoreFailed.clear();};
$('fullscreen').onclick=()=>document.fullscreenElement?document.exitFullscreen():viewport.requestFullscreen();
$('layer-file').onchange=async event=>{if(dataMode!=='local')return;const file=event.target.files[0];if(!file)return;userLayerLoad=true;
  try{await layerLoading.load(async()=>{if(file.size>16*1048576)throw Error('图层文件超过 16 MiB');return JSON.parse(await file.text());},doc=>openDocument(doc,file.name));}
  catch(error){fail(error);}finally{event.target.value='';}};
async function reload(){if(dataMode!=='local')return;return layerLoading.load(async()=>{const response=await fetch('layers/default.json',{cache:'no-store'});if(!response.ok)throw Error('尚未找到编辑端保存的图层文件，可使用“打开图层文件”');return response.json();},doc=>openDocument(doc,'编辑端 · 驻马店图层.json'));}
$('reload').onclick=()=>{userLayerLoad=true;reload().catch(fail);};

const connectionMessages={SIGNED_OUT:'已退出，授权数据已清空',UNAUTHENTICATED:'登录已失效，请重新登录',FORBIDDEN:'当前账号无访问权限',AUTH_EXPIRED:'登录已到期，授权数据已清空',CONNECTION_FAILED:'业务服务连接失败，授权数据已清空',CONFIG_INVALID:'业务连接配置无效，请联系管理员',CONFIG_UNAVAILABLE:'业务连接暂不可用，请稍后重试',LOGIN_INVALID:'登录校验失败，请重新登录',LOGIN_CANCELLED:'登录已取消',LOGIN_REJECTED:'身份平台拒绝登录，请重试',LOGIN_UNAVAILABLE:'身份平台暂不可用',LOGIN_STORAGE_UNAVAILABLE:'浏览器无法保存临时登录校验，请检查设置',DATA_CHANGED:'数据版本已变化，请刷新重试',POLICY_CHANGED:'授权范围已变化，请刷新重试',DATA_INVALID:'业务数据格式无效，请联系管理员',DATA_SOURCE_UNAVAILABLE:'业务数据源暂不可用',POLICY_UNAVAILABLE:'授权配置暂不可用'};
function gasFocusNotice(value){$('gas-focus-status').hidden=!value;$('gas-focus-status').textContent=value;if(value)message(value);}
function clearAuthorizedData(){
  cancelSignDrag();signOffsets.clear();signPrevious.clear();signLayoutKey='';signMetrics.clear();signPlacements.clear();signLayoutResult=null;signPreferenceKey='';
  gasFocusNotice('');
  layerLoading.revision++;businessLoadGeneration++;spatialLoadGeneration++;
  layersDoc={schema:'hongtu.landscape.layers.v1',scene:'zhumadian',coordinates:{srs:'EPSG:32650',unit:'metre',axes:'east,north,up',origin:[225319.5,3648440.1,30.9]},layers:[]};
  businessCatalog=null;spatialCatalog=null;spatialFingerprint='';apiBusinessState='unconfigured';layerOpacities.clear();hitTargets=[];imageCache.clear();tintedCache.clear();
  $('layers').replaceChildren();$('features').replaceChildren();$('connection-scope').textContent='';$('file-name').textContent='尚无授权数据';
  clearSelection(false);rebuildLayerUI();ctx.clearRect(0,0,width,height);
}
function connectionState(state){
  const ready=state.state==='ready',usable=ready||state.state==='error'&&businessConnection;$('business-login').textContent=ready?'切换账号':'登录业务平台';$('business-refresh').disabled=!usable;$('business-logout').disabled=!usable;
  $('connection-status').textContent=ready?'业务数据已连接（文件快照）':state.state==='loading'?'正在核对身份并读取授权数据':connectionMessages[state.code]??'业务服务暂不可用，授权数据已清空';
  if(ready){const session=state.session;apiBusinessState=state.businessState;$('connection-scope').textContent=`账号：${session.subject} · 企业范围：${session.allEnterprises?'全部获准企业':session.enterprises.join('、')||'无企业详情权限'}${session.publicSpatial?' · 可查看公共点位':''}`;refreshBusinessSummary();}
}
async function configureBusinessConnection(){
  const callback=new URL(location.href),hasCallback=['code','state','error'].some(key=>callback.searchParams.has(key));
  if(hasCallback)history.replaceState(null,'',location.pathname);
  let gasFocus=null,gasFocusError=null;try{gasFocus=hasCallback?resumeGasScene(sessionStorage,callback):gasSceneRequest(callback);}catch(error){gasFocusError=error;}
  let configuration;try{configuration=await readPortalConfiguration(fetch,location.origin);}catch(error){configuration={mode:'authenticated'};dataMode='authenticated';clearAuthorizedData();connectionState({state:'error',code:error.code});}
  dataMode=configuration.mode;$('local-file-controls').hidden=dataMode!=='local';$('data-advanced').hidden=dataMode!=='local';
  for(const section of document.querySelectorAll('.business-import'))section.hidden=dataMode!=='local';
  for(const id of ['business-connection','business-login','business-refresh','business-logout'])$(id).hidden=dataMode==='local';
  if(dataMode==='local')return;
  userLayerLoad=userSpatialLoad=userBusinessLoad=true;clearAuthorizedData();
  if(!configuration.oauth){connectionState({state:'signed-out',code:'CONFIG_INVALID'});$('business-login').disabled=true;return;}
  oauthLogin=new OAuthLogin(configuration,{storage:sessionStorage,fetcher:fetch,redirectUri:location.origin+location.pathname});
  businessConnection=new BusinessConnection({onClear:clearAuthorizedData,onState:connectionState,onData:async data=>{
    openDocument(data.document,'业务服务 · 授权空间对象');spatialCatalog=parseSpatialCatalog(data.catalog,'业务服务空间分类');spatialFingerprint=data.catalog.layerFingerprint;
    businessCatalog=data.records?parseBusinessRecords(data.records,'业务服务 · 文件快照'):null;apiBusinessState=data.businessState;rebuildLayerUI();message(`业务数据已更新：${data.document.layers.reduce((n,l)=>n+l.features.length,0)} 个授权对象`);
    if(gasFocusError){gasFocusNotice('气体点位定位请求无效，请返回工作台重试');gasFocusError=null;}
    const currentGasDocument=layersDoc;
    if(gasFocus){const request=gasFocus;gasFocus=null;try{
      const result=await businessConnection.gasPoint(request.id,request.revision,data.datasetVersion,request);
      if(layersDoc!==currentGasDocument)return;
      const target=gasSceneTarget(result,request,layersDoc,data.datasetVersion);
      selectFeature(target.feature,target.layer,'gas-event');locate();
      gasFocusNotice(`已定位气体异常${request.objectId?'周边对象':'关联点位'}：${target.feature.name} · 事件版本 ${request.revision}`);
    }catch(error){gasFocusNotice(error.code==='REVISION_CONFLICT'?'气体异常记录已更新，请返回工作台刷新后再定位':error.code==='POINT_HIDDEN'?'关联点位所在图层已隐藏，请在图层管理中开启后定位':'气体点位定位未完成：'+(connectionMessages[error.code]??'点位不可用或无访问权限'));}}

  }});
  $('business-login').onclick=async()=>{businessConnection.disconnect();try{const authorizationUrl=await oauthLogin.begin();rememberGasScene(sessionStorage,gasFocus,authorizationUrl,location.origin+location.pathname);location.assign(authorizationUrl);}catch(error){connectionState({state:'signed-out',code:error.code});}};
  $('business-refresh').onclick=()=>businessConnection.refresh();
  $('business-logout').onclick=()=>{gasFocus=null;rememberGasScene(sessionStorage,null);oauthLogin.cancel();businessConnection.disconnect();message('已退出当前应用，授权对象与业务详情已清空');};
  $('connection-status').textContent='尚未登录，请登录业务平台';
  if(hasCallback)try{await businessConnection.connect(await oauthLogin.complete(callback));}catch(error){businessConnection.disconnect(error.code??'LOGIN_INVALID');}
  setInterval(()=>{if(document.visibilityState==='visible')businessConnection.check();},15000);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')businessConnection.refresh();});
}

async function boot(){
  if(indexedCutsRequested&&!indexedRootsRequested)throw Error('混合层级实验需要同时启用LEVEL索引');
  await configureBusinessConnection();
  try{const response=await fetch('api/health',{cache:'no-store'});sourcePlansEnabled=response.ok&&supportsSourcePlans(await response.json());}catch{sourcePlansEnabled=false;}telemetry.sourcePlansEnabled=sourcePlansEnabled;
  try{const response=await fetch('api/prepared-textures',{cache:'no-store'});if(!response.ok)throw Error('纹理索引HTTP '+response.status);preparedTextures=new PreparedTextureIndex(await response.json(),location.href);telemetry.preparedTextureCount=preparedTextures.entries.size;telemetry.bc7Supported=supportsPreparedBc7(renderer);console.info('[prepared textures] '+JSON.stringify({indexed:telemetry.preparedTextureCount,supported:telemetry.bc7Supported}));}catch(error){telemetry.preparedTextureNotice='压缩纹理索引不可用，按原JPEG预算加载';telemetry.preparedTextureCount=0;}
  const atlas=new Image();atlas.src='assets/landscape/icons.png';markerAtlas=atlas;
  const catalogBytes=await(await fetch('data/showcase/zhumadian_native_hierarchy.json')).arrayBuffer();catalog=JSON.parse(new TextDecoder().decode(catalogBytes));if(catalog.base_root_count!==2346)throw Error('驻马店基础层目录不完整');telemetry.baseRoots=2346;
  if(indexedRootsRequested){sourceLevelIndex=await loadSourceLevelIndex();const records=new Map(catalog.root_records.map(r=>[r.tile_id,r]));if(records.size!==2346||sourceLevelIndex.index.records.some(r=>{const b=records.get(r.tile);return !b||b.bounds_min.some((v,a)=>v<r.boundsMin[a]-1e-7||b.bounds_max[a]>r.boundsMax[a]+1e-7);}))throw Error('LEVEL索引与基础地景范围不一致');telemetry.levelIndexIdentity=sourceLevelIndex.identity;telemetry.levelIndexRootCount=sourceLevelIndex.index.records.length;telemetry.levelIndexMode=indexedCutsRequested?'root_bvh_indexed_descendants_coverage':'root_bvh_direct_families';}
  await frameProfile.measureAsync('startup_context_wait',()=>loadModel('assets/showcase/runtime/zhumadian/context/context_fused.gltf',contextGroup,'卫片地形'));startupProfile.mark('context_model_ready');telemetry.context=true;
  const loaded=await frameProfile.measureAsync('startup_base_wait',()=>loadModel('assets/showcase/runtime/zhumadian/full/zhumadian_full.gltf',photoGroup,'完整倾斜摄影基础层',true));startupProfile.mark('base_model_ready');loaded.scene.traverse(n=>{if(n.isMesh){base=n;n.userData.photoMaterial=n.material;}});if(!base||base.geometry.index.count!==9166851)throw Error('驻马店基础层几何数量不符');telemetry.photo=true;$('loading').style.display='none';message('基础地景已加载，正在准备近景细节');
  const sourceTexture=base.userData.photoMaterial.map.source.data,qualityStart=performance.now();
  const digest=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),value=>value.toString(16).padStart(2,'0')).join('');
  const qualityTask=resolveBaseQuality({catalog,catalogBytes,gltf:loaded.parser.json,buffer:()=>loaded.parser.getDependency('buffer',0),geometry:{positions:base.geometry.attributes.position.array,indices:base.geometry.index.array,uvs:base.geometry.attributes.uv.array,textureWidth:sourceTexture.width,textureHeight:sourceTexture.height},digest,fetchPrepared:async()=>{
    const response=await fetch('assets/showcase/runtime/zhumadian/full/base_lod_quality.json');if(!response.ok||Number(response.headers.get('Content-Length'))>1048576)throw Error('prepared quality unavailable');const raw=await response.arrayBuffer();if(raw.byteLength>1048576)throw Error('prepared quality oversized');return JSON.parse(new TextDecoder().decode(raw));
  }}).then(quality=>{baseEdges=quality.edges;baseTexels=quality.texels;telemetry.ready=true;startupProfile.mark('base_quality_ready');telemetry.baseQualitySource=quality.source;telemetry.baseQualityMs=performance.now()-qualityStart;console.info('[base quality] '+JSON.stringify({source:quality.source,milliseconds:telemetry.baseQualityMs,roots:baseEdges.size}));message('驻马店地景已加载：倾斜摄影与卫片底景');});
  const initialLayers=(async()=>{if(dataMode==='local'&&!userLayerLoad){try{await reload();}catch(error){if(!userLayerLoad)await layerLoading.load(async()=>{const response=await fetch('layers/sample.json');if(!response.ok)throw error;return response.json();},doc=>openDocument(doc,'图层示例（可用编辑端重新绘制）'));}}})();
  await Promise.all([qualityTask,initialLayers]);
  reloadSpatial(true).catch(error=>spatialNotice(error.message));
  reloadBusinessRecords(true).catch(error=>businessNotice(`发布台账读取失败：${error.message}`));
}
if(staticOnlyQA){const button=document.createElement('button');button.textContent='释放静态验收资源';button.style.cssText='position:absolute;top:95px;left:300px;z-index:30';button.onclick=()=>{telemetry.ready=false;const geometries=new Set(),materials=new Set(),textures=new Set();for(const group of [photoGroup,contextGroup]){group.traverse(n=>{if(n.isMesh){geometries.add(n.geometry);for(const m of Array.isArray(n.material)?n.material:[n.material]){materials.add(m);if(m.map)textures.add(m.map);}}});group.clear();}for(const g of geometries)g.dispose();for(const t of textures){t.dispose();t.image?.close?.();}for(const m of materials)m.dispose();button.disabled=true;message('静态验收资源已释放');};viewport.append(button);}
const startupWitness=new FixedFrameWitness({enabled:new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('witness')==='1'}),witnessImages=new Map();let witnessPanel=null;
if(startupWitness.enabled){const section=document.createElement('section'),title=document.createElement('h3'),pre=document.createElement('pre');title.textContent='固定时刻加载验收（5 / 20 / 40秒）';pre.dataset.testid='startup-witness-json';pre.style.cssText='white-space:pre-wrap;font-size:10px;max-height:240px;overflow:auto';section.append(title,pre);$('information').append(section);witnessPanel={section,pre};window.addEventListener('pagehide',()=>{for(const value of witnessImages.values())URL.revokeObjectURL(value.url);});}
function publishStartupWitness(){if(witnessPanel)witnessPanel.pre.textContent=JSON.stringify(startupWitness.snapshot(),null,2);}
function captureStartupWitness(record){const requested=performance.now(),filename=`zhumadian_${record.targetMs/1000}s_scene.png`;record.imageStatus='pending';record.imageFile=filename;record.imageRequestedElapsedMs=requested;
 try{renderer.domElement.toBlob(blob=>{if(!blob||blob.size>8*1048576){record.imageStatus='failed_or_oversized';publishStartupWitness();return;}const url=URL.createObjectURL(blob),image=document.createElement('img'),link=document.createElement('a');image.src=url;image.alt=`${record.targetMs/1000}秒三维画面`;image.dataset.testid='startup-witness-image-'+record.targetMs;image.style.cssText='width:100%;height:auto';link.href=url;link.download=filename;link.textContent=`下载${record.targetMs/1000}秒画面`;witnessPanel.section.append(link,image);witnessImages.set(record.targetMs,{url});record.imageStatus='ready';record.imageBytes=blob.size;publishStartupWitness();},'image/png');}catch(error){record.imageStatus='failed';}
 const data={balancedRegions,observedUTC:new Date().toISOString(),visibilityState:document.visibilityState,staticUploadConcurrency,sourcePreparationConcurrency,preserveWantedRoots,sourceBudgetEvents:sourceBudgetEvents.map(e=>({...e})),viewport:{width,height},camera:camera.position.toArray(),target:controls.target.toArray(),context:telemetry.context,photo:telemetry.photo,ready:telemetry.ready,presentation:{photoEnabled:$("photo").checked,photoOpacity:sceneOpacity("photo"),terrainEnabled:$("satellite").checked,terrainOpacity:sceneOpacity("satellite")},baseQualitySource:telemetry.baseQualitySource??null,indexIdentity:telemetry.levelIndexIdentity??null,desiredRoots:telemetry.nativeDesired??0,errorCount:telemetry.errors.length,errors:telemetry.errors.slice(-16),lastSourceResponse:telemetry.lastSourceResponse??null,coverageChecks:telemetry.coverageChecks??0,coverageRejections:telemetry.coverageRejections??0,restoreErrors:telemetry.restoreErrors??0,pageBudget:pageBudget.snapshot(),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,roots:[...resident].map(([id,r])=>({id,depth:r.frontier?.maxDepth??r.depth,bytes:r.bytes,visible:[...r.frontier.visible]})),frame:frameProfile.snapshot()};
 if(base&&catalog&&telemetry.photo){const rasterWidth=96,rasterHeight=Math.max(16,Math.round(rasterWidth*height/width));if(rasterWidth*rasterHeight>65536)throw Error('Witness viewport exceeds diagnostic raster bound');const diagnostic=new SourceVisibility(renderer,scene,contextGroup),savedInfo={...renderer.info.render};try{const obscured=sourceOcclusionRects();data.obscured=obscured;data.visibility=diagnostic.sample({camera,width,height,base,catalog,residents:resident,obscured,baseQuality:{edges:baseEdges,texels:baseTexels}});data.grid=visibilityWitnessGrid({samples:diagnostic.visibleSnapshot.samples,width,height,rasterWidth,rasterHeight,obscured,metrics:diagnostic.visibleSnapshot.metrics,fov:camera.fov});data.fullCanvasGrid=visibilityWitnessGrid({samples:diagnostic.visibleSnapshot.samples,width,height,rasterWidth,rasterHeight,metrics:diagnostic.visibleSnapshot.metrics,fov:camera.fov});if(residencyAuditEnabled){data.residency=captureSourceResidency({residents:resident,samples:diagnostic.visibleSnapshot.samples,width,height,obscured,ledger:pageBudget.snapshot()});data.rejectedProbes=residencyRejectedProbes.map(v=>({...v}));data.allocationScan={...allocationScanStats};}}finally{diagnostic.dispose();Object.assign(renderer.info.render,savedInfo);}}
 else data.gridStatus='base_not_ready';return data;
}
function animate(now){requestAnimationFrame(animate);frameProfile.frame(now);frameProfile.measure('frame_cpu',()=>{if(!signDrag?.moved)frameProfile.measure('orbit',()=>orbitActivity.update());frameProfile.measure('render_submit',()=>sceneGpuTimer.measure(()=>startupProfile.render(renderer.getContext(),()=>renderer.render(scene,camera),()=>({context:telemetry.context,photo:telemetry.photo,ready:telemetry.ready,contextImages:contextGroup.children.flatMap(group=>{const images=[];group.traverse(n=>{if(n.isMesh&&n.material.map)images.push({width:n.material.map.image?.width,height:n.material.map.image?.height,type:n.material.map.image?.constructor?.name});});return images;})}))));frameProfile.measure('annotations',drawAnnotations);if(startupWitness.enabled){const count=startupWitness.records.length;startupWitness.tick(performance.now(),captureStartupWitness);if(startupWitness.records.length!==count)publishStartupWitness();}frames++;if(now-frameClock>1000){$('command-clock').textContent=new Date().toLocaleTimeString('zh-CN',{hour12:false});fps=frames*1000/(now-frameClock);frames=0;frameClock=now;$('status').textContent=`${Math.round(fps)} FPS · 2346 基础瓦片 · 细层 ${resident.size}/${telemetry.nativeDesired??0} 块 / ${Math.round(telemetry.nativeBytes/1048576)} MiB · 已加载最高层级 ${resident.size?Math.max(...[...resident.values()].map(r=>r.frontier?.maxDepth??r.depth)):"基础层"}`;}
  if(now-lastRank>700&&telemetry.ready&&!staticOnlyQA){lastRank=now;frameProfile.measure('maintain',maintain);}continueAllocationScan();});if(frameProfile.enabled&&now-lastProfilePublish>1000){lastProfilePublish=now;publishFrameProfile();}}
requestAnimationFrame(animate);if(new URLSearchParams(location.search).get('qa')==='1'&&new URLSearchParams(location.search).get('bitmapQA')==='1')installOriginalImageQA(viewport);else boot().catch(error=>{$('loading').style.display='none';fail(error);});
// Read-only QA observation and reproducible camera controls; no private files.
window.hongtuViewer={telemetry,validate,openDocument,preset,locate,get document(){return layersDoc;},get selected(){return selected;},get residents(){return [...resident].map(([id,r])=>({id,depth:r.depth,parts:r.marker.parts.length}));},get camera(){return camera.position.toArray();}};
