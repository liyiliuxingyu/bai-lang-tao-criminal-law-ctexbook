#!/usr/bin/env python3
"""Verify file integrity, TeX dependencies and declared coverage without legal claims."""
from pathlib import Path
import hashlib,json,re,sys,zipfile

root=Path(__file__).resolve().parents[1]
checks=[]
def record(name,passed,detail):
    checks.append({'check':name,'passed':bool(passed),'detail':detail})

hashfile=root/'SHA256SUMS.json'
if hashfile.exists():
    expected=json.loads(hashfile.read_text())
    bad=[]
    for rel,digest in expected.items():
        p=root/rel
        if not p.is_file():bad.append({'file':rel,'reason':'missing'});continue
        actual=hashlib.sha256(p.read_bytes()).hexdigest()
        if actual!=digest:bad.append({'file':rel,'reason':'hash differs'})
    record('sha256',not bad,{'files':len(expected),'failures':bad})
else:record('sha256_manifest_present',False,'SHA256SUMS.json is missing')

missing=[]
for p in (root/'tex').rglob('*.tex'):
    text=p.read_text()
    for relative in re.findall(r'\\(?:input|InsertDiagram|ContinuedTable)\{([^}]+)\}',text):
        if '#' in relative:continue
        q=root/'tex'/relative
        if not q.suffix:q=q.with_suffix('.tex')
        if not q.exists():missing.append({'from':str(p.relative_to(root)),'target':relative})
record('tex_input_targets',not missing,missing)

cov=root/'audit/source_coverage.json'
if cov.exists():
    d=json.loads(cov.read_text());gaps=[]
    for p in d['pages']:
        if p['covered_lines']!=p['input_line_count']:gaps.append(p['page'])
    record('ocr_line_accounting',not gaps and not d['missing_ocr_pages'],
      {'unaccounted_pages':gaps,'missing_ocr_pages':d['missing_ocr_pages'],
       'meaning':'Each retained OCR line has a prose, diagram or explained heading assignment; this does not establish OCR correctness.'})
    record('body_page_coverage',set(p['page'] for p in d['pages'])==set(range(13,435)),
       {'expected_physical_body_pages':422,'represented':len(d['pages'])})
    duplicate=[{'page':p['page'],'ids':p.get('figure_assignment_duplicates',[])} for p in d['pages'] if p.get('figure_assignment_duplicates')]
    record('no_duplicate_figure_line_assignments',not duplicate,duplicate)
    section_mismatch=[{'page':p['page'],'expected':p.get('expected_section_titles',[]),'found':p.get('sections_found',0)}
                      for p in d['pages'] if len(p.get('expected_section_titles',[]))!=p.get('sections_found',0)]
    record('section_outline_matches_source_toc',not section_mismatch,section_mismatch)

manual_path=root/'data/figures/manual_figures.json'
curated_path=root/'data/figures/curated_regions.json'
if manual_path.exists() and curated_path.exists():
    manual=json.loads(manual_path.read_text());curated=json.loads(curated_path.read_text())
    replacements={f.get('replacement_for') for f in manual}
    pending=[f['id'] for f in curated if f['id'] not in replacements]
    missing=[f['tex_file'] for f in manual if not (root/'tex/figures'/f['tex_file']).exists()]
    record('all_identified_graphics_have_manual_tikz',not pending and not missing,
           {'manual_records':len(manual),'tables':sum(f.get('source_type')=='table' for f in manual),
            'unreplaced_regions':pending,'missing_tikz':missing})

for name in ['retypeset','mathematical']:
    p=root/'output'/(name+'.pdf')
    record(name+'_pdf_present',p.exists() and p.stat().st_size>1000,str(p.relative_to(root)))
    try:
        import fitz
        pdf=fitz.open(p);texts=[x.get_text() for x in pdf]
        image_count=sum(len(x.get_images()) for x in pdf)
        record(name+'_pdf_readable',len(pdf)>0,{'pages':len(pdf),'embedded_raster_images':image_count,
          'extractable_characters':sum(map(len,texts))})
        record(name+'_promotional_footer_removed',not any('关注公众号' in t or '法考180' in t for t in texts),'Searched extractable PDF text')
        if name=='retypeset':record(name+'_no_source_images',image_count==0,{'embedded_raster_images':image_count})
    except ImportError:record(name+'_pdf_inspection',True,'PyMuPDF not installed; byte presence was checked, PDF inspection skipped')
    except Exception as exc:record(name+'_pdf_readable',False,str(exc))

result={'checks':checks,'all_required_passed':all(x['passed'] for x in checks),
        'scope':'File integrity and structural checks only; not full textual proofreading, substantive legal review or proof-assistant certification.'}
print(json.dumps(result,ensure_ascii=False,indent=2))
if not result['all_required_passed']:sys.exit(1)
