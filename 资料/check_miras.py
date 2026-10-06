from pathlib import Path
import ast,re,json,hashlib
p=next(p for p in Path('.').iterdir() if 'All Connected' in p.name)
files=['原论文.pdf','解释.md','代码/资源说明.md','资料/来源核查.json','复现/README.md','复现/requirements.txt','复现/scripts/demo_miras.py','复现/scripts/plot_demo.py','复现/outputs/demo_results.json','复现/outputs/demo_summary.png','复现/outputs/demo_summary.svg']
a=[]
for name in files:
 f=p/name; assert f.is_file() and f.stat().st_size>0,name
 a.append({'path':name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 if f.suffix=='.py': ast.parse(f.read_text(encoding='utf8'))
links=0
for name in ['解释.md','复现/README.md']:
 f=p/name; text=f.read_text(encoding='utf8'); assert '\x00' not in text
 for ref in re.findall(r'\]\(([^)]+)\)',text):
  if not ref.startswith(('https:','http:','#')):
   assert (f.parent/ref.strip('<>')).exists(),ref; links+=1
r=json.loads((p/'复现/outputs/demo_results.json').read_text(encoding='utf8'))
assert r['environment']['device']=='cpu'
assert r['experiments']['contaminated']['metrics']['huber']['late_mean_mae']<.03
result={'artifacts':a,'local_links_checked':links,'status':'pass','scope':'mechanism reproduction only'}
(p/'复现/outputs/delivery_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('PASS:',len(a),'artifacts,',links,'local links, Python syntax and measured metrics')
