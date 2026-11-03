from pathlib import Path
import ast
R=Path('D:/Project/Zhumadian');V=Path(__file__).parent
s=(R/'Application/tools/frontend/static_performance_r229/validation/verify_static_transport_r230.py').read_text(encoding='utf-8')
s=s.replace('static-transport-r230','static-transport-r277').replace('personal-workflow-routes-r195/dist','plan-exercise-retained-r224/dist').replace('r36-native-history-candidate-r2/bundle/payload/payload-manifest.json','r38-unified-original-mappers-r1/bundle/payload/payload-manifest.json').replace('wf-index-DxxdT4hP.js','wf-index-CeoNouGN.js').replace('exactPublicR36StaticRootVerified','exactR38CandidateStaticRootVerified')
ast.parse(s);p=V/'verify_unified_static_transport_r277.py';assert not p.exists();p.write_text(s,encoding='utf-8');print('R38_EXACT_FRONTEND_TRANSPORT_COMPARISON_PREPARED')
