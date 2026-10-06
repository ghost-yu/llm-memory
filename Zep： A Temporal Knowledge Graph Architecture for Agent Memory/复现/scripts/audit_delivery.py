import ast,hashlib,json,re,sqlite3,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'复现'/'outputs';REPO=ROOT/'代码'/'graphiti-historical'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
assert len(r['checks'])==14 and all(r['checks'].values())
assert len(r['model_calls'])==16 and len(r['final'])==4
assert r['answers']==[['Beijing'],['Hangzhou'],['Shanghai']]
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()==r['commit']
assert subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()==''
for p,h in r['sources'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h
for p in (ROOT/'复现'/'scripts').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
links=[]
for p in [ROOT/'解释.md',ROOT/'复现'/'README.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if target.startswith('http'):continue
        q=p.parent/target.strip('<>');assert q.exists(),str(q);links.append(str(q.relative_to(ROOT)))
conn=sqlite3.connect(OUT/r['database']);saved=[json.loads(x[0]) for x in conn.execute('SELECT payload FROM snapshots ORDER BY rowid')];conn.close();assert saved==r['snapshots']
files=['解释.md','复现/README.md','复现/requirements.txt','复现/scripts/demo_zep.py','复现/scripts/plot_results.py','复现/scripts/audit_delivery.py','复现/outputs/results.json','复现/outputs/temporal.png','复现/outputs/temporal.svg','复现/outputs/'+r['database']]
report=dict(status='passed',checks=14,controlled_calls=16,local_links=len(links),snapshots=len(saved),files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files})
(OUT/'delivery_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(status='passed',files=len(files),links=len(links),snapshots=len(saved))))
