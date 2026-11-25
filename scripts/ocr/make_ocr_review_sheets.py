#!/usr/bin/env python3
import os,json,io,argparse
from pathlib import Path
import fitz
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(os.environ.get('CRIMINAL_LAW_PROJECT_ROOT',str(Path(__file__).resolve().parents[2])))
p=argparse.ArgumentParser();p.add_argument('--start',type=int,default=13);p.add_argument('--end',type=int,default=434);p.add_argument('--prefix',default='review');a=p.parse_args()
ocr=ROOT/'data/ocr';out=ROOT/'build/qa_ocr';out.mkdir(exist_ok=True);d=fitz.open(os.environ.get('CRIMINAL_LAW_SOURCE_PDF',str(ROOT/'source/original.pdf')))
rows=[]
for file in sorted((ocr/'clean').glob('p*.json')):
 try:r=json.loads(file.read_text())
 except:continue
 if not a.start<=r['page']<=a.end:continue
 for l in r['lines']:
  if l['confidence']<.94 and len(l['text'])>=10:rows.append((r['page'],l))
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',17,index=2)
for batch in range((len(rows)+11)//12):
 subset=rows[batch*12:(batch+1)*12];sheet=Image.new('RGB',(1800,len(subset)*115),'white');draw=ImageDraw.Draw(sheet)
 for j,(n,l) in enumerate(subset):
  im=Image.open(io.BytesIO(d.extract_image(d[n-1].get_images()[0][0])['image'])).convert('RGB');x0,y0,x1,y1=l['bbox'];crop=im.crop((int(x0)-3,int(y0)-4,int(x1)+4,int(y1)+4));crop=crop.resize((crop.width*2,crop.height*2));crop.thumbnail((1700,70));sheet.paste(crop,(90,j*115+18));draw.text((2,j*115),f'{n}/{l["id"]}',fill='blue',font=font);draw.text((90,j*115+88),l['text'],fill='black',font=font)
 sheet.save(out/f'{a.prefix}_{batch+1}.png')
(out/f'{a.prefix}_manifest.json').write_text(json.dumps([{'page':n,**l} for n,l in rows],ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'rows':len(rows),'sheets':(len(rows)+11)//12,'prefix':str(out/a.prefix)}),flush=True)
