"""Match the published native SDK login request contract; preserve original credential transform and authentication."""
from pathlib import Path
from contextlib import contextmanager
import hashlib
@contextmanager
def published_login_query_override(project,reference):
 project=Path(project);target=project/'src/api/login/index.ts';raw=target.read_bytes();text=raw.decode('utf-8');old='import { encrypt } from "@/utils/common";';call='request.post<LoginResult>("/jnpf/oauth/Login", params, {'
 assert text.count(old)==text.count(call)==1,'EXACT_ORIGINAL_LOGIN_CALL_REQUIRED'
 changed=text.replace(old,'import { encrypt, toURLSearch } from "@/utils/common";').replace(call,'request.post<LoginResult>(toURLSearch(params, "/jnpf/oauth/Login"), undefined, {')
 note={'originalSHA256':hashlib.sha256(raw).hexdigest(),'patchedSHA256':hashlib.sha256(changed.encode()).hexdigest(),'nativeOriginalPOSTQueryContract':True,'passwordTransformTokenStorageAndBackendAuthenticationUnchanged':True,'referenceChanged':False}
 try:
  target.write_text(changed,encoding='utf-8');yield note
 finally:
  target.write_bytes(raw);note['sourceFilesRestored']=target.read_bytes()==raw
