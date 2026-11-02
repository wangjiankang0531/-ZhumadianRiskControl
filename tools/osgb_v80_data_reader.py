"""Bounded data-only OSGB v80 decoder for an explicit photogrammetry subset.

Independent Python implementation of the public OSG serialization layout.
No plugins, native libraries, executables, external references or asset writes.
Unsupported versions/classes/state remain errors, never silently skipped.
"""
import math
import struct


class UnsupportedOSGB(ValueError):
    pass


ARRAYS={0:('b',1),1:('B',1),2:('h',1),3:('H',1),4:('i',1),5:('I',1),6:('f',1),7:('d',1),
        8:('b',2),9:('b',3),10:('b',4),11:('B',4),12:('h',2),13:('h',3),14:('h',4),
        15:('f',2),16:('f',3),17:('f',4),18:('d',2),19:('d',3),20:('d',4),21:('B',2),22:('B',3),
        23:('H',2),24:('H',3),25:('H',4),26:('i',2),27:('i',3),28:('i',4),29:('I',2),30:('I',3),31:('I',4)}


class DataReader:
    def __init__(self,data,maximum=64*1048576):
        if type(data) is not bytes or not 25<=len(data)<=maximum:
            raise UnsupportedOSGB('Invalid bounded immutable OSGB input')
        self.data=data;self.offset=0;self.objects={};self.arrays={};self.active=set();self.depth=0;self.trace=[]

    def fail(self,message):raise UnsupportedOSGB(f'{message} at byte {self.offset}')
    def take(self,n):
        if type(n) is not int or n<0 or n>len(self.data)-self.offset:self.fail('Truncated OSGB field')
        start=self.offset;self.offset+=n;return self.data[start:self.offset]
    def number(self,code):return struct.unpack('<'+code,self.take(struct.calcsize('<'+code)))[0]
    def u32(self):return self.number('I')
    def i32(self):return self.number('i')
    def floats(self,count,code='f'):
        if not 0<=count<=4000000:self.fail('Numeric field exceeds bound')
        values=struct.unpack('<'+str(count)+code,self.take(count*struct.calcsize(code)))
        if not all(math.isfinite(v) for v in values):self.fail('Nonfinite OSGB numeric value')
        return values
    def boolean(self):
        v=self.number('B')
        if v not in (0,1):self.fail('Noncanonical OSGB boolean')
        return bool(v)
    def count(self,maximum=65536):
        n=self.u32()
        if n>maximum:self.fail('OSGB collection exceeds bound')
        return n
    def string(self,opaque=False):
        n=self.count(4096)
        if opaque:return self.take(n)
        try:return self.take(n).decode('utf-8')
        except UnicodeError:self.fail('Invalid OSGB UTF-8 string')
    def optional_object(self):return self.object() if self.boolean() else None
    def require_absent(self,label):
        if self.boolean():self.fail('Unsupported '+label)

    def common(self,out):
        out['nameBytes']=self.string(opaque=True);out['name']=out['nameBytes'].decode('utf-8','surrogateescape');out['variance']=self.u32()
        if out['variance'] not in (0,1,2):self.fail('Invalid data variance')
        out['userData']=self.optional_object()

    def node(self,out):
        out['initialBound']=self.floats(4,'d') if self.boolean() else None
        for key in ('boundCallback','updateCallback','eventCallback','cullCallback'):out[key]=self.optional_object()
        out['cullingActive']=self.boolean();out['nodeMask']=self.u32();out['stateSet']=self.optional_object()

    def children(self):return [self.object() for _ in range(self.count())]

    def lod(self,out):
        out['centerMode']=self.u32();out['userCenter']=self.floats(4,'d') if self.boolean() else None
        out['rangeMode']=self.u32()
        out['ranges']=[self.floats(2) for _ in range(self.count())] if self.boolean() else []

    def state_attribute(self,out):
        out['updateCallback']=self.optional_object();out['eventCallback']=self.optional_object()

    def attributes(self):return [(self.object(),self.u32()) for _ in range(self.count(1024))]
    def modes(self):return [(self.u32(),self.u32()) for _ in range(self.count(1024))]

    def state_set(self,out):
        out['modes']=self.modes() if self.boolean() else []
        out['attributes']=self.attributes() if self.boolean() else []
        out['textureModes']=[self.modes() for _ in range(self.count(32))] if self.boolean() else []
        out['textureAttributes']=[self.attributes() for _ in range(self.count(32))] if self.boolean() else []
        self.require_absent('uniform state')
        out['renderingHint']=self.i32();out['renderBinMode']=self.u32();out['binNumber']=self.i32();out['binName']=self.string();out['nestRenderBins']=self.boolean()
        out['updateCallback']=self.optional_object();out['eventCallback']=self.optional_object()

    def texture(self,out):
        for key in ('wrapS','wrapT','wrapR','minFilter','magFilter'):
            out[key]=self.u32() if self.boolean() else None
        out['anisotropy']=self.floats(1)[0]
        for key in ('hardwareMipmaps','unrefAfterApply','clientStorage','resizeNPOT'):out[key]=self.boolean()
        out['borderColor']=self.floats(4,'d');out['borderWidth']=self.i32();out['internalFormatMode']=self.u32()
        for key in ('internalFormat','sourceFormat','sourceType'):out[key]=self.u32() if self.boolean() else None
        out['shadowComparison']=self.boolean();out['shadowCompareFunc']=self.u32();out['shadowTextureMode']=self.u32();out['shadowAmbient']=self.floats(1)[0]
        out['image']=self.image() if self.boolean() else None
        out['textureWidth']=self.i32();out['textureHeight']=self.i32()

    def image(self):
        identifier=self.u32()
        if identifier in self.objects:
            out=self.objects[identifier]
            if out['class']!='osg::Image':self.fail('Image reference changes type')
            return out
        name=self.string(opaque=True);hint=self.i32();decision=self.i32()
        if decision!=1 or not name.lower().endswith((b'.jpg',b'.jpeg')):self.fail('Only inline original JPEG images supported')
        raw=self.take(self.count(32*1048576))
        if not raw.startswith(b'\xff\xd8') or not raw.endswith(b'\xff\xd9'):self.fail('Invalid bounded embedded JPEG')
        out=dict({'class':'osg::Image','id':identifier,'filenameBytes':name,'writeHint':hint,'encoded':raw})
        self.common(out);self.objects[identifier]=out;return out

    def array(self):
        identifier=self.u32()
        if identifier in self.arrays:return self.arrays[identifier]
        kind=self.u32()
        if kind not in ARRAYS:self.fail('Unsupported OSGB array type')
        code,components=ARRAYS[kind];count=self.count(2000000);raw=self.take(count*components*struct.calcsize(code))
        if code in ('f','d') and any(not math.isfinite(v[0]) for v in struct.iter_unpack('<'+code,raw)):
            self.fail('Nonfinite OSGB array')
        out=dict(id=identifier,kind=kind,code=code,components=components,count=count,raw=raw)
        self.arrays[identifier]=out;return out

    def array_data(self):
        out=dict(array=self.array() if self.boolean() else None,indices=self.array() if self.boolean() else None,binding=self.i32(),normalize=self.i32())
        if out['binding'] not in range(5) or out['normalize'] not in (0,1):self.fail('Unsupported array binding')
        return out

    def primitive(self):
        kind=self.u32();mode=self.u32()
        if kind==50:out=dict(first=self.i32(),count=self.i32())
        elif kind==51:out=dict(first=self.i32(),lengths=[self.i32() for _ in range(self.count())])
        elif kind in (52,53,54):
            code={52:'B',53:'H',54:'I'}[kind];n=self.count(6000000);out=dict(count=n,code=code,raw=self.take(n*struct.calcsize(code)))
        else:self.fail('Unsupported primitive type')
        out.update(kind=kind,mode=mode);return out

    def geometry(self,out):
        out['stateSet']=self.optional_object();out['initialBound']=self.floats(6,'d') if self.boolean() else None
        out['boundCallback']=self.optional_object();out['shape']=self.optional_object()
        for key in ('supportsDisplayList','useDisplayList','useVBO'):out[key]=self.boolean()
        for key in ('updateCallback','eventCallback','cullCallback','drawCallback'):out[key]=self.optional_object()
        out['primitives']=[self.primitive() for _ in range(self.count(65536))]
        for key in ('vertices','normals','colors','secondaryColors','fogCoords'):
            out[key]=self.array_data() if self.boolean() else None
        for key in ('texCoords','vertexAttributes'):
            out[key]=[self.array_data() for _ in range(self.count(32))] if self.boolean() else []
        out['fastPathHint']=self.boolean()

    def object(self):
        if self.depth>=128 or len(self.objects)>=65536:self.fail('OSGB object graph exceeds bound')
        start=self.offset;kind=self.string()
        if kind=='NULL':return None
        identifier=self.u32()
        if identifier in self.active:self.fail('Cyclic OSGB object reference')
        if identifier in self.objects:
            out=self.objects[identifier]
            if out['class']!=kind:self.fail('Object reference changes type')
            return out
        if kind not in ('osg::Group','osg::PagedLOD','osg::Geode','osg::Geometry','osg::StateSet','osg::Material','osg::Texture2D'):
            self.fail('Unsupported OSGB class '+kind)
        out={'class':kind,'id':identifier};self.objects[identifier]=out;self.active.add(identifier);self.depth+=1
        self.trace.append(dict(offset=start,kind=kind,id=identifier))
        try:
            self.common(out)
            if kind in ('osg::Group','osg::PagedLOD','osg::Geode'):self.node(out)
            if kind=='osg::Group':out['children']=self.children() if self.boolean() else []
            elif kind=='osg::PagedLOD':
                self.lod(out)
                if self.boolean():out['databasePath']=self.string() if self.boolean() else None
                out['nonExpiringChildren']=self.u32();out['disablePaging']=self.boolean()
                if self.boolean():
                    out['fileNames']=[self.string() for _ in range(self.count())]
                    out['priorities']=[self.floats(2) for _ in range(self.count())]
                else:out['fileNames']=[];out['priorities']=[]
                out['children']=self.children() if self.boolean() else []
            elif kind=='osg::Geode':out['drawables']=self.children() if self.boolean() else []
            elif kind=='osg::Geometry':self.geometry(out)
            elif kind=='osg::StateSet':self.state_set(out)
            elif kind in ('osg::Material','osg::Texture2D'):
                self.state_attribute(out)
                if kind=='osg::Material':
                    out['colorMode']=self.u32()
                    for key,components in (('ambient',4),('diffuse',4),('specular',4),('emission',4),('shininess',1)):
                        out[key]=(self.boolean(),self.floats(components*2)) if self.boolean() else None
                else:self.texture(out)
        finally:self.depth-=1;self.active.remove(identifier)
        return out

    def parse(self):
        if self.take(8)!=bytes.fromhex('a10e916c4545fb1a'):self.fail('Unsupported OSGB signature or endian')
        if (self.u32(),self.u32(),self.u32())!=(1,80,0):self.fail('Only OSGB v80 scene without schema/domains/brackets supported')
        if self.string()!='0':self.fail('Compressed OSGB is not supported')
        root=self.object()
        if self.offset!=len(self.data):self.fail('Unconsumed OSGB bytes')
        return root
