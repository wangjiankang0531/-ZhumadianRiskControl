"""Declared disposal submit guard on the exact 204-file login candidate.

All other emitted differences must invert to consistent module filename changes.
Equivalent Vue sources are review aids, not a claim of a whole source rebuild.
"""
from pathlib import Path
import hashlib
import json
import sys

T = Path('D:/Project/Zhumadian/Application/tools')
sys.path.insert(0, str(T))
from build_published_emergency_login_query_20261101 import materialize as login_candidate

W = Path('D:/Project/Zhumadian/work/user_feedback_20261031')
D = W / 'emergency-disposal-busy-r1'
OLD_SUBMIT = 'y({submit:async()=>{b.value.id=n.query.id;const e=O,a="操作成功！";await u.value.validate()&&(await e(b.value),E.success(a),c.push({path:"/emergencyResponse/taskSend"}))}})'
NEW_SUBMIT = 'y({submitting:ownDisposalSaving,submit:async()=>{if(ownDisposalSaving.value)return!1;ownDisposalSaving.value=!0;try{b.value.id=n.query.id;if(!await u.value.validate())return!1;await O(b.value);E.success("操作成功！");await c.push({path:"/emergencyResponse/taskSend"});return!0}catch(ownError){if(!ownError||!ownError.response&&!ownError.data)E.error("提交失败，请重试");return!1}finally{ownDisposalSaving.value=!1}}})'
OLD_BUTTON = 'g(y).query.judge?(f(),k(n,{key:1,type:"primary",onClick:(e=u.value)==null?void 0:e.submit},{default:v(()=>c[1]||(c[1]=[h("提交")])),_:1},8,["onClick"])):x("",!0)'
NEW_BUTTON = 'g(y).query.judge?(f(),k(n,{key:1,type:"primary",loading:!!(u.value&&u.value.submitting),disabled:!!(u.value&&u.value.submitting),onClick:(e=u.value)==null?void 0:e.submit},{default:v(()=>c[1]||(c[1]=[h("提交")])),_:1},8,["loading","disabled","onClick"])):x("",!0)'
OLD_DECLARATION = 'c=R(),n=D();return U(async()=>{if(!n.query.id)return;'
NEW_DECLARATION = 'c=R(),n=D(),ownDisposalSaving=o(!1);return U(async()=>{if(!n.query.id)return;'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def materialize():
    source = login_candidate()
    base = json.loads((source.parent / 'candidate-proof.json').read_bytes())
    inputs = {name: (source / name).read_bytes() for name in base['files']}
    assert len(inputs) == 204
    for name, raw in inputs.items():
        assert sha(raw) == base['files'][name]['sha256']
    renamed = {name: 'assets/js/q2-' + Path(name).name.removeprefix('q1-') for name in inputs if name.startswith('assets/js/') and name.endswith('.js')}
    target = 'assets/js/q1-index-CVlZSchS.js'
    outputs = {}
    for name, raw in inputs.items():
        expected = raw
        if name == target:
            text = raw.decode('utf-8')
            assert 'ownDisposalSaving' not in text
            for old, new in [(OLD_DECLARATION, NEW_DECLARATION), (OLD_SUBMIT, NEW_SUBMIT), (OLD_BUTTON, NEW_BUTTON)]:
                assert text.count(old) == 1
                text = text.replace(old, new, 1)
            expected = text.encode('utf-8')
        result = expected
        for before, after in renamed.items():
            result = result.replace(Path(before).name.encode(), Path(after).name.encode())
        inverted = result
        for before, after in renamed.items():
            inverted = inverted.replace(Path(after).name.encode(), Path(before).name.encode())
        assert inverted == expected, 'ONLY_DECLARED_SUBMIT_AND_FILENAME_REFERENCES_MAY_CHANGE'
        if Path(name).suffix not in ['.js', '.html', '.css', '.json', '.svg', '.txt']:
            assert result == raw
        outputs[renamed.get(name, name)] = result
    files = {name: {'bytes': len(raw), 'sha256': sha(raw)} for name, raw in outputs.items()}
    if D.exists():
        saved = json.loads((D / 'candidate-proof.json').read_bytes())
        assert saved['files'] == files
        for name, raw in outputs.items():
            assert (D / 'frontend' / name).read_bytes() == raw
        return D / 'frontend'
    D.mkdir()
    for name, raw in outputs.items():
        p = D / 'frontend' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
    originals = Path('D:/Project/Zhumadian/Application/work/tianjin_native_20261023/emergency_pc/src/views/emergencyResponse/taskSend/info')
    detail = (originals / 'detail.vue').read_text(encoding='utf-8')
    start = detail.index('const handleSubmit = async () => {')
    end = detail.index('\ndefineExpose({', start)
    replacement = '''const submitting = ref(false);
const handleSubmit = async () => {
  if (submitting.value) return false;
  submitting.value = true;
  try {
    fieldJudge.value.id = route.query.id;
    if (!(await form1Ref.value!.validate())) return false;
    await updateById(fieldJudge.value);
    ElMessage.success("操作成功！");
    await router.push({ path: "/emergencyResponse/taskSend" });
    return true;
  } catch (error: any) {
    // Preserve existing server errors; show a fallback for failures without a response.
    if (!error || (!error.response && !error.data)) ElMessage.error("提交失败，请重试");
    return false;
  } finally {
    submitting.value = false;
  }
};
'''
    detail = detail[:start] + replacement + detail[end:]
    detail = detail.replace('defineExpose({\n  submit: handleSubmit', 'defineExpose({\n  submitting,\n  submit: handleSubmit', 1)
    parent = (originals / 'index.vue').read_text(encoding='utf-8')
    anchor = 'v-if="route.query.judge" @click="detailRef?.submit"'
    assert parent.count(anchor) == 1
    parent = parent.replace(anchor, 'v-if="route.query.judge" :loading="detailRef?.submitting" :disabled="detailRef?.submitting" @click="detailRef?.submit"', 1)
    (D / 'detail-source-equivalent.vue').write_text(detail, encoding='utf-8')
    (D / 'parent-source-equivalent.vue').write_text(parent, encoding='utf-8')
    proof = {'files': files, 'fileCount': 204, 'loginCandidateManifestSHA256': sha((source.parent / 'candidate-proof.json').read_bytes()),
             'originalPublishedBaseFiles': 204, 'old206CandidateNotUsed': True,
             'onlyOneOriginalTaskDetailModuleSemanticallyChanged': True,
             'changes': ['synchronous guard before validation', 'finally clears guard on validation/error/success',
                         'existing error presentation retained and form values kept', 'loading/disabled bindings with Vue patch props'],
             'allOtherDifferencesInvertToFilenameReferences': True, 'renamedModules': renamed,
             'equivalentVueOnlyNotClaimedAsWholeSourceBuild': True, 'originalVueSourcesUnmodified': True,
             'backendAuthenticationBusinessModelsAndCallbackUnchanged': True, 'publicInstalled': False}
    (D / 'candidate-proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    return D / 'frontend'


if __name__ == '__main__':
    print('DISPOSAL_SUBMIT_GUARD_CANDIDATE', materialize())
