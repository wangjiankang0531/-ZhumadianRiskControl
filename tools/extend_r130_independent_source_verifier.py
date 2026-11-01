from pathlib import Path
R=Path('D:/Project/Zhumadian');p=R/'Application/tools/verify_emergency_workflow_source_20261101.py';s=p.read_text(encoding='utf-8');anchor=" assert sha(actual)==expected,'UNDECLARED_BUILD_SOURCE_DIFFERENCE:'+rel"
extra=''' if c.get('tableRequestOrderAdaptation',{}).get('path')=='src/'+rel:
  import importlib.util
  spec=importlib.util.spec_from_file_location('independent_order',T/'original_table_request_order_compat.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r9/source/src'/rel
  recreated,receipt=helper.transform(origin.read_bytes())
  assert receipt['inputSHA256']==c['tableRequestOrderAdaptation']['inputSHA256']and hashlib.sha256(recreated).hexdigest()==expected
 if c.get('sameOriginMapRestoration',{}).get('path')=='src/'+rel:
  origin=R/'work/user_feedback_20261031/emergency-workflow-source-r10/source/src'/rel
  before=origin.read_bytes();assert hashlib.sha256(before).hexdigest()==c['sameOriginMapRestoration']['beforeSHA256']and before.count(b'"/tianjinrisk/map/"')==1
  assert hashlib.sha256(before.replace(b'"/tianjinrisk/map/"',b'"/zhumadian/map/"')).hexdigest()==expected
'''
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor);p.write_text(s,encoding='utf-8');print('REQUEST_ORDER_AND_MAP_RESTORATION_NOW_INDEPENDENTLY_REGENERATED_FROM_PINNED_PRIOR_INPUTS')
