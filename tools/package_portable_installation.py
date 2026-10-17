"""Build a relocatable installation with a common launcher and external user data.

GIS hardlinks are optional local staging only; archives and cross-machine copies
contain actual file bytes. Never stage into an existing destination.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import time
from package_landscape_version import copy_file, copy_tree, sha
from release_catalog import Catalog

ROOT=Path(__file__).resolve().parents[1]


def prepare(source, output, link_gis=False):
    source=Path(source).resolve();out=Path(output).resolve()
    if out.exists():raise ValueError('Use a new installation directory; retain previous evidence')
    if not out.is_relative_to(ROOT/'work'):raise ValueError('Staging must stay below Application/work')
    release=json.loads((source/'package.json').read_text('utf8'))
    version=release['editorVersion']
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise ValueError('Invalid version folder')
    Catalog(ROOT,ROOT/'work/installation_validation.json').package(source.relative_to(ROOT),full=True)
    dataset=json.loads((source/'dataset_manifest.json').read_text('utf8'))
    out.mkdir(parents=True);started=time.time();state=out/'preparation.json'
    record={'status':'staging','pid':os.getpid(),'source':str(source),'output':str(out),'linkGisStaging':link_gis,'originalDataModified':False}
    def save():state.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    save();app=out/'Application';package=app/'Packages/versions'/version
    package.mkdir(parents=True)
    for entry in release['files']:
        copy_file(source/entry['path'],package/entry['path'])
    copy_file(source/'package.json',package/'package.json')
    if (source/'projects').is_dir():copy_tree(source/'projects',package/'projects')
    raw=dataset['sourceFiles'];assert len({r['path'] for r in raw})==len(raw)
    def copy_raw(entry):
        part=Path(entry['path'])
        if part.is_absolute() or '..' in part.parts or not part.as_posix().startswith('assets/驻马店园区/'):
            raise ValueError('Invalid source GIS record')
        source_file=source/part
        if source_file.stat().st_size!=entry['bytes']:raise ValueError('GIS source length changed')
        copy_file(source_file,package/part,link=link_gis)
    with ThreadPoolExecutor(max_workers=8 if link_gis else 2) as pool:
        for index,_ in enumerate(pool.map(copy_raw,raw),1):
            if index%20000==0:
                record['gisCopied']=index;save();print('GIS',index,flush=True)
    for name in ['release_catalog.py','launch_selected_release.py']:
        copy_file(ROOT/'tools'/name,app/'tools'/name)
    copy_tree(source/'runtime/python',app/'runtime/python')
    for name in ['run_editor.cmd','run_web.cmd','run_portal.cmd']:
        copy_file(ROOT/name,app/name)
        (out/name).write_bytes(('@echo off\r\ncall "%~dp0Application\\'+name+'" %*\r\n').encode('utf8'))
    (out/'run_business_qa.cmd').write_bytes(b'@echo off\r\n"%~dp0Application\\runtime\\python\\python.exe" -X utf8 "%~dp0Application\\tools\\launch_selected_release.py" --kind qa --port 8790 %*\r\n')
    layers=ROOT.parent/'Assets/DLG/驻马店图层.json';layer_sha=sha(layers)
    target_layer=out/'Assets/DLG/驻马店图层.json';copy_file(layers,target_layer)
    target_db=out/'Assets/BusinessData/xnby_business.sqlite';target_db.parent.mkdir(parents=True)
    original_db=ROOT.parent/'Assets/BusinessData/xnby_business.sqlite'
    with sqlite3.connect(original_db.as_uri()+'?mode=ro',uri=True) as database,sqlite3.connect(target_db) as backup:
        assert database.execute('PRAGMA user_version').fetchone()[0]==2
        database.backup(backup)
    assert sha(layers)==layer_sha
    selected={'package':'Packages/versions/'+version,'manifestSha256':sha(package/'package.json'),
              **{k:release[k] for k in ('editorVersion','webVersion','apiVersion')},'candidate':True,
              'data':{'layers':'../Assets/DLG/驻马店图层.json','database':'../Assets/BusinessData/xnby_business.sqlite'}}
    (app/'Packages/active_release.json').write_text(json.dumps({'schema':'xnby.release.selection.v1','revision':1,'selected':selected,'history':[]},ensure_ascii=False,indent=2),encoding='utf8')
    (out/'Logs').mkdir()
    (out/'README.md').write_text(f'''# 信能本源驻马店独立测试安装目录

EXE{version} / WEB{release["webVersion"]} / API{release["apiVersion"]}。本目录整体复制到笔记本F盘，例如F:/XNBY/ZhumadianTest_{version.replace(".","_")}。
run_editor.cmd启动编辑器；run_web.cmd打开本机三维；run_portal.cmd打开门户。
run_business_qa.cmd是独立合成业务验收：临时模拟身份与企业数据，未接生产统一认证。真实登录、真实业务源仍待接入。
Assets/DLG与Assets/BusinessData保存共享标注/业务数据库，版本切换不会从包内种子覆盖它们。不要只拷贝EXE或覆盖既有用户数据。
本包包含所有原始OSGB、底景、转换器、Python和shaderc；无需开发机目录链接或联网安装依赖，但需本机可用Vulkan驱动。
仅127.0.0.1访问，团队本机或UU轮流测试。旧天津系统与其它服务保持。当前为体验版；全区画质、长稳、UE性能和目标机验收未完成。
''',encoding='utf8')
    outer=[]
    for directory in [app/'tools',app/'runtime',out/'Assets']:
        for path in sorted(directory.rglob('*')):
            if path.is_file():outer.append({'path':path.relative_to(out).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    for path in [*(app/n for n in ['run_editor.cmd','run_web.cmd','run_portal.cmd','Packages/active_release.json']),*(out/n for n in ['run_editor.cmd','run_web.cmd','run_portal.cmd','run_business_qa.cmd','README.md'])]:
        outer.append({'path':path.relative_to(out).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    extra_files=[]
    for path in sorted((package/'projects').rglob('*')):
        if path.is_file():extra_files.append({'path':path.relative_to(package).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)})
    manifest={'schema':'xnby.portable.installation.v1','versions':{k:release[k] for k in ('editorVersion','webVersion','apiVersion')},
              'package':'Application/Packages/versions/'+version,'packageManifestSha256':selected['manifestSha256'],
              'datasetManifestSha256':sha(package/'dataset_manifest.json'),'outerFiles':outer,'packageExtraFiles':extra_files,
              'sourceGisFiles':len(raw),'layerSnapshotSha256':layer_sha,'databaseSchema':2,'prepared':True,'verified':False}
    (out/'installation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    record.update(status='prepared',gisCopied=len(raw),sourceGisFiles=len(raw),coreFiles=len(release['files']),outerFiles=len(outer),elapsedSeconds=time.time()-started);save()
    print(json.dumps(record,ensure_ascii=False),flush=True)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--link-gis',action='store_true')
    args=parser.parse_args();prepare(args.source,args.output,args.link_gis)


if __name__=='__main__':main()
