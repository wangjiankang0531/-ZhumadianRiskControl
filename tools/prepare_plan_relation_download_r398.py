from pathlib import Path
import ast,hashlib,json,subprocess
R=Path('D:/Project/Zhumadian');V=Path(__file__).resolve().parent;D=R/'Document/Deployment/native_plan_resource_cancel_r385_20261103'
J=lambda p:json.loads(p.read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
C=R/'work/event_delivery_consistency_20261030/full-controller-r163/r155'
t=J(R/'work/plan-six-relations-ui-r396/terminal.json');assert t['allOwnedControllerHandlesTerminal']and t['originalGCodeAndPointersRestored']
f=J(C/'plan-browser/failure.json');assert f['message']=='EXERCISE_NATIVE_ATTACHMENT_DISK_BYTES'and len(f['cases'])==18 and not f['exceptions']
downloaded=list((C/'plan-browser/downloads').iterdir());assert len(downloaded)==1 and downloaded[0].read_bytes()==(C/'plan-browser/own-plan-exercise-r222.png').read_bytes()
b=(V/'verify_native_plan_six_relations_readonly_r396.mjs').read_text(encoding='utf-8')
anchor="  await until(()=>downloads.some(x=>x.state==='completed'));const downloaded=await fs.readdir(O+'/downloads');if(downloaded.length!==1||!(await fs.readFile(O+'/downloads/'+downloaded[0])).equals(png))throw Error('EXERCISE_NATIVE_ATTACHMENT_DISK_BYTES');"
replace=r'''
  stage='native-attachment-final-file-and-bytes';
  await until(()=>downloads.some(x=>x.state==='completed'));
  const diskObservations=[];let finalDownloadedName='';
  await until(async()=>{
   const names=await fs.readdir(O+'/downloads'),name=names.length===1?names[0]:null;
   const expectedName=downloads.find(x=>x.state==='begin')?.name;
   let exactBytes=false;try{if(name===expectedName&&!/\.(crdownload|tmp)$/i.test(name))exactBytes=(await fs.readFile(O+'/downloads/'+name)).equals(png)}catch{}
   if(diskObservations.length<16||exactBytes)diskObservations.push({files:names.length,finalNameMatches:name===expectedName,exactBytes});
   if(exactBytes)finalDownloadedName=name;return exactBytes;
  });
  await fs.writeFile(O+'/attachment-disk-evidence.json',JSON.stringify({passed:true,actualAnchorDownload:true,finalNameMatched:true,all68BytesExactlyMatched:true,completedEventObserved:true,observations:diskObservations},null,2));
'''
assert b.count(anchor)==1;b=b.replace(anchor,replace,1)
bf=V/'verify_native_plan_six_relations_disk_r398.mjs';assert not bf.exists();bf.write_text(b,encoding='utf-8')
p=subprocess.run(['D:/Program Files/nodejs/node.exe','--check',str(bf)],capture_output=True);assert p.returncode==0
s=(V/'plan_relation_ui_r396.py').read_text(encoding='utf-8').replace('plan-six-relations-ui-r396','plan-six-relations-ui-r398').replace('lifecycle-r396','lifecycle-r398')
s=s.replace("full-controller-r163/r155'","full-controller-r163/r157'").replace('verify_native_plan_six_relations_readonly_r396.mjs',bf.name)
s=s.replace('cb10dfddcbd49031662d7fea0267dc6bbbd3d9268d38692bb0274c4d0952edd3',sha(bf)).replace('verified-native-r396.json','verified-native-r398.json')
out=V/'plan_relation_ui_r398.py';assert not out.exists();ast.parse(s);out.write_text(s,encoding='utf-8')
prep=(V/'prepare_plan_relation_ui_fixture_r396.py').read_text(encoding='utf-8').replace('plan-six-relations-ui-r396','plan-six-relations-ui-r398').replace('lifecycle-r396','lifecycle-r398')
pf=V/'prepare_plan_relation_ui_fixture_r398.py';assert not pf.exists();ast.parse(prep);pf.write_text(prep,encoding='utf-8')
proof={'preparedOnly':True,'r396Native18CasesIncludingAllSixRelationReadonlyPassed':True,'r396CompletedDownloadFinalBytesActuallyMatchedAfterExit':True,
 'newTestWaitsForFinalFileNameAndExactBytesNotOnlyDownloadEvent':True,'actualContentEqualityRequirementRetained':True,
 'browserSHA256':sha(bf),'driverSHA256':sha(out),'fixturePreparerSHA256':sha(pf),'productCandidateChanged':False,'native29Pending':True}
(D/'download-retry-prepared-r398.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
