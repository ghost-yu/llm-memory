import json, subprocess
from pathlib import Path
import requests, fitz
ROOT=Path(__file__).resolve().parents[1]
P=next(ROOT.glob('Zep*'))
(P/'图片').mkdir(exist_ok=True);(P/'代码').mkdir(exist_ok=True)
doc=fitz.open(str(P/'原论文.pdf'))
(P/'资料'/'全文.txt').write_text('\n'.join('=== PAGE %d ===\n%s'%(i+1,p.get_text()) for i,p in enumerate(doc)),encoding='utf-8')
for i,p in enumerate(doc): p.get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(str(P/'图片'/('page-%d.png'%(i+1))))
u='https://api.github.com/repos/getzep/graphiti/commits'
r=requests.get(u,params={'until':'2025-01-21T00:00:00Z','per_page':1},timeout=45);r.raise_for_status();item=r.json()[0]
(P/'资料'/'代码版本.json').write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding='utf-8')
repo=P/'代码'/'graphiti-historical'
if not repo.exists(): subprocess.run(['git','clone','--filter=blob:none','--no-checkout','https://github.com/getzep/graphiti.git',str(repo)],check=True)
subprocess.run(['git','-C',str(repo),'checkout','--detach',item['sha']],check=True)
print(item['sha']);print(item['commit']['committer']);print('pages',len(doc))
