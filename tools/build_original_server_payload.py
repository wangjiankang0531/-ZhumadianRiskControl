"""Stream one private server payload from a pinned input plan; never stage a full copy."""
from pathlib import Path,PurePosixPath
import argparse,datetime,hashlib,json,os,shutil,stat,subprocess,time,uuid,zipfile

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=a.plan.read_bytes();assert hashlib.sha256(raw).hexdigest()==a.plan_sha256,'PINNED_PRIVATE_INPUT_PLAN_REQUIRED'
    spec=json.loads(raw);assert spec['schema']=='zhumadian.original.server.private-inputs.v1'
    rows=spec['files'];assert len(rows)==15950 and sum(v['bytes'] for v in rows.values())==2126305460
    out=a.output.resolve();assert not out.exists() and out.suffix=='.zip' and shutil.disk_usage(out.parent).free>=6*1024**3
    cmd="Get-CimInstance Win32_Process -Filter \"Name='mysqld.exe'\" | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress"
    r=subprocess.run(['powershell.exe','-NoProfile','-Command',cmd],capture_output=True,timeout=15);assert r.returncode==0
    active=json.loads(r.stdout.decode('utf-8-sig'));active=active if isinstance(active,list) else [active]
    assert all('own-mysql-r26' not in v['CommandLine'].lower() for v in active),'CLOSED_RECONSTRUCTED_SEED_REQUIRED'
    manifest={'schema':'zhumadian.original.server.payload.v1','releaseId':str(uuid.uuid4()),'createdAt':datetime.datetime.now().astimezone().isoformat(),'inputPlanSHA256':a.plan_sha256,'testRelease':True,'publicAccepted':False,'files':{k:{'bytes':v['bytes'],'sha256':v['sha256']} for k,v in rows.items()}}
    start=time.monotonic();last=start;done=0;total=0
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        for rel,row in sorted(rows.items()):
            name=PurePosixPath(rel);assert not name.is_absolute() and '\\' not in rel and ':' not in rel and '..' not in name.parts and str(name)==rel
            h=hashlib.sha256();count=0
            with open(row['source'],'rb') as source,z.open('Application/'+rel,'w',force_zip64=True) as target:
                info=os.fstat(source.fileno());assert stat.S_ISREG(info.st_mode) and info.st_size==row['bytes']
                while True:
                    block=source.read(1024*1024)
                    if not block:break
                    count+=len(block);assert count<=row['bytes'];h.update(block);target.write(block)
            assert count==row['bytes'] and h.hexdigest()==row['sha256'],'SOURCE_CHANGED:'+rel
            done+=1;total+=count
            if time.monotonic()-last>=30:
                print(json.dumps({'files':done,'bytes':total,'elapsedSeconds':round(time.monotonic()-start)}),flush=True);last=time.monotonic()
        private={k:spec[k] for k in ['platformArguments','businessArguments','configuration','seedRootPassword','seedServerUUID']}
        private['schema']='zhumadian.original.server.configuration.v1'
        data=json.dumps(private,ensure_ascii=False,indent=2).encode('utf-8');rel='private/server-configuration.json'
        z.writestr('Application/'+rel,data);manifest['files'][rel]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        z.writestr('Application/payload-manifest.json',json.dumps(manifest,indent=2).encode('utf-8'))
    receipt={'schema':'zhumadian.original.server.payload-build.v1','releaseId':manifest['releaseId'],'inputPlanSHA256':a.plan_sha256,'verifiedSourceFiles':done,'sourceBytes':total,'archiveBytes':out.stat().st_size,'elapsedSeconds':round(time.monotonic()-start,2),'archiveNotYetLaunchable':True,'controllerAndInstallValidationPending':True,'publicDeployed':False}
    out.with_suffix('.receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
