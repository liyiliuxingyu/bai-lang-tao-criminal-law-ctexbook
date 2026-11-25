#!/usr/bin/env python3
"""Compile the editable books with a local, reproducible XeLaTeX format.

Requires an installed XeTeX/LaTeX base distribution. Bundled Chinese packages
and fonts are preferred; no administrator access or global TeX changes occur.
"""
from pathlib import Path
import os,subprocess,sys,json,shutil

root=Path(__file__).resolve().parents[1]
tex=root/'tex';output=root/'output';output.mkdir(exist_ok=True)
env=dict(os.environ)
local=root/'texmf'
if not local.exists():local=root.parent/'texdeps/texmf'
cache=root/'build';cache.mkdir(exist_ok=True)
for binary in ['xelatex','xetex','kpsewhich']:
    if not shutil.which(binary):
        raise SystemExit('Missing '+binary+'. Install TeX Live with XeTeX, LaTeX, TikZ and recommended/extra LaTeX packages; see README.txt.')
if local.exists():
    dist=subprocess.check_output(['kpsewhich','-var-value=TEXMFDIST'],text=True).strip()
    roots=[str(local),dist]
    if Path('/usr/share/texmf').exists():roots.append('/usr/share/texmf')
    env['TEXMF']='{'+','.join(roots)+'}'
    env['TEXMFVAR']=str(cache/'texvar');env['TEXMFCONFIG']=str(cache/'texconfig')
    # Formats are engine-specific. Build from source instead of shipping a binary
    # cache compiled on a different TeX Live version or architecture.
    fmt=cache/'formats';fmt.mkdir(exist_ok=True)
    env['TEXFORMATS']=str(fmt)+'//:'
    version=subprocess.check_output(['xetex','--version'],text=True).splitlines()[0]
    stamp=fmt/'engine_version.txt'
    if not (fmt/'xelatex.fmt').exists() or not stamp.exists() or stamp.read_text()!=version:
        # The books use Chinese and English only. A full distribution's generated
        # language.dat can refer to unrelated hyphenation packages not installed
        # on a minimal host, so use a local build configuration.
        (fmt/'language.dat').write_text('english hyphen.tex\n=usenglish\n=american\nnohyphenation zerohyph.tex\n')
        command=['xetex','-ini','-interaction=nonstopmode','-halt-on-error',
                 '-jobname=xelatex','-progname=xelatex','*xelatex.ini']
        initialized=subprocess.run(command,cwd=fmt,env=env,capture_output=True,text=True)
        (cache/'format_build.txt').write_text(initialized.stdout+'\n'+initialized.stderr)
        if initialized.returncode:
            print(initialized.stdout[-6000:]);print(initialized.stderr[-1000:])
            raise SystemExit('Local XeLaTeX format creation failed. See build/format_build.txt.')
        stamp.write_text(version)
names=sys.argv[1:] or ['retypeset','mathematical']
report=[]
for name in names:
    if not name.replace('_','').isalnum() or not (tex/(name+'.tex')).is_file():
        raise SystemExit('Unknown TeX entry: '+name)
    passes=int(env.get('TEX_BUILD_PASSES','3'))
    for run in range(passes):
        cmd=['xelatex','-interaction=nonstopmode','-halt-on-error','-file-line-error',
             '-output-directory='+str(output),name+'.tex']
        res=subprocess.run(cmd,cwd=tex,env=env,capture_output=True,text=True)
        (output/(name+f'.pass{run+1}.txt')).write_text(res.stdout+'\n'+res.stderr)
        if res.returncode:
            print(res.stdout[-7000:]);print(res.stderr[-2000:]);sys.exit(res.returncode)
    log=(output/(name+'.log')).read_text(errors='replace')
    row={'name':name,'compiled':True,'runs':passes,'overfull_hbox':log.count('Overfull \\hbox'),
         'overfull_vbox':log.count('Overfull \\vbox'),'missing_characters':log.count('Missing character:'),
         'undefined_references':len(__import__('re').findall(r'LaTeX Warning: (?:Reference|Citation).*undefined',log))}
    report.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
audit=root/'audit';audit.mkdir(exist_ok=True)
for row in report:(audit/(row['name']+'_compile_status.json')).write_text(json.dumps(row,ensure_ascii=False,indent=2))
(audit/'compile_status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
