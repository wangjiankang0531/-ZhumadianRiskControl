from pathlib import Path
import ast,hashlib,json
R=Path('D:/Project/Zhumadian');T=R/'Application/tools';W=R/'work/user_feedback_20261031';script=T/'prepare_workflow_outcome_reconcile_20261101.py';tree=ast.parse(script.read_bytes());values={}
def value(n):
 if isinstance(n,ast.Constant):return n.value
 if isinstance(n,ast.Name):return values[n.id]
 if isinstance(n,ast.BinOp)and isinstance(n.op,ast.Add):return value(n.left)+value(n.right)
 if isinstance(n,(ast.List,ast.Tuple)):return [value(x)for x in n.elts]
 raise AssertionError('NON_LITERAL_PATCH_DEFINITION')
for n in tree.body:
 if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in ('helper','reconcile'):values[n.targets[0].id]=value(n.value)
rows=[]
for n in tree.body:
 if not(isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and isinstance(n.value.func,ast.Name)and n.value.func.id=='change'):continue
 rel=value(n.value.args[0]);pairs=value(n.value.args[1]);raw=(W/'emergency-workflow-source-r5/source'/rel).read_bytes();nl='\r\n'if b'\r\n'in raw else'\n';s=raw.decode().replace('\r\n','\n')
 for old,new in pairs:assert s.count(old)==1;s=s.replace(old,new,1)
 expected=s.replace('\n',nl).encode();actual=(W/'emergency-workflow-source-r6/source'/rel).read_bytes();assert expected==actual,'GENERATOR_BYTES_DIFFER:'+rel
 reverse=s
 for old,new in reversed(pairs):assert reverse.count(new)==1;reverse=reverse.replace(new,old,1)
 assert reverse.replace('\n',nl).encode()==raw
 rows.append({'source':rel,'generatorPatchPairs':len(pairs),'generatorReproducesActualBytes':True,'reverseToR5ByteExact':True,'sha256':hashlib.sha256(actual).hexdigest()})
assert len(rows)==2
p=R/'work/event_delivery_consistency_20261030/full-controller-r123/reconcile-source-generation-proof.json';p.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print(json.dumps(rows))
