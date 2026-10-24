"""Require an owned platform to finish original initialization before business launch."""
from pathlib import Path
import re
import time

def require_semantics_pair(config,pin):
 if (config is None)!=(pin is None):raise ValueError('ORIGINAL_CONFIG_AND_PIN_REQUIRED_TOGETHER')
 if pin is not None and not re.fullmatch('[0-9a-f]{64}',pin):raise ValueError('ORIGINAL_CONFIG_PIN_SHAPE')
 return config is not None

def allowed_ports(mysql,redis,platform=None):
 ports=[mysql,redis]+([] if platform is None else [platform])
 if any(type(p) is not int or not 1024<=p<=65535 for p in ports) or len(set(ports))!=len(ports):raise ValueError('OWN_DISTINCT_COMPONENT_PORTS_REQUIRED')
 return ','.join(map(str,ports))

def wait_for_platform(root,platform,dependencies,timeout=90,clock=time.monotonic,nap=time.sleep,progress=None):
 root=Path(root);deadline=clock()+timeout;last=clock()-30
 while True:
  if platform.poll() is not None or any(p.poll() is not None for p in dependencies):raise RuntimeError('OWN_PLATFORM_OR_DEPENDENCY_EXITED')
  receipt=root/'bootstrap-rehydration-observation.properties';data={}
  if receipt.exists():
   data=dict(line.split('=',1) for line in receipt.read_text('ascii').splitlines() if line and not line.startswith(('#','!')))
   if data.get('failureClass'):raise RuntimeError('OWN_ORIGINAL_BOOTSTRAP_FAILED')
  if (root/'original-platform-main-returned.txt').exists() and (root/'own-platform-http-port.txt').exists():
   if data.get('originalBootstrapMethodCompleted')!='true' or data.get('outsideBootstrapCriticalFieldsSignaturePreserved')!='true':raise RuntimeError('OWN_PLATFORM_BOOTSTRAP_NOT_VERIFIED')
   text=(root/'own-platform-http-port.txt').read_text('ascii').strip()
   if not re.fullmatch('[0-9]{4,5}',text) or not 1024<=int(text)<=65535:raise RuntimeError('OWN_PLATFORM_PORT_SHAPE')
   if platform.poll() is not None or any(p.poll() is not None for p in dependencies):raise RuntimeError('OWN_PLATFORM_EXITED_DURING_GATE')
   return int(text)
  if clock()>=deadline:raise TimeoutError('OWN_PLATFORM_ORIGINAL_MAIN_WAIT_TIMEOUT')
  if progress is not None and clock()-last>=30:progress();last=clock()
  nap(.2)
