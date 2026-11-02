"""Apply PNG import preflight to a fresh, pinned 0.9.8-preview.1 source export.

Does not patch a current checkout or build/start a renderer. The PNG raster decoder
still validates compressed pixels after this structural preflight.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json

PINS = {'Application/native/landscape_document.hpp':'ef850c95236a9cf66fade321e880cba613724c5df656734bf34aa6379627c6b7',
        'Application/native/landscape_editor.inl':'298084de099cd69b71a4659490f95df640a9715e31d5c390a7efb3022eaba10d'}
RECIPE_SHA256='935c9b66480b395d3f2ed6cdca625cafc60e573a5aaa37b8c323e28d2fed5da2'

def sha(raw):return hashlib.sha256(raw).hexdigest()
def replace_once(raw,old,new):
    text=raw.decode('utf-8');newline='\r\n' if text.count('\r\n')==text.count('\n') else '\n'
    old=old.replace('\n',newline);new=new.replace('\n',newline)
    if text.count(old)!=1:raise ValueError('Fixed PNG source boundary changed')
    return text.replace(old,new).encode('utf-8')
def patch_document(raw):
    if sha(raw)!=PINS['Application/native/landscape_document.hpp']:raise ValueError('Fixed document source changed')
    raw=replace_once(raw,'#include <vector>','#include <vector>\n#include "png_icon.hpp"')
    return replace_once(raw,'''          auto data = s.at("iconData").get<std::string>();
          if (data.rfind("data:image/png;base64,", 0) != 0 || data.size() > 6 * 1024 * 1024)
            throw std::runtime_error("自定义图标须为内嵌 PNG，小于 4 MiB");''',
                        '''          (void)decodePNGIconData(s.at("iconData").get<std::string>());''')
def patch_editor(raw):
    if sha(raw)!=PINS['Application/native/landscape_editor.inl']:raise ValueError('Fixed editor source changed')
    return replace_once(raw,'''      int w = 0, h = 0, c = 0;
      if (!stbi_info_from_memory(data.data(), int(data.size()), &w, &h, &c) || w > 2048 || h > 2048)
        throw std::runtime_error("图标应为有效 PNG，尺寸不超过 2048×2048");
      editorDraft_["style"]["iconData"] = "data:image/png;base64," + hongtu::landscape::encode64(data);''',
                        '''      const auto embedded = "data:image/png;base64," + hongtu::landscape::encode64(data);
      (void)hongtu::landscape::decodePNGIconData(embedded);
      int w = 0, h = 0, c = 0;
      auto pixels = stbi_load_from_memory(data.data(), int(data.size()), &w, &h, &c, 4);
      if (!pixels) throw std::runtime_error("PNG 图标无法解码");
      stbi_image_free(pixels);
      editorDraft_["style"]["iconData"] = embedded;''')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source',type=Path,required=True);args=parser.parse_args()
    root=args.source.resolve();overlay=Path(__file__).resolve().parent.parent
    if root==overlay or root.is_relative_to(overlay):raise ValueError('A separate prepared source export is required')
    receipt=json.loads((root/'source-receipt.json').read_text(encoding='utf-8'))
    if receipt.get('recipeSHA256')!=RECIPE_SHA256 or receipt.get('sourceFiles')!=391:raise ValueError('Wrong source recipe')
    for name,pin in receipt['sourceSHA256'].items():
        p=PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or p.parts[0] not in ('Application','XNBYEngine'):raise ValueError('Unsafe source receipt path')
        if sha((root/name).read_bytes())!=pin:raise ValueError('Prepared source changed: '+name)
    header=root/'Application/native/png_icon.hpp';output=root/'png-source-receipt.json'
    if header.exists() or output.exists():raise ValueError('PNG overlay already exists; do not repeat')
    data={name:(root/name).read_bytes() for name in PINS}
    prepared={'Application/native/landscape_document.hpp':patch_document(data['Application/native/landscape_document.hpp']),
              'Application/native/landscape_editor.inl':patch_editor(data['Application/native/landscape_editor.inl']),
              'Application/native/png_icon.hpp':(overlay/'native/png_icon.hpp').read_bytes()}
    # Every existing source and both patch inputs are checked before the first write.
    for name,raw in prepared.items():(root/name).write_bytes(raw)
    final=dict(receipt['sourceSHA256']);final.update({name:sha(raw) for name,raw in prepared.items()})
    result={'schema':'xnby.native.png-source.v1','sourceFiles':len(final),'sourceSHA256':final,
            'baseRecipeSHA256':RECIPE_SHA256,'fullEditorCompiled':False,'graphicsStarted':False}
    output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'prepared':True,'sourceFiles':len(final),'fullEditorCompiled':False,'graphicsStarted':False}))
if __name__=='__main__':main()
