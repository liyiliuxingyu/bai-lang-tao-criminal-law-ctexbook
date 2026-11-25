#!/usr/bin/env python3
"""Regenerate the transcription from the retained OCR data, then compile.

This intentionally replaces generated chapter and automatic-figure TeX files.
For normal editing, run compile.py instead; it preserves edited TeX.
"""
from pathlib import Path
import subprocess,sys,json
root=Path(__file__).resolve().parents[1]
source=root/'source/original.pdf';data=root/'data'
required=[source,data/'ocr/clean/p434.json',data/'figures/manual_figures.json',data/'figures/curated_regions.json']
missing=[str(p) for p in required if not p.exists()]
if missing:raise SystemExit('Missing required inputs: '+', '.join(missing))
manual=json.loads((data/'figures/manual_figures.json').read_text())
curated=json.loads((data/'figures/curated_regions.json').read_text())
replaced={row.get('replacement_for') for row in manual}
remaining=[row for row in curated if row['id'] not in replaced and not row.get('replacement_id')]
commands=[]
if remaining:
 commands.append([sys.executable,str(root/'scripts/rebuild_figures.py'),'--source',str(source),
  '--ocr',str(data/'ocr/clean'),'--regions',str(data/'figures/curated_regions.json'),
  '--manual',str(data/'figures/manual_figures.json'),'--out',str(root/'tex/auto_figures')])
else:
 out=root/'tex/auto_figures';out.mkdir(exist_ok=True)
 (out/'manifest.json').write_text(json.dumps({'figures':[],'pending_missing_ocr':[],
   'note':'Every identified region has a manually reviewed editable TikZ replacement.'},ensure_ascii=False,indent=2)+'\n')
commands.extend([
 [sys.executable,str(root/'scripts/build_retypeset.py'),'--work',str(data),'--project',str(root)],
 [sys.executable,str(root/'scripts/compile.py')]
])
for cmd in commands:subprocess.run(cmd,cwd=root,check=True)
