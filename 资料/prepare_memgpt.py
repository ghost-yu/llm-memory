from pathlib import Path
import requests,json,fitz
from bs4 import BeautifulSoup
p=next(p for p in Path('.').iterdir() if p.name.startswith('MemGPT'))
d=fitz.open(str(p/'原论文.pdf'));(p/'图片').mkdir(exist_ok=True)
for n in [3,4,5,6,7,10,11,12,13]:d[n-1].get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(str(p/'图片'/('page-'+str(n)+'.png')))
urls=['https://research.memgpt.ai/','https://api.github.com/repos/letta-ai/letta/commits?until=2024-02-13T00:00:00Z&per_page=1','https://api.github.com/repos/letta-ai/letta/tags?per_page=100']
r=[]
for u in urls:
 x=requests.get(u,timeout=30);r.append({'url':u,'status':x.status_code,'body':x.text})
 if 'commits?' in u and x.status_code==200:
  c=x.json()[0];print('COMMIT',c['sha'],c['commit']['committer']['date'],c['commit']['message'])
  (p/'资料'/'代码版本.json').write_text(json.dumps({'repository':'https://github.com/letta-ai/letta','ref':c['sha'],'date':c['commit']['committer']['date'],'message':c['commit']['message'],'selection':'latest available commit before 2024-02-13 UTC, near paper v2; not a proven paper release'},indent=2),encoding='utf8')
 elif 'tags?' in u:print('TAGS',[a['name'] for a in x.json()][:12])
 else:
  s=BeautifulSoup(x.text,'html.parser');print('LINKS',[(a.get_text(' ',strip=True),a.get('href')) for a in s.find_all('a') if 'github' in a.get('href','')])
(p/'资料'/'来源核查.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
