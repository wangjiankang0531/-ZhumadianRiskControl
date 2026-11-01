from pathlib import Path
import hashlib,json,os,shutil
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';B=R/'work/user_feedback_20261031';old=B/'emergency-workflow-source-r10';new=B/'emergency-workflow-source-r11';assert not new.exists()
pub=B/'published-emergency-frontend-r1';pins=json.loads((pub/'source-proof.json').read_bytes());rel='assets/js/index.vue_vue_type_script_setup_true_lang-DJ82oF-j.js';raw=(pub/'frontend'/rel).read_bytes();assert hashlib.sha256(raw).hexdigest()==pins['files'][rel]['sha256']and b'/zhumadian/map/'in raw
shutil.copytree(old/'source',new/'source',copy_function=os.link);rel='src/components/Map/index.vue';p=new/'source'/rel;before=p.read_bytes();marker=b'"/tianjinrisk/map/"';assert before.count(marker)==1;after=before.replace(marker,b'"/zhumadian/map/"');p.unlink();p.write_bytes(after)
stored=T/'frontend/emergency-map-same-origin'/rel;stored.parent.mkdir(parents=True,exist_ok=True);stored.write_bytes(after)
m=json.loads((old/'source-closure.json').read_bytes());key=rel.removeprefix('src/');m['sourceFiles'][key]={'source':str(stored),'sha256':hashlib.sha256(after).hexdigest(),'bytes':len(after),'overlay':True};m['overlayFiles']=sorted(set(m['overlayFiles'])|{key});m['sameOriginMapRestoration']={'path':rel,'beforeSHA256':hashlib.sha256(before).hexdigest(),'afterSHA256':hashlib.sha256(after).hexdigest(),'onlyExistingPublishedTileURLRestored':True,'coordinateLogicAndOriginalCenterUnchanged':True,'realZhumadianBaseMapAcceptance':False}
(new/'source-closure.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for name in ['build_emergency_workflow_source_20261101.mjs','verify_emergency_workflow_source_20261101.py']:
 p=T/name;s=p.read_text(encoding='utf-8');needle="'r8','r9','r10'";assert needle in s;s=s.replace(needle,"'r8','r9','r10','r11'");p.write_text(s,encoding='utf-8')
p=T/'verify_full_controller_material_r130_20261101.py';s=p.read_text(encoding='utf-8');s=s.replace("'candidate','guarded']","'candidate','guarded','manual']");s=s.replace('options=parser.parse_args()',"parser.add_argument('--seed-material-dictionary',action='store_true');options=parser.parse_args()")
s=s.replace("if options.variant=='guarded':prepared_base=guard_base/'candidate-install-r1'","if options.variant=='guarded':prepared_base=guard_base/'candidate-install-r1'\nif options.variant=='manual':prepared_base=base/'candidate-install-r2'")
anchor="        own=read(R/'work/event_delivery_consistency_20261030/full-business-main-r114/own-normal-login.private.json');"
extra='''        if options.seed_material_dictionary:
            assert options.variant=='manual'
            classes=root/'dictionary-classes';classes.mkdir();source=R/'Application/tools/java/material_full_controller_r1/OwnMaterialDictionaryFixture.java'
            compiled=subprocess.run([str(app/'runtime/jdk17/bin/javac.exe'),'-J-Xmx128m','--release','17','-encoding','UTF-8','-proc:none','-d',str(classes),str(source)],capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            assert compiled.returncode==0,'OWN_DICTIONARY_FIXTURE_COMPILE_FAILED'
            driver=next((app/'payload/business/lib').glob('mysql-connector-*.jar'))
            seeded=subprocess.run([reader['java'],'-Xmx128m','-cp',str(classes)+';'+str(driver),'OwnMaterialDictionaryFixture',str(row['databasePort']),identity['databaseUUID'],str(app/'UserData/OriginalServer/database/data')],input=fake_password.encode(),capture_output=True,timeout=40,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            assert seeded.returncode==0,'OWN_DICTIONARY_THREE_ROW_SEED_FAILED'
            checks['onlyExactThreeOwnSyntheticDictionaryRowsPrepared']=True
'''
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor)
s=s.replace("browser_source=R/'Application/tools/verify_full_controller_material_browser_r130_20261101.mjs'","browser_source=R/('Application/tools/verify_full_controller_material_add_browser_r130_20261101.mjs'if options.variant=='manual'else'Application/tools/verify_full_controller_material_browser_r130_20261101.mjs')")
p.write_text(s,encoding='utf-8')
installer=(T/'install_owned_table_order_candidate_r130_20261101.py').read_text(encoding='utf-8').replace('emergency-workflow-source-r10','emergency-workflow-source-r11').replace("C/'r1/","C/'r2/")
installer=installer.replace("baseline['originalDefectReproduced']","baseline['candidateProtected']").replace('full-controller-r129/candidate-install-r1/controller-fixture-ready.json','full-controller-r130/candidate-install-r1/controller-fixture-ready.json').replace("out=C/'candidate-install-r1'","out=C/'candidate-install-r2'")
installer=installer.replace("['tableRequestOrderWF10']={'onlyLatestRowsLoadingCallbacks':True,'WF9AllPriorGuardsPreserved':True,'publicInstalled':False}","['sameOriginMapWF11']={'onlyOriginalTileURLRestored':True,'originalCoordinateLogicUnchanged':True,'publicInstalled':False}").replace("release['tableRequestOrderCandidate']='WF10-only-newest-request-owns-table-state'","release['mapTileSameOriginCandidate']='WF11-restore-published-zhumadian-map-url'")
(T/'install_owned_map_candidate_r130_20261101.py').write_text(installer,encoding='utf-8')
print(json.dumps({'sourceRevision':'r11','onlyMapTileURLChanged':True,'existingPublishedR21MapURLVerified':True,'manualHostOptionalLiteralFDictionaryFixture':True,'dataOrRunningApplicationChanged':False}))
