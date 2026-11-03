"""Catch only normal Element Plus cancel/close rejections in the exact R224 resource components."""
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path
BASE='src/views/emergencyPlans/structured/components/'
PINS={'goodsList':'e81317dcafbf5c1108775f7cbc3e892709f1af03618eea029d294fef7bb33b45',
      'teamsList':'0aaa1adc6691b055a2a50e3ac3533184ba227b52bc7cea35eeda329cbd50723c',
      'expertsList':'5298e8308b6fbdac305f54a38832b0936c2514d087104c025f0f1623dcfb0de7'}
def transform(kind,raw):
    if kind not in PINS or sha256(raw).hexdigest()!=PINS[kind]:raise ValueError('EXACT_RETAINED_PLAN_RESOURCE_COMPONENT_REQUIRED')
    text=raw.decode('utf-8').replace('\r\n','\n');old='    emit("delete", index);\n  });'
    if text.count(old)!=1:raise ValueError('EXACT_RESOURCE_DELETE_CONFIRM_ANCHOR_REQUIRED')
    text=text.replace(old,'    emit("delete", index);\n  }).catch(action => {\n    if (action !== "cancel" && action !== "close") throw action;\n  });',1)
    candidate=text.encode('utf-8')
    return candidate,{'beforeSHA256':sha256(raw).hexdigest(),'afterSHA256':sha256(candidate).hexdigest(),
        'onlyExpectedCancelAndCloseRejectionsConsumed':True,'unexpectedRejectionsRethrown':True,'resourceSelectionIDsAndSaveAPIsChanged':False}
@contextmanager
def resource_cancel_override(project):
    project=Path(project).resolve();work=Path('D:/Project/Zhumadian/work').resolve()
    if not project.is_relative_to(work):raise ValueError('ONLY_OWN_BUILD_PROJECT_UNDER_WORK')
    saved={};after={};receipt={'files':{},'sourceRestored':False}
    for kind in PINS:
        rel=BASE+kind+'.vue';raw=(project/rel).read_bytes();candidate,proof=transform(kind,raw);saved[rel]=raw;after[rel]=candidate;receipt['files'][rel]=proof
    try:
        for rel,raw in after.items():(project/rel).write_bytes(raw)
        yield receipt
    finally:
        for rel,raw in after.items():
            if(project/rel).read_bytes()!=raw:raise ValueError('FOREIGN_BUILD_SOURCE_DRIFT_REFUSE_RESTORE')
        for rel,raw in saved.items():(project/rel).write_bytes(raw)
        receipt['sourceRestored']=all((project/rel).read_bytes()==raw for rel,raw in saved.items())
