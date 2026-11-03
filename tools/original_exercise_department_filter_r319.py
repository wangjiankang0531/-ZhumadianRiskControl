"""Bind original exercise department search to its actual backend query field."""
from contextlib import contextmanager
from pathlib import Path
from hashlib import sha256

REL='src/views/emergencyPlans/structured/info/exerciseList.vue'
PIN='1a25dc4b6730467f834ebf074fbba723dd887eee136318bb11080c3b642f65cb'

@contextmanager
def exercise_department_override(project):
    root=Path(project).absolute()
    allowed=Path('D:/Project/Zhumadian/work/user_feedback_20261031')
    if root.resolve()!=root or not root.is_relative_to(allowed):
        raise ValueError('ISOLATED_EXERCISE_FILTER_BUILD_ONLY')
    file=root/REL
    for parent in [file,*file.parents]:
        if parent.exists()and(parent.lstat().st_file_attributes&1024):
            raise ValueError('EXERCISE_FILTER_REPARSE_REFUSED')
        if parent==root:break
    before=file.read_bytes()
    if sha256(before).hexdigest()!=PIN:
        raise ValueError('EXACT_ACTUAL_COMPILED_EXERCISE_LIST_REQUIRED')
    anchor=b'v-model={searchParam.department}'
    if before.count(anchor)!=1:raise ValueError('EXACT_EXERCISE_DEPARTMENT_BINDING_REQUIRED')
    after=before.replace(anchor,b'v-model={searchParam.organizeDepartment}',1)
    receipt={'path':REL,'beforeSHA256':sha256(before).hexdigest(),'afterSHA256':sha256(after).hexdigest(),
             'onlyOriginalBackendQueryFieldBindingChanged':True,'sourceRestored':False}
    try:
        file.write_bytes(after)
        yield receipt
    finally:
        if file.read_bytes()!=after:raise ValueError('FOREIGN_EXERCISE_FILTER_SOURCE_CHANGE_PRESERVED')
        file.write_bytes(before)
        receipt['sourceRestored']=file.read_bytes()==before
