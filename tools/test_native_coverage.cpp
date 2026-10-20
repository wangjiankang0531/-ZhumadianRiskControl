#undef NDEBUG
#include <cassert>
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>
#ifndef ZMD_NATIVE_COVERAGE_HEADER
#error Define ZMD_NATIVE_COVERAGE_HEADER to the materialized experimental header
#endif
#include ZMD_NATIVE_COVERAGE_HEADER
using Guard=ZhumadianNativeCoverageMask;
uint64_t checked=0;
uint64_t oracle(const std::vector<uint8_t>& p,const std::vector<uint8_t>& c,int w,int h) {
 uint64_t n=0;
 for(int y=0;y<h;++y)for(int x=0;x<w;++x){
  bool inside=true,child=false;
  for(int yy=std::max(0,y-2);yy<std::min(h,y+3);++yy)
   for(int xx=std::max(0,x-2);xx<std::min(w,x+3);++xx){
    inside&=p[(yy*w+xx)*4]!=0;child|=c[(yy*w+xx)*4]!=0;++checked;
   }
  n+=inside&&!child;
 }
 return n;
}
int main(){
 const int w=32,h=32;std::vector<uint8_t> p(w*h*4),c(p.size());
 for(size_t i=0;i<p.size();i+=4)p[i]=c[i]=255;
 assert(Guard::coverageInteriorLoss(p,c,w,h)==0);
 for(int y=11;y<21;++y)for(int x=11;x<21;++x)c[(y*w+x)*4]=0;
 assert(Guard::coverageInteriorLoss(p,c,w,h)==36);
 c=p;
 for(int y=0;y<10;++y)for(int x=0;x<10;++x)c[(y*w+x)*4]=0;
 assert(Guard::coverageInteriorLoss(p,c,w,h)==64);
 c=p;for(int x=0;x<w;++x)c[(14*w+x)*4]=0;
 assert(Guard::coverageInteriorLoss(p,c,w,h)==0);
 std::mt19937 random(20261020);
 for(int i=0;i<180;++i){
  int width=1+random()%47,height=1+random()%31;
  std::vector<uint8_t> a(width*height*4),b(a.size());
  for(size_t j=0;j<a.size();j+=4){a[j]=(random()%100<99)*255;b[j]=(random()%100<35)*255;}
  assert(Guard::coverageInteriorLoss(a,b,width,height)==oracle(a,b,width,height));
 }
 bool rejected=false;try{Guard::coverageInteriorLoss({}, {}, 0,1);}catch(const std::runtime_error&){rejected=true;}
 assert(rejected);
 std::cout<<"{\"passed\":true,\"randomMasks\":180,\"independentPixelChecks\":"<<checked<<",\"scope\":\"exact interior loss oracle, corner holes and raster fringe tolerance; not all source geometry acceptance\"}\n";
}
