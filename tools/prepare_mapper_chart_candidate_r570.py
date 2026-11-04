from pathlib import Path
import ast, hashlib, json, sys
sys.dont_write_bytecode = True
R = Path('D:/Project/Zhumadian')
A, V = R/'Application', Path(__file__).resolve().parent
D = R/'Document/Deployment/mapper_chart_candidate_r44_20261104'
S = R/'Document/Deployment/workplace_style_delivery_r564_20261104'
J = lambda p: json.loads(p.read_bytes())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert not D.exists()
base = A/'tools/original_public_test_update_r42_mapper_equivalence_r457.py'
assert sha(base) == '5e63e0f3e1f7d1064b5ae1276bfee56d51ce58b0e0ea64f59e30238c1c2d8b30'
styles = J(S/'prepared-css-delivery-r564.json')
assert J(S/'nginx-transport-result-r566.json')['passed']
assert J(S/'chart-style-browser-result-r562.json')['passed']
rows = styles['files']
assert set(rows) == {'frontend/security_pc/index.html', 'frontend/security_pc/assets/css/xnby-workplace-period-736f7b07dd2c.css'}
assert sum(p['bytes'] for p in rows.values()) == 4506
contract = {'revision':'scoped-chart-period-header-and-content-spacing-v1',
    'files':rows, 'scopeIds':['data-v-0c8e02ef','data-v-7ffd414d'],
    'onlyScopedLayoutAndOneHTMLLink':True, 'originalScriptsAPIsAndDateQueriesRetained':True,
    'originalHashNamedAssetsNotOverwritten':True, 'publicLayoutAcceptedByStartup':False}
source = base.read_text('utf-8')
tree = ast.parse(source)
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'r38_unified_bundle_contract')
old = ast.get_source_segment(source, function)
new = old
replacements = [
    ('expected_files.update(R38_FRONTEND_ROWS);expected_files[R39_PLAN_CLASS]=R39_PLAN_ROW',
     'expected_files.update(R38_FRONTEND_ROWS);expected_files.update(R44_STYLE_ROWS);expected_files[R39_PLAN_CLASS]=R39_PLAN_ROW'),
    ('expected.update(publicAccepted=False,publicTestRevision=R38_REVISION)',
     'expected.update(publicAccepted=False,publicTestRevision=R38_REVISION);expected[R44_STYLE_FIELD]=R44_STYLE_CONTRACT'),
    ("changed={n:p for n,p in R38_FRONTEND_ROWS.items()if oldfront.get(n)!=p}",
     "changed={n:p for n,p in R38_FRONTEND_ROWS.items()if oldfront.get(n)!=p};changed.update({n:p for n,p in R44_STYLE_ROWS.items()if previous['files'].get(n)!=p})")]
for before, after in replacements:
    assert new.count(before) == 1
    new = new.replace(before, after)
constants = ('R44_STYLE_ROWS = '+repr(rows)+'\nR44_STYLE_FIELD = "workplacePeriodHeaders"\nR44_STYLE_CONTRACT = '+repr(contract)+'\n\n')
source = source.replace(old, constants+new)
revision = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == 'R38_REVISION' for x in n.targets))
old_revision = ast.get_source_segment(base.read_text('utf-8'), revision)
assert source.count(old_revision) == 1
source = source.replace(old_revision, "R38_REVISION='20261104-R44-mapper-and-workplace-period-style'")
candidate_tree = ast.parse(source)
before_functions = {n.name:ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
after_functions = {n.name:ast.dump(n, include_attributes=False) for n in candidate_tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
assert set(before_functions) == set(after_functions)
changed = [n for n in before_functions if before_functions[n] != after_functions[n]]
assert changed == ['r38_unified_bundle_contract']
out = V/'original_public_test_update_r44_mapper_chart_r570.py'
assert not out.exists()
out.write_text(source, encoding='utf-8', newline='\n')
D.mkdir()
report = {'prepared':True,'runtimeSource':str(out),'runtimeSHA256':sha(out),'runtimeBytes':out.stat().st_size,
    'parentR42SHA256':sha(base),'changedFunctions':changed,'unchangedFunctions':len(before_functions)-1,
    'exactStyleRows':rows,'styleContract':contract,'originalMapperEquivalenceFixRetained':True,
    'lifecycleRestoreHealthAndAuthFunctionASTRetained':True,'supervisionModuleOrOnlineFormCandidateIncluded':False,
    'publicUploadedOrDeployed':False,'fullCloneReady':False}
(D/'prepared-runtime-r570.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'prepared':True,'changedFunctions':changed,'unchangedFunctions':report['unchangedFunctions'],'styleFiles':2,'publicDeployed':False}))
