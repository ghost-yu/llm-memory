import ast,copy,hashlib,json,pathlib,platform,sys,textwrap,subprocess
from collections import Counter
from datetime import datetime,timedelta
from types import SimpleNamespace
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2];REPO=ROOT/'代码/LongMemEval-historical';OUT=ROOT/'复现/outputs';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'复现/vendor'))
from rank_bm25 import BM25Okapi

def original(path,names,namespace):
 tree=ast.parse(path.read_text(encoding='utf-8'));nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
 assert len(nodes)==len(names)
 exec(compile(ast.Module(body=nodes),str(path),'exec'),namespace)
 return namespace

env={'np':np}
original(REPO/'src/retrieval/eval_utils.py',['dcg','ndcg','evaluate_retrieval','evaluate_retrieval_turn2session'],env)
original(REPO/'src/retrieval/run_retrieval.py',['process_item_flat_index','DenseRetrievalMaster'],env)
original(REPO/'src/retrieval/index_expansion_utils.py',['resolve_expansion'],env)
original(REPO/'src/evaluation/evaluate_qa.py',['get_anscheck_prompt'],env)
master=object.__new__(env['DenseRetrievalMaster']) # bypass CUDA/model factory; original BM25 branch
source=ROOT/'资料/数据/longmemeval_s.json';blob=source.read_bytes();assert hashlib.sha256(blob).hexdigest()=='08d8dad4be43ee2049a22ff5674eb86725d0ce5ff434cde2627e5e8e7e117894'
data=json.loads(blob.decode('utf-8'));counts=Counter();selected=[]
for e in data:
 if '_abs' in e['question_id']:continue
 if counts[e['question_type']]<10:selected.append(e);counts[e['question_type']]+=1
assert len(selected)==60 and len(counts)==6
env['BM25Okapi']=BM25Okapi
rows=[];empty_gold=[];ks=[1,3,5,10,30,50]
for n,e in enumerate(selected):
 for gran in ['session','turn']:
  corpus=[];ids=[];dates=[]
  for sid,session,date in zip(e['haystack_session_ids'],e['haystack_sessions'],e['haystack_dates']):
   texts,keys,ts=env['process_item_flat_index'](session,gran,sid,date);corpus+=texts;ids+=keys;dates+=ts
  rank=master.run_flat_retrieval(e['question'],'flat-bm25',corpus).tolist()
  # Ranking is computed from raw query/user text only. Label-bearing IDs never reach BM25.
  gold=sorted(set(x for x in ids if 'answer' in x))
  if not gold:empty_gold.append([e['question_id'],gran])
  metrics={str(k):list(map(float,env['evaluate_retrieval'](rank,gold,ids,k))) for k in ks}
  canonical=None
  if gran=='session':
   rawids=e['haystack_session_ids'];canonical={str(k):list(map(float,env['evaluate_retrieval'](rank,e['answer_session_ids'],rawids,k))) for k in ks}
  rows.append(dict(question_id=e['question_id'],question_type=e['question_type'],question=e['question'],granularity=gran,n_documents=len(ids),gold=gold,corpus_ids=ids,ranking=rank,metrics=metrics,canonical_session_metrics=canonical,top10=[dict(id=ids[i],date=dates[i],text=corpus[i][:300]) for i in rank[:10]]))
 print('processed %s/60'% (n+1),flush=True) if (n+1)%10==0 else None
summary={}
for gran in ['session','turn']:
 for task in ['overall']+sorted(counts):
  rr=[r for r in rows if r['granularity']==gran and (task=='overall' or r['question_type']==task)]
  summary[gran+'/'+task]=dict(n=len(rr),metrics={str(k):np.mean([r['metrics'][str(k)] for r in rr],axis=0).tolist() for k in ks})
diagnostic_summary={}
for gran in ['session','turn']:
 rr=[r for r in rows if r['granularity']==gran and r['gold']]
 diagnostic_summary[gran+'/nonempty']=dict(n=len(rr),metrics={str(k):np.mean([r['metrics'][str(k)] for r in rr],axis=0).tolist() for k in ks})
rr=[r for r in rows if r['granularity']=='session']
diagnostic_summary['session/canonical']=dict(n=len(rr),metrics={str(k):np.mean([r['canonical_session_metrics'][str(k)] for r in rr],axis=0).tolist() for k in ks})
# Mechanism probes execute original time parser/prompt and stable partition, with explicit fake responses.
responses=iter(['{"start":"2023/04/01","end":"2023/04/30"}','N/A','{"start":"2023/05/30","end":"2023/05/30"}'])
calls=[]
def provider(client,**kwargs):
 calls.append(kwargs);return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=next(responses)))])
te={'datetime':datetime,'timedelta':timedelta,'json':json,'client':None,'model':'controlled-provider','chat_completions_with_backoff':provider}
timefile=REPO/'src/index_expansion/temp_query_search_pruning.py'
original(timefile,['increment_date','infer_time_range'],te)
tr=te['infer_time_range']('Which pair of shoes did I clean last month?','2023/05/30 (Tue) 01:50')
na=te['infer_time_range']('How many bikes do I own?','2023/05/30 (Tue) 01:50')
hack=te['infer_time_range']('What happened today?','2023/05/30 (Tue) 01:50')
code=timefile.read_text(encoding='utf-8').split('            # filter haystack\n',1)[1].split('            # print the new evaluation results',1)[0]
partition=textwrap.dedent(code)
original_items=[dict(corpus_id='filler_old'),dict(corpus_id='answer_event'),dict(corpus_id='filler_future')]
def run_partition(timerange):
 entry={'retrieval_results':{'ranked_items':copy.deepcopy(original_items)}}
 scope=dict(te,timerange=timerange,event_date_to_sid={'2023/04/10':['answer_event'],'2023/04/01':['filler_old'],'2023/05/20':['filler_future']},ranked_items_original=entry['retrieval_results']['ranked_items'],granularity='session',entry=entry,out_data=[])
 exec(compile(partition,str(timefile)+'#original-partition','exec'),scope)
 return scope['ranked_items_new']
good=run_partition({'start':'2023/04/09','end':'2023/04/11'});wrong=run_partition({'start':'2023/05/19','end':'2023/05/21'})
merged=env['resolve_expansion']('session-userfact','merge',['original detail'],['s'],['date'],['user likes Sony'],'s','date')
# Observe original quirks, not claims of model correctness.
probes=dict(time_range=tr,no_temporal_range=na,current_date_hack=hack,good_time_order=[x['corpus_id'] for x in good],wrong_time_order=[x['corpus_id'] for x in wrong],merge_key=merged[0],empty_gold_metric=list(map(float,env['evaluate_retrieval']([0],[],['d'],1))),dcg_pattern=float(env['dcg']([0,1,0],3)),judge_temporal_prompt=env['get_anscheck_prompt']('temporal-reasoning','How many days?','18','19'),judge_abs_prompt=env['get_anscheck_prompt']('multi-session','Unknown?','not stated','I do not know',True))
checks=dict(real_data_hash=True,stratified_60=len(selected)==60,all_rankings_permutations=all(sorted(r['ranking'])==list(range(r['n_documents'])) for r in rows),all_gold_in_corpus=all(set(r['gold'])<=set(r['corpus_ids']) for r in rows),nonempty_any_ge_all=all(v[0]>=v[1] for r in rows if r['gold'] for v in r['metrics'].values()),time_prompt_10_examples=all(len(x['messages'])==22 for x in calls),NA_returns_empty=na=={},current_date_hack_observed=hack=={},time_stable_partition=good[0]['corpus_id']=='answer_event' and len(good)==3,wrong_time_hurts=wrong[-1]['corpus_id']=='answer_event',merge_preserves_original=merged[0]==['user likes Sony original detail'],empty_gold_all_vacuous=probes['empty_gold_metric']==[0.,1.,0.],dcg_second_rank_undiscounted=probes['dcg_pattern']==1.)
assert all(checks.values())
paths=['src/retrieval/eval_utils.py','src/retrieval/run_retrieval.py','src/retrieval/index_expansion_utils.py','src/index_expansion/temp_query_search_pruning.py','src/evaluation/evaluate_qa.py']
r=dict(commit=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip(),environment=dict(python=platform.python_version(),numpy=np.__version__,rank_bm25='0.2.2',device='cpu'),selection='first 10 non-abstention questions per source task; no random population estimate',dataset=dict(instances=len(data),abstention=sum('_abs' in x['question_id'] for x in data),bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),task_counts=dict(Counter(x['question_type'] for x in data))),selected_counts=dict(counts),diagnostic_summary=diagnostic_summary,empty_gold=empty_gold,summary=summary,rows=rows,probes=probes,controlled_calls=calls,checks=checks,sources={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in paths})
(OUT/'results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(checks=checks,empty_gold=empty_gold,summary={k:v for k,v in summary.items() if k.endswith('overall')}),ensure_ascii=False,indent=2))
