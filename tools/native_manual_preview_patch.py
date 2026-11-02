"""Fixed-source opt-in manual preview; does not change the full-LOD default."""
import hashlib

ORIGINAL_SHA256='d3c1f182bbaf25799365229c23dce1f97a8d0990cae30f305c7f425c7866ed07'

def patched_main(raw):
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA256:raise ValueError('Frozen annotation source changed')
    text=raw.decode('utf-8')
    def once(old,new):
        nonlocal text
        if '\n' in old or text.count(old)!=1:raise ValueError('Unique single-line source boundary missing: '+old[:60])
        text=text.replace(old,new.replace('\n','\r\n'))
    once('    bool editorAnnotationProbe = false;','    bool editorAnnotationProbe = false;\n    bool editorManualPreview = false;')
    once('      if (arg == "--editor-annotation-probe") {','      if (arg == "--editor-static-preview") {\n        cli.editorManualPreview = true;\n        cli.editorStaticShellQA = true;\n        continue;\n      }\n      if (arg == "--editor-annotation-probe") {')
    once('(cli.editorShellProbe == cli.editorAnnotationProbe)', '(!cli.editorManualPreview && (cli.editorShellProbe == cli.editorAnnotationProbe))')
    once('cli.landscapeValidate || cli.stats.empty()', 'cli.landscapeValidate || (!cli.editorManualPreview && cli.stats.empty())')
    once('  if (cli.editorAnnotationProbe && !cli.editorStaticShellQA) {', '''  if (cli.editorManualPreview) {
    if (cli.editorShellProbe || cli.editorAnnotationProbe || cli.landscapeLayers.empty() ||
        !cli.landscapeLayers.is_absolute() || !fs::is_regular_file(cli.landscapeLayers) ||
        (!cli.stats.empty() && fs::absolute(fs::u8path(cli.stats)).lexically_normal() ==
                               fs::absolute(cli.landscapeLayers).lexically_normal())) {
      std::cerr << "Manual preview requires an absolute existing project and separate diagnostics path.\\n";
      return 1;
    }
#ifdef _WIN32
    DWORD consoleProcesses[2]{};
    if (GetConsoleProcessList(consoleProcesses, 2) == 1 && consoleProcesses[0] == GetCurrentProcessId()) {
      if (const HWND console = GetConsoleWindow()) ShowWindow(console, SW_HIDE);
    }
#endif
  }
  if (cli.editorAnnotationProbe && !cli.editorStaticShellQA) {''')
    once('(editorDirty_ ? L" *" : L"")','(cli_.editorManualPreview ? L" · 基础地景体验版" : L"") << (editorDirty_ ? L" *" : L"")')
    once('      ++limitedFrames;', '''      ++limitedFrames;
      if (cli_.editorManualPreview && limitedFrames == 1) {
        SetWindowTextW(editorFrame_, L"驻马店重大风险防控 · 基础地景体验版");
        if (!cli_.stats.empty()) {
          wchar_t title[512]{}; GetWindowTextW(editorFrame_, title, 512);
          const int titleLength = int(std::wcslen(title));
          const int titleBytes = WideCharToMultiByte(CP_UTF8,0,title,titleLength,nullptr,0,nullptr,nullptr);
          std::string titleUtf8(size_t(titleBytes), '\\0');
          WideCharToMultiByte(CP_UTF8,0,title,titleLength,titleUtf8.data(),titleBytes,nullptr,nullptr);
          size_t features = 0;
          for (const auto& layer : editorDocument_["layers"]) features += layer["features"].size();
          std::ofstream status(fs::u8path(cli_.stats));
          status << Json{{"schema","xnby.native.preview.start.v1"},{"manual_preview",true},
            {"title",titleUtf8},{"layers",editorDocument_["layers"].size()},
            {"features",features},{"static_base_only",true},{"automatic_probe",false}}.dump(2);
        }
      }''')
    return text.encode('utf-8')

def patched_editor_dialog(raw):
    if hashlib.sha256(raw).hexdigest()!='35c1daf7f75a9853a1b6e4eb77b4138686cea581deb1a45f793b2938355fcf1f':raise ValueError('Frozen editor dialog source changed')
    text=raw.decode('utf-8');old='    ofn.lpstrFile = file;'
    if text.count(old)!=1:raise ValueError('Editor file dialog boundary changed')
    replacement='''    fs::path previewDirectory;
    if (cli_.editorManualPreview) {
      previewDirectory = editorFile_.empty() ? cli_.landscapeLayers.parent_path() : editorFile_.parent_path();
      ofn.lpstrInitialDir = previewDirectory.c_str();
    }
    ofn.lpstrFile = file;'''
    return text.replace(old,replacement.replace('\n','\r\n')).encode('utf-8')
