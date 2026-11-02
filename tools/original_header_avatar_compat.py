"""Scope original native header images and retain a real icon when an image fails."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
T=Path(__file__).resolve().parent
HEADER='src/layout/components/header-user.vue'
EXTRA='src/utils/OriginalHeaderAvatarSource.ts'
SOURCE_SHA256='1176f65a5db7361ebbea1c542c30c117b4f77b291cd385eb7214e32b94fa37bc'
def adapt_header_avatar(raw):
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('EXACT_ORIGINAL_HEADER_AVATAR_SOURCE_REQUIRED')
    text=raw.decode('utf-8')
    def once(a,b):
        nonlocal text
        if text.count(a)!=1:raise ValueError('EXACT_HEADER_AVATAR_ANCHOR_REQUIRED')
        text=text.replace(a,b,1)
    once(':src="loginUser.headIcon"',':src="avatarImageSource"')
    once(':icon="loginUser.headIcon ? void 0 : UserOutlined"',':icon="UserOutlined"')
    once('import { computed, ref, unref } from "vue";','import { computed, ref, unref } from "vue";\nimport { projectAvatarImageSource } from "@/utils/OriginalHeaderAvatarSource";')
    once('const loginUser = computed<any>(() => userStore.info ?? {});','const loginUser = computed<any>(() => userStore.info ?? {});\nconst avatarImageSource = computed(() => projectAvatarImageSource(loginUser.value.headIcon, import.meta.env.VITE_API_URL, window.location.origin));')
    return text.encode('utf-8')
@contextmanager
def header_avatar_override(project):
    project=Path(project).absolute();roots=[Path('D:/Project/Zhumadian/work'),Path('D:/Project/Zhumadian/Application/work')]
    if project.resolve()!=project or not any(project.is_relative_to(root)for root in roots):raise ValueError('ONLY_ISOLATED_OWN_BUILD_COPY')
    p=project/HEADER;extra=project/EXTRA
    for target in [project,p,p.parent,extra.parent]:
        if target.resolve()!=target or target.is_symlink()or getattr(target.lstat(),'st_file_attributes',0)&0x400:raise ValueError('REGULAR_BUILD_INPUT_REQUIRED')
    before=p.read_bytes()
    if extra.exists():raise ValueError('AVATAR_HELPER_ALREADY_PRESENT')
    transformed=adapt_header_avatar(before);helper=(T/'frontend/OriginalHeaderAvatarSource.ts').read_bytes()
    receipt={'files':{HEADER:{'beforeSHA256':hashlib.sha256(before).hexdigest(),'adaptedSHA256':hashlib.sha256(transformed).hexdigest()},EXTRA:{'beforeSHA256':None,'adaptedSHA256':hashlib.sha256(helper).hexdigest()}},'originalSourcesRestored':False}
    try:
        p.write_bytes(transformed);extra.write_bytes(helper);yield receipt
    finally:
        if p.read_bytes()not in[before,transformed]:raise ValueError('OTHER_BUILD_HEADER_EDIT_REFUSED_RESTORE')
        if extra.exists()and extra.read_bytes()!=helper:raise ValueError('OTHER_BUILD_HELPER_EDIT_REFUSED_RESTORE')
        p.write_bytes(before);extra.unlink(missing_ok=True)
        if p.read_bytes()!=before or extra.exists():raise ValueError('ORIGINAL_AVATAR_INPUT_RESTORE_REQUIRED')
        receipt['originalSourcesRestored']=True
