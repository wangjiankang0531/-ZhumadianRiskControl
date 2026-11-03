from pathlib import Path
import ast,hashlib,json
V=Path(__file__).resolve().parent
source=V/'plan_lifecycle_run_r37_native_r347.py'
raw=source.read_bytes();old=hashlib.sha256(raw).hexdigest()
assert old=='fb800729ab402e6412b05d92dfdbce0a56fc325a1505b1845f0dbd04fb0c4bb3'
text=source.read_text(encoding='utf-8')
a="        native_ui=verify_native_candidate(row)\n        print('OWN_FINAL_R39_NATIVE_21_CASES_WITH_DELETED_DETAIL_NAVIGATION_RETRY_REFRESH_PASSED',flush=True)"
b="""        native_ui_failure=None
        try:
            native_ui=verify_native_candidate(row)
            print('OWN_FINAL_R39_NATIVE_21_CASES_WITH_DELETED_DETAIL_NAVIGATION_RETRY_REFRESH_PASSED',flush=True)
        except BaseException as error:
            native_ui_failure={'type':type(error).__name__,'message':str(error)if isinstance(error,AssertionError)else'OWN_BROWSER_FAILED_SEE_SCOPED_DIAGNOSTIC'}
            dump(O/'candidate-native-ui-failure.json',native_ui_failure)
            print('OWN_NATIVE_UI_FAILED_PROCEEDING_TO_ACTUAL_ROLLBACK_AND_NORMAL_STOP',flush=True)"""
assert text.count(a)==1;text=text.replace(a,b,1)
a="phase='restore-original-G-code-and-pointers';restore_original();restored=True"
b=a+"\n        assert native_ui_failure is None,'OWN_NATIVE_UI_FAILED_AFTER_SAFE_ACTUAL_ROLLBACK_AND_RESTORE'"
assert text.count(a)==1;text=text.replace(a,b,1);ast.parse(text)
source.write_text(text,encoding='utf-8')
proof={'preparedOnly':True,'source':source.name,'supersededUnexecutedSourceSHA256':old,'finalSourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'onlyUIFailureHandlingChanged':True,'browserFailureWillBeRecordedAndReportedAfterActualRollbackNormalExitAndRestore':True,
 'candidateUpdaterOrBrowserSourceChanged':False,'actualLifecycleExecutedByThisPreparation':False}
out=V/'plan-native-lifecycle-driver-final-r348.json';assert not out.exists();out.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');print(json.dumps(proof))
