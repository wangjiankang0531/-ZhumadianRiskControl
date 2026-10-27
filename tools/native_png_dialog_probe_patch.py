"""Fixed-source test-only common-dialog and PNG roundtrip acceptance extension."""
import hashlib
ORIGINAL_SHA256='9a73f6c4fd0d697ff400054b6b4015171281b1c80fbd64029f9ea3b254270a2b'

def patched_probe(raw):
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA256:raise ValueError('Frozen annotation probe changed')
    text=raw.decode('utf-8');newline='\r\n' if text.count('\r\n')==text.count('\n') else '\n'
    def once(old,new):
        nonlocal text
        old=old.replace('\n',newline);new=new.replace('\n',newline)
        if text.count(old)!=1:raise ValueError('Unique PNG dialog probe boundary missing')
        text=text.replace(old,new)
    helper='''  // Only the newly started test process and its directly-owned common dialog
  // receive control messages. No global mouse/keyboard or other process is used.
  auto dialogCommand = [&](int command, const fs::path& target) {
    const HWND owner = editorFrame_;
    const DWORD ownPID = GetCurrentProcessId();
    bool submitted = false, cancelled = false;
    std::thread picker([&] {
      const auto deadline = GetTickCount64() + 5000;
      HWND dialog = nullptr;
      while (!dialog && GetTickCount64() < deadline) {
        for (HWND w = FindWindowExW(nullptr,nullptr,L"#32770",nullptr); w;
             w = FindWindowExW(nullptr,w,L"#32770",nullptr)) {
          DWORD pid = 0; GetWindowThreadProcessId(w,&pid);
          if (pid == ownPID && GetWindow(w,GW_OWNER) == owner && IsWindowVisible(w)) { dialog=w; break; }
        }
        if (!dialog) Sleep(20);
      }
      if (!dialog) {
        std::ofstream trace(fs::u8path(cli_.stats).parent_path()/("dialog-"+std::to_string(command)+".json"));
        trace<<Json{{"own_pid",ownPID},{"command",command},{"dialog_found",false}}.dump(2);return;
      }
      struct DialogControls { int command; HWND edit=nullptr; HWND combo=nullptr; } controls{command};
      EnumChildWindows(dialog,[](HWND w,LPARAM data)->BOOL {
        auto& c=*reinterpret_cast<DialogControls*>(data);wchar_t name[80]{};
        GetClassNameW(w,name,80);const int id=GetDlgCtrlID(w);
        if(wcscmp(name,L"Edit")==0) {
          if(id==0x0480||id==0x047c)c.edit=w;
          else if(c.command==3003&&id==1001&&!c.edit)c.edit=w;
        }
        if(id==0x047c&&wcscmp(name,L"ComboBoxEx32")==0)c.combo=w;
        return TRUE;
      },reinterpret_cast<LPARAM>(&controls));
      DWORD_PTR result = 0;
      if(controls.combo)SendMessageTimeoutW(controls.combo,WM_SETTEXT,0,
        reinterpret_cast<LPARAM>(target.c_str()),SMTO_ABORTIFHUNG,1500,&result);
      if(controls.edit)SendMessageTimeoutW(controls.edit,WM_SETTEXT,0,
        reinterpret_cast<LPARAM>(target.c_str()),SMTO_ABORTIFHUNG,1500,&result);
      wchar_t actual[32768]{};if(controls.edit)GetWindowTextW(controls.edit,actual,32768);
      const bool matches=target.native()==actual;
      if(!matches){
        std::ofstream trace(fs::u8path(cli_.stats).parent_path()/("dialog-"+std::to_string(command)+".json"));
        trace<<Json{{"own_pid",ownPID},{"command",command},{"filename_text_matches",false},
          {"filename_edit_found",controls.edit!=nullptr},{"filename_combo_found",controls.combo!=nullptr}}.dump(2);
        PostMessageW(dialog,WM_COMMAND,IDCANCEL,0);cancelled=true;return;
      }
      const HWND button=GetDlgItem(dialog,IDOK);
      PostMessageW(dialog,WM_COMMAND,MAKEWPARAM(IDOK,BN_CLICKED),reinterpret_cast<LPARAM>(button)); submitted=true;
      const auto closeDeadline=GetTickCount64()+4000;
      while(IsWindow(dialog) && GetTickCount64()<closeDeadline) {
        for(HWND w=FindWindowExW(nullptr,nullptr,L"#32770",nullptr);w;w=FindWindowExW(nullptr,w,L"#32770",nullptr)) {
          DWORD pid=0;GetWindowThreadProcessId(w,&pid);
          if(pid==ownPID&&GetWindow(w,GW_OWNER)==dialog&&IsWindowVisible(w)) {
            // Unexpected overwrite/error prompts are declined, never approved.
            PostMessageW(w,WM_USER+102,IDNO,0);
            PostMessageW(dialog,WM_COMMAND,IDCANCEL,0);cancelled=true;
          }
        }
        Sleep(20);
      }
      DWORD pid=0;GetWindowThreadProcessId(dialog,&pid);
      if(IsWindow(dialog) && pid==ownPID && GetWindow(dialog,GW_OWNER)==owner) {
        PostMessageW(dialog,WM_COMMAND,IDCANCEL,0);cancelled=true;
      }
      std::ofstream trace(fs::u8path(cli_.stats).parent_path()/("dialog-"+std::to_string(command)+".json"));
      trace<<Json{{"own_pid",ownPID},{"command",command},{"filename_text_matches",matches},
        {"filename_edit_found",controls.edit!=nullptr},{"filename_combo_found",controls.combo!=nullptr},
        {"submitted",submitted},{"cancelled",cancelled}}.dump(2);
    });
    editorCommand(command);
    picker.join();
    require(submitted && !cancelled,"Owned common dialog did not accept the synthetic file");
  };
'''
    once('  auto controls = [&](const wchar_t* name, int icon, int pattern, const wchar_t* width,',
         helper+'  auto controls = [&](const wchar_t* name, int icon, int pattern, const wchar_t* width,')
    once('    controls(L"QA-native-point-edited",2,0,L"5",L"#BB22FF",L"0.5",L"0.3");editorCommand(3060);',
         '''    const auto iconFile=fs::u8path(cli_.stats).parent_path()/L"验收自定义图标.png";
    std::ifstream iconStream(iconFile,std::ios::binary);
    const std::vector<uint8_t> iconBytes((std::istreambuf_iterator<char>(iconStream)),{});
    const auto expectedIcon="data:image/png;base64,"+hongtu::landscape::encode64(iconBytes);
    dialogCommand(3052,iconFile);
    const auto afterPNG=editorDocument_;
    require(afterPNG["layers"][0]["features"][0]["style"]["icon"]=="custom" &&
            afterPNG["layers"][0]["features"][0]["style"]["iconData"]==expectedIcon,
            "PNG chooser did not embed the exact selected bytes");
    controls(L"QA-native-custom-png",5,0,L"5",L"#BB22FF",L"0.75",L"0.3");
    editorRefreshing_=true;set(3053,L"96");editorRefreshing_=false;editorCommand(3060);''')
    once('    require(f["name"]=="QA-native-point-edited" && f["style"]["icon"]=="square" &&',
         '    require(f["name"]=="QA-native-custom-png" && f["style"]["icon"]=="custom" && f["style"]["iconData"]==expectedIcon && f["style"]["opacity"]==.75 &&')
    once('    editorCommand(3030);require(editorDocument_==pointBeforeEdit,"Style edit undo failed");\n    editorCommand(3031);require(editorDocument_==edited,"Style edit redo failed");',
         '''    editorCommand(3030);require(editorDocument_==afterPNG,"PNG style undo failed");
    editorCommand(3030);require(editorDocument_==pointBeforeEdit,"PNG selection undo failed");
    editorCommand(3031);require(editorDocument_==afterPNG,"PNG selection redo failed");
    editorCommand(3031);require(editorDocument_==edited,"PNG style redo failed");''')
    once('    checks.push_back({{"case","point_style_edit_undo_redo"},{"passed",true}});',
         '    checks.push_back({{"case","png_file_dialog_exact_bytes_style_undo_redo"},{"passed",true}});')
    once('    editorFile_=fs::path(cli_.stats).parent_path()/"native_roundtrip.json";\n    editorCommand(3002);',
         '''    const auto output=fs::u8path(cli_.stats).parent_path()/L"PNG标注保存重开.json";
    require(!fs::exists(output),"Save-as target must be new");
    dialogCommand(3003,output);
    require(editorFile_==output,"Save-as dialog returned a different path");''')
    once('    checks.push_back({{"case","save_command_and_reopen"},{"passed",true}});',
         '    checks.push_back({{"case","save_as_dialog_and_reopen"},{"passed",true}});')
    once('{"pixel_clicks_use_real_terrain_pick",true},{"manual_human_acceptance",false}',
         '{"pixel_clicks_use_real_terrain_pick",true},{"automated_common_dialogs",true},{"manual_human_acceptance",false}')
    return text.encode('utf-8')
