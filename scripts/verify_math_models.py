#!/usr/bin/env python3
"""有限域模型核验，不验证法律前提、证据或全部LaTeX论证。"""
from itertools import product
from fractions import Fraction
from pathlib import Path
import json

def conjunction(a, b):
    if a == 0 or b == 0:
        return 0
    if a == 1 and b == 1:
        return 1
    return None

def unit_bribery_condition(amount_in_wan, listed_circumstance):
    v = Fraction(amount_in_wan)
    return v >= 20 or (10 <= v < 20 and listed_circumstance)

def sentence_interval(years):
    assert years and all(x > 0 for x in years)
    total = sum(years)
    ceiling = 20 if total < 35 else 25
    return max(years), min(total, ceiling)

checks = []
for a, b, c in product((0, 1, None), repeat=3):
    assert conjunction(conjunction(a,b),c) == conjunction(a,conjunction(b,c))
checks.append({'name':'三值合取结合律','cases':27,'passed':True})
for a, b in product((0,1,None), repeat=2):
    assert conjunction(a,b) == conjunction(b,a)
    if a == 0 or b == 0:
        assert conjunction(a,b) == 0
checks.append({'name':'三值合取交换律与零吸收','cases':9,'passed':True})
assert (not False or True) and True and not False
checks.append({'name':'肯定后件的反模型','assignment':{'P':False,'Q':True},'passed':True})
assert not (False and True)
assert not (True and False)
checks.append({'name':'过当双条件不能由单项推出','assignments':[{'X':False,'H':True},{'X':True,'H':False}],'passed':True})
# 同一共同条件P无法区分两个互斥标签的具体反模型。
x1={'P':True,'C1':True,'C2':False}
x2={'P':True,'C1':False,'C2':True}
assert x1['P']==x2['P'] and x1['C1']!=x2['C1']
checks.append({'name':'共同条件不能唯一分类的反模型','assignments':[x1,x2],'passed':True})
# 验证金额分支边界及单位为万元的明确约定。
amount_checks=[('9.999',False,False),('9.999',True,False),('10',False,False),('10',True,True),('15',False,False),('15',True,True),('19.999',False,False),('19.999',True,True),('20',False,True),('20',True,True)]
for v,e,want in amount_checks:
    assert unit_bribery_condition(v,e)==want
checks.append({'name':'2026单位受贿示例条件的金额边界','cases':len(amount_checks),'passed':True,'scope':'仅核验已给定Q公式，不验证其他构成、版本适用或法律充分性'})
for xs,want in [([8,10,12],(12,20)),([7,11,12],(12,20)),([10,12,15],(15,25)),([10,10,15],(15,25)),([10,10,14],(14,20))]:
    assert sentence_interval(xs)==want
checks.append({'name':'通常同种有期徒刑并罚例题及35年分界','cases':5,'passed':True,'scope':'仅纯有期徒刑且无特别限制模型'})
source=(Path(__file__).resolve().parents[1]/'tex/math_content.tex').read_text()
import re
assert len(re.findall(r'\\section\{第[一二三四五六七八九十]+讲',source))==25
assert len(re.findall(r'\\memorycard\{',source))==25
assert set(re.findall(r'\\lawref\{([^}]+)\}',source)) <= set(re.findall(r'\\hypertarget\{([^}]+)\}',source))
checks.append({'name':'二十五讲与记忆卡齐全、来源标签闭合','passed':True})
report={'scope':'有限赋值、数值边界与源文件结构核验；不等于法律校订或证明助手认证','checks':checks,'all_passed':True}
out=(Path(__file__).resolve().parents[1]/'audit/model_checks.json')
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
