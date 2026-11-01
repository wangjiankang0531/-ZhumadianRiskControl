from pathlib import Path
import ast
T=Path('D:/Project/Zhumadian/Application/tools')
s=(T/'build_public_unified_r23_20261101.py').read_text(encoding='utf-8')
s=s.replace('r23','r24').replace('R23','R24')
s=s.replace('original_public_test_update_r24_graceful_20261101.py','original_public_test_update_r24_20261101.py')
s=s.replace('r24-graceful-updater-contract-r1','r24-inherited-updater-contract-r1')
s=s.replace('full-controller-r117/r3','full-controller-r127/r1')
s=s.replace("assert checks['allPassed']and checks['checks']==123", "workflow=read(R/'work/user_feedback_20261031/r24-workflow-contract-r1/result.json')\nassert checks['allPassed']and checks['checks']==123 and workflow['allPassed']and workflow['checks']==34\nassert workflow['sourceSHA256']==checks['sourceSHA256']")
s=s.replace("len(tx['recoveryScenarios'])==10", "len(tx['recoveryScenarios'])==12")
s=s.replace('599','758').replace('584','607').replace('1183','1365')
s=s.replace("'updaterContractChecks':123", "'updaterContractChecks':157").replace("'actualCodeRecoveryScenarios':10", "'actualCodeRecoveryScenarios':12")
s=s.replace("'tools/original_platform_async_release_support.py'}", "'tools/original_platform_async_release_support.py','tools/original_server_release_parameters.py'}")
s=s.replace('other16OriginalControllersAndIISPreserved','other15OriginalControllersAndIISPreserved')
s=s.replace("'fullLoggedInBrowserOnWholeControllerAndRealNangangAcceptancePassed':False,", "'workflowCompiledFrontendFiles':338, 'workflowNormalRoleBrowserChecksInIndependentWF6Fixture':9,\n    'workflowWholeControllerAndSchemaPassedRunsInIndependentFixture':2, 'actualR24TaskAndParameterRuntimePinsPassed':True,\n    'fullLoggedInBrowserOnWholeControllerAndRealNangangAcceptancePassed':False,")
# The fresh lifecycle verifies the new updater's readiness addition against actual processes.
s=s.replace("assert whole['wholeSixComponentControllerActuallyExecuted']", "assert whole['checks']['actualR24WorkflowGuardRuntimePinsPassed']\nassert whole['wholeSixComponentControllerActuallyExecuted']")
ast.parse(s);p=T/'build_public_unified_r24_20261101.py';assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
print('R24 transport builder prepared, execution gated by new whole-controller result.')
