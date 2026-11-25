#!/usr/bin/env python3
"""Deterministic cleaning of detected running headers/footer; raw OCR remains intact."""
from pathlib import Path
import os,json,re
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
OCR=ROOT/'data/ocr'
def run():
 count=0;removed_count=0
 for path in sorted((OCR/'raw').glob('p[0-9][0-9][0-9].json')):
  try:d=json.loads(path.read_text())
  except (OSError,ValueError):continue
  h=d['image_height'];number=d['page'];kept=[];removed=[]
  for r in d['lines']:
   x0,y0,x1,y1=r['bbox'];txt=r['text'];reason=None
   if '关注公众号' in txt or ('法考180' in txt and y0>h*.9):reason='promotional_footer'
   elif y1<h*.075 and number>=13:reason='running_header'
   elif y0<h*.12 and number>=13 and ('专题讲座' in txt or '精讲卷' in txt):reason='running_header'
   elif y0>h*.935 and (re.fullmatch(r'[\d\sivxIVXⅠⅡⅢⅣⅤ·.]+',txt) or y0>h*.957):reason='page_number_or_footer'
   if reason:removed.append({**r,'removal_reason':reason})
   else:kept.append(r)
  clean={**d,'lines':kept,'removed_lines':removed,'cleanup_note':'Promotional footer, running header, page numerals excluded by deterministic layout rules; original OCR retained in raw. Text and reading order remain unproofread.'}
  dest=OCR/'clean'/path.name;temp=dest.with_suffix('.json.tmp');temp.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(dest)
  dest.with_suffix('.txt').write_text('\n'.join(r['text'] for r in kept)+'\n',encoding='utf-8')
  count+=1;removed_count+=len(removed)
 print(json.dumps({'pages_cleaned':count,'removed_lines':removed_count}),flush=True)
if __name__=='__main__':run()
