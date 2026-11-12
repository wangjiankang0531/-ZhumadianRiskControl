from pathlib import Path
import hashlib,json,sys
from unittest.mock import patch
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_control_20261112';GIS=A/'Packages/ClientGISSettingsCandidate_20261107';D=R/'Document/Deployment/resource_gis_control_20261112'
sys.path[:0]=[str(P/'code'),str(GIS/'code'),str(GIS/'provider/tools')]
from registered_gis import RegisteredGIS
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[A/'private/client-workspace.json',GIS/'client-gis-install.json',R/'UserData/ClientGIS/active.private.json'];before=[sha(f)for f in files]
def forbidden(*args,**kw):raise AssertionError('READONLY_MUST_NOT_START_STOP_OR_RECOVER')
with patch('registered_gis.original_stop',forbidden),patch('registered_gis.subprocess.Popen',forbidden),patch('registered_gis.recover',forbidden),patch('registered_gis.state_directory',forbidden):
 gis=RegisteredGIS(GIS,files[0],expected_manifest=before[1]);gis.starter=gis.stopper=forbidden;value=gis.status();assert value['phase']=='ready'and value['owned']is True
 assert [sha(f)for f in files]==before
(D/'actual250-readonly-status.json').write_text(json.dumps({'passed':True,'registered953Qualified':True,'currentGISPhase':value['phase'],'ownedOriginalInstance':value['owned'],'protectedConfigManifestAndActiveUnchanged':True,'startStopSpawnRecoveryAndStateWriteForbidden':True,'notPublicOr252OrRootRelocationAcceptance':True},indent=2)+'\n')
print(json.dumps({'actual250ReadOnly':True,'phase':value['phase'],'allProtectedPinsUnchanged':True}))
