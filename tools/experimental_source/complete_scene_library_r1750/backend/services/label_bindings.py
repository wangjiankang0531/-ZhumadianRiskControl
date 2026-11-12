"""Saved spatial-sign data references, shared with native and Web validators."""
import re
BUSINESS_TYPES={'enterprise','enterprise-boundary','major-hazard','hidden-danger','special-work','road','access','video','gas-monitor','emergency-resource','firefighting','patrol','public-area'}
def _text(value,maximum,required=False,reference=False):
    return (isinstance(value,str) and (not required or bool(value.replace(' ','')))
            and len(value.encode('utf-8'))<=maximum
            and not re.search(r'[\x00-\x20\x7f]' if reference else r'[\x00-\x1f\x7f]',value))
def validate_label_data_bindings(label):
    if 'dataBindings' not in label:return label
    rows=label['dataBindings']
    if not isinstance(rows,list) or len(rows)>8:raise ValueError('invalid sign data binding count')
    if rows and label.get('placement')!='billboard':raise ValueError('data bindings require a spatial sign')
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or set(row)-{'reference','attribute','caption','unit'}:raise ValueError('invalid sign data binding')
        ref=row.get('reference')
        if (not isinstance(ref,dict) or set(ref)-{'objectType','businessId','enterpriseId','sourceSystem'}
                or not isinstance(ref.get('objectType'),str) or ref['objectType'] not in BUSINESS_TYPES):raise ValueError('invalid sign reference')
        for name,maximum,required in [('businessId',256,True),('sourceSystem',128,True),('enterpriseId',256,False)]:
            if name in ref or required:
                if not _text(ref.get(name),maximum,required,True):raise ValueError('invalid sign reference identifier')
        if (not _text(row.get('attribute'),96,True) or not _text(row.get('caption'),96,True)
                or ('unit' in row and not _text(row['unit'],32))):raise ValueError('invalid sign display field')
        key=(ref['sourceSystem'],ref['objectType'],ref['businessId'],row['attribute'])
        if key in seen:raise ValueError('duplicate sign field')
        seen.add(key)
    return label
