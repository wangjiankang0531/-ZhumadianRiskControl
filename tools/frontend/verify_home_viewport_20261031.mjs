import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import { spawn } from 'node:child_process';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';

const sourceDir = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
if (!process.argv[2]) throw Error('EXPLICIT_OWN_LAYOUT_OUTPUT_REQUIRED');
const root = path.resolve(process.argv[2]);
await fs.mkdir(root, { recursive: true });
const sourceRoot = 'D:/Project/Zhumadian/Application/work/tianjin_native_20261023/security_pc';
const referenceRoot = 'D:/Project/Zhumadian/Reference/02安全风险管控平台/代码及开发环境搭建移交资料/源码包/安全风险管控平台前台代码/security-risk-web';
const require = createRequire(sourceRoot + '/package.json');
const source = await fs.readFile(sourceRoot + '/src/views/home/index.vue', 'utf8');
const reference = await fs.readFile(referenceRoot + '/src/views/home/index.vue', 'utf8');
if (source !== reference) throw Error('PRISTINE_HOME_SOURCE_REQUIRED');
const descriptor = require('@vue/compiler-sfc').parse(source).descriptor;
const scss = require('sass').compileString(descriptor.styles[0].content).css;
const originalCSS = require('@vue/compiler-sfc').compileStyle({source:scss,filename:'home.vue',id:'data-v-home-probe',scoped:true}).code.replaceAll('@/assets/', '/assets/');
const candidateCSS = await fs.readFile(sourceDir + '/home-viewport.css', 'utf8');
const template = descriptor.template.content.replaceAll('@/assets/', '/assets/').replaceAll('天津南港危化品智慧物流综合服务中心', '驻马店重大风险防控');
const groups = [['安全风险智能管控平台', '敏捷应急管理', '敏捷应急指挥'], ['双重预防', '智能巡检', '特殊作业', '重大危险源', '应急处置', '我的待办']];
const html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>html,body,#app{margin:0;min-height:100%;}body{font-family:Arial,"Microsoft YaHei",sans-serif;line-height:1.5;font-size:14px;}@font-face{font-family:YouSheBiaoTiHei;src:url("/assets/fonts/YouSheBiaoTiHei.ttf")}</style><link rel="stylesheet" href="/original.css"><link rel="stylesheet" href="/candidate.css"></head><body><div id="app"></div><script type="module">import {createApp} from "/vue.js";createApp({__scopeId:"data-v-home-probe",template:' + JSON.stringify(template) + ',data(){return {nav_link:null,userStore:{info:{userName:"布局验收"}},nav_list1:' + JSON.stringify(groups[0].map(fullName => ({ fullName }))) + ',nav_list2:' + JSON.stringify(groups[1].map(fullName => ({ fullName }))) + '}},methods:{handleTo(){},handleLogout(){}}}).mount("#app");</script></body></html>';
let candidate = false;
const server = http.createServer(async (req, res) => {
  try {
    const u = new URL(req.url, 'http://localhost');
    let body, type = 'application/octet-stream';
    if (u.pathname === '/') { body = html; type = 'text/html; charset=utf-8'; }
    else if (u.pathname === '/original.css') { body = originalCSS; type = 'text/css'; }
    else if (u.pathname === '/candidate.css') { body = candidate ? candidateCSS : ''; type = 'text/css'; }
    else if (u.pathname === '/vue.js') { body = await fs.readFile(sourceRoot + '/node_modules/vue/dist/vue.esm-browser.prod.js'); type = 'text/javascript'; }
    else if (u.pathname === '/qrcode.png') { body = await fs.readFile('D:/Zqa20261025/Application/frontend/security_pc/qrcode.png'); type = 'image/png'; }
    else if (u.pathname.startsWith('/assets/')) {
      const assetRoot = path.resolve(sourceRoot + '/src/assets');
      const asset = path.resolve(assetRoot, decodeURIComponent(u.pathname.slice(8)));
      if (!asset.startsWith(assetRoot + path.sep)) throw Error('ASSET_SCOPE');
      body = await fs.readFile(asset);
      type = asset.endsWith('.png') ? 'image/png' : asset.endsWith('.ttf') ? 'font/ttf' : 'application/octet-stream';
    } else { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
    res.end(body);
  } catch { res.writeHead(404); res.end(); }
});
await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
const base = 'http://127.0.0.1:' + server.address().port;
const profile = root + '/layout-chrome-profile';
let chrome, ws, session, seq = 0;
const pending = new Map();
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
async function until(fn, timeout = 20000) {
  const end = Date.now() + timeout;
  while (!await fn()) {
    if (Date.now() > end) throw Error('LAYOUT_WAIT_TIMEOUT');
    await sleep(40);
  }
}
function send(method, params = {}, sessionId) {
  return new Promise((resolve, reject) => {
    const id = ++seq;
    const timer = setTimeout(() => { pending.delete(id); reject(Error('CDP_TIMEOUT_' + method)); }, 12000);
    pending.set(id, { resolve: value => { clearTimeout(timer); resolve(value); }, reject });
    ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
}
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, session);
  if (result.exceptionDetails) throw Error('LAYOUT_EVALUATION_FAILED');
  return result.result.value;
}
const measure = '(' + (() => {
  const width = innerWidth, height = innerHeight;
  const entries = Array.from(document.querySelectorAll('.menu-item'));
  const fits = element => {
    const r = element.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.left >= -1 && r.top >= -1 && r.right <= width + 1 && r.bottom <= height + 1;
  };
  return {
    width, height, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight,
    menuCount: entries.length, allMenusInViewport: entries.every(fits),
    allMenusHitTest: entries.every(e => { const r = e.getBoundingClientRect(); return e.contains(document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2)); }),
    noLabelsClipped: entries.every(e => { const label = e.querySelector('.menu-item_label'); return label.scrollWidth <= label.clientWidth + 1; }),
    qrInViewport: fits(document.querySelector('.qr-code')),
    titleInViewport: fits(document.querySelector('header .title')),
  };
}).toString() + ')()';
const results = [];
let baseline;
try {
  chrome = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', '--no-first-run', '--no-default-browser-check', '--no-proxy-server', '--disable-background-networking', '--disable-gpu', '--remote-debugging-port=0', '--user-data-dir=' + profile, 'about:blank'], { windowsHide: true, stdio: 'ignore' });
  let active;
  await until(async () => { try { active = (await fs.readFile(profile + '/DevToolsActivePort', 'utf8')).trim().split('\n'); return true; } catch { return false; } });
  ws = new WebSocket('ws://127.0.0.1:' + active[0] + active[1]);
  await new Promise((resolve, reject) => { ws.addEventListener('open', resolve, { once: true }); ws.addEventListener('error', reject, { once: true }); });
  ws.addEventListener('message', event => {
    const message = JSON.parse(event.data);
    if (message.id) {
      const callback = pending.get(message.id);
      pending.delete(message.id);
      if (callback) message.error ? callback.reject(Error('CDP_ERROR')) : callback.resolve(message.result);
    }
  });
  const target = await send('Target.createTarget', { url: 'about:blank' });
  session = (await send('Target.attachToTarget', { targetId: target.targetId, flatten: true })).sessionId;
  await send('Runtime.enable', {}, session);
  await send('Page.enable', {}, session);
  await send('Emulation.setDeviceMetricsOverride', { width: 1536, height: 704, deviceScaleFactor: 1.25, mobile: false }, session);
  await send('Page.navigate', { url: base }, session);
  await until(() => evaluate('document.querySelectorAll(".menu-item").length===9 && Array.from(document.images).every(x=>x.complete&&x.naturalWidth>0) && document.fonts.status==="loaded"'));
  baseline = await evaluate(measure);
  if (baseline.scrollHeight <= baseline.height) throw Error('REPORTED_HOME_OVERFLOW_NOT_REPRODUCED');
  const before = await send('Page.captureScreenshot', { format: 'png' }, session);
  await fs.writeFile(root + '/home-before-1536x704.png', Buffer.from(before.data, 'base64'));
  candidate = true;
  await send('Page.reload', { ignoreCache: true }, session);
  await until(() => evaluate('document.querySelectorAll(".menu-item").length===9 && Array.from(document.images).every(x=>x.complete&&x.naturalWidth>0) && document.fonts.status==="loaded"'));
  if (!await evaluate('document.querySelectorAll(".menu-item[data-v-home-probe]").length===9')) throw Error('ORIGINAL_SCOPED_STYLE_REQUIRED');
  for (const [width, height, dpr] of [[1536,704,1.25],[1920,1080,1],[1366,650,1],[1280,600,1],[1024,576,1],[960,480,1],[1920,880,1]]) {
    await send('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: dpr, mobile: false }, session);
    await sleep(150);
    const point = await evaluate('(()=>{const r=document.querySelector(".menu-item").getBoundingClientRect();return{x:r.left+r.width/2,y:r.top+r.height/2}})()');
    await send('Input.dispatchMouseEvent', {type:'mouseMoved',x:point.x,y:point.y}, session);
    await sleep(350);
    const row = await evaluate(measure);
    row.hoverAndScopedCSSChecked = true;
    row.passed = row.menuCount === 9 && row.scrollWidth <= row.width + 1 && row.scrollHeight <= row.height + 1 && row.allMenusInViewport && row.allMenusHitTest && row.noLabelsClipped && row.qrInViewport && row.titleInViewport;
    results.push(row);
    if ([1536,960].includes(width)) {
      const shot = await send('Page.captureScreenshot', { format: 'png' }, session);
      await fs.writeFile(root + '/home-after-' + width + 'x' + height + '.png', Buffer.from(shot.data, 'base64'));
    }
    if (!row.passed) throw Error('HOME_VIEWPORT_REJECTED_' + width + 'x' + height);
  }
  console.log('HOME_VIEWPORT_LAYOUT_PASSED_' + results.length);
} finally {
  if (ws?.readyState === WebSocket.OPEN) { try { await send('Browser.close'); } catch {} ws.close(); }
  if (chrome) await until(() => chrome.exitCode !== null, 15000);
  await new Promise(resolve => server.close(resolve));
  const report = {
    sourceHomeSha256: createHash('sha256').update(source).digest('hex'),
    candidateCSSSha256: createHash('sha256').update(candidateCSS).digest('hex'),
    actualOriginalHomeTemplateAndSCSS: true, originalVueScopedCSSApplied: true, syntheticNineMenus: true,
    originalBusinessScriptOrAuthenticationExercised: false,
    independentLocalBrowserOnly: true, liveViewportChangesWithoutPageReload: true,
    baseline, candidateResults: results, passed: results.length === 7 && results.every(x => x.passed),
    chromeExitCode: chrome?.exitCode, normalBrowserClosed: chrome?.exitCode === 0,
    formalOrPublicApplicationChanged: false, originalSheetChanged: false,
  };
  await fs.writeFile(root + '/home-viewport-layout-result.json', JSON.stringify(report, null, 2));
}
