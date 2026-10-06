import pathlib,json,requests,subprocess,fitz,hashlib
p=pathlib.Path(__file__).resolve().parents[2]
doc=fitz.open(str(p/'原论文.pdf'))
(p/'资料/全文.txt').write_text('\n'.join('=== PAGE %s ===\n%s'%(i+1,page.get_text()) for i,page in enumerate(doc)),encoding='utf-8')
(p/'图片').mkdir(exist_ok=True)
for i in [0,1,2,3,4,5,6,7]:
 doc[i].get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(str(p/('图片/page_%02d.png'%(i+1))))
r=requests.get('https://api.github.com/repos/xiaowu0162/LongMemEval/commits',params={'until':'2025-03-05T00:00:00Z','per_page':1},timeout=60);r.raise_for_status();c=r.json()[0]; sha=c['sha']
repo=p/'代码/LongMemEval-historical';repo.parent.mkdir(exist_ok=True)
if not repo.exists(): subprocess.check_call(['git','clone','https://github.com/xiaowu0162/LongMemEval.git',str(repo)])
subprocess.check_call(['git','-C',str(repo),'checkout',sha])
(p/'资料/代码版本.json').write_text(json.dumps({'repo':'https://github.com/xiaowu0162/LongMemEval','sha':sha,'date':c['commit']['committer']['date']},ensure_ascii=False,indent=2),encoding='utf-8')
print(sha,c['commit']['committer']['date'])
print((repo/'README.md').read_text(encoding='utf-8'))
