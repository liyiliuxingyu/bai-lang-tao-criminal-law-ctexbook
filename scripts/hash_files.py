#!/usr/bin/env python3
"""Write a manifest for the intended source/output files; do not include caches."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
skip={'SHA256SUMS.json','build','__pycache__'}
hashes={}
for p in sorted(root.rglob('*')):
    if not p.is_file() or any(x in skip for x in p.relative_to(root).parts):continue
    if p.suffix in {'.aux','.log','.out','.toc','.pyc','.fmt','.xdv','.synctex'}:continue
    if '.pass' in p.name:continue
    hashes[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
(root/'SHA256SUMS.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'files_hashed':len(hashes)}))
