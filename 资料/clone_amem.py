import json,subprocess
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1];P=next(ROOT.glob('A-MEM*'));versions={}
for name in ['A-mem','A-mem-sys']:
    response=requests.get('https://api.github.com/repos/WujiangXu/'+name+'/commits',params={'until':'2025-10-09T00:00:00Z','per_page':1},timeout=45);response.raise_for_status();item=response.json()[0];versions[name]=item
    repo=P/'代码'/(name+'-historical')
    if not repo.exists():subprocess.run(['git','clone','--filter=blob:none','--no-checkout','https://github.com/WujiangXu/'+name+'.git',str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'checkout','--detach',item['sha']],check=True)
    print(name,item['sha'],item['commit']['committer']['date'])
(P/'资料'/'代码版本.json').write_text(json.dumps(versions,ensure_ascii=False,indent=2),encoding='utf-8')
