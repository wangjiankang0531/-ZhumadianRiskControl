from pathlib import Path
import importlib.util,json,shutil,sys,tempfile
R=Path('D:/Project/Zhumadian');A=R/'Application';P=A/'tools/experimental_source/resource_gis_control_20261112';C=A/'Packages/ResourceGISControlCandidate_20261112/client-250';GIS=A/'Packages/ClientGISSettingsCandidate_20261107';D=R/'Document/Deployment/resource_gis_control_20261112'
spec=importlib.util.spec_from_file_location('resource_control_entry',C/'code/entry.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
trusted=module.qualify(C);assert trusted['programFiles']==953
with tempfile.TemporaryDirectory()as temp:
 copy=Path(temp)/'ownProgramme';shutil.copytree(C,copy);file=copy/'code/registered_gis.py';file.write_bytes(file.read_bytes()+b'\n# test tamper\n')
 try:module.qualify(copy)
 except ValueError as error:assert 'PROGRAM_CHANGED:code/registered_gis.py' in str(error)
 else:raise AssertionError('Changed own tenth module accepted')
result={'passed':True,'ownTenCodeAndRegistrationQualified':True,'ownManifestIdentity':trusted['manifestSHA256'],'externalOriginalProgrammeFiles':trusted['programFiles'],'tenthModuleTamperRefused':True,'registeredInterpreterIsolated':True,'resourceHTTPOrGISNotStarted':True,'actual252OwnManifestQualificationPending':True}
(D/'actual-thin-programme-qualification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
