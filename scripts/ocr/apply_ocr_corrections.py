#!/usr/bin/env python3
"""Apply only recorded, visually checked local corrections; preserve raw OCR."""
import os,json
from pathlib import Path
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
OCR=ROOT/'data/ocr'
def main():
 rows=json.loads((OCR/'verified_corrections.json').read_text());applied=0
 for c in rows:
  p=OCR/'clean'/f'p{c["page"]:03d}.json';d=json.loads(p.read_text());matches=[r for r in d['lines'] if r['id']==c['line_id']]
  if len(matches)!=1:raise ValueError(f'Missing or duplicate line {c["page"]}/{c["line_id"]}')
  r=matches[0]
  if r['text']==c['new_text']:continue
  if r['text']!=c['old_text']:raise ValueError(f'Conflicting previous edit at {c["page"]}/{c["line_id"]}')
  r['text']=c['new_text'];r['original_ocr_text']=c['old_text'];r['correction_status']='visually_checked_against_scan';r['correction_note']=c['note']
  tmp=p.with_suffix('.json.tmp');tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
  p.with_suffix('.txt').write_text('\n'.join(x['text'] for x in d['lines'])+'\n',encoding='utf-8');applied+=1
 print(json.dumps({'verified_corrections_applied':applied}),flush=True)
if __name__=='__main__':main()
