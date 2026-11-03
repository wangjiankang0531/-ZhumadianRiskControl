from pathlib import Path
V=Path(__file__).parent
s=(V/'cleanup_completed_browser_profiles_r254.ps1').read_text(encoding='utf-8').replace("@('r119','r120','r122')","@('r131','r132')").replace('original_task_attachment_verified_r254_20261103','original_mapper_product_verified_r272_20261103').replace('xnby.r254','xnby.r272').replace('r122','r132').replace('full-controller-r163/r119/','full-controller-r163/r131/').replace('full-controller-r163/r120/','full-controller-r163/r132/')
p=V/'cleanup_product_browsers_r272.ps1';assert not p.exists();p.write_text(s,encoding='utf-8');print('SCOPED_R131_R132_COMPLETED_PROFILE_CLEANUP_PREPARED')
