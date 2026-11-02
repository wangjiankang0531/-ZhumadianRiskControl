"""Generate synthetic PNG interoperability cases; no user images or project input."""
import base64, struct, zlib

SIGNATURE=b'\x89PNG\r\n\x1a\n'
def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
def png(width=1,height=1,color=6,depth=8,raw=b'\x00\xff\x40\x20\xff',extra=()):
    return SIGNATURE+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,depth,color,0,0,0))+b''.join(extra)+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
def uri(raw):return 'data:image/png;base64,'+base64.b64encode(raw).decode('ascii')
def marker():
    rows=[]
    for y in range(64):
        row=bytearray([0])
        for x in range(64):
            # Deterministic red emergency cross on a white disk; transparent corners.
            disk=(x-31.5)**2+(y-31.5)**2<=30**2
            red=disk and (24<=x<40 or 24<=y<40)
            row.extend((230,35,45,255) if red else (255,255,255,255) if disk else (0,0,0,0))
        rows.append(bytes(row))
    return png(64,64,raw=b''.join(rows))
def cases():
    good=png();bad_crc=bytearray(good);bad_crc[29]^=1
    valid=[('rgba',good),('emergency-cross',marker()),('grayscale',png(color=0,depth=1,raw=b'\0\0')),
      ('rgb',png(color=2,raw=b'\0\xff\0\0')),('gray-alpha',png(color=4,raw=b'\0\x80\xff')),
      ('palette',png(color=3,depth=1,raw=b'\0\0',extra=[chunk(b'PLTE',b'\xff\0\0')])),
      ('dimension-boundary-container',png(width=2048,height=2048))]
    invalid=[('empty','data:image/png;base64,'),('alphabet','data:image/png;base64,!!!!'),
      ('text','data:image/png;base64,SGVsbG8='),('wrong-MIME',uri(good).replace('image/png','image/jpeg')),
      ('noncanonical-padding','data:image/png;base64,AB=='),('padding-position','data:image/png;base64,AA=A'),
      ('whitespace',uri(good)+'\n'),('bad-crc',uri(bytes(bad_crc))),('truncated',uri(good[:-1])),
      ('missing-IEND',uri(good[:-12])),('missing-IDAT',uri(good[:33]+good[-12:])),
      ('duplicate-IHDR',uri(good[:33]+good[8:33]+good[33:])),('trailing-byte',uri(good+b'\0')),
      ('zero-width',uri(png(width=0))),('zero-height',uri(png(height=0))),
      ('oversized-width',uri(png(width=2049))),('oversized-height',uri(png(height=2049))),
      ('unknown-color',uri(png(color=1))),('bad-depth',uri(png(color=6,depth=4))),
      ('palette-missing',uri(png(color=3,depth=1,raw=b'\0\0')))]
    return [{'name':name,'data':uri(raw),'accepted':True} for name,raw in valid]+[{'name':name,'data':data,'accepted':False} for name,data in invalid]
