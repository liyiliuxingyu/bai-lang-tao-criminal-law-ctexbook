#!/usr/bin/env python3
"""Reconstruct identified source figures as OCR text + measured vector geometry.

No source image is embedded in the resulting TeX or PDF. This is an automatic
transcription, not a claim that labels or graph semantics were manually checked.
Manual semantic TikZ replacements always take precedence.
"""
from pathlib import Path
import argparse, json, io, re, os, sys
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[name]='1'
vendor=Path(__file__).resolve().parents[2]/'ocr/vendor'
if vendor.exists():sys.path.insert(0,str(vendor))
import fitz, cv2, numpy as np
from PIL import Image
from tex_support import escape
cv2.setNumThreads(1)

def read_image(doc, page):
    p=doc[page-1]
    im=doc.extract_image(p.get_images()[0][0])['image']
    return np.array(Image.open(io.BytesIO(im)).convert('RGB'))

def intersects_center(line,bbox):
    x0,y0,x1,y1=line['bbox'];a,b,c,d=bbox
    return a-2<=(x0+x1)/2<=c+2 and b-2<=(y0+y1)/2<=d+2

def contained_fraction(a,b):
    x0,y0,x1,y1=a;u0,v0,u1,v1=b
    return max(0,min(x1,u1)-max(x0,u0))*max(0,min(y1,v1)-max(y0,v0))/max(1,(x1-x0)*(y1-y0))

def reconstruction(rgb,lines,box,outfile,meta):
    h,w=rgb.shape[:2]
    # Include complete OCR labels when their centers belong to the region.
    chosen=[x for x in lines if intersects_center(x,box)]
    x0,y0,x1,y1=box
    if chosen:
        x0=min(x0,min(x['bbox'][0]-3 for x in chosen));x1=max(x1,max(x['bbox'][2]+3 for x in chosen))
        y0=min(y0,min(x['bbox'][1]-3 for x in chosen));y1=max(y1,max(x['bbox'][3]+3 for x in chosen))
    x0,y0,x1,y1=map(int,[max(0,x0),max(0,y0),min(w,x1),min(h,y1)])
    crop=rgb[y0:y1,x0:x1].astype(np.int16)
    R,G,B=crop[:,:,0],crop[:,:,1],crop[:,:,2]
    # Structural ink is usually green; black rules occur in some diagrams.
    green=((G-R>10)&(B-R>3)&(R<234)&(G>65)).astype(np.uint8)*255
    black=((np.max(crop,axis=2)<155)&((np.max(crop,axis=2)-np.min(crop,axis=2))<40)).astype(np.uint8)*255
    for item in chosen:
        a,b,c,d=item['bbox']
        xa=max(0,int(a-x0)-2);ya=max(0,int(b-y0)-1)
        xb=min(x1-x0,int(c-x0)+3);yb=min(y1-y0,int(d-y0)+2)
        green[ya:yb,xa:xb]=0;black[ya:yb,xa:xb]=0
    # Exclude filled background panels; their thin frames can still remain.
    solid=cv2.morphologyEx(green,cv2.MORPH_OPEN,np.ones((7,7),np.uint8))
    green=cv2.bitwise_and(green,cv2.bitwise_not(solid))
    ink=cv2.bitwise_or(green,black)
    # Remove isolated photographic noise / residual glyph specks.
    num,lab,st,cent=cv2.connectedComponentsWithStats(ink,8)
    clean=np.zeros_like(ink)
    kept=0
    for j in range(1,num):
        a,b,ww,hh,area=st[j]
        if area>=9 and (ww>=12 or hh>=10):
            clean[lab==j]=255;kept+=1
    contours,hierarchy=cv2.findContours(clean,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    unit=.50
    # Fit source horizontal span at roughly a 17 cm text block.
    if x1-x0>950:unit=480/(x1-x0)
    result=[f'% {meta["id"]}; source page {meta["pdf_page"]}; automatic measured-geometry reconstruction',
      '% Text and vector paths are editable. OCR labels require semantic proofreading.',
      r'\begin{tikzpicture}[x='+f'{unit:.5f}pt'+r',y=-'+f'{unit:.5f}pt'+r']']
    result.append(r'\path[use as bounding box] (0,0) rectangle '+f'({x1-x0},{y1-y0});')
    vector_paths=0
    if hierarchy is not None:
        hier=hierarchy[0]
        for i,contour in enumerate(contours):
            if hier[i][3]!=-1:continue
            ids=[i];child=hier[i][2]
            while child!=-1:
                ids.append(child);child=hier[child][0]
            parts=[]
            for cid in ids:
                poly=cv2.approxPolyDP(contours[cid],.65,True).reshape(-1,2)
                if len(poly)<3:continue
                parts.append(' -- '.join(f'({int(a)},{int(b)})' for a,b in poly)+' -- cycle')
            if parts:
                result.append(r'\path[fill=black!65,draw=none,even odd rule] '+' '.join(parts)+';')
                vector_paths+=1
    for item in chosen:
        a,b,c,d=item['bbox'];txt=item['text']
        # Retain circled references and mathematical arrows as editable Unicode/TeX.
        fs=max(5.5,min(12,(d-b)*unit*.87))
        width=max(1,(c-a)*unit)
        xc=(a+c)/2-x0;yc=(b+d)/2-y0
        result.append(r'\node[anchor=center,inner sep=0pt,outer sep=0pt] at '+f'({xc:.2f},{yc:.2f}) '+
          r'{\resizebox{'+f'{width:.3f}pt'+r'}{!}{\fontsize{'+f'{fs:.3f}'+r'}{'+f'{fs*1.2:.3f}'+r'}\selectfont '+escape(txt)+r'}};')
    result.append(r'\end{tikzpicture}')
    outfile.write_text('\n'.join(result)+'\n',encoding='utf-8')
    return dict(meta,bbox_native=[x0,y0,x1,y1],image_width=w,image_height=h,
       text_line_ids=[x['id'] for x in chosen],node_count=len(chosen),vector_path_count=vector_paths,
       tex_file=outfile.name,method='OCR text nodes plus vector reconstruction of measured rules and curves',
       label_review='not individually proofread',raster_images_embedded=0)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--ocr',required=True)
    ap.add_argument('--regions',required=True);ap.add_argument('--manual',required=True);ap.add_argument('--out',required=True)
    args=ap.parse_args();out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    regions=json.loads(Path(args.regions).read_text());manual=json.loads(Path(args.manual).read_text())
    replaced={m.get('replacement_for') for m in manual if m.get('replacement_for')}
    regions=[r for r in regions if r['id'] not in replaced and not r.get('replacement_id')]
    doc=fitz.open(args.source);cache={};records=[];pending=[]
    # Thumbnail estimates can be displaced; table frames give measured bounds.
    candidate_path=Path(args.regions).parent/'figure_candidates.json'
    candidates=json.loads(candidate_path.read_text()) if candidate_path.exists() else []
    for rec in regions:
        rec['estimated_bbox_native']=rec['bbox_native'][:]
        if rec.get('category')!='表格':continue
        w=rec['image_width'];h=rec['image_height'];b=rec['bbox_native'];cy=(b[1]+b[3])/2
        pool=[c for c in candidates if c['pdf_page']==rec['pdf_page'] and
              c['bbox_native'][2]-c['bbox_native'][0]>.42*w and c['vertical_pixels']>35]
        if pool:
            def score(c):
                q=c['bbox_native'];mid=(q[1]+q[3])/2
                overlap=max(0,min(q[3],b[3])-max(q[1],b[1]))
                return abs(mid-cy)-.6*overlap
            best=min(pool,key=score);bb=best['bbox_native']
            if abs((bb[1]+bb[3])/2-cy)<.24*h:
                rec['bbox_native']=bb[:]
                rec['bbox_normalized']=[bb[0]/w,bb[1]/h,bb[2]/w,bb[3]/h]
                rec['bounds_refinement']='matched to measured table/panel frame'
    # Merge regions whose OCR text would otherwise be included twice.
    merged=[]
    for rec in regions:
        rec['source_region_ids']=[rec['id']]
        other=next((m for m in merged if m['pdf_page']==rec['pdf_page'] and
              max(contained_fraction(m['bbox_native'],rec['bbox_native']),contained_fraction(rec['bbox_native'],m['bbox_native']))>.35),None)
        if other:
            aa=other['bbox_native'];bb=rec['bbox_native'];bb=[min(aa[0],bb[0]),min(aa[1],bb[1]),max(aa[2],bb[2]),max(aa[3],bb[3])]
            other['bbox_native']=bb;w=other['image_width'];h=other['image_height']
            other['bbox_normalized']=[bb[0]/w,bb[1]/h,bb[2]/w,bb[3]/h]
            other['source_region_ids']+=rec['source_region_ids']
        else:merged.append(rec)
    regions=merged
    for rec in regions:
        no=rec['pdf_page'];p=Path(args.ocr)/f'p{no:03d}.json'
        if not p.exists():pending.append(rec['id']);continue
        if any(m['pdf_page']==no and contained_fraction(rec['bbox_native'],m['bbox_native'])>.7 for m in manual):continue
        data=json.loads(p.read_text());rgb=cache.get(no)
        if rgb is None:rgb=read_image(doc,no);cache={no:rgb}
        # Use normalized bounds because scan image heights vary by a few pixels.
        h,w=rgb.shape[:2];bn=rec['bbox_normalized'];box=[bn[0]*w,bn[1]*h,bn[2]*w,bn[3]*h]
        record=reconstruction(rgb,data['lines'],box,out/(rec['id']+'.tex'),rec)
        records.append(record)
    (out/'manifest.json').write_text(json.dumps({'figures':records,'pending_missing_ocr':pending},ensure_ascii=False,indent=2))
    print(json.dumps({'reconstructed':len(records),'pending':len(pending),'ocr_nodes':sum(x['node_count'] for x in records),'paths':sum(x['vector_path_count'] for x in records)},ensure_ascii=False))
if __name__=='__main__':main()
