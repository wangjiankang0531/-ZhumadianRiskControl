from pathlib import Path
V=Path(__file__).resolve().parent;R=Path('D:/Project/Zhumadian')
assert not(R/'work/dl958').exists()
s=(V/'test_stable_download_click_r956.mjs').read_text('utf8').replace('work/dl956/','work/dl958/').replace('own-download-r956.bin','own-download-r958.bin')
s="import{win32}from'node:path';\n"+s
a="downloadPath:dir+'downloads',eventsEnabled:true";assert s.count(a)==1;s=s.replace(a,"downloadPath:win32.normalize(dir+'downloads'),eventsEnabled:true")
p=V/'test_stable_download_click_r958.mjs';assert not p.exists();p.write_text(s,encoding='utf8')
s=(V/'run_stable_download_test_r956.py').read_text('utf8').replace('test_stable_download_click_r956.mjs','test_stable_download_click_r958.mjs').replace('work/dl956','work/dl958').replace('stable-download-r956.private.log','stable-download-r958.private.log').replace('stable-download-terminal-r956.json','stable-download-terminal-r958.json')
p=V/'run_stable_download_test_r958.py';assert not p.exists();p.write_text(s,encoding='utf8');print('NATIVE_WINDOWS_DOWNLOAD_PATH_VARIANT_READY')
