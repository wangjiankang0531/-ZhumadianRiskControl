import {referenceCommandURL} from './reference-deployment.js';

export function referenceRoute(hash, catalog) {
 const route=String(hash||'').replace(/^#/, '');
 return route==='dashboard'||catalog.some(m=>m.id===route)?route:'home';
}
export function homeShortcuts(catalog) {
 const entries=[['双重预防','risk-unit'],['智能巡检','inspection-task'],['特殊作业','special-work'],['重大危险源','major-hazard'],['应急处置','events'],['我的待办','approval-todo']];
 return entries.filter(([,id])=>id==='dashboard'||catalog.some(m=>m.id===id));
}
const artwork={
 navigation:'<rect x="48" y="42" width="116" height="94" rx="8"/><rect x="68" y="25" width="116" height="94" rx="8"/><path d="M88 56h58M88 75h72M88 94h44"/>',
 links:'<path d="m110 18 48 28v55l-48 28-48-28V46zM62 46l48 28 48-28M110 74v55"/><path d="m143 87 33 19v38l-33 19-33-19v-38z"/>',
 scan:'<rect x="52" y="31" width="116" height="93" rx="9"/><path d="M72 99V77m23 22V62m23 37V48m23 51V69"/><circle cx="157" cy="116" r="24"/><path d="m174 134 22 22"/>'
};
function illustration(kind) {
 const node=document.createElement('div');node.className='home-art';node.setAttribute('aria-hidden','true');
 node.innerHTML='<svg viewBox="0 0 230 190" fill="none" xmlns="http://www.w3.org/2000/svg"><path class="home-plinth" d="m115 102 100 42-100 42L15 144z"/><g class="home-artwork">'+artwork[kind]+'</g></svg>';
 return node;
}
export function renderReferenceHome({app,deployment,catalog,el,anchor,button,logout}) {
 app.className='reference-home';
 const header=el('header','home-header'),brand=anchor('园区风险防控','#home','home-brand');
 header.append(brand,el('h1','','驻马店高新开发区重大风险防控平台'));
 const account=el('div','home-account');account.append(el('span','',deployment?.mode==='public-business'?'欢迎，'+deployment.user:'独立模拟验收'));
 if(deployment?.mode==='public-business')account.append(button('退出登录',logout,'home-logout'));
 header.append(account);
 const main=el('main','home-main'),intro=el('div','home-intro');intro.append(el('span','home-eyebrow','RISK PREVENTION · EMERGENCY RESPONSE'),el('p','','一体化业务协同 · 园区风险防控 · 三维应急指挥'));main.append(intro);
 const cards=el('div','home-cards');
 function card(kind,title,desc){const n=el('section','home-card home-card-'+kind);n.append(illustration(kind),el('h2','',title),el('p','home-card-desc',desc));cards.append(n);return n;}
 function entry(text,href,local=false){const a=anchor(' ',href,'home-entry');a.replaceChildren(el('span','',text),el('span','home-arrow','➤'));if(local){a.target='_blank';a.rel='noopener noreferrer';a.append(el('small','','本机三维场景 ↗'));}return a;}
 const systems=card('navigation','系统导航','业务管理与本地三维协同入口'),systemLinks=el('nav','home-system-links');systemLinks.setAttribute('aria-label','系统导航');
 systemLinks.append(entry('安全风险智能管控平台','#dashboard'),entry('敏捷应急管理','#events'),entry('敏捷应急指挥',referenceCommandURL(deployment),true));systems.append(systemLinks,el('p','home-local-note','三维指挥使用当前电脑的本地地景，请先启动本地场景服务。'));
 const quick=card('links','快捷链接','常用业务，快速抵达'),quickLinks=el('nav','home-quick-links');quickLinks.setAttribute('aria-label','快捷链接');for(const [text,id] of homeShortcuts(catalog))quickLinks.append(entry(text,'#'+id));quick.append(quickLinks);
 const scan=card('scan','浏览器扫码','在其他设备打开公网业务测试'),qr=el('img','home-qr');qr.src=new URL('home-access-qr.svg',new URL('./',location.href)).href;qr.alt='公网模拟业务测试入口二维码';qr.width=220;qr.height=220;
 scan.append(qr,anchor('打开公网测试入口','https://www.joinlinksmart.com/zhumadian/','home-scan-link'),el('p','home-scan-note','扫码后使用分配的测试账号登录。三维地景在本地测试电脑运行。'));
 main.append(cards);
 const footer=el('footer','home-footer');footer.append(el('span','','模拟业务测试环境 · 仅使用合成业务样本'),el('span','','重大风险防控 · 应急协同'));
 app.replaceChildren(header,main,footer);
}
