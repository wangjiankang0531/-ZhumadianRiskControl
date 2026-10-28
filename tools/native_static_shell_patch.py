"""Fixed-source opt-in shell acceptance mode; not a production LOD change."""
import hashlib

ORIGINAL_SHA256='cb86cba500cfcc14c7e471982cb645691aa4403bedbbfed8b0d34cc6f0b01172'

def patched_main(raw):
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError('Fixed isolated main.cpp changed; do not patch a held working tree')
    text=raw.decode('utf-8')
    newline='\r\n' if text.count('\r\n')==text.count('\n') else '\n'
    def replace_once(old,new):
        nonlocal text
        old=old.replace('\n',newline);new=new.replace('\n',newline)
        if text.count(old)!=1:raise ValueError('Unique source boundary missing: '+old[:60])
        text=text.replace(old,new)
    replace_once('    bool landscapeValidate = false;', '    bool landscapeValidate = false;\n    bool editorStaticShellQA = false;')
    replace_once('      if (arg == "--editor-shell-probe") {', '      if (arg == "--editor-static-shell-qa") {\n        cli.editorStaticShellQA = true;\n        continue;\n      }\n      if (arg == "--editor-shell-probe") {')
    replace_once('    if (cli_.preset == Preset::Zhumadian && cli_.zhumadianNativeGeometry) {\n      const glm::vec3 direction = {',
                 '    if (cli_.preset == Preset::Zhumadian && cli_.zhumadianNativeGeometry && !cli_.editorStaticShellQA) {\n      const glm::vec3 direction = {')
    replace_once('  if (cli.landscapeValidate) {', '''  if (cli.editorStaticShellQA &&
      (!cli.landscapeEditor || !cli.editorShellProbe || cli.editorBusinessProbe || cli.screenshotRequested ||
       cli.zhumadianNativeProbe || cli.landscapePickProbe || cli.landscapeValidate || cli.stats.empty())) {
    std::cerr << "Static shell QA requires the landscape shell probe and a separate stats path.\\n";
    return 1;
  }
  if (cli.landscapeValidate) {''')
    return text.encode('utf-8')
