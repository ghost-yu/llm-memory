import requests,json
from pathlib import Path
p=next(p for p in Path('.').iterdir() if 'All Connected' in p.name)
urls=['https://arxiv.org/abs/2504.13173','https://api.github.com/search/repositories?q=MIRAS+Moneta','https://api.github.com/search/repositories?q=2504.13173','https://abehrouz.github.io/']
r=[]
for u in urls:
 try:
  x=requests.get(u,timeout=30); r.append({'url':u,'status':x.status_code,'body':x.text[:100000]}); print(u,x.status_code); print(x.text[:160] if 'api.github' in u else '')
 except Exception as e: r.append({'url':u,'error':str(e)}); print(str(e))
(p/'资料'/'来源核查.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8')
