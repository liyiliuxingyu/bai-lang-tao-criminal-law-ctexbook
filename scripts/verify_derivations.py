"""Finite checks of the explicitly delimited models; not certification of law."""
from itertools import product
from pathlib import Path
import json
out=Path(__file__).resolve().parents[1]/'audit'
checks=[]
vals=list(product([False,True], repeat=3))
examined=0
for mask in range(1,1<<len(vals)):
 models=[v for i,v in enumerate(vals) if mask>>i&1]
 compatible=any((not a) and b for a,b,c in models)
 if compatible:
  narrowed=[v for v in models if not v[0]]
  assert any(a or b or c for a,b,c in narrowed)
  examined+=1
checks.append({'name':'析取替代路径在相容背景下的反模型','background_model_sets':255,'compatible_cases':examined,'passed':True})
for B,S,X,H in product([False,True],repeat=4):
 ds=[not B, B and S, B and not S and X and H, B and not S and not(X and H)]
 assert sum(ds)==1
checks.append({'name':'防卫四分支互斥且穷尽','assignments':16,'passed':True})
for V,E in product([False,True],repeat=2):
 R=True
 assert (V and ((not R) or E))==(V and E)
assert not (True and ((not True) or False))
checks.append({'name':'仅在已限定中止适用域内的有效性分支','assignments':4,'passed':True})
for C2 in [False,True]:
 G1=True and True and True;G2=True and False and C2
 assert G1 and not G2
checks.append({'name':'相同行为贡献不保证相同归责候选','countermodels':2,'passed':True})
# Events can all exist while a required causal connector is false.
for edge in range(3):
 links=[True]*3;links[edge]=False
 assert all([True]*5) and not all([True]*5+links)
checks.append({'name':'三角诈骗事件并存不能替代三段机制连接','countermodels':3,'passed':True})
# A finite family supporting Q does not establish every additional family.
listed_models=[{'Q':True}];extra_models=[{'Q':False}]
assert all(v['Q'] for v in listed_models) and not all(v['Q'] for v in extra_models)
checks.append({'name':'学说比较的一般性反例，非对任意Q假设反方案','passed':True})
a,b,e=10,8,3
assert max(a,b)-e==7 and max(a-e,b)==8
checks.append({'name':'先并后减/先减后并的玩具算子不交换','scope':'仅代数反例，绝非实际量刑算法','passed':True})
report={'scope':'有限模型与反模型复核；不等于规范有效性、全部案例校订或证明助手认证','checks':checks,'all_passed':all(c['passed'] for c in checks)}
(out/'derivation_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
