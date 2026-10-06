import requests,pathlib,json,hashlib
p=pathlib.Path(__file__).resolve().parents[2]; d=p/'资料/数据';d.mkdir(exist_ok=True)
info=requests.get('https://huggingface.co/api/datasets/xiaowu0162/longmemeval',timeout=60).json(); revision=info['sha']
f=d/'longmemeval_s.json';url='https://huggingface.co/datasets/xiaowu0162/longmemeval/resolve/'+revision+'/longmemeval_s'
if not f.exists():
 r=requests.get(url,stream=True,timeout=120);r.raise_for_status()
 with f.open('wb') as out:
  for chunk in r.iter_content(1024*1024):out.write(chunk)
h=hashlib.sha256(f.read_bytes()).hexdigest()
assert h=='08d8dad4be43ee2049a22ff5674eb86725d0ce5ff434cde2627e5e8e7e117894'
data=json.loads(f.read_text(encoding='utf-8'))
(d/'来源.json').write_text(json.dumps({'revision':revision,'url':url,'bytes':f.stat().st_size,'sha256':h,'instances':len(data),'version':'original, not cleaned'},indent=2),encoding='utf-8')
from collections import Counter
print(len(data),Counter(x['question_type'] for x in data)); print(json.dumps({k:v for k,v in data[0].items() if k!='haystack_sessions'},ensure_ascii=False)[:5000]);print(data[0]['haystack_sessions'][0][:2])
