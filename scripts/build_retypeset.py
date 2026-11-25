#!/usr/bin/env python3
"""Generate an editable ctexbook transcription from source OCR and figure manifests.

The output is explicitly marked as a proofreading draft. All included source
lines are accounted for in a per-page manifest; exclusions are enumerated.
"""
from pathlib import Path
import json, re, argparse, shutil, statistics
from collections import defaultdict
from tex_support import escape,weighted_spans,character_spans
from edition_notes import apply_footnotes
from edition_text import apply_text
from edition_terms import apply_terms
from edition_panels import apply_panels

CN='一二三四五六七八九十百零〇两'
MANUAL_CORRECTIONS={15:{'“户体”':'“尸体”'},6:{'自已':'自己'}}

def inside(line,box):
    a,b,c,d=line['bbox'];x0,y0,x1,y1=box
    return x0-2<=(a+c)/2<=x1+2 and y0-2<=(b+d)/2<=y1+2

def make_page(no, data, figures, underlines, first=False, chapter=None, expected_sections=None):
    lines=[dict(x) for x in data['lines']]
    for l in lines:
        for a,b in MANUAL_CORRECTIONS.get(no,{}).items():l['text']=l['text'].replace(a,b)
    heights=[x['bbox'][3]-x['bbox'][1] for x in lines if len(x['text'])>15]
    median=statistics.median(heights) if heights else 21
    waveby=defaultdict(list);charby=defaultdict(list)
    for w in underlines.get('wave_candidates',[]):
        match=w.get('ocr_match')
        if match and match.get('line_id') is not None:
            x,y,ww,hh=w['bbox_xywh'];waveby[match['line_id']].append((x,x+ww))
            charby[match['line_id']].append((match['char_start'],match['char_end_exclusive']))
    included=[];excluded=[];graphic_lines=[];events=[]
    # Some scanned page numbers sit a few pixels above the original OCR cleanup
    # threshold. Require both the known printed-page value and its footer corner.
    retained=[]
    for l in lines:
        a,b,c,d=l['bbox'];s=l['text'].strip()
        is_page_number=(no>=13 and s==str(no-10) and b>data['image_height']*.925 and
                        (c<data['image_width']*.16 or a>data['image_width']*.84))
        if is_page_number:
            excluded.append({'id':l['id'],'reason':'original printed page number at footer corner','text':l['text']})
        else:retained.append(l)
    lines=retained
    if first:
        idx=next((i for i,l in enumerate(lines) if '特别提示' in l['text'] or '特别提醒' in l['text']),None)
        if idx is not None:
            for l in lines[:idx]:excluded.append({'id':l['id'],'reason':'chapter title replaced by LaTeX chapter heading','text':l['text']})
            lines=lines[idx:]
        else:
            original=lines
            lines=[l for l in lines if l['bbox'][1]>data['image_height']*.235]
            excluded.extend({'id':l['id'],'reason':'chapter title block replaced','text':l['text']} for l in original if l not in lines)
    for f in figures:
        ids=[]
        for l in lines:
            # For manually transcribed tables the reviewed line list is more
            # precise than geometry, especially where OCR merges two cells.
            if 'text_line_ids' in f:
                selected=l['id'] in f['text_line_ids']
            else:selected=inside(l,f['bbox_native'])
            if selected and l['id'] not in f.get('release_line_ids',[]):ids.append(l['id'])
        graphic_lines.extend(ids)
        # Source-space geometry is only used to preserve ordering, never printed as a page label.
        events.append((f['bbox_native'][1],-1,{'figure':f,'ids':ids}))
    for l in lines:
        if l['id'] in graphic_lines:continue
        events.append((l['bbox'][1],l['id'],{'line':l}))
    events.sort(key=lambda e:(e[0],e[1]))
    lefts=[l['bbox'][0] for l in lines if len(l['text'])>24]
    left=sorted(lefts)[max(0,len(lefts)//5)] if lefts else 100
    right=max([l['bbox'][2] for l in lines if len(l['text'])>20] or [data['image_width']*.91])
    out=[f'% Source PDF physical page {no}; see audit/source_coverage.json.']
    para=[];last=None;foot=False;foottext=[]
    def flush():
        nonlocal para
        if para:out.append(''.join(para)+'\n');para=[]
    def footflush():
        nonlocal foottext
        if foottext:out.append(r'\SourceFootnote{'+''.join(foottext)+'}\n');foottext=[]
    k=0;sections_seen=0
    while k<len(events):
        y,_,ev=events[k];k+=1
        if 'figure' in ev:
            flush();footflush();f=ev['figure']
            folder='figures' if f.get('manual') else 'auto_figures'
            out.append(r'\InsertDiagram{'+folder+'/'+f['tex_file']+'}\n')
            last=None;continue
        l=ev['line'];text=l['text'].strip();included.append(l['id'])
        x0,y0,x1,y1=l['bbox']
        verified_long_heading=False
        # Source p331 has a single two-line offence heading. Its second OCR
        # row starts inside the word 制造; retain the whole title as one heading.
        if no==331 and l['id']==22 and text.endswith('非法制') and k<len(events) and 'line' in events[k][2]:
            continuation=events[k][2]['line']
            if continuation['id']==23 and continuation['text'].startswith('造、买卖、运输、储存危险物质罪'):
                text+=continuation['text'];included.append(continuation['id']);k+=1
                verified_long_heading=True
        # Recombine section numbers separated from their titles by OCR.
        if re.fullmatch(r'第['+CN+r']+节',text) and k<len(events) and 'line' in events[k][2]:
            nxt=events[k][2]['line']
            if abs(nxt['bbox'][1]-y0)<70 and len(nxt['text'])<48:
                text+=nxt['text'];included.append(nxt['id']);k+=1
        section=re.match(r'^第['+CN+r']+节\s*(.*)',text)
        if section:
            # Ornamental separators can be misread as "开" and split title rows.
            while k<len(events) and 'line' in events[k][2]:
                nxt=events[k][2]['line'];nb=nxt['bbox']
                if abs((nb[1]+nb[3]-y0-y1)/2)<max(12,(y1-y0)*.7) and nb[0]>x0:
                    included.append(nxt['id']);k+=1
                else:break
            if expected_sections and sections_seen<len(expected_sections):
                title=expected_sections[sections_seen]
            else:title=section.group(1)
            sections_seen+=1
        smallhead=verified_long_heading or (len(text)<45 and re.match(r'^['+CN+r']+[、．]\s*\S',text))
        subhead=(len(text)<45 and re.match(r'^[（(]['+CN+r']+[）)]',text))
        panel=text in ['特别提示','特别提醒','真题演练','典型真题','本讲小结']
        note_start=bool(re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]',text))
        if note_start and y0>data['image_height']*.67 and y1-y0<median*.88:
            flush();foot=True
        tex=character_spans(text,charby[l['id']]) if charby[l['id']] else escape(text)
        if foot:
            foottext.append(tex);last=l;continue
        if section:
            flush();out.append(r'\section{'+escape(title)+'}\n');last=None;continue
        if smallhead:
            flush();out.append(r'\subsection*{'+tex+'}\n');last=None;continue
        if subhead:
            flush();out.append(r'\subsubsection*{'+tex+'}\n');last=None;continue
        if panel:
            flush();out.append(r'\OriginalPanel{'+tex+'}\n');last=None;continue
        startlist=bool(re.match(r'^(?:\d+[.．、]|[（(]\d+[）)]|\[|【|题\d+|例\d*)',text))
        if last:
            gap=y0-last['bbox'][3]
            indented=x0>left+median*.9
            shortprev=last['bbox'][2]<right-median*3.5
            terminated=last['text'].endswith(('。','！','？','：','；','”','）'))
            if startlist or (indented and gap>median*.08) or (shortprev and terminated) or gap>median*1.3:
                flush()
        if startlist and para:flush()
        para.append(tex);last=l
    flush();footflush()
    return '\n'.join(out),{'page':no,'input_line_count':len(data['lines']),
        'prose_ids':sorted(set(included)),'figure_ids':sorted(set(graphic_lines)),
        'excluded':excluded,'covered_lines':len(set(included)|set(graphic_lines)|{x['id'] for x in excluded}),
        'machine_underline_segments':sum(len(x) for x in waveby.values()),
        'figure_assignment_duplicates':sorted({i for i in graphic_lines if graphic_lines.count(i)>1}),
        'expected_section_titles':expected_sections or [],'sections_found':sections_seen,
        'manually_proofread_full_page':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--project',required=True)
    p.add_argument('--max-page',type=int,default=434)
    a=p.parse_args();work=Path(a.work);project=Path(a.project);td=project/'tex'
    manual=json.loads((work/'figures/manual_figures.json').read_text())
    for f in manual:
        f['manual']=True
        figure_source=work/'figures'/f['tex_file']
        if not figure_source.exists():figure_source=td/'figures'/f['tex_file']
        figure_text=figure_source.read_text()
        figure_text=figure_text.replace(r'\begin{center}','').replace(r'\end{center}','')
        (td/'figures'/f['tex_file']).write_text(figure_text)
    auto_path=td/'auto_figures/manifest.json'
    auto=json.loads(auto_path.read_text())['figures'] if auto_path.exists() else []
    bypage=defaultdict(list)
    for f in manual+auto:
        if f['pdf_page']>=13:bypage[f['pdf_page']].append(f)
    outline=json.loads((work/'ocr/chapter_outline.json').read_text())
    sections=defaultdict(list)
    toc='\n'.join((work/'ocr/clean'/f'p{n:03d}.txt').read_text() for n in range(7,11))
    for m in re.finditer(r'第['+CN+r']+节\s*([^/／]+?)[/／]\s*(\d+)',toc):
        title=re.sub(r'\s+','',m.group(1)).rstrip('J')
        if len(title)<70:
            title=title.replace('介人因素','介入因素').replace('翰旋受贿','斡旋受贿')
            sections[int(m.group(2))+10].append(title)
    (project/'audit/section_outline.json').write_text(json.dumps(sections,ensure_ascii=False,indent=2))
    audit=[];includes=[];missing=[]
    for ch in outline:
        if ch['pdf_start']>a.max_page:break
        parts=[r'\chapter{'+escape(ch['title'])+'}\n']
        for no in range(ch['pdf_start'],min(ch['pdf_end'],a.max_page)+1):
            src=work/'ocr/clean'/f'p{no:03d}.json'
            if not src.exists():missing.append(no);continue
            data=json.loads(src.read_text());up=work/'ocr/underlines'/f'p{no:03d}.json'
            us=json.loads(up.read_text()) if up.exists() else {}
            content,record=make_page(no,data,bypage[no],us,no==ch['pdf_start'],ch,sections.get(no))
            audit.append(record);parts.append(content)
        fname=f'chapter{ch["chapter"]:02d}.tex'
        chapter_tex = apply_footnotes('\n'.join(parts))
        (td/'chapters'/fname).write_text(apply_terms(apply_text(chapter_tex)),encoding='utf-8')
        includes.append(r'\input{chapters/'+fname+'}')
    apply_panels(project, (ch['chapter'] for ch in outline if ch['pdf_start'] <= a.max_page))
    # The source bibliography is content and is retained.
    if a.max_page>=434 and (work/'ocr/clean/p434.json').exists():
        data=json.loads((work/'ocr/clean/p434.json').read_text())
        lines=[x for x in data['lines'] if x['text']!='参考文献']
        data['lines']=lines
        underline_file=work/'ocr/underlines/p434.json'
        reference_underlines=json.loads(underline_file.read_text()) if underline_file.exists() else {}
        txt,rec=make_page(434,data,[],reference_underlines)
        (td/'chapters/references.tex').write_text(r'\chapter*{参考文献}\addcontentsline{toc}{chapter}{参考文献}'+'\n'+txt)
        includes.append(r'\input{chapters/references.tex}');audit.append(rec)
    main=r'''\documentclass[UTF8,fontset=fandol,openany]{ctexbook}
\input{common.tex}
\input{edition_tables.tex}
\input{edition_panels.tex}
\renewcommand{\BookEditionDate}{2026 年 11 月 25 日}
\hypersetup{pdftitle={刑法：原文重排校对稿},pdfauthor={原著：柏浪涛；重排整理}}
\begin{document}
\BookCover{2027 年版 · 专题讲座精讲卷}{原文重排校对稿}{原著：柏浪涛}{文字识别重排与可编辑图表\quad ctexbook 默认风格\\[4pt]全书文字尚未逐字完成独立校对}
\frontmatter
\tableofcontents
\clearpage
\input{frontmatter.tex}
\mainmatter
'''+ '\n'.join(includes)+'\n'+r'\end{document}'+'\n'
    (td/'retypeset.tex').write_text(main,encoding='utf-8')
    result={'source_page_count':434,'included_body_pages':len(audit),'missing_ocr_pages':missing,
      'frontmatter_original_pages_retained':[5,6,11],
      'original_pages_omitted':[1,2,3,4,7,8,9,10,12],
      'omission_explanation':'Cover and TOC rebuilt; original cover, publishing data, preface, author intro and blank page omitted.',
      'manual_diagrams':len(manual),'automatic_diagrams':len(auto),'pages':audit}
    (project/'audit/source_coverage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'body_pages':len(audit),'missing_pages':len(missing),'chapters':len(includes),'manual_figures':len(manual),'auto_figures':len(auto),'underlines':sum(r['machine_underline_segments'] for r in audit),'unaccounted_lines':sum(r['input_line_count']-r['covered_lines'] for r in audit)},ensure_ascii=False))
if __name__=='__main__':main()
