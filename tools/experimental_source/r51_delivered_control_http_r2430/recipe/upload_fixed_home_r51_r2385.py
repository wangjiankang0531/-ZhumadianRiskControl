"""Upload only the fixed four-file R51 transport through the pinned SSH channel."""
from pathlib import Path
import base64, hashlib, importlib.util, json, secrets, subprocess

R=Path('D:/Project/Zhumadian')
D=R/'Document/Deployment/public_home_same_window_r51_20261112'
PIN='47d94deddaa3e73f70e0f09a9538edcbc5fa73637984cc1ed10deae588cc01ed'
REMOTE='/C:/FTP_Root/Zhumadian/Zhumadian_Home_Same_Window_20261112_R51'


def main():
    scope=json.loads((D/'fixed-transport-scope.json').read_bytes())
    assert scope['preparedManifestSHA256']==PIN
    assert hashlib.sha256((D/'prepared-manifest.json').read_bytes()).hexdigest()==PIN
    assert len(scope['files'])==4 and scope['totalBytes']==5614188
    for name,row in scope['files'].items():
        assert (D/name).stat().st_size==row['bytes'] and hashlib.sha256((D/name).read_bytes()).hexdigest()==row['sha256']
    spec=importlib.util.spec_from_file_location('r51_fixed_channel',R/'Application/tools/remote_publish/zhumadian_ssh_channel.py')
    channel=importlib.util.module_from_spec(spec);spec.loader.exec_module(channel)
    state=channel.inspect();assert state['ready']
    config=channel.PRIVATE_ROOT/channel.CONFIG_NAME;assert config.read_text('ascii')==state['config']
    def invoke(argv,body):
        p=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        first=True
        while True:
            try:out,err=p.communicate(body if first else None,timeout=15);break
            except subprocess.TimeoutExpired:
                first=False;body=b''
                print(json.dumps({'sameActualChannelHandleLive':p.poll()is None,'noRepeat':True}),flush=True)
        assert len(out)<=131072 and len(err)<=131072,'BOUNDED_CHANNEL_RESULT_REQUIRED'
        return p.returncode,out,err
    def inspect():
        code=r'''$ErrorActionPreference='Stop';if([Environment]::MachineName-ine 'iZcdi578349jceZ'){throw 'EXACT_SERVER_REQUIRED'};$root='C:\FTP_Root\Zhumadian\Zhumadian_Home_Same_Window_20261112_R51';$part=$root;while($part){if(Test-Path -LiteralPath $part){$f=Get-Item -LiteralPath $part;if(($f.Attributes-band [IO.FileAttributes]::ReparsePoint)-ne 0){throw 'REPARSE_REFUSED'}};$part=Split-Path -Path $part -Parent};$pins=ConvertFrom-Json ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('__PINS__')));$rows=@();foreach($item in $pins.PSObject.Properties){$p=Join-Path $root $item.Name;$exists=Test-Path -LiteralPath $p;$match=$false;if($exists){$f=Get-Item -LiteralPath $p;$match=(-not $f.PSIsContainer-and ($f.Attributes-band [IO.FileAttributes]::ReparsePoint)-eq 0-and $f.Length-eq $item.Value.bytes-and (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()-ceq $item.Value.sha256)};$rows+=[pscustomobject]@{name=$item.Name;exists=$exists;shaAndBytesMatch=$match}};[pscustomobject]@{releaseSHA256=(Get-FileHash -LiteralPath 'C:\inetpub\wwwroot\Zhumadian\Application\release-manifest.json' -Algorithm SHA256).Hash.ToLowerInvariant();targetExists=(Test-Path -LiteralPath $root);files=$rows;noServiceChanged=$true}|ConvertTo-Json -Depth 5 -Compress'''
        code=code.replace('__PINS__',base64.b64encode(json.dumps(scope['files']).encode()).decode())
        boot="& ([ScriptBlock]::Create([Console]::In.ReadToEnd()))"
        args=[str(channel.SSH),'-F',str(config),'-T',channel.ALIAS,'powershell.exe','-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(boot.encode('utf-16-le')).decode()]
        rc,out,err=invoke(args,code.encode('ascii'));assert rc==0,'REMOTE_INSPECT_FAILED_NO_UPLOAD_RETRY'
        return json.loads(out.decode('utf-8-sig'))
    before=inspect()
    assert before['releaseSHA256']=='c28b3dc4de2ce70ce4d4fdc1add37e606dd1c15c953225760e08d044f601e55d' and not before['targetExists'],'EXACT_R50_AND_NEW_TRANSPORT_REQUIRED'
    nonce=secrets.token_hex(10);lines=['mkdir "'+REMOTE+'"']
    for name in scope['files']:
        temporary=REMOTE+'/.r51-'+nonce+'-'+name+'.part'
        lines+=['put "'+(D/name).as_posix()+'" "'+temporary+'"','rename "'+temporary+'" "'+REMOTE+'/'+name+'"']
    lines+=['bye']
    rc,out,err=invoke([str(channel.SSH.with_name('sftp.exe')),'-F',str(config),'-b','-',channel.ALIAS],('\n'.join(lines)+'\n').encode('ascii'))
    after=inspect();after['actualSFTPExitCode']=rc;after['publicApplicationNotDeployed']=True
    with(D/'server-upload-readback-r2385.json').open('x',encoding='utf-8')as f:json.dump(after,f,indent=2)
    assert rc==0 and all(row['shaAndBytesMatch']for row in after['files']),'UPLOAD_INCOMPLETE_DO_NOT_REPEAT'
    print(json.dumps({'passed':True,'uploadedFiles':4,'bytes':5614188,'everyServerSHA256Matched':True,'publicApplicationStillR50':True}))


if __name__=='__main__':main()
