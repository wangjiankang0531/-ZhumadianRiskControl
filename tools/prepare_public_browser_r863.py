"""Prepare an isolated anonymous browser timing probe from the proven R728 driver."""
from pathlib import Path
import hashlib,json
V=Path(__file__).resolve().parent
source=(V/'measure_public_login_browser_r728.mjs').read_text('utf8')
source=source.replace('public-login-browser-r728','public-login-browser-r863')
marker='const output=process.argv[2];'
assert source.count(marker)==1
source=source.replace(marker,"let gate='';for await(const chunk of process.stdin){gate+=chunk.toString();if(gate.length>128)throw Error('BOUNDED_PUBLIC_BROWSER_GATE');}if(gate!=='XNBY_PUBLIC_STATIC_BROWSER_R863\\n')throw Error('OWN_BUDGET_GATE_REQUIRED');\n"+marker)
marker="'--remote-debugging-port=0'";assert source.count(marker)==1
source=source.replace(marker,"'--host-resolver-rules=MAP www.joinlinksmart.com 101.201.65.94',"+marker)
target=V/'measure_public_login_browser_r863.mjs';assert not target.exists();target.write_text(source,encoding='utf8')
print(json.dumps({'newDriverSHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'anonymousOnly':True,'credentialOrUserProfileUsed':False,'explicitGateAddedBeforeChromeLaunch':True}))
