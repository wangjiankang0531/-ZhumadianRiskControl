"""Pure byte-preserving IIS upload-limit plan; contains no credentials or I/O.

Call inside the owned server process with a freshly pinned config. Never return
the original/new configuration bytes through a remote result, log or transport.
Both bounds must be the exact legacy pair or the exact new pair; custom/mixed
limits are refused. This function does not install the derived configuration.
"""
import hashlib,re,xml.parsers.expat
OLD=(102400,104857600)
NEW=(103424,105906176)
HTTP=('configuration','system.web','httpRuntime')
IIS=('configuration','system.webServer','security','requestFiltering','requestLimits')

def need(value,code):
    if not value:raise ValueError(code)

def parsed_offsets(raw):
    need(isinstance(raw,bytes)and 0<len(raw)<=1024*1024,'IIS_UPLOAD_BOUNDED_CONFIG_BYTES_REQUIRED')
    parser=xml.parsers.expat.ParserCreate();stack=[];found={}
    def forbidden(*_):raise ValueError('IIS_UPLOAD_DTD_OR_ENTITY_REFUSED')
    parser.StartDoctypeDeclHandler=forbidden;parser.EntityDeclHandler=forbidden;parser.ExternalEntityRefHandler=forbidden
    def start(name,attrs):
        stack.append(name);path=tuple(stack)
        if path not in (HTTP,IIS):return
        need(path not in found,'IIS_UPLOAD_DUPLICATE_LIMIT_NODE')
        begin=parser.CurrentByteIndex;quote=None;end=begin
        while end<len(raw):
            b=raw[end]
            if quote is not None:
                if b==quote:quote=None
            elif b in (34,39):quote=b
            elif b==62:break
            end+=1
        need(end<len(raw),'IIS_UPLOAD_START_TAG_BOUND_REQUIRED')
        attribute='maxRequestLength'if path==HTTP else'maxAllowedContentLength'
        matches=list(re.finditer(rb'''(?<![A-Za-z0-9_:.-])'''+attribute.encode()+rb'''\s*=\s*(["'])([0-9]+)\1''',raw[begin:end+1]))
        need(len(matches)==1 and attrs.get(attribute)==matches[0].group(2).decode('ascii'),'IIS_UPLOAD_EXACT_NUMERIC_ATTRIBUTE_REQUIRED')
        match=matches[0];found[path]={'value':int(match.group(2)),'start':begin+match.start(2),'end':begin+match.end(2)}
    parser.StartElementHandler=start;parser.EndElementHandler=lambda _:stack.pop()
    try:parser.Parse(raw,True)
    except xml.parsers.expat.ExpatError as e:raise ValueError('IIS_UPLOAD_XML_INVALID')from e
    need(set(found)=={HTTP,IIS},'IIS_UPLOAD_EXACT_TWO_LIMIT_NODES_REQUIRED')
    return found

def prepare(raw,expected_before_sha256):
    need(isinstance(expected_before_sha256,str)and re.fullmatch('[0-9a-f]{64}',expected_before_sha256),'IIS_UPLOAD_BEFORE_PIN_REQUIRED')
    need(isinstance(raw,bytes)and hashlib.sha256(raw).hexdigest()==expected_before_sha256,'IIS_UPLOAD_CONFIG_CHANGED_BEFORE_PLAN')
    offsets=parsed_offsets(raw);before=tuple(offsets[p]['value']for p in (HTTP,IIS))
    need(before in (OLD,NEW),'IIS_UPLOAD_CUSTOM_OR_MIXED_LIMITS_REFUSED')
    replacements=[(offsets[p]['start'],offsets[p]['end'],str(value).encode())for p,value in zip((HTTP,IIS),NEW)]
    output=raw
    for start,end,value in sorted(replacements,reverse=True):output=output[:start]+value+output[end:]
    check=parsed_offsets(output);need(tuple(check[p]['value']for p in (HTTP,IIS))==NEW,'IIS_UPLOAD_RENDERED_LIMITS_MISMATCH')
    # Reverse only the two parsed numeric spans. Every other byte, including
    # private app settings, comments, handler definitions and formatting, stays.
    reversed_bytes=output
    for p,value in sorted(zip((HTTP,IIS),before),key=lambda item:check[item[0]]['start'],reverse=True):
        row=check[p];reversed_bytes=reversed_bytes[:row['start']]+str(value).encode()+reversed_bytes[row['end']:]
    need(reversed_bytes==raw,'IIS_UPLOAD_UNRELATED_BYTES_CHANGED')
    return output,{'schema':'xnby.iis-upload-limits.v1','beforeSHA256':expected_before_sha256,'afterSHA256':hashlib.sha256(output).hexdigest(),'changed':output!=raw,'httpRuntimeKiBBefore':before[0],'httpRuntimeKiBAfter':NEW[0],'requestFilteringBytesBefore':before[1],'requestFilteringBytesAfter':NEW[1],'allOtherBytesPreserved':True,'configurationContentsIncluded':False,'actualIISPipelineAccepted':False}
