#!/usr/bin/env python3
"""Refine wave underline boundaries with CTC character positions; save second OCR evidence.
This refines a layout estimate. It does not certify spelling or whole-book proofreading.
"""
import os,sys,json,io,math,time,difflib,concurrent.futures
from pathlib import Path
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
OCR=ROOT/'data/ocr';VENDOR=OCR/'vendor'
if VENDOR.exists():sys.path.insert(0,str(VENDOR))
sys.path.insert(0,str(Path(__file__).parent))
from detect_underlines import map_to_line
OUT=OCR/'char_alignment';OUT.mkdir(exist_ok=True)
ENGINE=None;DOCUMENT=None

def init():
 global ENGINE,DOCUMENT
 from rapidocr_onnxruntime import RapidOCR
 import fitz,cv2
 cv2.setNumThreads(1)
 ENGINE=RapidOCR(intra_op_num_threads=1,inter_op_num_threads=1,rec_batch_num=6)
 DOCUMENT=fitz.open(os.environ.get('CRIMINAL_LAW_SOURCE_PDF',str(ROOT/'source/original.pdf')))

def character_index_map(original,recognized):
 mapping={};exact=True
 for op,i0,i1,j0,j1 in difflib.SequenceMatcher(None,original,recognized,autojunk=False).get_opcodes():
  if op=='equal':
   for i,j in zip(range(i0,i1),range(j0,j1)):mapping[j]=i
  elif op=='replace' and i1-i0==j1-j0:
   for i,j in zip(range(i0,i1),range(j0,j1)):mapping[j]=i
   exact=False
  elif op=='insert' and recognized[j0:j1].isspace():pass
  elif op=='delete' and original[i0:i1].isspace():pass
  else:exact=False
 return mapping,exact

def process(number):
 import numpy as np,cv2
 from PIL import Image
 start=time.time();clean=json.loads((OCR/'clean'/f'p{number:03d}.json').read_text());lines=clean['lines'];line_by_id={r['id']:r for r in lines}
 sets=[];selected=set()
 for kind in ['underlines','short_underlines']:
  f=OCR/kind/f'p{number:03d}.json'
  if not f.exists():continue
  d=json.loads(f.read_text())
  for c in d['wave_candidates']:
   c['ocr_match']=map_to_line(c,lines)
   if c['ocr_match']:selected.add(c['ocr_match']['line_id'])
  sets.append((f,d))
 # Include long low-confidence lines for a second, localized recognition record.
 selected.update(r['id'] for r in lines if r['confidence']<.94 and len(r['text'])>=10)
 if not selected:return {'page':number,'selected_lines':0}
 p=DOCUMENT[number-1];image=Image.open(io.BytesIO(DOCUMENT.extract_image(p.get_images()[0][0])['image'])).convert('RGB')
 crops=[];origins=[];ids=sorted(selected)
 for lid in ids:
  r=line_by_id[lid];x0,y0,x1,y1=r['bbox'];x0=max(0,math.floor(x0)-2);y0=max(0,math.floor(y0)-2);x1=min(image.width,math.ceil(x1)+2);y1=min(image.height,math.ceil(y1)+2)
  crop=image.crop((x0,y0,x1,y1));crop=crop.resize((crop.width*2,crop.height*2),Image.Resampling.LANCZOS);crops.append(cv2.cvtColor(np.asarray(crop),cv2.COLOR_RGB2BGR));origins.append((x0,y0))
 predictions,elapsed=ENGINE.text_rec(crops,return_word_box=True)
 boxes=[np.array([[0.,0.],[float(c.shape[1]),0.],[float(c.shape[1]),float(c.shape[0])],[0.,float(c.shape[0])]],dtype=np.float32) for c in crops]
 enriched=ENGINE.cal_rec_boxes(crops,boxes,predictions);records=[]
 for lid,origin,result in zip(ids,origins,enriched):
  recognized,confidence,word_boxes,word_contents,word_confidences=result
  original=line_by_id[lid]['text'];mapping,exact=character_index_map(original,recognized);chars=[];cursor=0
  for k,(token,box) in enumerate(zip(word_contents,word_boxes)):
   token=str(token);pos=recognized.find(token,cursor)
   if pos<0:pos=cursor
   end=pos+len(token);cursor=end
   coords=[[float(x)/2+origin[0],float(y)/2+origin[1]] for x,y in box];xs=[q[0] for q in coords];ys=[q[1] for q in coords];mapped=[mapping[z] for z in range(pos,end) if z in mapping]
   chars.append({'text':token,'recognized_start':pos,'recognized_end':end,'original_indices':mapped,'bbox':[min(xs),min(ys),max(xs),max(ys)],'confidence':float(np.mean(word_confidences[k])) if k<len(word_confidences) else None})
  records.append({'line_id':lid,'original_text':original,'second_pass_text':recognized,'second_pass_confidence':float(confidence),'character_text_alignment_exact':exact,'characters':chars})
 by_id={r['line_id']:r for r in records};updated=0
 for f,d in sets:
  for c in d['wave_candidates']:
   m=c.get('ocr_match')
   if not m or m['line_id'] not in by_id:continue
   r=by_id[m['line_id']];x,y,w,h=c['bbox_xywh'];selected_indices=[]
   for char in r['characters']:
    x0,y0,x1,y1=char['bbox'];center=(x0+x1)/2
    if x-1.5<=center<=x+w+1.5:selected_indices.extend(char['original_indices'])
   if not selected_indices:continue
   a=min(selected_indices);b=max(selected_indices)+1
   c['previous_geometric_match']=m
   c['ocr_match']={**m,'char_start':a,'char_end_exclusive':b,'estimated_text':r['original_text'][a:b],'boundary_status':'character_aligned_not_proofread','alignment_method':'PP-OCR CTC character coordinates with sequence alignment','character_text_alignment_exact':r['character_text_alignment_exact'],'second_pass_confidence':r['second_pass_confidence']}
   updated+=1
  temp=f.with_suffix('.json.tmp');temp.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(f)
 (OUT/f'p{number:03d}.json').write_text(json.dumps({'page':number,'status':'localized_second_pass_not_whole_page_proofreading','lines':records},ensure_ascii=False,indent=2),encoding='utf-8')
 return {'page':number,'selected_lines':len(ids),'updated_wave_boundaries':updated,'seconds':round(time.time()-start,2),'text_disagreements':sum(r['original_text']!=r['second_pass_text'] for r in records)}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--pages');p.add_argument('--workers',type=int,default=6);a=p.parse_args()
 nums=[int(x) for x in a.pages.split(',')] if a.pages else list(range(1,435))
 failed=0
 with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers,initializer=init) as ex:
  fs={ex.submit(process,n):n for n in nums}
  for fut in concurrent.futures.as_completed(fs):
   try:print(json.dumps(fut.result()),flush=True)
   except Exception as e:
    failed+=1;print(json.dumps({'page':fs[fut],'error':str(e)}),flush=True)
 if failed:raise SystemExit(1)
