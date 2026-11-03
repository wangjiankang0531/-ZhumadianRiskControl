from pathlib import Path
V=Path(__file__).parent
s=(V/'cleanup_completed_browser_profiles_r254.ps1').read_text(encoding='utf-8').replace("@('r119','r120','r122')","@('r130')").replace('original_task_attachment_verified_r254_20261103','original_mapper_registration_verified_r264_20261103').replace('xnby.r254','xnby.r264').replace('full-controller-r163/r119/','full-controller-r163/r130/').replace('full-controller-r163/r120/','full-controller-r163/r130/').replace('full-controller-r163/r122/','full-controller-r163/r130/')
p=V/'cleanup_mapper_browser_r264.ps1';assert not p.exists();p.write_text(s,encoding='utf-8')
print('EXACT_R130_OWN_COMPLETED_PROFILE_CLEANUP_PREPARED')
