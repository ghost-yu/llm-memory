import ast,hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'复现'/'outputs'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
assert len(r['checks'])==14 and all(r['checks'].values())
assert len(r['model_calls'])==6 and len(r['final'])==3
for key,repo in [('evaluation','A-mem-historical'),('system','A-mem-sys-historical')]:
    path=ROOT/'代码'/repo
    assert subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==r['commits'][key]
    assert subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True).strip()==''
for path,h in r['sources'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
for path in (ROOT/'复现'/'scripts').glob('*.py'):ast.parse(path.read_text(encoding='utf-8'))
state=json.loads((OUT/r['state_file']).read_text(encoding='utf-8'));assert state['notes']==r['final'] and state['corpus']==r['refreshed_corpus']
cache=next(x for x in r['final'] if x['id']=='cache');assert cache['context']=='cache uses LRU eviction'
assert r['system_wrong_update']['art']=='evolved_cache' and r['system_wrong_update']['cache']=='cache'
assert [x['id'] for x in r['system_search_result']]==['lru']
datafile=ROOT/'代码'/'A-mem-historical'/'data'/'locomo10.json';data=json.loads(datafile.read_text(encoding='utf-8'));counts=Counter(str(q['category']) for x in data for q in x['qa']);stats=json.loads((ROOT/'资料'/'数据核查.json').read_text(encoding='utf-8'));assert len(data)==stats['samples'] and dict(counts)==stats['categories'] and sum(counts.values())==stats['questions']==1986
links=[]
for p in [ROOT/'解释.md',ROOT/'复现'/'README.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if target.startswith('http'):continue
        q=p.parent/target.strip('<>');assert q.exists(),str(q);links.append(str(q.relative_to(ROOT)))
files=['解释.md','资料/数据核查.json','复现/README.md','复现/requirements.txt','复现/scripts/demo_amem.py','复现/scripts/plot_results.py','复现/scripts/audit_delivery.py','复现/outputs/results.json','复现/outputs/original_stdout.txt','复现/outputs/mechanism.png','复现/outputs/mechanism.svg','复现/outputs/'+r['state_file']]
report=dict(status='passed',checks=14,local_links=len(links),dataset_questions=1986,data_sha256=hashlib.sha256(datafile.read_bytes()).hexdigest(),files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files})
(OUT/'delivery_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(status='passed',files=len(files),links=len(links),questions=1986)))
