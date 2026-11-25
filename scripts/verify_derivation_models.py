#!/usr/bin/env python3
"""Exhaust finite models used in math_derivations.tex; not a legal verifier."""
from itertools import product
from pathlib import Path
from fractions import Fraction
import json

checks=[]
def passed(name,cases,scope):
    checks.append({'name':name,'cases':cases,'passed':True,'scope':scope})

valuations=list(product((False,True),repeat=3))
partial=list(product((None,False,True),repeat=3))
def completions(p):
    return {v for v in valuations if all(a is None or a==b for a,b in zip(p,v))}
count=0
for p,q in product(partial,repeat=2):
    if all(a is None or a==b for a,b in zip(p,q)):
        assert completions(q)<=completions(p)
        count+=1
passed('一致事实扩充缩小模型集合',count,'三原子、所有部分赋值的扩充关系')

count=0
for b,s,x,h in product((False,True),repeat=4):
    branches=[not b,b and s,b and not s and x and h,b and not s and not(x and h)]
    assert sum(branches)==1
    count+=1
passed('防卫四检索分支互斥并穷尽',count,'仅验证已定义分支；不认定基础事实或特殊防卫条件')

for v,r,e in product((False,True),repeat=3):
    z=v and (not r or e)
    if r:assert z==(v and e)
passed('中止必要有效性分支化简',8,'R取真时Z等价于V且E；不把Z为假自动认作未遂')

count=0
for n in range(1,7):
    assert all([True]*n)
    for removed in range(n):
        v=[True]*n;v[removed]=False
        assert not all(v) and all(v[i] for i in range(n) if i!=removed)
        count+=1
passed('独立合取条件集的逐项缺失反模型',count,'一至六个独立原子的有限验证')

for c1,c2 in product((False,True),repeat=2):
    g1=True and True and c1
    g2=True and False and c2
    assert not g2
passed('逐人故意归责的零条件阻断',4,'行为贡献相同并不补出缺失故意；不评价其他责任')

# A true negative branch does not eliminate another true branch.
assert (not False) and (False or True)
passed('析取的单支否定反模型',1,'A为假且B为真，整体析取仍真')

# Same state pair, distinct labelled mechanisms: endpoint observation is not injective.
histories=[('owner_controls','peaceful_taking','actor_controls'),
           ('owner_controls','deceived_disposition','actor_controls')]
assert histories[0][::2]==histories[1][::2] and histories[0][1]!=histories[1][1]
passed('相同占有端点不能识别取得机制',2,'结构反例；未在程序中认定具体罪名')

# D(d,p), P(q,o), but no P(p,o): a relational join must share its middle key.
deceives={('d','p')};disposes={('q','o')}
joined={(d,o) for d,p in deceives for q,o in disposes if p==q}
assert not joined
passed('三角关系连接不能更换中间主体',1,'只验证连接逻辑；不决定处分地位的法律含义')

assert all(p or not p for p in (False,True))
passed('一致补全保留重复原子的相关性',2,'P或非P在每个二值补全中为真')

count=0
for xs in product(range(1,16),repeat=3):
    total=sum(xs);maximum=max(xs);cap=20 if total<35 else 25
    nonempty=maximum<=min(total,cap)
    assert nonempty==(maximum<=cap)
    count+=1
passed('并罚数值区间非空条件',count,'三项正整数期数的模型检查；不验证法律适用与裁量')

def q(v,e):return v>=20 or (10<=v<20 and e)
count=0
for v in (Fraction('9.999'),Fraction(10),Fraction(15),Fraction('19.999'),Fraction(20)):
    for e in (False,True):
        want=False if v<10 else e if v<20 else True
        assert q(v,e)==want
        count+=1
passed('带额外情节的双金额路径',count,'万元单位下的已声明公式；不是完整犯罪构成')

assert max(10,8)-3 != max(10-3,8)
passed('先并后减与先减后并不当然可交换',1,'max仅是代数反例，明确不是实际并罚算子')

report={'all_passed':True,'checks':checks,
        'scope':'有限模型、关系连接、分支穷尽和数值边界检查；不验证规范的合法性、证据真实性或全部法律结论。'}
(Path(__file__).resolve().parents[1]/'audit/derivation_model_checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
