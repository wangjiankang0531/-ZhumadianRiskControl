#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#endif
#include "landscape_document.hpp"
#include <iostream>
int main(int argc,char** argv){
  if(argc!=2)return 2;
  std::ifstream input(argv[1],std::ios::binary);
  hongtu::landscape::Json cases;input>>cases;
  size_t checked=0,acceptedCount=0;auto results=hongtu::landscape::Json::array();
  for(const auto& row:cases){
    auto doc=hongtu::landscape::emptyDocument();
    auto style=hongtu::landscape::defaultStyle();style["icon"]="custom";style["iconData"]=row.at("data");
    auto point=hongtu::landscape::Json{{"id","synthetic-point"},{"name","PNG fixture"},{"type","point"},
      {"positions",{{0,0,0}}},{"style",style}};
    doc["layers"]={{{"id","synthetic-layer"},{"name","PNG fixture"},{"visible",true},{"locked",false},{"features",{point}}}};
    const auto before=doc.dump();bool accepted=false;
    try{hongtu::landscape::validate(doc);accepted=true;}catch(const std::exception&){}
    if(accepted!=row.at("accepted").get<bool>()||doc.dump()!=before){std::cerr<<"PNG_CASE_FAILED "<<row.at("name")<<"\n";return 1;}
    ++checked;if(accepted)++acceptedCount;results.push_back({{"name",row.at("name")},{"accepted",accepted}});
  }
  std::cout<<hongtu::landscape::Json{{"checked",checked},{"accepted",acceptedCount},{"sourceDocumentUnchanged",true},{"cases",results}}.dump(2)<<"\n";
}
