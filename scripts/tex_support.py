"""Shared, deterministic TeX escaping for source transcriptions."""
import re

SYMBOLS={
    '→':r'\ensuremath{\rightarrow}', '←':r'\ensuremath{\leftarrow}',
    '⇒':r'\ensuremath{\Rightarrow}', '⇔':r'\ensuremath{\Leftrightarrow}',
    '↔':r'\ensuremath{\leftrightarrow}', '≥':r'\ensuremath{\ge}',
    '≤':r'\ensuremath{\le}', '≠':r'\ensuremath{\ne}',
    '∈':r'\ensuremath{\in}', '∉':r'\ensuremath{\notin}',
    '∧':r'\ensuremath{\land}', '∨':r'\ensuremath{\lor}',
    '¬':r'\ensuremath{\neg}', '⊂':r'\ensuremath{\subset}',
    '×':r'\ensuremath{\times}', '÷':r'\ensuremath{\div}',
    'Ⅰ':'I', 'Ⅱ':'II', 'Ⅲ':'III', 'Ⅳ':'IV',
    '□':r'\ensuremath{\square}', '■':r'\ensuremath{\blacksquare}',
    '✓':r'\ensuremath{\checkmark}', '√':r'\ensuremath{\surd}',
    '★':r'\ensuremath{\star}', '☆':r'\ensuremath{\star}',
    '︱':'|', ' ':' ', '\u200b':'', '\ufeff':''}
SPECIAL={'\\':r'\textbackslash{}','{':r'\{','}':r'\}',
    '$':r'\$','&':r'\&','#':r'\#','%':r'\%','_':r'\_',
    '^':r'\textasciicircum{}','~':r'\textasciitilde{}',
    '<':r'\ensuremath{<}','>':r'\ensuremath{>}'}
def escape(s):
    return ''.join(SYMBOLS.get(c,SPECIAL.get(c,c)) for c in s)

def weighted_spans(text,bbox,segments):
    """Map measured underline extents to Unicode positions, retaining diagnostics."""
    x0,_,x1,_=bbox
    widths=[.56 if ord(c)<128 else 1. for c in text]
    total=sum(widths) or 1
    mids=[]; acc=0
    for w in widths:
        mids.append(x0+(acc+w/2)/total*(x1-x0));acc+=w
    on=[False]*len(text)
    for xa,xb in segments:
        for k,x in enumerate(mids):
            if xa-1<=x<=xb+1:on[k]=True
    out=[];i=0
    while i<len(text):
        j=i+1
        while j<len(text) and on[j]==on[i]:j+=1
        part=escape(text[i:j])
        out.append((r'\CJKunderwave{'+part+'}') if on[i] else part);i=j
    return ''.join(out)

def character_spans(text,ranges):
    on=[False]*len(text)
    for a,b in ranges:
        for i in range(max(0,int(a)),min(len(text),int(b))):on[i]=True
    out=[];i=0
    while i<len(text):
        j=i+1
        while j<len(text) and on[j]==on[i]:j+=1
        part=escape(text[i:j])
        out.append((r'\CJKunderwave{'+part+'}') if on[i] else part);i=j
    return ''.join(out)
