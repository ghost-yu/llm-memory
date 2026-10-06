import ast,hashlib,json,re,subprocess
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'代码'/'locomo-official';OUT=ROOT/'复现'/'outputs'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'));assert len(r['checks'])==9 and all(r['checks'].values())
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()==r['commit']
assert subprocess.check_output(['git','-C',str(REPO),'status','--porcelain']).decode().strip()==''
for p,h in r['sources'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
for p in (ROOT/'复现'/'scripts').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
data=json.loads((REPO/'data'/'locomo10.json').read_text(encoding='utf-8'));byid={x['sample_id']:x for x in data}
counts=Counter(str(q['category']) for x in data for q in x['qa']);assert dict(counts)==r['category_counts'] and sum(counts.values())==1986
assert len(r['rows'])==r['overall']['n']==1536 and len(r['missing_evidence_ids'])==9
for row in r['rows']:
    q=byid[row['sample']]['qa'][row['question_index']];assert q['evidence']==row['evidence'] and q['question']==row['question']
    for k,ids in row['retrieved'].items():
        assert len(ids)==int(k) and len(set(ids))==len(ids)
        recall=sum(e in ids for e in q['evidence'])/len(q['evidence']);assert abs(recall-row['recalls'][k])<1e-12
for k,mean in r['overall']['bm25'].items():assert abs(mean-sum(x['recalls'][k] for x in r['rows'])/1536)<1e-12
assert r['metric_probes']['comma_list_extra_predictions']==1 and r['metric_probes']['missing_context_default_recall']==1
links=[]
for p in [ROOT/'解释.md',ROOT/'复现'/'README.md']:
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if target.startswith('http'):continue
        q=p.parent/target.strip('<>');assert q.exists(),str(q);links.append(str(q.relative_to(ROOT)))
files=['解释.md','复现/README.md','复现/requirements.txt','复现/scripts/demo_locomo.py','复现/scripts/plot_results.py','复现/scripts/audit_delivery.py','复现/outputs/results.json','复现/outputs/scorer_stdout.txt','复现/outputs/retrieval.png','复现/outputs/retrieval.svg']
report=dict(status='passed',checks=9,questions=1536,links=len(links),files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files})
(OUT/'delivery_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(status='passed',files=len(files),links=len(links),questions=1536)))
