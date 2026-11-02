// Test-only member implementation, compiled only by the fixed-source candidate recipe.
void ShowcaseInteractiveApp::editorAnnotationProbeStep(int frame) {
  if (frame % 8) return;
  static Json checks = Json::array();
  static Json pointBeforeEdit, movedLine;
  const size_t stage = checks.size();
  auto require = [](bool ok, const char* message) { if (!ok) throw std::runtime_error(message); };
  auto set = [&](int control, const wchar_t* value) { SetWindowTextW(editorControls_.at(control), value); };
  auto choose = [&](int control, int value) { SendMessageW(editorControls_.at(control), CB_SETCURSEL, value, 0); };
  auto controls = [&](const wchar_t* name, int icon, int pattern, const wchar_t* width,
                      const wchar_t* color, const wchar_t* opacity, const wchar_t* fillOpacity) {
    editorRefreshing_ = true;
    set(3050,name); choose(3051,icon); set(3053,L"40"); choose(3054,pattern); set(3055,width);
    set(3056,color); set(3057,opacity); set(3058,L"#0088FF"); set(3059,fillOpacity);
    SendMessageW(editorControls_.at(3070),BM_SETCHECK,BST_CHECKED,0);
    set(3071,name); set(3072,L"16"); set(3073,L"#FFFFFF"); set(3075,L"12"); set(3076,L"-16");
    choose(3141,0); editorRefreshing_ = false;
  };
  auto click = [&](float x, float y) { editorClick({windowWidth_*x,windowHeight_*y}); };
  auto selectFeature = [&](int layer, int feature, int tab) {
    editorLayer_=layer; editorFeature_=feature; editorTabIndex_=tab;
    refreshEditor(); editorSelectFeature();
  };
  if (stage==0) {
    require(editorDocument_["layers"].size()==1 && editorDocument_["layers"][0]["features"].empty(),"Probe requires one empty synthetic layer");
    editorCommand(3007);
    editorLayer_=0;editorTabIndex_=0;editorCommand(3011);
    controls(L"QA-native-point",4,0,L"4",L"#FFAA00",L"0.65",L"0.2");
    click(.5f,.5f);
    require(editorDocument_["layers"][0]["features"].size()==1,"Point click did not commit");
    const auto& f=editorDocument_["layers"][0]["features"][0];
    require(f["type"]=="point" && f["style"]["icon"]=="warning" && f["style"]["opacity"]==.65,"Point controls were not applied");
    checks.push_back({{"case","point_click_and_icon"},{"passed",true}});
  } else if (stage==1) {
    editorTabIndex_=1;editorCommand(3012);
    controls(L"QA-native-line",0,1,L"7.5",L"#EE2233",L"0.4",L"0.2");
    click(.43f,.57f);click(.60f,.57f);editorCommand(3061);
    require(editorDocument_["layers"][0]["features"].size()==2,"Line clicks did not commit");
    const auto& f=editorDocument_["layers"][0]["features"][1];
    require(f["type"]=="line" && f["positions"].size()==2 && f["style"]["pattern"]=="dash" &&
            f["style"]["widthPx"]==7.5 && f["style"]["color"]=="#EE2233" && f["style"]["opacity"]==.4,"Line controls were not applied");
    checks.push_back({{"case","line_clicks_style_and_finish"},{"passed",true}});
  } else if (stage==2) {
    editorTabIndex_=2;editorCommand(3013);
    controls(L"QA-native-region",0,2,L"3.5",L"#22DD88",L"0.8",L"0.25");
    click(.42f,.40f);click(.60f,.40f);click(.60f,.60f);click(.42f,.60f);click(.42f,.40f);
    require(editorDocument_["layers"][0]["features"].size()==3,"Region closing click did not commit");
    const auto& f=editorDocument_["layers"][0]["features"][2];
    require(f["type"]=="region" && f["positions"].size()==4 && f["style"]["pattern"]=="dot" &&
            f["style"]["fillColor"]=="#0088FF" && f["style"]["fillOpacity"]==.25,"Region fill or closing vertex changed");
    checks.push_back({{"case","region_four_clicks_and_closure"},{"passed",true}});
  } else if (stage==3) {
    selectFeature(0,0,0);pointBeforeEdit=editorDocument_;
    const auto identity=editorDocument_["layers"][0]["features"][0]["id"];
    const auto positions=editorDocument_["layers"][0]["features"][0]["positions"];
    controls(L"QA-native-point-edited",2,0,L"5",L"#BB22FF",L"0.5",L"0.3");editorCommand(3060);
    const auto edited=editorDocument_;
    const auto& f=edited["layers"][0]["features"][0];
    require(f["name"]=="QA-native-point-edited" && f["style"]["icon"]=="square" &&
            f["id"]==identity && f["positions"]==positions,"Style edit changed identity or geometry");
    editorCommand(3030);require(editorDocument_==pointBeforeEdit,"Style edit undo failed");
    editorCommand(3031);require(editorDocument_==edited,"Style edit redo failed");
    checks.push_back({{"case","point_style_edit_undo_redo"},{"passed",true}});
  } else if (stage==4) {
    editorCommand(3021);require(editorDocument_["layers"].size()==2,"New layer did not commit");
    editorRefreshing_=true;set(3025,L"QA-native-target");editorRefreshing_=false;editorCommand(3026);
    selectFeature(0,1,1);movedLine=editorDocument_["layers"][0]["features"][1];
    choose(3043,1);editorCommand(3042);
    require(editorDocument_["layers"][0]["features"].size()==2 && editorDocument_["layers"][1]["features"].size()==1 &&
            editorDocument_["layers"][1]["features"][0]==movedLine,"Move-to-layer changed feature data");
    checks.push_back({{"case","create_rename_and_move_layer"},{"passed",true}});
  } else if (stage==5) {
    selectFeature(1,0,1);editorCommand(3023);const auto locked=editorDocument_;
    editorRefreshing_=true;set(3050,L"MUST-NOT-APPLY");editorRefreshing_=false;editorLiveStyle();
    require(editorDocument_==locked,"Locked layer accepted a live style edit");
    editorCommand(3023);editorCommand(3022);
    require(editorDocument_["layers"][1]["visible"]==false && editorDocument_["layers"][1]["features"][0]==movedLine,"Hidden layer lost feature data");
    editorCommand(3022);require(editorDocument_["layers"][1]["visible"]==true,"Layer visibility restore failed");
    checks.push_back({{"case","locked_style_refusal_and_visibility"},{"passed",true}});
  } else if (stage==6) {
    editorFile_=fs::path(cli_.stats).parent_path()/"native_roundtrip.json";
    editorCommand(3002);
    require(!editorDirty_ && hongtu::landscape::load(editorFile_)==editorDocument_,"Save command and reopen changed document");
    checks.push_back({{"case","save_command_and_reopen"},{"passed",true}});
  } else {
    const auto saved=hongtu::landscape::load(editorFile_);
    require(saved==editorDocument_,"Final saved state differs");
    device_->waitIdle();
    std::vector<uint8_t> pixels; uint32_t width=0,height=0;
    require(device_->readCapturedFrame(pixels,width,height) && width>0 && height>0,"Annotation frame capture failed");
    const auto picture=fs::path(cli_.stats).parent_path()/"native_annotation_frame.png";
    require(stbi_write_png(picture.string().c_str(),int(width),int(height),4,pixels.data(),int(width*4))!=0,"Annotation frame write failed");
    std::ofstream output(fs::u8path(cli_.stats));
    output<<Json{{"passed",true},{"checks",checks},{"layers",saved["layers"].size()},
      {"features",3},{"test_control_messages",true},{"mouse_keyboard_injection",false},
      {"pixel_clicks_use_real_terrain_pick",true},{"manual_human_acceptance",false}}.dump(2);
    output.close();PostMessageW(editorFrame_,WM_CLOSE,0,0);
  }
}
