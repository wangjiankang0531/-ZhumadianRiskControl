"""Real two-variant R48-r3 extraction plus changed-payload refusal checks."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import io
import json
import zipfile

R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent
D=R/'Document/Deployment/public_test_event_write_results_r48_20261105_r3'
DEL=D/'delivery';W=R/'work/ut1052'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
    prepared=json.loads((D/'prepared-r1051.json').read_bytes())
    manifest=DEL/'delivery-manifest.json';assert sha(manifest.read_bytes())==prepared['deliveryManifestSHA256']
    data=json.loads(manifest.read_bytes())
    assert set(p.name for p in DEL.iterdir())==set(data['files'])|{'delivery-manifest.json'}
    for name,row in data['files'].items():
        raw=(DEL/name).read_bytes();assert len(raw)==row['bytes']and sha(raw)==row['sha256']
    spec=importlib.util.spec_from_file_location('actual_transport_r48_r3_r1052',DEL/'deploy_event_write_results_r48.py')
    wrapper=importlib.util.module_from_spec(spec);spec.loader.exec_module(wrapper)
    archive=DEL/wrapper.ARCHIVE_NAME
    assert sha(archive.read_bytes())==wrapper.ARCHIVE_SHA
    assert not W.exists();W.mkdir()
    checks=[]
    for key,base in wrapper.BASES.items():
        stage=W/base['label'];plan=wrapper.extract_selected_archive(archive,stage,base)
        expected={'web.config','update-manifest.json'}|{'payload/'+name for name in plan['files']}
        assert {p.relative_to(stage).as_posix()for p in stage.rglob('*')if p.is_file()}==expected
        for name,row in plan['files'].items():
            raw=(stage/'payload'/name).read_bytes();assert len(raw)==row['bytes']and sha(raw)==row['SHA256']
        checks.append({'case':base['label']+'-actual-extraction-all-payload-pins','passed':True,'writes':len(plan['files']),'removals':len(plan['removedFrontendFiles'])})
    with zipfile.ZipFile(archive)as z:members=[(copy.copy(item),z.read(item.filename))for item in z.infolist()]
    def altered(kind):
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED)as z:
            for item,raw in members:
                info=copy.copy(item)
                if kind=='runtime-byte-drift'and item.filename=='payload/tools/original_public_test_update.py':raw=raw+b'\n# altered\n'
                if kind=='variant-manifest-drift'and item.filename=='variants/r45/update-manifest.json':raw=raw+b' '
                z.writestr(info,raw)
            if kind=='extra-undeclared-payload':z.writestr('payload/unknown.py',b'unknown')
        output.seek(0);return output
    for kind in ['runtime-byte-drift','variant-manifest-drift','extra-undeclared-payload']:
        with zipfile.ZipFile(altered(kind))as z:
            try:wrapper.validate_archive(z,next(iter(wrapper.BASES.values())))
            except ValueError as exc:checks.append({'case':kind,'rejected':True,'reason':str(exc)})
            else:raise AssertionError('MUTATED_TRANSPORT_ACCEPTED:'+kind)
    assert (DEL/'r48_update_runtime.py').read_bytes()==(V/'static-control-bridge-r1046/r48_update_runtime.py').read_bytes()
    report={'passed':True,'checks':checks,'checkCount':len(checks),'files':9,'transportBytes':prepared['bytes'],
        'deliveryManifestSHA256':prepared['deliveryManifestSHA256'],'runtimeMatchesActualApplyTest':True,
        'twoRealSelectedArchiveExtractionsPerformed':True,'sourceZipInfoCopiedBeforeMutation':True,
        'serverDeploymentOrIISAccepted':False,'publicMutation':False,'fullCloneReady':False}
    (D/'verified-transport-r1052.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
