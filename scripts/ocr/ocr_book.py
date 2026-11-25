#!/usr/bin/env python3
"""Resumable geometric OCR. Original page coordinates are native image pixels.
Machine recognition does not constitute textual or legal proofreading.
"""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
 os.environ[name]='1'
from pathlib import Path
import sys,time,json,csv,io,hashlib,argparse,statistics,re,concurrent.futures
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
OCR=ROOT/'data/ocr'
VENDOR=OCR/'vendor'
if VENDOR.is_dir(): sys.path.insert(0,str(VENDOR))
PDF=Path(os.environ.get('CRIMINAL_LAW_SOURCE_PDF',str(ROOT/'source/original.pdf')))
ENGINE=None
DOCUMENT=None

def initialize():
 global ENGINE,DOCUMENT
 from rapidocr_onnxruntime import RapidOCR
 import fitz
 ENGINE=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,rec_batch_num=6)
 DOCUMENT=fitz.open(str(PDF))

def process_page(number):
 from PIL import Image
 import numpy as np
 start=time.time()
 raw_file=OCR/'raw'/f'p{number:03d}.json'
 clean_file=OCR/'clean'/f'p{number:03d}.json'
 if raw_file.exists() and clean_file.exists():
  try:
   previous_raw=json.loads(raw_file.read_text()); previous_clean=json.loads(clean_file.read_text())
   if previous_raw.get('page')==number and previous_clean.get('page')==number:
    return {'page':number,'cached':True}
  except (OSError,ValueError):
   pass
 page=DOCUMENT[number-1]
 xref=page.get_images()[0][0]
 image=Image.open(io.BytesIO(DOCUMENT.extract_image(xref)['image'])).convert('RGB')
 w,h=image.size
 # Neural detection benefits from an expanded dense source; keep original coordinates in output.
 image=image.resize((2*w,2*h),Image.Resampling.LANCZOS)
 result,timings=ENGINE(np.array(image),use_cls=False)
 rows=[]
 for k,item in enumerate(result or []):
  polygon,text,confidence=item
  box=[[round(float(x)/2,2),round(float(y)/2,2)] for x,y in polygon]
  xs=[v[0] for v in box];ys=[v[1] for v in box]
  rows.append({'id':k,'text':text,'confidence':round(float(confidence),6),'polygon':box,'bbox':[min(xs),min(ys),max(xs),max(ys)]})
 raw={'page':number,'image_width':w,'image_height':h,'pdf_width_pt':page.rect.width,'pdf_height_pt':page.rect.height,'engine':'rapidocr_onnxruntime / PP-OCR','source_scale':2,'lines':rows,'timings_s':timings,'proofread':False}
 raw_file.write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
 (OCR/'raw'/f'p{number:03d}.txt').write_text('\n'.join(r['text'] for r in rows)+'\n',encoding='utf-8')
 with (OCR/'raw'/f'p{number:03d}.tsv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.writer(f,delimiter='\t');writer.writerow(['id','left','top','right','bottom','confidence','text'])
  for r in rows:writer.writerow([r['id'],*r['bbox'],r['confidence'],r['text']])
 kept=[];removed=[]
 for r in rows:
  x0,y0,x1,y1=r['bbox'];txt=r['text'];reason=None
  if '关注公众号' in txt or ('法考180' in txt and y0>h*.9):reason='promotional_footer'
  elif y1<h*.068 and number>=13:reason='running_header'
  elif y0>h*.935 and (re.fullmatch(r'[\d\sivxIVX·.]+',txt) or y0>h*.957):reason='page_number_or_footer'
  if reason:removed.append({**r,'removal_reason':reason})
  else:kept.append(r)
 clean={**raw,'lines':kept,'removed_lines':removed,'cleanup_note':'Promotional footer, running header, page numerals excluded; original OCR retained in raw. Text and reading order remain unproofread.'}
 clean_file.write_text(json.dumps(clean,ensure_ascii=False,indent=2),encoding='utf-8')
 (OCR/'clean'/f'p{number:03d}.txt').write_text('\n'.join(r['text'] for r in kept)+'\n',encoding='utf-8')
 return {'page':number,'lines':len(rows),'chars':sum(len(r['text']) for r in kept),'low_conf_lines':sum(r['confidence']<.95 for r in kept),'seconds':round(time.time()-start,1)}

def combine():
 files=sorted((OCR/'clean').glob('p*.json'))
 summary=[];text=[]
 for f in files:
  try: d=json.loads(f.read_text())
  except (OSError,ValueError): continue
  ls=d['lines'];n=d['page']
  summary.append({'page':n,'lines':len(ls),'characters':sum(len(r['text']) for r in ls),'low_confidence_lines':sum(r['confidence']<.95 for r in ls),'removed_lines':len(d.get('removed_lines',[])),'proofread':False})
  text.append(f'\n\n===== PDF PAGE {n:03d} =====\n'+'\n'.join(r['text'] for r in ls))
 (OCR/'full_book_clean.txt').write_text(''.join(text),encoding='utf-8')
 (OCR/'page_manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 return {'pages':len(summary),'characters':sum(x['characters'] for x in summary)}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--pages');p.add_argument('--workers',type=int,default=6);p.add_argument('--all',action='store_true');a=p.parse_args()
 for name in ['raw','clean','images']: (OCR/name).mkdir(parents=True,exist_ok=True)
 if a.pages:
  nums=[]
  for s in a.pages.split(','):
   if '-' in s:
    l,r=map(int,s.split('-'));nums.extend(range(l,r+1))
   else:nums.append(int(s))
 else:nums=list(range(1,435))
 nums=list(dict.fromkeys(nums))
 with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers,initializer=initialize) as ex:
  futures={ex.submit(process_page,n):n for n in nums}
  for fut in concurrent.futures.as_completed(futures):
   try:r=fut.result();print(json.dumps(r,ensure_ascii=False),flush=True)
   except Exception as e:print(json.dumps({'page':futures[fut],'error':str(e)},ensure_ascii=False),flush=True)
 print('SUMMARY '+json.dumps(combine(),ensure_ascii=False),flush=True)
