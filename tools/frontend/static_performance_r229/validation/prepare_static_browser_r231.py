from pathlib import Path
V=Path(__file__).resolve().parent
s=(V/'verify_static_transport_r230.py').read_text(encoding='utf-8')
s=s.replace("O=V/'static-transport-r230'","O=V/'static-transport-r231'")
needle="dump(gateway/'results.json',{'elapsedSeconds':round(time.monotonic()-started,3),'cases':rows})"
assert s.count(needle)==1
s=s.replace(needle,needle+'''
   browserlog=(gateway/'browser-driver.log').open('wb')
   browser=subprocess.Popen(['node',str(V/'measure_static_browser_r231.mjs'),gateway.as_posix(),mode],stdout=browserlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
   browserjob=OwnedWindowsJob(browser)
   browser.wait(timeout=180)
   end=time.monotonic()+8
   while browserjob.active_processes() and time.monotonic()<end:time.sleep(.1)
   active=browserjob.active_processes();dump(gateway/'browser-owned-exit.json',{'exitCode':browser.returncode,'ownedActiveProcesses':active});assert browser.returncode==0 and active==0
   browserjob.close();browserlog.close()
''')
s=s.replace("assert len(observed)==2 and all(","assert len([x for x in observed if x['path']=='/performance-fixture'])==2 and all(").replace("for x in observed),observed","for x in observed if x['path']=='/performance-fixture'),observed")
s=s.replace("'normalNginxExitAndOwnedDescendantsZero':True}","'normalNginxExitAndOwnedDescendantsZero':True,'actualHeadlessChromeColdWarmAnonymousLogin':True,'browserResults':{mode:json.loads((O/mode/'browser-results.json').read_text(encoding='utf-8')) for mode in ['baseline','candidate']}}")
(V/'verify_static_transport_r231.py').write_text(s,encoding='utf-8')
print('prepared R231 isolated browser comparison')
