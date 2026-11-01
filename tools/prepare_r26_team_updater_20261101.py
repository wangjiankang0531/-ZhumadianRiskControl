from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';old=T/'original_public_test_update_r25_20261101.py';out=T/'original_public_test_update_r26_20261101.py';assert not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old)=='44c846481bc7eb58447374ea37653da6b806e4471ce6a2a83d64c9e901010cb3'
q=json.loads((W/'r25-material-unified-candidate-r1/bundle/payload/payload-manifest.json').read_bytes())
target='payload/business/run-template/classes/mapper/FirstAidTeamMembersMapper.xml';jar='payload/business/application.jar';service='payload/business/run-template/classes/com/iemp/endanger/server/firstAidTeams/service/impl/FirstAidTeamsServiceImpl.class'
assert q['files'][service]['sha256']=='69268ff421ea2f19f03f9616dae73d3f24c8fa52f7031419b48339cfbb1d4ac4'and target not in q['files']
rows={target:{'bytes':2568,'sha256':'2da1a794cc65c6fc7c024c2a647cf9e2e2d967f1b14bdf53e90c35776e45e8fd'}}
block='R26_TEAM_FIELD = "nativeTeamMemberMapper"\nR26_TEAM_ROWS = '+repr(rows)+'\nR26_TEAM_SOURCE = '+repr({jar:q['files'][jar],service:q['files'][service]})+'\nR26_TEAM_CONTRACT = {"revision": "original-members-default-scan-v1", "resources": R26_TEAM_ROWS, "retainedSources": R26_TEAM_SOURCE}\n\n'
block+='''def team_declared(release, payload):
    present = set(R26_TEAM_ROWS).intersection(payload['files'])
    require({n for n in payload['files'] if n.startswith('payload/business/run-template/classes/mapper/')}
            <= set(R26_TEAM_ROWS), 'UNDECLARED_TEAM_MAPPER_RESOURCE_REFUSED')
    if R26_TEAM_FIELD not in release:
        require(not present, 'EXPLICIT_TEAM_MAPPER_DESCRIPTOR_REQUIRED')
        return False
    require(release[R26_TEAM_FIELD] == R26_TEAM_CONTRACT, 'EXACT_TEAM_MAPPER_DESCRIPTOR_REQUIRED')
    require(material_declared(release, payload), 'TEAM_MAPPER_REQUIRES_RETAINED_MATERIAL_CONTRACT')
    require(all(payload['files'].get(n) == pin for n, pin in {**R26_TEAM_ROWS, **R26_TEAM_SOURCE}.items()),
            'EXACT_TEAM_MAPPER_AND_RETAINED_SOURCE_PINS_REQUIRED')
    return True


def team_bundle_contract(app, bundle, plan, old, release, payload):
    declared = team_declared(release, payload)
    if not declared:
        require(R26_TEAM_FIELD not in old and not set(R26_TEAM_ROWS).intersection(plan['files']),
                'RETAINED_TEAM_MAPPER_CANNOT_BE_DROPPED')
        return False
    previous = read(check_file(app, 'payload-manifest.json', old['payloadManifestSHA256']))
    require(old.get(R25_MATERIAL_FIELD) == R25_MATERIAL_CONTRACT
            and all(previous['files'].get(n) == pin for n, pin in R25_MATERIAL_ROWS.items()),
            'TEAM_UPDATE_REQUIRES_EXACT_INSTALLED_MATERIAL_BASE')
    fresh = R26_TEAM_FIELD not in old
    if fresh:
        require(not set(R26_TEAM_ROWS).intersection(previous['files'])
                and set(R26_TEAM_ROWS).issubset(plan['files']), 'COMPLETE_FRESH_TEAM_MAPPER_TRANSPORT_REQUIRED')
    else:
        require(old[R26_TEAM_FIELD] == R26_TEAM_CONTRACT
                and all(previous['files'].get(n) == pin for n, pin in R26_TEAM_ROWS.items()),
                'EXACT_RETAINED_TEAM_MAPPER_REQUIRED')
    retained = lambda files: {n: pin for n, pin in files.items()
        if not n.startswith('frontend/emergency_pc/') and n not in R26_TEAM_ROWS}
    require(retained(previous['files']) == retained(payload['files']), 'TEAM_UPDATE_OTHER_PAYLOAD_MUST_BE_RETAINED')
    legal = {'release-manifest.json', 'payload-manifest.json', 'tools/original_public_test_update.py'} | set(R26_TEAM_ROWS)
    legal.update(n for n in payload['files'] if n.startswith('frontend/emergency_pc/'))
    require(set(plan['files']) <= legal, 'TEAM_UPDATE_EXACT_TRANSPORT_SCOPE_REQUIRED')
    for name, pin in R26_TEAM_SOURCE.items():
        check_file(app, name, pin['sha256'], pin['bytes'])
    import zipfile
    source = 'payload/business/application.jar'
    with zipfile.ZipFile(regular(app, source)) as archive:
        info = archive.getinfo('xml/FirstAidTeamMembersMapper.xml')
        require(info.file_size == 2568, 'ORIGINAL_MEMBER_XML_SIZE_REQUIRED')
        raw = archive.read(info)
    require(hashlib.sha256(raw).hexdigest() == next(iter(R26_TEAM_ROWS.values()))['sha256'],
            'ORIGINAL_MEMBER_XML_BYTES_REQUIRED')
    for name, pin in R26_TEAM_ROWS.items():
        if name in plan['files']:
            require(plan['files'][name] == {'bytes': pin['bytes'], 'SHA256': pin['sha256']},
                    'EXACT_TEAM_MAPPER_TRANSPORT_PIN_REQUIRED')
        check_file(bundle / 'payload' if name in plan['files'] else app, name, pin['sha256'], pin['bytes'])
    return True


def team_ready(app, row):
    release = read(regular(app, 'release-manifest.json'))
    payload = read(check_file(app, 'payload-manifest.json', release['payloadManifestSHA256']))
    if not team_declared(release, payload):
        return None
    require(material_ready(app, row) is not None, 'TEAM_MAPPER_RUNTIME_REQUIRES_RETAINED_MATERIAL')
    run = regular(app, Path(row['run']).absolute().relative_to(app).as_posix())
    require(run.parent == app / 'UserData/OriginalServer/runs'
            and re.fullmatch(r'j[1-9][0-9]{0,3}', run.name) is not None, 'OWNED_TEAM_MAPPER_RUN_REQUIRED')
    business = regular(run, 'b')
    owner = marker(regular(business, 'server-owner.properties'))
    require(owner.get('schema') == 'zhumadian.original.server.owner.v1'
            and owner.get('ownerId') == row['ownerId'], 'TEAM_MAPPER_RUNTIME_OWNER_MISMATCH')
    for name, pin in {**R26_TEAM_ROWS, **R26_TEAM_SOURCE}.items():
        check_file(app, name, pin['sha256'], pin['bytes'])
        if name.startswith('payload/business/run-template/'):
            check_file(business, name.removeprefix('payload/business/run-template/'), pin['sha256'], pin['bytes'])
    return {'originalTeamMemberXMLAndRetainedServiceRuntimeBytePinned': True,
            'actualMappedStatementOrAuthenticatedBusinessAcceptanceClaimed': False,
            'businessRecordsAccountsSessionsOrCredentialsRead': False}


'''
s=old.read_text(encoding='utf-8');a='def material_declared(release, payload):';assert s.count(a)==1;s=s.replace(a,block+a)
a="    legal = {'release-manifest.json', 'payload-manifest.json', 'tools/original_public_test_update.py'} | set(R25_MATERIAL_ROWS)";assert s.count(a)==1;s=s.replace(a,"    team = team_bundle_contract(app, bundle, plan, old, release, payload)\n"+a+" | (set(R26_TEAM_ROWS) if team else set())")
a="if not n.startswith('frontend/emergency_pc/') and n not in R25_MATERIAL_ROWS}";assert s.count(a)==1;s=s.replace(a,"if not n.startswith('frontend/emergency_pc/') and n not in R25_MATERIAL_ROWS and not (team and n in R26_TEAM_ROWS)}")
a='or name in R25_MATERIAL_ROWS or name in (';assert s.count(a)==1;s=s.replace(a,'or name in R25_MATERIAL_ROWS or name in R26_TEAM_ROWS or name in (')
a='    material_ready(app, row)\n\ndef installed_overlay';assert s.count(a)==1;s=s.replace(a,'    material_ready(app, row)\n    team_ready(app, row)\n\ndef installed_overlay')
defs=lambda raw:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
x=defs(old.read_text(encoding='utf-8'));y=defs(s);assert {n for n in x if x[n]!=y[n]}=={'load_bundle','health','material_bundle_contract'}and set(y)-set(x)=={'team_declared','team_bundle_contract','team_ready'}
out.write_text(s,encoding='utf-8',newline='\n');print(json.dumps({'updaterPrepared':True,'changedExistingFunctions':['load_bundle','health','material_bundle_contract'],'newFunctions':['team_declared','team_bundle_contract','team_ready'],'normalStopBackupReplaceRestoreASTUnchanged':True,'oneExactOriginalXMLPermitted':True,'sourceSHA256':sha(out),'publicOrOwnedApplicationChanged':False}))
