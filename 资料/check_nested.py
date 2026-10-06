from pathlib import Path
import json,hashlib,re,ast,importlib.util
import torch
p=next(p for p in Path('.').iterdir() if p.name.startswith('Nested'))
out=p/'复现/outputs';r=json.loads((out/'demo_results.json').read_text(encoding='utf8'))
meta=json.loads((p/'资料/论文元数据.json').read_text(encoding='utf8'))
assert hashlib.sha256((p/'原论文.pdf').read_bytes()).hexdigest()==meta['sha256']
assert len(r['runs'])==5
for run in r['runs']:
 for name,q in run['models'].items():
  periods=r['config']['periods'][name]
  assert len(q['change_log'])==640 and len(q['trace_before_write'])==640
  assert q['parameter_updates_per_block']==[640//c for c in periods]
  for j,c in enumerate(periods):
   actual=sum(z[j] for z in q['change_log'])
   assert actual==640//c,(name,j,actual)
   assert all(not z[j] for i,z in enumerate(q['change_log'],1) if i%c!=0)
  for point in ['128','384','640']:
   for metric in q['snapshots_after_write'][point]:
    mean=sum(s['models'][name]['snapshots_after_write'][point][metric] for s in r['runs'])/5
    assert abs(mean-r['summary'][name]['after_step_'+point][metric])<1e-12
spec=importlib.util.spec_from_file_location('cms_demo',p/'复现/scripts/demo_cms.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
torch.set_num_threads(1)
ck=torch.load(out/'toy_cms_checkpoint.pt',weights_only=True)
a=torch.eye(8);b=a.clone();b[4:]=a[torch.tensor([5,6,7,4])]
reload_checks={}
for name,state in ck['states'].items():
 model=module.CMS();model.load_state_dict(state)
 actual=module.evaluate(model,a,a,b,a)
 expected=r['runs'][0]['models'][name]['snapshots_after_write']['640']
 diff=max(abs(actual[k]-expected[k]) for k in actual)
 assert diff<1e-7,(name,diff)
 reload_checks[name]=diff
files=['原论文.pdf','解释.md','代码/资源说明.md','资料/来源核查.json','复现/README.md','复现/requirements.txt','复现/scripts/demo_cms.py','复现/scripts/plot_demo.py','复现/outputs/demo_results.json','复现/outputs/toy_cms_checkpoint.pt','复现/outputs/demo_summary.png','复现/outputs/demo_summary.svg']
artifacts=[]
for name in files:
 f=p/name;assert f.is_file() and f.stat().st_size>0,name
 artifacts.append({'path':name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 if f.suffix=='.py':ast.parse(f.read_text(encoding='utf8'))
links=0
for name in ['解释.md','复现/README.md']:
 f=p/name;text=f.read_text(encoding='utf8');assert '\x00' not in text
 for ref in re.findall(r'\]\(([^)]+)\)',text):
  if not ref.startswith(('https:','http:','#')):
   target=f.parent/ref.strip('<>')
   if target.name!='delivery_check.json':assert target.exists(),ref
   links+=1
result={'status':'pass','scope':'CMS mechanism only','artifacts':artifacts,'local_links_checked':links,'checkpoint_metric_max_errors':reload_checks,'trajectory_checks':'all 5 seeds, 3 modes, 640 steps: counts, holds and summary means'}
(out/'delivery_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('PASS:',len(artifacts),'artifacts,',links,'links, 9600 update records, summary and checkpoint predictions')
print('Checkpoint prediction differences:',reload_checks)
