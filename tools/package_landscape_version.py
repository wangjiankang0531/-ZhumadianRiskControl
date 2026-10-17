"""Prepare an immutable version folder with a portable runtime and separate derived cache."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1048576),b''):h.update(block)
    return h.hexdigest()


def copy_file(source,target,link=False):
    if source.is_symlink() or source.is_junction():raise ValueError('Package file cannot be a link: '+str(source))
    target.parent.mkdir(parents=True,exist_ok=True)
    if link:
        try:os.link(source,target);return
        except OSError:pass
    shutil.copy2(source,target)


def copy_tree(source,target,link=False):
    count=0
    with ThreadPoolExecutor(max_workers=8 if link else 1) as pool:
        for directory,dirs,files in os.walk(source):
            dirs[:]=[d for d in dirs if d not in ('__pycache__','test','tests')]
            for d in dirs:
                if (Path(directory)/d).is_symlink() or (Path(directory)/d).is_junction():raise ValueError('Package directory cannot be a link')
            paths=[Path(directory)/n for n in files if not n.endswith(('.pyc','.pdb'))]
            list(pool.map(lambda p:copy_file(p,target/p.relative_to(source),link),paths))
            count+=len(paths)
            if count and count%20000<len(paths):print('STAGING',source.name,count,flush=True)
    return count


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,required=True)
    parser.add_argument('--editor',type=Path,required=True)
    parser.add_argument('--web-dist',type=Path,required=True)
    parser.add_argument('--exporter',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output.resolve();base=args.base.resolve()
    if out.exists():raise ValueError('Use a new version directory; inspect any previous preparation first')
    if not out.is_relative_to(ROOT/'Packages/versions'):raise ValueError('Version output must stay in Application/Packages/versions')
    old=json.loads((base/'package.json').read_text('utf-8'))
    assert old['editorVersion']=='0.9.6' and old['webVersion']=='0.8.4'
    assert sha(base/old['activeExecutable'])=='14c1e22bb81e1ac25c1a0d8c7276b593cfde63cee995145d3661e4d1939c8ae9'
    assert sha(args.editor)=='69533de112ab60a686cbc2f477d37bc43d5b10be2cee690c43be269f5733b660'
    capability=args.exporter.with_name('ht_osgb_exporter.capabilities.json')
    exporter_contract=json.loads(capability.read_text('utf-8'))
    assert exporter_contract['exe_sha256']==sha(args.exporter) and exporter_contract['unicode_source_paths'] is True
    assert 'data-viewer-version="0.8.5"' in (args.web_dist/'index.html').read_text('utf-8')
    out.mkdir(parents=True);state=out/'preparation.json';started=time.time()
    record={'status':'staging','pid':os.getpid(),'base':str(base),'output':str(out),'originalGisModified':False}
    state.write_text(json.dumps(record,indent=2),encoding='utf-8')
    for name in ['runtime','data','shared','services']:copy_tree(base/name,out/name)
    copy_file(base/'services/tests/test_api.py',out/'services/tests/test_api.py')
    asset_count=copy_tree(base/'assets',out/'assets',link=True)
    for p in base.glob('*.dll'):copy_file(p,out/p.name)
    executable='XNBY_ZhumadianEditor_0_9_7.exe';copy_file(args.editor,out/executable)
    copy_tree(args.web_dist,out/'apps/landscape_web/dist')
    tools={r['path'].split('/',1)[1] for r in old['files'] if r['path'].startswith('tools/')}
    tools|={'native_atlas_recipe.py','native_tight_atlas.py','serve_business_portal_qa.py','launch_business_portal_qa.py'}
    for name in sorted(tools):copy_file(ROOT/'tools'/name,out/'tools'/name)
    for name in ['osgb_exporter_build','osg-build-min']:copy_tree(base/'work'/name,out/'work'/name)
    copy_file(args.exporter,out/'work/osgb_exporter_build/Release/ht_osgb_exporter.exe')
    copy_file(capability,out/'work/osgb_exporter_build/Release/ht_osgb_exporter.capabilities.json')
    (out/'work/zhumadian_native_chunk_cache').mkdir()
    (out/'projects').mkdir()
    layer=ROOT/'projects/驻马店图层.json';layer_sha=sha(layer)
    shutil.copy2(layer,out/'projects/驻马店图层.json');assert sha(layer)==layer_sha==sha(out/'projects/驻马店图层.json')
    copy_file(base/'projects/驻马店图层示例.json',out/'projects/驻马店图层示例.json')
    recipe={'schema':'xnby.native.atlas.release.v1','atlas_layout_policy':'tight_square_gutter4_v1','cache_relative_path':'work/zhumadian_native_chunk_cache'}
    (out/'data/showcase/zhumadian_native_recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf-8')
    for name,mode in [('run_web.cmd','scene'),('run_portal.cmd','portal')]:
        command='@echo off\r\nsetlocal\r\nchcp 65001 >nul\r\n"%~dp0runtime\\python\\python.exe" -X utf8 "%~dp0tools\\launch_landscape_web.py" --page '+mode+' --layers "%~dp0projects\\驻马店图层.json" --layer-database "%~dp0work\\business\\layers.sqlite" %*\r\n'
        (out/name).write_bytes(command.encode('utf-8'))
    (out/'run_editor.cmd').write_bytes(('@echo off\r\nsetlocal\r\nchcp 65001 >nul\r\nstart "" "%~dp0'+executable+'" "--layers=%~dp0projects\\驻马店图层.json" %*\r\n').encode('utf-8'))
    dataset=json.loads((base.parent/'transfer_manifest.json').read_text('utf-8'))
    gis=[dict(r,path=r['path'].removeprefix('Application/')) for r in dataset['files'] if r['path'].startswith('Application/assets/驻马店园区/')]
    assert gis and all(r['path'].startswith('assets/驻马店园区/') for r in gis)
    for r in gis:assert (out/r['path']).is_file() and (out/r['path']).stat().st_size==r['bytes'],r['path']
    (out/'dataset_manifest.json').write_text(json.dumps({'schema':'xnby.native.dataset.v1','sourceFiles':gis},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (out/'README.md').write_text('信能本源驻马店候选 EXE0.9.7 / WEB0.8.5 / API0.3.0。\n独立版本和派生缓存，原GIS只读文件，项目图层为独立测试副本。默认版本尚未替换。\n使用run_editor.cmd、run_web.cmd或run_portal.cmd；浏览器仅loopback。\n完整包、版本切换、迁移和回滚验证完成前不能称正式发布。\n',encoding='utf-8')
    files=[]
    for p in sorted(out.rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(out).as_posix()
        if rel=='preparation.json' or rel.startswith(('assets/驻马店园区/','projects/')):continue
        files.append({'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)})
    release={'schema':'xnby.zhumadian.release.v1','editorVersion':'0.9.7','webVersion':'0.8.5','apiVersion':'0.3.0','activeExecutable':executable,'prepared':True,'verified':False,'nativeAtlasRecipe':recipe,'initialLayerSha256':layer_sha,'sourceGisFiles':len(gis),'assetFiles':asset_count,'files':files}
    (out/'package.json').write_text(json.dumps(release,ensure_ascii=False,indent=2),encoding='utf-8')
    record.update(status='prepared',coreFiles=len(files),sourceGisFiles=len(gis),elapsedSeconds=time.time()-started)
    state.write_text(json.dumps(record,indent=2),encoding='utf-8');print(json.dumps(record),flush=True)


if __name__=='__main__':main()