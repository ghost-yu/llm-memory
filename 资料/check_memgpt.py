from pathlib import Path
import json,hashlib,ast,re,sqlite3,subprocess
p=next(p for p in Path('.').iterdir() if p.name.startswith('MemGPT'));repo=p/'代码/MemGPT-historical';out=p/'复现/outputs'
r=json.loads((out/'demo_results.json').read_text(encoding='utf8'))
head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
assert head==r['repository_commit']=='a0139b5fdc203f827168cb741c9f4fea3cec09bf'
assert not subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True).strip()
for source in r['source_symbols']:assert hashlib.sha256((repo/source['path']).read_bytes()).hexdigest()==source['sha256']
assert len(r['runs'])==20
for q in r['runs']:
 assert q['full_correct'] and q['full_answer']==q['gold']
 assert not q['first_page_correct'] and not q['one_call_correct'] and not q['fifo_contains_gold']
 assert any(z['page']==1 for z in q['trace'])
 assert q['full_calls']==len(q['trace'])==2*q['depth_links']+1
assert r['checks']['max_observed_context_chars']<=r['config']['budget_chars']
assert r['checks']['recall_after_eviction']['result_reentered_context']
conn=sqlite3.connect(out/r['database_file'])
assert conn.execute("SELECT COUNT(*) FROM records WHERE kind='recall' AND content LIKE '%Aster secret%'").fetchone()[0]>0
for q in r['runs']:
 row=conn.execute("SELECT content FROM records WHERE kind='archive' AND content LIKE ?",('Key: '+q['start']+'; Value:%',)).fetchone();assert row
conn.close()
meta=json.loads((p/'资料/论文元数据.json').read_text(encoding='utf8'));assert hashlib.sha256((p/'原论文.pdf').read_bytes()).hexdigest()==meta['sha256']
files=['原论文.pdf','解释.md','资料/代码版本.json','复现/README.md','复现/requirements.txt','复现/scripts/demo_memgpt.py','复现/scripts/plot_demo.py','复现/outputs/demo_results.json','复现/outputs/memory_state.json','复现/outputs/demo_summary.png','复现/outputs/demo_summary.svg','复现/outputs/'+r['database_file']]
a=[]
for name in files:
 f=p/name;assert f.is_file() and f.stat().st_size>0,name
 a.append({'path':name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
 if f.suffix=='.py':ast.parse(f.read_text(encoding='utf8'))
links=0
for name in ['解释.md','复现/README.md']:
 f=p/name;text=f.read_text(encoding='utf8');assert '\x00' not in text
 for ref in re.findall(r'\]\(([^)]+)\)',re.sub(r'(?ms)^~~~[^\n]*\n.*?^~~~[^\n]*(?:\n|$)','',text)):
  if not ref.startswith(('https:','http:','#')):
   if not ref.endswith('delivery_check.json'):assert (f.parent/ref.strip('<>')).exists(),ref
   links+=1
result={'status':'pass','scope':'tool/system mechanism only, deterministic controller, no LLM','commit':head,'clean_original_checkout':True,'artifacts':a,'local_links_checked':links,'all_20_pagination_traces_checked':True,'database_rows_verified':True}
(out/'delivery_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print('PASS:',len(a),'artifacts,',links,'links, pinned clean original code, 20 traces and SQLite data')
