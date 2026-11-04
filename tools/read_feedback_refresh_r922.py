"""Fresh anonymous feedback read; compare against the most recent fixed snapshot."""
from pathlib import Path
import contextlib,datetime,hashlib,io,json,sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;prior=V/'feedback-read-r670-20261104';O=V/'feedback-read-r922-20261104'
assert not O.exists();O.mkdir();source=prior/'read_public_sheet.py';raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='26187c9c3afe37756b2aa7a20d075b620b49d3b3da53d6b1815873b3e27b68cd'
assert b'ANONYMOUS_DOCUMENT_READ_NOT_ALLOWED'in raw and b"'Cache-Control':'no-cache'"in raw and b'cookies'not in raw.lower()
(O/'read_public_sheet.py').write_bytes(raw)
scope={'__name__':'fresh_readonly_feedback_r922','__file__':str(O/'read_public_sheet.py')};exec(compile(raw,str(O/'read_public_sheet.py'),'exec'),scope)
receipt=dict(at=datetime.datetime.now().astimezone().isoformat(),anonymousReadOnly=True,cookiesCredentialsOrLoggedInProfileUsed=False,
             freshFetchNoLocalCachedRead=True,desktopUsed=False,sheetWriteAttempted=False,rawIssueDataKeptLocalNotPublicGit=True)
try:
    args=sys.argv;sys.argv=[str(O/'read_public_sheet.py'),'--fetch']
    try:
        with contextlib.redirect_stdout(io.StringIO()):scope['main']()
    finally:sys.argv=args
    now=json.loads((O/'issues.json').read_bytes());old=json.loads((prior/'issues.json').read_bytes())
    n={v['sourceRow']:v for v in now['issues']};p={v['sourceRow']:v for v in old['issues']}
    receipt.update(readSucceeded=True,issueCount=now['issueCount'],anonymousCanEdit=now['anonymousCanEdit'],addedRows=sorted(n.keys()-p.keys()),removedRows=sorted(p.keys()-n.keys()),
                   changedDescriptionRows=[r for r in n.keys()&p.keys()if n[r]['descriptionSha256']!=p[r]['descriptionSha256']],
                   changedCompletionRows=[r for r in n.keys()&p.keys()if n[r]['currentCompletion']!=p[r]['currentCompletion']],issueSnapshotSHA256=hashlib.sha256((O/'issues.json').read_bytes()).hexdigest())
except Exception as e:receipt.update(readSucceeded=False,errorType=type(e).__name__,httpStatus=getattr(e,'code',None))
(O/'read-receipt-r922.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(receipt,ensure_ascii=False))
