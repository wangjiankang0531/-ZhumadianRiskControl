"""Append exact own source/proofs to existing local review branches; never push."""
from pathlib import Path
import ast,hashlib,importlib.util,json,shutil
R=Path('D:/Project/Zhumadian');A=R/'Application';E=R/'XNBYEngine';V=Path(__file__).resolve().parent
D=R/'Document/Deployment/resource_control_integration_r2440_20261112';S=A/'tools/experimental_source/resource_control_integration_r2440';P=A/'deploy/verification/resource_control_integration_r2440'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report=D/'local-review-git-r2442.json';assert not report.exists()
 result=json.loads((D/'source-retirement-r2441.json').read_bytes());assert result['retiredFiles']==319
 for src,dst in [(D/'source-retirement-r2441.json',P/'source-retirement-r2441.json'),(V/'retire_scene_source_r2441.py',S/'recipe/retire_scene_source_r2441.py'),(Path(__file__),S/'recipe/commit_control_integration_r2442.py')]:
  assert not dst.exists();shutil.copyfile(src,dst);assert sha(src)==sha(dst)
 note='\n\nR2442清理实记：已核原R2435根0/Job0、新鲜成功CIM零引用、绝对边界/无重解析与319份保留源SHA，仅退本轮source副本319文件5,595,971逻辑字节。保五当前产物与完整固定源索引/原源；磁盘同期可用量331991109632→331997437952字节，仅作观察，非独占物理释放。旧source副本已无，重跑构建须从固定索引重新准备；未删服务器或GIS/业务数据。\n'
 handbook=A/'deploy/handbook/完整资源控制整合与客户机启动缺口_r2440_20261112.md';eng=E/'docs/project/资源完整整合与客户机启动链_r2440_20261112.md'
 for p in(handbook,eng,D/'阶段说明.md'):
  with p.open('a',encoding='utf8')as f:f.write(note)
 files=[]
 for root in(S,P,A/'tools/experimental_source/resource_control_merge_r2433'):
  for p in root.rglob('*'):
   if not p.is_file():continue
   assert not p.is_symlink()and not p.is_junction()and not p.lstat().st_file_attributes&1024
   if p.suffix=='.py':ast.parse(p.read_text('utf8'),filename=str(p))
   if p.suffix=='.json':json.loads(p.read_bytes())
   files.append(p.relative_to(A).as_posix())
 files.append(handbook.relative_to(A).as_posix())
 held=sha(A/'native/main.cpp')
 spec=importlib.util.spec_from_file_location('r2442own_git',V/'commit_r18_local_review.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
 a=g.commit(A,'de1832200d019bde6985d9495f63ef5a2e13d8d8','review/workplace-r19-live-local-20261031',sorted(files),'r2442-app','Record fixed D176 full portal and scene integration, closed graph audit and client startup gap',update_existing=True)
 e=g.commit(E,'04c61968ced7d6bf6c5aca8de9a14fe6f5fd986f','review/workplace-r19-live-progress-local-20261031',[eng.relative_to(E).as_posix()],'r2442-engine','Record local integration and pending normal two-client acceptance without changing public R51',update_existing=True)
 assert held==sha(A/'native/main.cpp')
 value={'application':a,'engine':e,'heldNativeUnchanged':True,'publicPushed':False,'publicReleaseUnchangedR51':True}
 with report.open('x',encoding='utf8')as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(value,ensure_ascii=False))
if __name__=='__main__':main()
