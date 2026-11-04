"""Prepare transport tests adapted to the exact nested R46-core/R47 archive."""
from pathlib import Path
import ast
V=Path(__file__).resolve().parent
s=(V/'verify_home_delivery_r917.py').read_text('utf8')
for a,b in [('public_test_home_transfer_r46_20261104','public_test_home_supervision_r47_20261104'),('preparation-result-r916.json','preparation-r932.json'),('deploy_home_transfer_r46.py','deploy_home_supervision_r47.py'),('work/hf915/Application','work/sv929/Application'),('work/home-sparse-r914/bundle','work/unified-home-supervision-r928/bundle'),('r46_frozen_delivery','r47_frozen_delivery'),('home-transport-r917-','home-supervision-transport-r933-'),('r46-scoped-result.json','r47-scoped-result.json'),('xnby.r46.','xnby.r47.'),('verified-transport-r917.json','verified-transport-r933.json')]:s=s.replace(a,b)
s=s.replace("len(selected['files'])==7", "len(selected['files'])==11")
old="=={'web.config','update-manifest.json'}|{'payload/'+n for n in selected['files']}"
assert s.count(old)==1;s=s.replace(old,old+"|{n for n in members if n.startswith('base-r46/')}")
s=s.replace("'transportFiles':8", "'transportFiles':9").replace("'archiveMembers':9,'exactExtractedFiles':9", "'archiveMembers':21,'exactExtractedFiles':21")
s=s.replace("'home_sparse_update_r914_20261104/verified-files-r915.json'", "'unified_home_supervision_r928_20261104/verified-files-r929.json'")
marker="  mutated('changed-fixed-manifest'";position=s.index(marker);end=s.index('\n',position)
s=s[:end]+"\n  mutated('changed-inner-home-manifest',lambda x:[(n,b+b' 'if n=='base-r46/update-manifest.json'else b)for n,b in x])\n  mutated('changed-frozen-core-payload',lambda x:[(n,b+b' 'if n=='payload/tools/original_public_test_base_r46.py'else b)for n,b in x])"+s[end:]
marker="archive=T/m.ARCHIVE_NAME;assert sha(archive.read_bytes())==m.ARCHIVE_SHA";assert s.count(marker)==1;s=s.replace(marker,marker+"\nassert sha((T/'original_public_test_base_r46.py').read_bytes())==m.CORE_SHA")
ast.parse(s);p=V/'verify_unified_transport_r933.py';assert not p.exists();p.write_text(s,encoding='utf8');print('R933_TRANSPORT_TEST_SOURCE_PREPARED_NOT_EXECUTED')
