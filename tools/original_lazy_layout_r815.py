"""Defer authenticated layout evaluation while retaining the original route guard."""
from contextlib import contextmanager
from pathlib import Path
import hashlib

RELATIVE = 'src/router/routes.ts'
REPLACEMENTS = {
    'import Layout from "@/layout/index.vue";':
        'const Layout = () => import("@/layout/index.vue");',
    'import RedirectLayout from "@/components/RedirectLayout/index.vue";':
        'const RedirectLayout = () => import("@/components/RedirectLayout/index.vue");',
}

def transform(before):
    source = before.decode('utf8')
    for old, new in REPLACEMENTS.items():
        if source.count(old) != 1 or new in source:
            raise ValueError('EXACT_ORIGINAL_LAYOUT_IMPORT_REQUIRED')
        source = source.replace(old, new)
    return source.encode('utf8')

@contextmanager
def lazy_layout_override(project):
    project = Path(project).absolute()
    assert project == Path('D:/Project/Zhumadian/work/user_feedback_20261031/event-research-level-r418/source')
    target = project/RELATIVE
    for parent in [target, *target.parents]:
        assert not parent.lstat().st_file_attributes & 0x400
    before = target.read_bytes()
    after = transform(before)
    proof = {'sourceRestored': False, 'onlyTwoLayoutImportsChanged': True,
        'beforeSHA256': hashlib.sha256(before).hexdigest(),
        'afterSHA256': hashlib.sha256(after).hexdigest()}
    try:
        target.write_bytes(after)
        yield proof
    finally:
        assert target.read_bytes() == after, 'FOREIGN_ROUTE_CHANGE_REFUSE_RESTORE'
        target.write_bytes(before)
        proof['sourceRestored'] = target.read_bytes() == before
