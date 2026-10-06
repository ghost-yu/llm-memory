from pathlib import Path
import requests,json,fitz
p=next(p for p in Path('.').iterdir() if p.name.startswith('Mem0'))
d=fitz.open(str(p/'原论文.pdf'));(p/'图片').mkdir(exist_ok=True)
for n in [3,4,5,6,7,8,9,10,11,12,15,18,22,23]:d[n-1].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(p/'图片'/('page-'+str(n)+'.png')))
r=[]
for u in ['https://api.github.com/repos/mem0ai/mem0/commits?until=2025-04-29T00:00:00Z&per_page=1','https://api.github.com/repos/mem0ai/mem0']:
 x=requests.get(u,timeout=30);r.append({'url':u,'status':x.status_code,'body':x.text})
 if 'commits?' in u:
  c=x.json()[0];print('COMMIT',c['sha'],c['commit']['committer']['date'],c['commit']['message'])
  (p/'资料'/'代码版本.json').write_text(json.dumps({'repository':'https://github.com/mem0ai/mem0','commit':c['sha'],'date':c['commit']['committer']['date'],'selection':'latest available commit before 2025-04-29 UTC; near v1, not a proven exact experiment release'},indent=2),encoding='utf8')
(p/'资料'/'来源核查.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
