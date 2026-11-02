"""Public numeric acceptance boundary for offline opaque BC7 mip chains."""
import math

QUALITY_POLICY='xnby.bc7.opaque_quality_psnr40_p99_16_max96.v1'

def validate_bc7_quality(manifest):
    def require(ok,message):
        if not ok:raise ValueError('Prepared BC7 quality: '+message)
    def number(v):return type(v) in (int,float) and math.isfinite(v)
    require(isinstance(manifest,dict) and manifest.get('accepted') is True,'complete chain was not accepted')
    limits=manifest.get('qualityThresholds');require(isinstance(limits,dict),'missing declared thresholds')
    psnr,p99,maximum=(limits.get(k) for k in ('rgbPSNRMin','rgbChannelP99Max','rgbMaxErrorMax'))
    require(number(psnr) and 40<=psnr<=999 and number(p99) and 0<=p99<=16 and number(maximum) and 0<=maximum<=96,'missing, nonfinite or relaxed thresholds')
    rows=manifest.get('mips');require(isinstance(rows,list) and 0<len(rows)<=12,'missing mip evidence')
    sanitized=[]
    for row in rows:
        require(isinstance(row,dict) and row.get('accepted') is True,'a mip was not accepted')
        metrics=row.get('quality');require(isinstance(metrics,dict),'missing mip quality')
        a,b,c=(metrics.get(k) for k in ('rgbPSNR','rgbChannelP99','rgbMaxError'))
        require(number(a) and psnr<=a<=999 and type(b) is int and 0<=b<=p99 and type(c) is int and b<=c<=maximum,'mip failed declared quality thresholds')
        sanitized.append(dict(rgbPSNR=a,rgbChannelP99=b,rgbMaxError=c))
    return dict(thresholds=dict(rgbPSNRMin=psnr,rgbChannelP99Max=p99,rgbMaxErrorMax=maximum),mips=sanitized)
