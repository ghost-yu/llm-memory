import ast, hashlib, json, re, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'复现'/'outputs';REPO=ROOT/'代码'/'mem0-historical'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
assert len(r['checks'])==13 and all(r['checks'].values())
assert len(r['model_calls'])==14 and len(r['final'])==5
for p,h in r['sources'].items(): assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h
for p in (ROOT/'复现'/'scripts').glob('*.py'): ast.parse(p.read_text(encoding='utf-8'))
links=[]
for p in [ROOT/'解释.md',ROOT/'复现'/'README.md']:
    text=p.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if target.startswith('http'): continue
        q=p.parent/target.strip('<>');assert q.exists(),str(q);links.append(str(q.relative_to(ROOT)))
vp,hp=[OUT/x for x in r['databases']]
c=sqlite3.connect(vp);live=[dict(id=i,vector=json.loads(v),payload=json.loads(p)) for i,v,p in c.execute('SELECT * FROM vectors ORDER BY id')];assert live==r['final'];c.close()
c=sqlite3.connect(hp);events=dict(c.execute('SELECT event,COUNT(*) FROM history GROUP BY event'))
assert events=={'ADD':6,'UPDATE':1,'DELETE':1},events
assert c.execute('SELECT COUNT(*) FROM history WHERE is_deleted=1').fetchone()[0]==1;c.close()
files=['解释.md','复现/README.md','复现/scripts/demo_mem0.py','复现/scripts/plot_results.py','复现/scripts/audit_delivery.py','复现/outputs/results.json','复现/outputs/mechanism.png','复现/outputs/mechanism.svg']+['复现/outputs/'+x for x in r['databases']]
report=dict(checks='passed',local_links=len(links),history_events=events,files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files})
(OUT/'delivery_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(local_links=len(links),files=len(files),history_events=events)))
