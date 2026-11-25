#!/usr/bin/env python3
"""Narrow OCR homograph normalization, with per-occurrence audit; raw remains unchanged.
Rules are based on visually checked exemplars and context. Not every occurrence is
individually image-verified, so these must not be counted as manual proofreading.
"""
import os,json,re
from pathlib import Path
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
OCR=ROOT/'data/ocr'
RULES=[
 ('介人','介入','legal term 介入因素; exemplar PDF63/line14'),
 ('吸人沙子','吸入沙子','exemplar PDF87/line15'),
 ('(?P<prefix>应|不能|不|[A-D]项)人选',r'\g<prefix>入选','answer-selection context only; exemplar PDF87/line16'),
 ('进人','进入','entry verb; exemplar PDF82/line8 and PDF247/line20'),
 ('非法侵人','非法侵入','criminal-law phrase; exemplar PDF247/line20'),
 ('人户(?=盗窃|抢)','入户','burglary/robbery modifier only; exemplar PDF118/line15'),
 ('投人流通','投入流通','currency phrase; exemplar PDF340/line12'),
 ('壹死','噎死','choking example; exemplar PDF42/line27'),
 ('翰旋受贿','斡旋受贿','legal term; exemplar PDF10/line55')
]
def main():
 audit=[]
 existing_file=OCR/'term_correction_audit.json'
 prior=json.loads(existing_file.read_text()) if existing_file.exists() else []
 for file in sorted((OCR/'clean').glob('p[0-9][0-9][0-9].json')):
  try:d=json.loads(file.read_text())
  except (OSError,ValueError):continue
  prev='';changed=False
  for line in d['lines']:
   original=line['text'];value=original;rule_names=[]
   for pattern,replacement,note in RULES:
    new,n=re.subn(pattern,replacement,value)
    if n:rule_names.append({'pattern':pattern,'replacement':replacement,'occurrences':n,'rationale':note});value=new
   if value.startswith('人因素') and prev.endswith('介'):
    value='入因素'+value[3:];rule_names.append({'pattern':'line-break 介 / 人因素','replacement':'介 / 入因素','occurrences':1,'rationale':'continuation of same legal term'})
   if value!=original:
    audit.append({'page':d['page'],'line_id':line['id'],'before':original,'after':value,'rules':rule_names,'review_status':'rule_based_with_visually_checked_exemplars_not_individual_proofreading'})
    line['pre_term_correction_text']=original;line['text']=value;line['term_correction_status']='rule_based_with_audit';changed=True
   prev=value
  if changed:
   tmp=file.with_suffix('.json.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(file);file.with_suffix('.txt').write_text('\n'.join(r['text'] for r in d['lines'])+'\n',encoding='utf-8')
 merged={(r['page'],r['line_id'],r['before']):r for r in prior+audit}
 (OCR/'term_correction_audit.json').write_text(json.dumps(list(merged.values()),ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'corrected_lines':len(audit),'rule_occurrences':sum(sum(x['occurrences'] for x in r['rules']) for r in audit)}),flush=True)
if __name__=='__main__':main()
