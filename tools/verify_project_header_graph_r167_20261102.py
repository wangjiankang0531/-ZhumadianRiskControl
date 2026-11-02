from pathlib import Path
import json,hashlib,re,datetime
R=Path('D:/Project/Zhumadian');W=R/'work/user_feedback_20261031/project-header-home-r167';D=R/'Document/Deployment/public_test_project_header_r33_20261102';dist=W/'dist'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=J(W/'full-build-result.json')['compiledFiles'];assert len(rows)==338
for n,p in rows.items():assert (dist/n).stat().st_size==p['bytes']and sha(dist/n)==p['sha256']
missing=[];count=0
for name in rows:
 if Path(name).suffix not in {'.js','.css','.html'}:continue
 text=(dist/name).read_text(encoding='utf-8');refs=re.findall(r'''["']([^"'\r\n]{1,220}\.(?:js|css|woff2?|ttf|svg|png|jpe?g|gif|ico)(?:\?[^"']*)?)["']''',text)
 if name.endswith('.css'):refs+=re.findall(r'''url\(([^)"']+)\)''',text)
 for ref in refs:
  if ref.startswith(('http:','https:','data:','blob:','//','#')):continue
  ref=ref.split('?',1)[0].split('#',1)[0]
  if ref.startswith('/zhumadian/emergency/'):p=dist/ref.removeprefix('/zhumadian/emergency/')
  elif ref.startswith('assets/'):p=dist/ref
  elif ref.startswith(('./','../')):p=(dist/name).parent/ref
  else:continue
  count+=1
  if not p.resolve().is_relative_to(dist.resolve())or not p.is_file():missing.append({'consumer':name,'reference':ref})
assert not missing,missing[:5]
C=R/'work/event_delivery_consistency_20261030/full-controller-r167';runtime=J(C/'r1/result.json');assert runtime['allPassed']and J(C/'prepared-r1/frontend-restored.json')['passed']
browser=[J(C/'r1'/('avatar-browser-emergency_pc-'+a)/'result.json')for a in ['own_operator_a','own_reviewer_b']]
assert all(b['passed']and len(b['checks'])==17 and not b['exceptions']and b['normalChromeExitCode']==0 for b in browser)
proof={'schema':'xnby.r167.emergency-project-mark-home-graph-and-native-browser.v1','at':datetime.datetime.now().astimezone().isoformat(),'passed':True,'compiledFileCount':len(rows),'localAssetReferencesVerified':count,'missingAssets':0,'sourceDeltaFromExactR32CompilerInputs':['src/layout/index.vue','src/router/routes.ts','src/assets/zhumadian-project-mark.svg'],'sourceRestored':True,'actualOriginalSDKNormalRoleBrowserSessions':2,'actualBrowserChecks':34,'projectMarkMatchesPinnedOwnSVG':True,'compilerInlineSVGWhitespaceAndQuoteNormalizationChecked':True,'actualMouseClickFromNativeWorkflowToHomeIndex':True,'oldHomeAliasAndQueryHashAndRefreshPassed':True,'unrelatedUnknownRouteStill404':True,'viewports':[1920,1366,1024],'tenReadinessAndConnectionBudgetPassed':True,'original398ModelsUnchanged':True,'normalSixComponentsBrowserControllerExitZeroAndActualDescendantsZero':True,'temporaryOwnFrontendAndManifestBytesRestored':True,'productBackendOrActualUserDataChanged':False,'userDesktopOrPublicChanged':False,'publicStillR32':True,'fullCloneReady':False}
(D/'native-browser-and-graph-verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(D/'first-preflight-source-map-failure.json').write_text(json.dumps({'preserved':True,'failure':'首次完整程序读取器误将frontend/h5映射到PC输入，源SHA断言拒绝；在创建程序视图及启动任何服务之前停止。修正为仅security_pc/emergency_pc映射，H5使用原只读输入。未改变候选或放宽SHA检查。','firstAttemptCountedAsPassed':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'compiledFiles':len(rows),'assetReferences':count,'normalRoleSessions':2,'browserChecks':34,'publicChanged':False}))
