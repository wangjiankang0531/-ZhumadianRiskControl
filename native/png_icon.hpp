#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace hongtu::landscape {
inline constexpr size_t kMaximumPNGIconBytes = 4 * 1024 * 1024;
inline constexpr uint32_t kMaximumPNGIconDimension = 2048;
inline void invalidPNGIcon() {
  throw std::runtime_error("自定义图标须为有效 PNG，文件不超过 4 MiB、尺寸不超过 2048×2048");
}
inline std::vector<uint8_t> decodePNGIconData(std::string_view data) {
  constexpr std::string_view prefix = "data:image/png;base64,";
  if (data.substr(0, prefix.size()) != prefix) invalidPNGIcon();
  data.remove_prefix(prefix.size());
  if (data.empty() || data.size() > ((kMaximumPNGIconBytes + 2) / 3) * 4 || data.size() % 4) invalidPNGIcon();
  constexpr std::string_view alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  const auto value = [&](char c) { const auto p = alphabet.find(c); if (p == alphabet.npos) invalidPNGIcon(); return uint32_t(p); };
  std::vector<uint8_t> bytes;
  bytes.reserve(data.size() / 4 * 3);
  for (size_t i = 0; i < data.size(); i += 4) {
    const bool pad2 = data[i + 2] == '=', pad1 = data[i + 3] == '=';
    if ((pad2 && !pad1) || ((pad1 || pad2) && i + 4 != data.size())) invalidPNGIcon();
    const auto a=value(data[i]), b=value(data[i+1]), c=pad2?0:value(data[i+2]), d=pad1?0:value(data[i+3]);
    if ((pad2 && (b & 15)) || (!pad2 && pad1 && (c & 3))) invalidPNGIcon();
    bytes.push_back(uint8_t((a << 2) | (b >> 4)));
    if (!pad2) bytes.push_back(uint8_t((b << 4) | (c >> 2)));
    if (!pad1) bytes.push_back(uint8_t((c << 6) | d));
  }
  constexpr uint8_t signature[] = {137,80,78,71,13,10,26,10};
  if (bytes.size() < 57 || bytes.size() > kMaximumPNGIconBytes) invalidPNGIcon();
  for (size_t i=0;i<8;++i) if (bytes[i]!=signature[i]) invalidPNGIcon();
  const auto word=[&](size_t p) { return (uint32_t(bytes[p])<<24)|(uint32_t(bytes[p+1])<<16)|(uint32_t(bytes[p+2])<<8)|bytes[p+3]; };
  static const auto table=[] { std::array<uint32_t,256> out{}; for(uint32_t n=0;n<256;++n) {auto c=n;for(int i=0;i<8;++i)c=(c&1)?0xedb88320u^(c>>1):(c>>1);out[n]=c;}return out; }();
  size_t offset=8;uint32_t color=0;bool idat=false,palette=false,ended=false;
  while(offset<bytes.size()) {
    if(bytes.size()-offset<12) invalidPNGIcon();
    const auto size=word(offset);if(size>bytes.size()-offset-12)invalidPNGIcon();
    const size_t end=offset+8+size;
    const std::string type(reinterpret_cast<const char*>(bytes.data()+offset+4),4);
    for(char c:type)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')))invalidPNGIcon();
    uint32_t crc=0xffffffffu;for(size_t i=offset+4;i<end;++i)crc=table[(crc^bytes[i])&255]^(crc>>8);
    if((crc^0xffffffffu)!=word(end))invalidPNGIcon();
    if(offset==8) {
      if(type!="IHDR"||size!=13)invalidPNGIcon();
      const auto width=word(offset+8),height=word(offset+12);const auto depth=bytes[offset+16];color=bytes[offset+17];
      const bool validDepth = color==0?(depth==1||depth==2||depth==4||depth==8||depth==16):
          color==3?(depth==1||depth==2||depth==4||depth==8):
          (color==2||color==4||color==6)?(depth==8||depth==16):false;
      if(!width||!height||width>kMaximumPNGIconDimension||height>kMaximumPNGIconDimension||!validDepth||bytes[offset+18]!=0||bytes[offset+19]!=0||bytes[offset+20]>1)invalidPNGIcon();
    } else if(type=="IHDR")invalidPNGIcon();
    if(type=="PLTE"){if(idat||!size||size%3||size>768)invalidPNGIcon();palette=true;}
    if(type=="IDAT"){if(color==3&&!palette)invalidPNGIcon();idat=true;}
    offset=end+4;
    if(type=="IEND"){if(size||!idat||offset!=bytes.size())invalidPNGIcon();ended=true;break;}
  }
  if(!ended)invalidPNGIcon();
  return bytes;
}
} // namespace hongtu::landscape
