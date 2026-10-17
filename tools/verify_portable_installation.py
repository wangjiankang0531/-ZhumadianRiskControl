"""Verify every outer/core/GIS file of a prepared portable installation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import time
from package_landscape_version import sha


def verify(root, output):
    root=Path(root).resolve();output=Path(output)
    if output.exists():raise ValueError('Keep prior verdict; use a new evidence file')
    manifest=json.loads((root/'installation.json').read_text('utf8'))
    assert manifest['schema']=='xnby.portable.installation.v1'
    package=root/manifest['package']
    assert sha(package/'package.json')==manifest['packageManifestSha256']
    assert sha(package/'dataset_manifest.json')==manifest['datasetManifestSha256']
    release=json.loads((package/'package.json').read_text('utf8'));dataset=json.loads((package/'dataset_manifest.json').read_text('utf8'))
    selection=json.loads((root/'Application/Packages/active_release.json').read_text('utf8'))
    assert selection['selected']['manifestSha256']==manifest['packageManifestSha256']
    assert all(not Path(selection['selected']['data'][k]).is_absolute() for k in ('layers','database'))
    jobs=[(root,r) for r in manifest['outerFiles']]+[(package,r) for r in release['files']]+[(package,r) for r in manifest.get('packageExtraFiles',[])]+[(package,r) for r in dataset['sourceFiles']]
    assert len({str(base/r['path']) for base,r in jobs})==len(jobs)
    started=time.time();record={'status':'running','pid':os.getpid(),'root':str(root),'expectedFiles':len(jobs),'checkedFiles':0,'checkedBytes':0,'fullGisHash':True}
    def save():output.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
    save()
    def check(job):
        base,r=job;part=Path(r['path']);assert not part.is_absolute() and '..' not in part.parts
        p=base/part
        assert not p.is_symlink() and not p.is_junction() and p.is_file(),str(p)
        assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
        return r['bytes']
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for count,size in enumerate(pool.map(check,jobs),1):
                record['checkedFiles']=count;record['checkedBytes']+=size
                if count%20000==0:save();print('VERIFIED',count,flush=True)
    except BaseException as error:
        record.update(status='failed',error=str(error),elapsedSeconds=time.time()-started);save();raise
    record.update(status='passed',coreFiles=len(release['files']),outerFiles=len(manifest['outerFiles']),gisFiles=len(dataset['sourceFiles']),elapsedSeconds=time.time()-started,installationManifestSha256=sha(root/'installation.json'))
    save();print(json.dumps(record,ensure_ascii=False),flush=True);return record


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.root,a.output)


if __name__=='__main__':main()
