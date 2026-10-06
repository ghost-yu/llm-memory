import ast,hashlib,json,re,subprocess,pathlib
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2];REPO=ROOT/'代码/LongMemEval-historical';OUT=ROOT/'复现/outputs';r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
assert len(r['checks'])==13 and all(r['checks'].values()) and len(r['rows'])==120
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()==r['commit']
assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain']).decode().strip()
for p,h in r['sources'].items():assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==h
blob=(ROOT/'资料/数据/longmemeval_s.json').read_bytes();assert hashlib.sha256(blob).hexdigest()==r['dataset']['sha256']
data=json.loads(blob.decode('utf-8'));byid={x['question_id']:x for x in data}
namespace={'np':np};tree=ast.parse((REPO/'src/retrieval/eval_utils.py').read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)]),'original','exec'),namespace)
for row in r['rows']:
 assert row['question']==byid[row['question_id']]['question']
 assert sorted(row['ranking'])==list(range(row['n_documents']))
 for k,v in row['metrics'].items():assert np.allclose(v,namespace['evaluate_retrieval'](row['ranking'],row['gold'],row['corpus_ids'],int(k)))
 if row['canonical_session_metrics']:
  e=byid[row['question_id']]
  for k,v in row['canonical_session_metrics'].items():assert np.allclose(v,namespace['evaluate_retrieval'](row['ranking'],e['answer_session_ids'],e['haystack_session_ids'],int(k)))
for key,v in r['summary'].items():
 gran,task=key.split('/');rr=[x for x in r['rows'] if x['granularity']==gran and (task=='overall' or x['question_type']==task)]
 for k,m in v['metrics'].items():assert np.allclose(m,np.mean([x['metrics'][k] for x in rr],axis=0))
for key,v in r['diagnostic_summary'].items():
 gran,kind=key.split('/');rr=[x for x in r['rows'] if x['granularity']==gran and (kind=='canonical' or x['gold'])]
 assert len(rr)==v['n']
 for k,m in v['metrics'].items():assert np.allclose(m,np.mean([x['canonical_session_metrics' if kind=='canonical' else 'metrics'][k] for x in rr],axis=0))
links=[]
for p in [ROOT/'解释.md',ROOT/'复现/README.md']:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if target.startswith(('http','#')):continue
  q=p.parent/target.strip('<>');assert q.exists(),str(q);links.append(str(q.relative_to(ROOT)))
for p in (ROOT/'复现/scripts').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
files=['解释.md','复现/README.md','复现/requirements.txt','复现/scripts/demo_longmemeval.py','复现/scripts/plot_results.py','复现/scripts/audit_delivery.py','复现/outputs/results.json','复现/outputs/retrieval.png','复现/outputs/retrieval.svg','资料/数据/来源.json']
report=dict(status='passed',questions=60,rows=120,checks=13,links=len(links),files={p:dict(bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files})
(OUT/'delivery_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(status='passed',questions=60,links=len(links),files=len(files))))
