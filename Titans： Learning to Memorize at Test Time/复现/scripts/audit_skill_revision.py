"""Evidence consistency check; semantic coverage is reviewed in skill内容核查.md."""
from pathlib import Path
import ast,hashlib,json,re,subprocess
from urllib.parse import unquote
BASE=Path(__file__).resolve().parents[2];REPO=BASE/'代码/titans-pytorch';OUT=BASE/'复现/outputs'
r=json.loads((OUT/'contracts_trace.json').read_text(encoding='utf-8'))
assert len(r['checks'])==15 and all(r['checks'].values())
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()==r['commit']
assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain']).decode().strip()
for rel,h in r['sources'].items():assert hashlib.sha256((REPO/rel).read_bytes()).hexdigest()==h
assert r['first']['state'][0]==4 and r['first']['state'][2]['shape']==[2,1,8]
assert r['first']['state'][4]['weights.0']['shape']==[2,3,8,16]
assert r['continued']['state'][0]==8 and r['continued']['state'][2]['shape']==[2,0,8]
assert '4' in r['unaligned_continuation']['message'] and '6' in r['unaligned_continuation']['message']
assert r['mask_state_delta']>0
for name,c in r['contracts'].items():
 tree=ast.parse((REPO/c['file']).read_text(encoding='utf-8'))
 fname=name.split('.')[-1];nodes=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==fname and n.lineno==c['line']]
 assert len(nodes)==1,(name,c)
for row in r['mac_inference']:
 expected={'token_emb':[2,13,16],'layers.0.4':[2,19,16],'layers.0.5':[2,19,16],'norm':[2,13,16],'to_logits':[2,13,32]}
 actual=row['output'][0] if row['owner'] in ['NeuralMemory','SegmentedAttention'] else row['output'];assert actual['shape']==expected[row['name']]
for row in r['mac_training']:
 expected={'token_emb':[2,12,16],'layers.0.4':[2,16,16],'layers.0.5':[2,16,16],'norm':[2,12,16],'to_logits':[2,12,32]}
 actual=row['output'][0] if row['owner'] in ['NeuralMemory','SegmentedAttention'] else row['output'];assert actual['shape']==expected[row['name']]
for p in (BASE/'复现/scripts').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
links=0
for p in [BASE/'解释.md',BASE/'复现/README.md',BASE/'复现/demo说明.md',BASE/'资料/skill内容核查.md']:
 for ref in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  if ref.startswith(('http','#')):continue
  f=p.parent/unquote(ref.strip('<>'));assert f.exists(),str(f);links+=1
# Preserve earlier successful demo/actual checkpoint evidence, update document hashes.
old=json.loads((BASE/'资料/历史demo交付核验.json').read_text(encoding='utf-8'))
for item in old['checked_files']:
 f=BASE.parent/item['path']
 if f.name!='解释.md':assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256']
old['scope']='Titans revised reading and controlled demo; full paper benchmark not reproduced'
for item in old['checked_files']:
 f=BASE.parent/item['path'];item['bytes']=f.stat().st_size;item['sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
new=['复现/README.md','资料/skill内容核查.md','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','图片/page-9.png','图片/page-10.png','图片/page-11.png']
for rel in new:
 f=BASE/rel;old['checked_files'].append(dict(path=str(f.relative_to(BASE.parent)),bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
old['local_links_checked']=links;old['revision_checks']=15
(OUT/'demo_delivery_check.json').write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
report=dict(status='passed',role='artifact/source/observed trace consistency, not an automatic semantic judge',checks=15,contracts=11,local_links=links,semantic_review='资料/skill内容核查.md',artifacts={rel:dict(bytes=(BASE/rel).stat().st_size,sha256=hashlib.sha256((BASE/rel).read_bytes()).hexdigest()) for rel in ['解释.md']+new})
(OUT/'skill_revision_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(status='passed',contracts=11,runtime_checks=15,local_links=links)))
