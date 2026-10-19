"""Horizontal minimum distance in the existing local metre CRS, not a dispersion model."""
import math

def segment_distance(point,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];square=dx*dx+dy*dy
    t=0 if square==0 else max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/square))
    return math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)

def horizontal_distance(point,feature):
    positions=feature['positions'];kind=feature['type']
    if kind=='point':return math.hypot(point[0]-positions[0][0],point[1]-positions[0][1])
    closed=kind=='region';count=len(positions) if closed else len(positions)-1
    distance=min(segment_distance(point,positions[i],positions[(i+1)%len(positions)]) for i in range(count))
    if not closed or distance==0:return distance
    inside=False;x,y=point[:2]
    for i,a in enumerate(positions):
        b=positions[(i+1)%len(positions)]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return 0.0 if inside else distance
