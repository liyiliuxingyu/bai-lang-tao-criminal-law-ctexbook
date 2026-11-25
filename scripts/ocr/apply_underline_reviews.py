#!/usr/bin/env python3
"""Replay recorded visual decisions after machine underline detection/alignment."""
import os,json,copy
from pathlib import Path
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
OCR=ROOT/'data/ocr'
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 review=json.loads((OCR/'short_underline_review.json').read_text());merged=0
 for decision in review['decisions']:
  n=decision['page'];idx=decision['short_candidate_index'];sp=OCR/'short_underlines'/f'p{n:03d}.json';s=json.loads(sp.read_text());c=s['wave_candidates'][idx]
  if c['bbox_xywh']!=decision['bbox_xywh']:raise ValueError(f'Candidate identity changed at {n}/{idx}')
  if decision['decision']=='reject':c['visual_geometry_review']='rejected_character_stroke';save(sp,s);continue
  c['visual_geometry_review']='accepted'
  if n==140 and idx==0:
   m=c['ocr_match'];text=m['line_text'];assert text.endswith('官');m.update({'char_start':len(text)-1,'char_end_exclusive':len(text),'estimated_text':'官','boundary_status':'visually_checked_single_character','alignment_method':'direct source-image check of the final character 官'})
  save(sp,s);p=OCR/'underlines'/f'p{n:03d}.json';d=json.loads(p.read_text());item=copy.deepcopy(c);item['source']='short_wave_visual_review';item['source_short_candidate_index']=idx
  matching=[i for i,v in enumerate(d['wave_candidates']) if v['bbox_xywh']==c['bbox_xywh']]
  if matching:d['wave_candidates'][matching[0]]=item
  else:d['wave_candidates'].append(item);merged+=1
  save(p,d)
 audit=json.loads((OCR/'non_wave_exclusion_audit.json').read_text())
 for a in audit:
  p=OCR/'underlines'/f'p{a["page"]:03d}.json';d=json.loads(p.read_text());matches=[c for c in d['wave_candidates'] if c['bbox_xywh']==a['bbox_xywh']]
  if not matches:continue
  d['wave_candidates']=[c for c in d['wave_candidates'] if c['bbox_xywh']!=a['bbox_xywh']]
  d.setdefault('excluded_non_wave_candidates',[]).append({**matches[0],'visual_review_status':'rejected_non_wave','reason':a['reason']});save(p,d)
 manifest=[]
 for p in sorted((OCR/'underlines').glob('p[0-9][0-9][0-9].json')):
  d=json.loads(p.read_text());c=d['wave_candidates'];manifest.append({'page':d['page'],'wave_candidates':len(c),'matched':sum(bool(v.get('ocr_match')) for v in c),'short_visual_review_included':sum(v.get('source')=='short_wave_visual_review' for v in c),'excluded_non_waves':len(d.get('excluded_non_wave_candidates',[]))})
 save(OCR/'underlines/manifest.json',manifest)
 print(json.dumps({'new_short_merges':merged,'wave_segments':sum(v['wave_candidates'] for v in manifest),'matched':sum(v['matched'] for v in manifest)}),flush=True)
if __name__=='__main__':main()
