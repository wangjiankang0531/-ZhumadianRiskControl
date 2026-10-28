"""Repair independent credential persistence and fail atomically on invalid input.

Reference and installed runtimes remain read-only. This adapter does not change
dictionaries, permissions, docking, field widths or business ownership semantics.
"""
from pathlib import Path
import hashlib

SOURCE_SHA256 = 'ba420cb3938e31d105ad2c1fe6636089664acc53c65c1d7f209fe3db66074a7d'


def adapt(raw: bytes) -> bytes:
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError('PINNED_ORIGINAL_THIRD_PARTY_SERVICE_REQUIRED')
    newline = '\r\n' if b'\r\n' in raw else '\n'
    text = raw.decode('utf-8').replace('\r\n', '\n')
    before = '''        if(CommonUtil.isExist(vo.getCredentials())){
            vo.getCredentials().forEach(item->{
                item.setId(IdUtil.fastUUID());
                item.setSocialCode(info.getSocialCode());
            });
        }
        if(CommonUtil.isExist(vo.getAccidents())){
            credentialMapper.insertBatch(vo.getCredentials());
'''
    after = before.replace('            });\n        }',
                           '            });\n            credentialMapper.insertBatch(vo.getCredentials());\n        }', 1)
    after = after.replace('        if(CommonUtil.isExist(vo.getAccidents())){\n            credentialMapper.insertBatch(vo.getCredentials());\n',
                          '        if(CommonUtil.isExist(vo.getAccidents())){\n', 1)
    if text.count(before) != 1:
        raise ValueError('EXACT_MISPLACED_CREDENTIAL_INSERT_REQUIRED')
    result = text.replace(before, after, 1)
    for signature in ('public boolean save(ThirdPartyUnitInfoVo vo){',
                      'public boolean updateById(ThirdPartyUnitInfoVo vo){'):
        anchor = '    '+signature
        if result.count(anchor) != 1:
            raise ValueError('EXACT_THIRD_PARTY_SAVE_AND_UPDATE_REQUIRED')
        result = result.replace(anchor, '    @org.springframework.transaction.annotation.Transactional(rollbackFor = Exception.class)\n'+anchor, 1)
    for anchor in ('        LoginUser user=SecurityContextHolder.getLoginUser();',
                   '        getBaseMapper().updateById(info);'):
        if result.count(anchor) != 1:
            raise ValueError('EXACT_PREWRITE_VALIDATION_BOUNDARY_REQUIRED')
        result = result.replace(anchor, '        validateCredentialNames(vo);\n'+anchor, 1)
    anchor = '    //这个方法用于创建查询条件QueryWrapper并返回 当没有查询条件时可以直接返回null'
    if result.count(anchor) != 1:
        raise ValueError('EXACT_PRIVATE_VALIDATION_LOCATION_REQUIRED')
    helper = '''    private void validateCredentialNames(ThirdPartyUnitInfoVo vo){
        if(CommonUtil.isExist(vo.getCredentials())){
            for(ThirdPartyUnitInfoCredential credential:vo.getCredentials()){
                String name=credential.getLicenceName();
                if(name!=null && name.codePointCount(0,name.length())>16){
                    throw new ServiceException("证书名称不能超过16个字符");
                }
            }
        }
    }

'''
    return result.replace(anchor, helper+anchor, 1).replace('\n', newline).encode('utf-8')


def build(source: Path, output: Path):
    candidate = adapt(source.read_bytes())
    if output.exists():
        raise ValueError('FRESH_CANDIDATE_OUTPUT_REQUIRED')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(candidate)
    return {'originalSHA256': SOURCE_SHA256,
            'candidateSHA256': hashlib.sha256(candidate).hexdigest(),
            'referenceChanged': False, 'installed': False}
