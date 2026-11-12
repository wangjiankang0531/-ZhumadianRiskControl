"""Reuse known owned-process/request helpers; replace the test scenarios explicitly."""
from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent
source=V/'test_managed_worker_to_qualified_manager_r2395.py';text=source.read_text('utf8')
anchor="try:\n    config=Q/'private-QA/config/client-workspace.json'";assert text.count(anchor)==1
prefix=text[:text.index(anchor)].replace('xnby-resource-http-r2395','xnby-resource-control-r2422')
prefix=prefix.replace("A/'tools/experimental_source/client_resource_worker_r2369/package'","A/'tools/experimental_source/client_resource_ingress_r2397/package'")
prefix=prefix.replace("A/'Packages/ResourceManagerCandidate_20261112/client-250'","A/'Packages/ResourceGISControlCandidate_20261112/client-250'")
prefix=prefix.replace('e8aca5df66078aecba8414fbfff1e4249ec77a4a898cd55e0411b6d358deb8a6','6989d7a2429dc938bd8458c2a37fa038b3f847c61375f17395e44813a833a9a3')
prefix=prefix.replace('2d5561fa553ad5a199ff60a87cb1c89d334b78d3c0c67d2c909fb21f8db4e6b5','bdf6d7e1814deb80cb63db4235d6e5748175a4f4a0c2eac679a2b7d387a4674b')
prefix=prefix.replace('qualified_resource_http_backend_r2395.py','resource_control_http_backend_r2422.py')
prefix=prefix.replace('receiver-r2393-','receiver-r2422-').replace('R2393','R2422')
body=(V/'resource_control_chain_body_r2422.py').read_text('utf8');result=prefix+body
ast.parse(result);p=V/'test_resource_control_chain_r2422.py';assert not p.exists();p.write_text(result,'utf8')
print(json.dumps({'prepared':True,'driverSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'actualFixedD175OnlyQAFactoryOverrides':True,'productionPackageChanged':False}))
