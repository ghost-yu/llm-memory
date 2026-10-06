from pathlib import Path
import fitz,requests,json
from bs4 import BeautifulSoup
p=next(p for p in Path('.').iterdir() if p.name.startswith('Nested'))
d=fitz.open(str(p/'原论文.pdf')); (p/'图片').mkdir(exist_ok=True)
for n in [8,9,15,18,23,26,27,28,29,30,31,32,33,34,35,36,37,38,40,41]:
 d[n-1].get_pixmap(matrix=fitz.Matrix(1.4,1.4)).save(str(p/'图片'/('page-'+str(n)+'.png')))
r=[]
for u in ['https://arxiv.org/abs/2512.24695','https://abehrouz.github.io/','https://research.google/blog/introducing-nested-learning-a-new-ml-paradigm-for-continual-learning/','https://api.github.com/search/repositories?q=2512.24695','https://api.github.com/search/repositories?q=Nested+Learning+HOPE']:
 try:
  x=requests.get(u,timeout=25); item={'url':u,'status':x.status_code,'body':x.text};r.append(item)
  soup=BeautifulSoup(x.text,'html.parser')
  print(u,x.status_code)
  if 'api.github' in u:
   print([(a['full_name'],a.get('description')) for a in x.json().get('items',[])][:12])
  else:
   print([(a.get_text(' ',strip=True),a.get('href')) for a in soup.find_all('a') if any(s in (a.get('href','')).lower() for s in ['github','2512.24695','nested','nl.pdf'])][:15])
 except Exception as e: r.append({'url':u,'error':str(e)});print(str(e))
(p/'资料'/'来源核查.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
