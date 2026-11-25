#!/usr/bin/env python3
"""Detect wave-underlining geometry; character boundaries are estimates for review."""
import os,sys,json,io,unicodedata,math
from pathlib import Path
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
VENDOR=ROOT/'data/ocr/vendor'
if VENDOR.exists():sys.path.insert(0,str(VENDOR))
import cv2,numpy as np,fitz
from PIL import Image
cv2.setNumThreads(1)
OCR=ROOT/'data/ocr'; OUT=OCR/'short_underlines';OUT.mkdir(exist_ok=True)
PDF=Path(os.environ.get('CRIMINAL_LAW_SOURCE_PDF',str(ROOT/'source/original.pdf')))

def char_weights(text):
 return [1. if unicodedata.east_asian_width(c) in ('W','F','A') else .5 for c in text]

def map_to_line(candidate,lines):
 x,y,w,h=candidate['bbox_xywh'];possible=[]
 for r in lines:
  x0,y0,x1,y1=r['bbox'];overlap=max(0,min(x+w,x1)-max(x,x0))
  if overlap<=w*.35 or not y0<y:continue
  distance=abs(y-y1)
  if distance>max(9.,(y1-y0)*.45):continue
  possible.append((distance-overlap/w,r))
 if not possible:return None
 r=min(possible,key=lambda x:x[0])[1];text=r['text'];x0,y0,x1,y1=r['bbox']
 weights=char_weights(text);cum=np.concatenate(([0.],np.cumsum(weights)));total=cum[-1]
 begin=max(0,min(total,(x-x0)/(x1-x0)*total));end=max(0,min(total,(x+w-x0)/(x1-x0)*total))
 a=int(np.argmin(abs(cum-begin)));b=int(np.argmin(abs(cum-end)))
 if b<=a:b=min(len(text),a+1)
 return {'line_id':r['id'],'line_text':text,'char_start':a,'char_end_exclusive':b,'estimated_text':text[a:b],'ocr_confidence':r['confidence'],'boundary_status':'estimated_not_proofread'}

def process(d,number):
 page=d[number-1];im=Image.open(io.BytesIO(d.extract_image(page.get_images()[0][0])['image'])).convert('RGB');a=np.array(im);height,width=a.shape[:2]
 gray=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY);binary=(gray<175).astype('uint8')*255
 closed=cv2.morphologyEx(binary,cv2.MORPH_CLOSE,np.ones((1,3),np.uint8))
 n,labels,stats,centroids=cv2.connectedComponentsWithStats(closed,8)
 found=[];other=[]
 for x,y,w,h,area in stats[1:]:
  if not (14<=w<30 and 2<=h<=5 and height*.068<y<height*.945):continue
  sub=binary[y:y+h,x:x+w]>0;occupied=np.any(sub,axis=0);occupancy=float(np.mean(occupied))
  if occupancy<.85:continue
  center=[]
  for column in sub.T:
   ys=np.flatnonzero(column);center.append(float(np.mean(ys)) if len(ys) else float('nan'))
  center=np.array(center);xs=np.arange(w);good=np.isfinite(center)
  if np.sum(good)<20:continue
  coeff=np.polyfit(xs[good],center[good],1);residual=center[good]-np.polyval(coeff,xs[good]);std=float(np.std(residual))
  filled=np.interp(xs,xs[good],residual);freq=np.fft.rfftfreq(w);power=abs(np.fft.rfft(filled))**2
  band=(freq>.045)&(freq<.40);peak=float(np.max(power[band])/max(1e-9,np.sum(power[1:]))) if np.any(band) else 0.
  ink=a[y:y+h,x:x+w][sub];green=float(np.mean((ink[:,1]>ink[:,0]*1.12)&(ink[:,1]>ink[:,2]*1.02))) if len(ink) else 0.
  item={'bbox_xywh':[int(x),int(y),int(w),int(h)],'wave_score':round(peak,4),'detrended_center_std_px':round(std,4),'occupied_column_fraction':round(occupancy,4),'green_ink_fraction':round(green,4)}
  if .27<std<1.0 and peak>.45 and occupancy>.95:
   item['type']='short_wave_candidate';found.append(item)
  else:item['type']='other_line_candidate';other.append(item)
 clean_path=OCR/'clean'/f'p{number:03d}.json';lines=[]
 if clean_path.exists():lines=json.loads(clean_path.read_text())['lines']
 for c in found:c['ocr_match']=map_to_line(c,lines)
 result={'page':number,'image_width':width,'image_height':height,'method':'thin connected component + detrended oscillation spectrum','status':'automatically_detected_not_exhaustively_verified','wave_candidates':found,'other_line_candidates':other}
 (OUT/f'p{number:03d}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 return {'page':number,'wave_candidates':len(found),'matched':sum(c['ocr_match'] is not None for c in found)}

def rematch():
 total=0;matched=0
 for f in sorted(OUT.glob('p*.json')):
  r=json.loads(f.read_text());p=OCR/'clean'/f'p{r["page"]:03d}.json'
  if not p.exists():continue
  lines=json.loads(p.read_text())['lines']
  for c in r['wave_candidates']:
   c['ocr_match']=map_to_line(c,lines);total+=1;matched+=c['ocr_match'] is not None
  f.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
 return {'candidate_count':total,'ocr_matched_count':matched}

if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--rematch',action='store_true');parser.add_argument('--pages');args=parser.parse_args()
 if args.rematch:print(json.dumps(rematch()),flush=True)
 else:
  d=fitz.open(str(PDF));summary=[]
  nums=[int(i) for i in args.pages.split(',')] if args.pages else range(1,len(d)+1)
  for number in nums:
   r=process(d,number);summary.append(r)
   if number%20==0:print(json.dumps(r),flush=True)
  (OUT/'manifest.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'pages':len(summary),'wave_candidates':sum(i['wave_candidates'] for i in summary),'matched':sum(i['matched'] for i in summary)}),flush=True)
