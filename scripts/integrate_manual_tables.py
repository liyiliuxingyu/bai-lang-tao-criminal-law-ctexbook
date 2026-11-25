#!/usr/bin/env python3
"""Merge reviewed table replacements into the manual figure register.

All metadata paths are explicit. This does not infer that unreviewed drawings
are reviewed, and refuses duplicated replacement identifiers.
"""
from pathlib import Path
import argparse,json,shutil

ap=argparse.ArgumentParser()
ap.add_argument('--figures',required=True)
ap.add_argument('--table-dir',action='append',required=True)
args=ap.parse_args()
directory=Path(args.figures)
manual=json.loads((directory/'manual_figures.json').read_text())
curated=json.loads((directory/'curated_regions.json').read_text())
byid={r['id']:r for r in curated}
tables=[]
for name in args.table_dir:
    folder=Path(name);data=json.loads((folder/'metadata.json').read_text())
    rows=data['tables'] if isinstance(data,dict) else data
    for row in rows:
        replaced=row.get('replacement_for',row['id'])
        record=dict(row)
        record['replacement_for']=replaced
        record['id']=row.get('replacement_id','manual_table_'+replaced)
        record['source_type']='table'
        record['title']=row.get('title',byid.get(replaced,{}).get('title','原书表格 '+replaced))
        record['transcription_review']=row.get('source_review',row.get('transcription_review','See table audit metadata'))
        record['layout_review']=row.get('visual_review',row.get('layout_review','See table audit metadata'))
        source=folder/row['tex_file']
        if not source.is_file():raise ValueError('Missing table TeX: '+str(source))
        shutil.copy2(source,directory/row['tex_file'])
        tables.append(record)
replacements=[r['replacement_for'] for r in tables]
if len(replacements)!=len(set(replacements)):raise ValueError('Duplicated table replacement identifiers')
manual=[r for r in manual if r.get('replacement_for') not in set(replacements)]
manual.extend(tables)
for row in tables:
    if row['replacement_for'] not in byid:raise ValueError('Unknown curated table '+row['replacement_for'])
    byid[row['replacement_for']]['replacement_id']=row['id']
manual.sort(key=lambda r:(r['pdf_page'],r['bbox_native'][1],r['id']))
(directory/'manual_figures.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2)+'\n')
(directory/'curated_regions.json').write_text(json.dumps(curated,ensure_ascii=False,indent=2)+'\n')
(directory/'table_reconstruction_audit.json').write_text(json.dumps({'tables':tables,'count':len(tables)},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'manual_figures':len(manual),'manual_tables':len(tables),'manual_non_tables':len(manual)-len(tables)},ensure_ascii=False))
