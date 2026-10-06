from pathlib import Path
import json,hashlib,re,ast,subprocess
from urllib.parse import unquote
import fitz
ROOT=Path(__file__).resolve().parents[1];manifest=json.loads((ROOT/'资料/下载清单.json').read_text(encoding='utf-8'))['papers'];papers=[];links=0
for meta in manifest:
 p=Path(meta['local_pdf']).parent
 assert p.is_dir()
 assert hashlib.sha256((p/'原论文.pdf').read_bytes()).hexdigest()==meta['sha256']
 pdf=fitz.open(str(p/'原论文.pdf'));assert len(pdf)==meta['pages'];pdf.close()
 for rel in ['解释.md','复现/README.md','复现/requirements.txt']:assert (p/rel).stat().st_size>0
 explanation=(p/'解释.md').read_text(encoding='utf-8')
 assert '部分成功' in explanation and 'Code' in explanation
 assert not any(s in explanation.splitlines()[0] for s in ['零基础','从零开始','小白'])
 scripts=list((p/'复现/scripts').glob('*.py'));assert scripts
 for s in scripts:ast.parse(s.read_text(encoding='utf-8'))
 results=p/'复现/outputs/results.json'
 if not results.exists():results=p/'复现/outputs/demo_results.json'
 assert results.exists() and json.loads(results.read_text(encoding='utf-8'))
 audit=p/'复现/outputs/delivery_check.json'
 if not audit.exists():audit=p/'复现/outputs/demo_delivery_check.json'
 report=json.loads(audit.read_text(encoding='utf-8'));assert report
 # Recheck hashed delivery files (support all prior report formats).
 entries=[]
 if isinstance(report.get('files'),dict):entries=[dict(path=k,**v) for k,v in report['files'].items()]
 entries+=report.get('artifacts',[])+report.get('checked_files',[])
 for item in entries:
  rel=item['path'];f=p/rel
  if not f.exists():f=ROOT/rel
  assert f.exists(),str(f)
  if 'sha256' in item:assert hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256'],str(f)
 repos=[]
 for git in (p/'代码').glob('*/.git'):
  repo=git.parent;head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip();dirty=subprocess.check_output(['git','-C',str(repo),'status','--porcelain']).decode().strip()
  assert not dirty,(repo,dirty)
  repos.append(dict(path=str(repo.relative_to(ROOT)),head=head))
 files=[p/'解释.md',p/'复现/README.md',p/'复现/requirements.txt',results,audit]
 papers.append(dict(title=meta['title'],folder=p.name,pdf_pages=meta['pages'],pdf_sha256=meta['sha256'],scripts=len(scripts),repositories=repos,files={str(f.relative_to(ROOT)):dict(bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()) for f in files},scope='paper reading and small demo, partial reproduction'))
for doc in [ROOT/'论文索引.md',ROOT/'资料/阅读进度.md']+[ROOT/x['folder']/'解释.md' for x in papers]+[ROOT/x['folder']/'复现/README.md' for x in papers]:
 text=doc.read_text(encoding='utf-8');assert '\x00' not in text
 for target in re.findall(r'\]\(([^)]+)\)',re.sub(r'(?ms)^~~~[^\n]*\n.*?^~~~[^\n]*(?:\n|$)','',text)):
  if target.startswith(('http','#','codex:')):continue
  target=unquote(target.strip('<>')).split('#')[0];assert (doc.parent/target).exists(),(str(doc),target);links+=1
assert len(papers)==9
report=dict(status='passed',role='artifact consistency only; does not certify skill semantic completeness',content_review_progress='资料/skill补齐进度.md',papers=len(papers),scope='nine readings with modest demos, not full paper benchmarks',local_links_checked=links,details=papers)
(ROOT/'资料/最终核验.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(status='passed',papers=9,links=links,pdf_pages=sum(x['pdf_pages'] for x in papers))))
