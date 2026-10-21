import {referenceCommandURL,referenceSceneURL} from './reference-deployment.js';

export function referenceRoute(hash, catalog) {
 const route=String(hash||'').replace(/^#/, '');
 return route==='dashboard'||catalog.some(m=>m.id===route)?route:'home';
}
export function homeShortcuts(catalog) {
 const entries=[['双重预防','risk-unit'],['智能巡检','inspection-task'],['特殊作业','special-work'],['重大危险源','major-hazard'],['应急处置','events'],['业务工作台','dashboard']];
 return entries.filter(([,id])=>id==='dashboard'||catalog.some(m=>m.id===id));
}
const artwork={
 navigation:'<rect x="48" y="42" width="116" height="94" rx="8"/><rect x="68" y="25" width="116" height="94" rx="8"/><path d="M88 56h58M88 75h72M88 94h44"/>',
 links:'<path d="m110 18 48 28v55l-48 28-48-28V46zM62 46l48 28 48-28M110 74v55"/><path d="m143 87 33 19v38l-33 19-33-19v-38z"/>',
 scene:'<rect x="52" y="31" width="116" height="93" rx="9"/><path d="M72 99V77m23 22V62m23 37V48m23 51V69"/><circle cx="157" cy="116" r="24"/><path d="m174 134 22 22"/>'
};
function illustration(kind) {
 const node=document.createElement('div');node.className='home-art';node.setAttribute('aria-hidden','true');
 node.innerHTML='<svg viewBox="0 0 230 190" fill="none" xmlns="http://www.w3.org/2000/svg"><path class="home-plinth" d="m115 102 100 42-100 42L15 144z"/><g class="home-artwork">'+artwork[kind]+'</g></svg>';
 return node;
}
export function renderReferenceHome({app,deployment,catalog,el,anchor,button,logout}) {
 app.className='reference-home';
 const header=el('header','home-header'),brand=anchor('园区风险防控','#home','home-brand');
 const frame=el('div','home-title-frame');frame.append(el('div','home-eyebrow','INTEGRATED RISK CONTROL'),el('h1','','驻马店高新开发区重大风险防控'));header.append(brand,frame);
 const account=el('div','home-account');account.append(el('span','',deployment?.mode==='public-business'?'欢迎，'+deployment.user:'独立模拟验收'));
 if(deployment?.mode==='public-business')account.append(button('退出登录',logout,'home-logout'));
 header.append(account);
 const main=el('main','home-main'),intro=el('div','home-intro');intro.append(el('p','','一体化业务协同 · 园区风险防控 · 三维应急指挥'));main.append(intro);
 const cards=el('div','home-cards');
 function card(kind,title,desc){const n=el('section','home-card home-card-'+kind);n.append(illustration(kind),el('h2','',title),el('p','home-card-desc',desc));cards.append(n);return n;}
 function entry(text,href,local=false){const a=anchor(' ',href,'home-entry');a.replaceChildren(el('span','',text),el('span','home-arrow','➤'));if(local){a.target='_blank';a.rel='noopener noreferrer';a.append(el('small','','本机三维场景 ↗'));}return a;}
 const systems=card('navigation','系统导航','业务管理与本地三维协同入口'),systemLinks=el('nav','home-system-links');systemLinks.setAttribute('aria-label','系统导航');
 systemLinks.append(entry('安全风险智能管控平台','#dashboard'),entry('敏捷应急管理','#events'),entry('敏捷应急指挥',referenceCommandURL(deployment),true));systems.append(systemLinks,el('p','home-local-note','三维指挥使用当前电脑的本地地景，请先启动本地场景服务。'));
 const quick=card('links','快捷链接','常用业务，快速抵达'),quickLinks=el('nav','home-quick-links');quickLinks.setAttribute('aria-label','快捷链接');for(const [text,id] of homeShortcuts(catalog))quickLinks.append(entry(text,'#'+id));quick.append(quickLinks);
 const scene=card('scene','园区三维场景','驻马店实景地景 · 编辑图层同步'),graphic=el('div','home-scene-illustration');graphic.setAttribute('aria-hidden','true');
 graphic.innerHTML='<svg viewBox="0 0 210 160" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M8 112 90 40 200 91 117 153Z M23 112 93 52 186 93 116 140Z M8 112v8l109 40 83-61v-8 M46 96 152 125 M73 73 177 105 M62 135 139 73 M91 146 169 86 M76 80V57l22-14 23 12v24L99 95Z M76 57l23 14 22-16 M99 71v24 M124 112V88l22-14 21 10v24l-21 14Z M124 88l22 12 21-16 M146 100v22"/></svg>';
 const sceneURL=new URL(referenceSceneURL(deployment));
 scene.append(graphic,el('p','home-scene-note','点线面选择 / 分层浏览 / 近景细节'),entry('进入园区一张图',sceneURL.href,true));
 main.append(cards);
 const footer=el('footer','home-footer');footer.append(el('span','','模拟业务测试环境 · 仅使用合成业务样本'),el('span','','重大风险防控 · 应急协同'));
 app.replaceChildren(header,main,footer);
}
