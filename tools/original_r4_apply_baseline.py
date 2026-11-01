"""Verify unchanged approved R4 and data identity; bind exact current process only during preparation."""
from pathlib import Path
import hashlib,json,re
R=Path('D:/Project/Zhumadian');Q=Path('D:/Zqa20261025/Application');RELEASE='b88f18d617c9bca989cc63ec1d265261d86713716b8e6d4f570cc7a513500de2'
def validate(current,approved,pins):
 if current.get('releaseSHA256')!=RELEASE:raise ValueError('EXACT_APPROVED_R4_RELEASE_REQUIRED')
 if not isinstance(current.get('currentBS'),str) or not re.fullmatch('j[1-9][0-9]*',current['currentBS']) or type(current.get('controllerPID')) is not int or current['controllerPID']<=0:raise ValueError('VERIFIED_CURRENT_R4_RUNTIME_REQUIRED')
 if not approved.get('oldState',{}).get('databaseUUID') or current.get('databaseUUID')!=approved['oldState']['databaseUUID']:raise ValueError('EXACT_APPROVED_R4_DATABASE_IDENTITY_REQUIRED')
 if not approved.get('dataIdentityPins') or pins!=approved['dataIdentityPins']:raise ValueError('EXACT_APPROVED_R4_INSTALLATION_CONFIG_AND_STORE_REQUIRED')
 return current
def capture():
 from verify_plan_report_local_state_20261030 import current
 source=R/'work/emergency_plan_report_20261030/lifecycle-emergency-modules-r4/prepared.private.json';approved=json.loads(source.read_bytes());names={str(Q/'UserData/OriginalServer/installation.json'),str(Q/'private/server-configuration.json'),str(Q/'UserData/OriginalServer/store-credentials.private.json')}
 if set(approved['dataIdentityPins'])!=names:raise ValueError('EXACT_THREE_APPROVED_R4_IDENTITY_FILES_REQUIRED')
 pins={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in names};return validate(current(),approved,pins)
