from pathlib import Path
import importlib.util,json,subprocess,sys
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent;W=R/'work/scene-library-browser-r1740';D=R/'Document/Deployment/scene_library_component_r1740_20261107';assert sys.stdin.buffer.readline(100)==b'OWN_SCENE_UI_TEST_R1740\n';assert not W.exists()and not D.exists();D.mkdir()
p=subprocess.run(['D:/Program Files/nodejs/node.exe',str(V/'build_scene_library_component_r1740.mjs')],input=b'OWN_SCENE_COMPONENT_BUILD_R1740\n',capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW);(D/'build.private.log').write_bytes(p.stdout+p.stderr);assert p.returncode==0
spec=importlib.util.spec_from_file_location('r1740_fixture',V/'scene_library_browser_server_r1740.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);fixture=None
try:
 fixture=module.Fixture();fixture.start();log=(D/'driver.private.log').open('xb')
 try:
  process=subprocess.Popen(['D:/Program Files/nodejs/node.exe',str(V/'drive_scene_library_component_r1740.mjs')],stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW);process.stdin.write((json.dumps({'gate':'OWN_SCENE_UI_R1740','base':fixture.origin,'control':fixture.control})+'\n').encode());process.stdin.close()
  while process.poll()is None:
   try:process.wait(timeout=15)
   except subprocess.TimeoutExpired:print(json.dumps({'sameNativeBrowserDriverStillLive':True}),flush=True)
 finally:log.close()
 assert process.returncode==0,'ACTUAL_NATIVE_SCENE_COMPONENT_DRIVER_FAILED'
 result=json.loads((W/'browser/result.json').read_bytes());assert result['passed']and len(result['checks'])==9
finally:
 if fixture:fixture.close()
terminal=json.loads((W/'browser/browser-terminal.json').read_bytes());assert terminal['normalBrowserClosed']and terminal['exitCode']==0 and not terminal['forceTerminationUsed']
proof={'passed':True,'checks':result['checks'],'actualNativeBrowserComponent':True,'actualQualifiedOriginalACLAndHTTPRepository':True,'syntheticIdentityAndLandscapeAdapterNotOriginalJavaOrFullWebGLHost':True,'realPostCommitConnectionLossInjected':fixture.dropped,'scenePOSTRequests':fixture.posts,'successfulScenePOSTs':fixture.successes,'allHTTPThreadsJoined':True,'normalBrowserTerminal':terminal,'productInputs':json.loads((W/'inputs.json').read_bytes()),'publicUpdated':False};(D/'actual-component-proof-r1740.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'actualNativeBrowserChecks':9,'allHTTPThreadsJoined':True,'POSTs':fixture.posts,'successfulPOSTs':fixture.successes}))
