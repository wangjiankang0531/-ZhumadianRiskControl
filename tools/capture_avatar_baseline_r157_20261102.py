from pathlib import Path
import importlib.util,json,subprocess,sys
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';V=Path(__file__).parent
sys.path.insert(0,str(T));sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('r157_build_helpers',V/'build_avatar_full_r157_20261102.py');helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
import build_risk_frontend_r22_r2_20261101 as recipe
recipe.STAGE=helpers.ROOT/'security-baseline-source-capture'
assert not recipe.STAGE.exists()
class CapturedBeforeCompiler(Exception):pass
original_run=subprocess.run
def intercept(command,*args,**kwargs):
 if isinstance(command,list)and any('vite' in str(x)and str(x).endswith('vite.js')for x in command):
  helpers.dump(recipe.STAGE/'actual-retained-recipe-source-files.json',helpers.inventory(Path(kwargs['cwd'])))
  raise CapturedBeforeCompiler()
 return original_run(command,*args,**kwargs)
subprocess.run=intercept
try:
 try:recipe.main()
 except CapturedBeforeCompiler:pass
 else:raise AssertionError('BASELINE_COMPILER_UNEXPECTEDLY_RAN')
finally:subprocess.run=original_run
cfg=json.loads((R/'Document/Deployment/confirmed_operations_20261029/security-build-r2-config.json').read_bytes())
assert helpers.inventory(recipe.STAGE/'source')==helpers.inventory(Path(cfg['project']))
helpers.dump(recipe.STAGE/'capture-result.json',{'capturedActualFullPriorAdapterStackAtCompilerBoundary':True,'compilerExecuted':False,'allContextsUnwoundAndSourceRestored':True,'publicChanged':False})
print('ACTUAL_RETAINED_SAFETY_RECIPE_SOURCE_CAPTURED_WITHOUT_COMPILER_AND_RESTORED')
