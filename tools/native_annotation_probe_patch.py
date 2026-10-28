"""Compose a test-only annotation probe onto the frozen static-shell candidate source."""
import hashlib

ORIGINAL_SHA256='f5fd75daf3f9d566325e909a99abade3ad5d36b1bc10ed0cb50d6ecd2262308f'

def patched_main(raw):
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA256:raise ValueError('Frozen static shell source changed')
    text=raw.decode('utf-8');newline='\r\n' if text.count('\r\n')==text.count('\n') else '\n'
    def once(old,new):
        nonlocal text
        old=old.replace('\n',newline);new=new.replace('\n',newline)
        if text.count(old)!=1:raise ValueError('Source boundary is not unique: '+old[:60])
        text=text.replace(old,new)
    once('    bool editorStaticShellQA = false;', '    bool editorStaticShellQA = false;\n    bool editorAnnotationProbe = false;')
    once('    void editorShellProbeStep(int frame);','    void editorShellProbeStep(int frame);\n    void editorAnnotationProbeStep(int frame);')
    once('      if (arg == "--editor-static-shell-qa") {','      if (arg == "--editor-annotation-probe") {\n        cli.editorAnnotationProbe = true;\n        continue;\n      }\n      if (arg == "--editor-static-shell-qa") {')
    once('      if (cli_.editorBusinessProbe && limitedFrames == 8)','      if (cli_.editorAnnotationProbe)\n        editorAnnotationProbeStep(limitedFrames);\n      if (cli_.editorBusinessProbe && limitedFrames == 8)')
    once('#  include "landscape_editor.inl"','#  include "landscape_editor.inl"\n#  include "landscape_editor_annotation_probe.inl"')
    once('    if (cli_.editorShellProbe)\n      device_->recordSwapchainCapture(commandBuffer_, imageIndex);',
         '    if (cli_.editorShellProbe || cli_.editorAnnotationProbe)\n      device_->recordSwapchainCapture(commandBuffer_, imageIndex);')
    once('(!cli.landscapeEditor || !cli.editorShellProbe || cli.editorBusinessProbe || cli.screenshotRequested ||',
         '(!cli.landscapeEditor || (cli.editorShellProbe == cli.editorAnnotationProbe) || cli.editorBusinessProbe || cli.screenshotRequested ||')
    once('  if (cli.landscapeValidate) {','  if (cli.editorAnnotationProbe && !cli.editorStaticShellQA) {\n    std::cerr << "Annotation probe requires explicit static QA mode.\\n";\n    return 1;\n  }\n  if (cli.landscapeValidate) {')
    return text.encode('utf-8')
