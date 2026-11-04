"""Prepare lossless navigation assets against the exact last-delivered R45 inputs.

No deployed file, source asset, database or browser profile is modified.
"""
from pathlib import Path
import hashlib, io, json, sys
sys.dont_write_bytecode=True
V=Path(__file__).resolve().parent;W=V/'performance-assets-r893'
sys.path.insert(0,str(W/'direct-wheel-deps'))
from PIL import Image
from fontTools.ttLib import TTFont,woff2
R=Path('D:/Project/Zhumadian'); O=W/'candidate-r900'; assert not O.exists()
J=lambda p:json.loads(p.read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
plan=J(V/'feedback_r889/full-source-and-restore-plan.private.json')
def source(rel):
    row=plan['sources'][rel];p=Path(row['source']);raw=p.read_bytes()
    assert len(raw)==row['bytes'] and sha(raw)==row['sha256'], 'SEALED_R45_INPUT_REQUIRED'
    return raw
bg=source('frontend/security_pc/assets/png/background-BHYqFd8n.png')
font=source('frontend/security_pc/assets/ttf/YouSheBiaoTiHei-fahbdFno.ttf')
html=source('frontend/security_pc/index.html')
O.mkdir(); files={}
def emit(rel,raw):
    p=O/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    files[rel]={'bytes':len(raw),'sha256':sha(raw)}
image=Image.open(io.BytesIO(bg));assert image.format=='PNG' and image.width*image.height<30_000_000
pixels=image.convert('RGBA');buf=io.BytesIO()
# Exact transparent RGB and all decoded pixels retained; no resize or quantization.
pixels.save(buf,format='WEBP',lossless=True,exact=True,method=6,icc_profile=image.info.get('icc_profile',b''),exif=image.info.get('exif',b''))
webp=buf.getvalue();decoded=Image.open(io.BytesIO(webp)).convert('RGBA')
assert decoded.size==pixels.size and decoded.tobytes()==pixels.tobytes(), 'LOSSLESS_PIXEL_IDENTITY_REQUIRED'
assert Image.open(io.BytesIO(webp)).info.get('icc_profile')==image.info.get('icc_profile'), 'ORIGINAL_COLOR_PROFILE_REQUIRED'
assert len(webp)<len(bg)
bgname='home-background-'+sha(webp)[:16]+'.webp'
emit('assets/webp/'+bgname,webp)
out=io.BytesIO()
# Disabling transforms allows exact comparison of every reconstructed font table.
woff2.compress(io.BytesIO(font),out,transform_tables=set())
w2=out.getvalue();old=TTFont(io.BytesIO(font),recalcBBoxes=False,recalcTimestamp=False);new=TTFont(io.BytesIO(w2),recalcBBoxes=False,recalcTimestamp=False)
assert set(old.reader.keys())==set(new.reader.keys())
table_identity=[]
for tag in old.reader.keys():
    left,right=old.reader[tag],new.reader[tag]
    if tag=='head':
        # W3C WOFF2 section 5 requires exactly this lossless-transform flag.
        assert new['head'].flags == old['head'].flags | (1 << 11)
        left=left[:8]+b'\x00'*4+left[12:16]+(int.from_bytes(left[16:18],'big') | (1<<11)).to_bytes(2,'big')+left[18:]
        right=right[:8]+b'\x00'*4+right[12:]
    assert left==right, 'FONT_TABLE_IDENTITY_REQUIRED:'+tag
    table_identity.append(str(tag))
assert old.getBestCmap()==new.getBestCmap() and old.getGlyphOrder()==new.getGlyphOrder() and len(w2)<len(font)
fontname='YouSheBiaoTiHei-'+sha(w2)[:16]+'.woff2';emit('assets/woff2/'+fontname,w2)
base='/zhumadian/branding-20261025/'
css=('/* exact R45 lossless navigation assets; complete font retained */\n'
     '@font-face{font-family:YouSheBiaoTiHei;src:url("'+base+'assets/woff2/'+fontname+'") format("woff2");font-display:swap;}\n'
     'body .background-pattern[data-v-7244265a]{background-image:url("'+base+'assets/webp/'+bgname+'");}\n').encode('utf8')
cssname='xnby-home-transfer-'+sha(css)[:16]+'.css';emit('assets/css/'+cssname,css)
text=html.decode('utf8');assert text.count('</head>')==1 and 'data-xnby-home-transfer' not in text
text=text.replace('</head>','    <link rel="stylesheet" data-xnby-home-transfer="r894" href="'+base+'assets/css/'+cssname+'">\n</head>')
emit('index.html',text.encode('utf8'))
proof={'schema':'xnby.lossless-navigation-assets.v1','passed':True,'candidateOnly':True,'publicDeployed':False,
 'image':{'sourceBytes':len(bg),'outputBytes':len(webp),'width':image.width,'height':image.height,'rgbaPixelsIdentical':True,'originalICCProfilePreserved':True,'sourceSHA256':sha(bg),'outputSHA256':sha(webp)},
 'font':{'sourceBytes':len(font),'outputBytes':len(w2),'sourceSHA256':sha(font),'outputSHA256':sha(w2),'allOriginalCharactersRetained':True,'originalGlyphOrderRetained':True,'exactTablesExceptHeadChecksumAndRequiredBit11':table_identity,'WOFF2Specification':'https://www.w3.org/TR/WOFF2/#font_data'},
 'changes':['one stylesheet link added to original HTML','complete WOFF2 font with swap','exact-pixel WebP background'],
 'originalJavaScriptCSSMenuAndAuthenticationUnmodified':True,'oldAssetsRetainedForOtherReferences':True,
 'browserOriginalCompiledApplicationAndOriginalSDKAccepted':False,'publicIISCacheMIMEOrTimingAccepted':False,'files':files,'fullCloneReady':False}
(W/'lossless-candidate-r900.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in proof.items() if k not in ['files','font']},ensure_ascii=False));print(json.dumps({'fontBefore':len(font),'fontAfter':len(w2),'glyphs':len(old.getGlyphOrder()),'tables':len(table_identity)}))
