"""Original functions and prompt assembly; controlled responses, no model/API."""
import ast,copy,contextlib,hashlib,inspect,io,json,pathlib,sys,textwrap
from datetime import datetime,timedelta
from types import SimpleNamespace as NS
import numpy as np
P=pathlib.Path(__file__).resolve().parents[2];R=P/'代码/LongMemEval-historical'
sys.path.insert(0,str(P/'复现/vendor'))
from rank_bm25 import BM25Okapi
ns={'np':np,'BM25Okapi':BM25Okapi,'json':json,'datetime':datetime,'timedelta':timedelta}
sources={}
def load(path,names):
    f=R/path;sources[path]=hashlib.sha256(f.read_bytes()).hexdigest()
    tree=ast.parse(f.read_text(encoding='utf8'));nodes=[n for n in tree.body if getattr(n,'name',None) in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes),str(f),'exec'),ns)
load('src/retrieval/eval_utils.py',['dcg','ndcg','evaluate_retrieval','evaluate_retrieval_turn2session'])
load('src/retrieval/run_retrieval.py',['process_item_flat_index','DenseRetrievalMaster'])
load('src/retrieval/index_expansion_utils.py',['fetch_expansion_from_cache','resolve_expansion'])
load('src/index_expansion/temp_query_search_pruning.py',['increment_date','infer_time_range'])
load('src/evaluation/evaluate_qa.py',['get_anscheck_prompt'])
load('src/generation/run_generation.py',['prepare_prompt'])
checks={};obs={}
def check(name,test):
    assert test,name
    checks[name]=bool(test)
def error(name,fn,kind):
    try:fn()
    except kind as ex:obs[name]=type(ex).__name__+': '+str(ex);check(name,True)
    else:raise AssertionError(name)
class Tokens:
    def encode(self,text,**kwargs):return text.split()
    def decode(self,tokens,**kwargs):return ' '.join(tokens)
def entry():
    return dict(question='What degree?',question_date='2025/03/01',
      haystack_dates=['2025/01/01'],haystack_session_ids=['answer_s'],
      haystack_sessions=[[dict(role='user',content='OLDUSER',has_answer=True),dict(role='assistant',content='OLDASSISTANT',has_answer=True)]],
      retrieval_results={'ranked_items':[dict(corpus_id='answer_s_1',text='expanded facts')]})
def prompt(e,kind='flat-turn',k=1,useronly=False,limit=1000,con=False):
    return ns['prepare_prompt'](e,kind,k,useronly,'json',False,Tokens(),'openai',limit,None,con=con,con_client=None,con_model='controlled')
def main():
    ix=ns['process_item_flat_index'];f=ns['evaluate_retrieval']
    assistant=[dict(role='assistant',content='answer',has_answer=True)]
    values,ids,dates=ix(assistant,'session','answer_s','date')
    check('assistant_only_session_empty_key_noans',values==[''] and ids==['noans_s'])
    check('assistant_only_turn_no_documents',ix(assistant,'turn','answer_s','date')==([],[],[]))
    error('answer_user_missing_label_KeyError',lambda:ix([dict(role='user',content='x')],'session','answer_s','date'),KeyError)
    check('numeric_has_answer_1_accepted',ix([dict(role='user',content='x',has_answer=1)],'turn','answer_s','date')[1]==['answer_s_1'])
    error('unknown_granularity_NotImplemented',lambda:ix([],'round','s','date'),NotImplementedError)
    check('gold_unknown_any_all_ndcg_zero',f([0],['missing'],['d'],1)==(0.,0.,0.))
    check('gold_empty_vacuous_all',f([0],[],['d'],1)==(0.,1.,0.))
    check('k_zero_nonempty_gold_all_zero',f([0],['d'],['d'],0)==(0.,0.,0.))
    error('ranking_out_of_range_IndexError',lambda:f([1],['d'],['d'],1),IndexError)
    duplicate=f([0,0,0],['a'],['a','b','c'],3)
    check('duplicate_rank_can_ndcg_exceed_one',duplicate[2]>1)
    obs['duplicate_ranking_metric']=list(duplicate)
    turnscore=ns['evaluate_retrieval_turn2session']([0,1,2],['s_1'],['s_1','s_2','t_1'],2)
    check('turn2session_budget_expands_past_two_turns',turnscore==(1.,1.,1.))
    # No user corpus text or response API in cache/key operations.
    check('cache_prefix_normalization',ns['fetch_expansion_from_cache']({'s':'fact'},'answer_s')==['fact'])
    c=['original'];ids=['s'];dates=['date']
    result=ns['resolve_expansion']('session-userfact','separate',c,ids,dates,['f1','f2'],'s','date')
    check('separate_mutates_input_identity',result[0] is c and c==['original','f1 f2'] and ids==['s','s'])
    c=['original'];ids=['s'];dates=['date']
    result=ns['resolve_expansion']('session-userfact','split-merge',c,ids,dates,['f1','f2'],'s','date')
    check('split_merge_duplicates_ID_new_lists',result[0]==['f1 original','f2 original'] and result[1]==['s','s'] and c==['original'])
    result=ns['resolve_expansion']('session-userfact','merge',['original'],['s'],['date'],[],'s','date')
    check('empty_userfact_list_merge_drops_matching_key',result==([],[],[]))
    result=ns['resolve_expansion']('session-userfact','merge',['original'],['s'],['date'],None,'s','date')
    check('None_userfact_keeps_blank_prefixed_original',result[0]==[' original'])
    check('increment_date_calendar_rollover',ns['increment_date']('2024/02/28',2)=='2024/03/01')
    error('invalid_date_ValueError',lambda:ns['increment_date']('2024/02/30',1),ValueError)
    ns.update(client=None,model='controlled',chat_completions_with_backoff=lambda *a,**kw:NS(choices=[NS(message=NS(content='{"start":"2025/01/01"}'))]))
    check('time_parser_missing_end_not_validated',ns['infer_time_range']('when?','2025/03/01')=={'start':'2025/01/01'})
    # Prompt assembly accesses original value references and removes has_answer.
    e=entry();p=prompt(e)
    check('prompt_restores_round_and_pops_source_labels','OLDUSER' in p and 'OLDASSISTANT' in p and all('has_answer' not in x for x in e['haystack_sessions'][0]))
    obs['round_prompt']=p
    error('flat_turn_useronly_list_TypeError',lambda:prompt(entry(),useronly=True),TypeError)
    error('flat_turn_k_zero_empty_history_Assertion',lambda:prompt(entry(),k=0),AssertionError)
    p=prompt(entry(),kind='orig-session',k=0)
    check('orig_session_k_zero_returns_all','OLDUSER' in p and 'OLDASSISTANT' in p)
    p=prompt(entry(),limit=0)
    check('zero_token_budget_prompt_without_history','OLDUSER' not in p and 'What degree?' in p)
    ns['chat_completions_with_backoff']=lambda *a,**kw:NS(choices=[NS(message=NS(content='controlled reading note'))])
    p=prompt(entry(),con=True)
    check('CoN_JSON_replaces_round_with_controlled_note','controlled reading note' in p and 'OLDUSER' not in p)
    tree=ast.parse((R/'src/evaluation/evaluate_qa.py').read_text(encoding='utf8'))
    labelnode=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='label' for x in n.targets))
    labelns={'eval_response':'No. Yesterday was unrelated.'}
    exec(compile(ast.Module(body=[labelnode]),'original judge-label statement','exec'),labelns)
    check('judge_yes_substring_in_yesterday_passes',labelns['label'] is True)
    obs['judge_label_input']=labelns['eval_response']
    error('judge_unknown_task_NotImplemented',lambda:ns['get_anscheck_prompt']('unknown','q','a','r'),NotImplementedError)
    # Actual partition block uses substring membership for turn IDs.
    tf=R/'src/index_expansion/temp_query_search_pruning.py'
    block=textwrap.dedent(tf.read_text(encoding='utf8').split('            # filter haystack\n',1)[1].split('            # print the new evaluation results',1)[0])
    scoped=dict(ns,timerange={'start':'2025/01/01','end':'2025/01/01'},event_date_to_sid={'2025/01/01':['s1']},ranked_items_original=[dict(corpus_id='other_1'),dict(corpus_id='s10_1')],granularity='turn',entry={'retrieval_results':{}},out_data=[])
    exec(compile(block,str(tf)+'#partition','exec'),scoped)
    check('turn_time_filter_session_substring_false_match',scoped['ranked_items_new'][0]['corpus_id']=='s10_1')
    obs['partition_false_match']=[x['corpus_id'] for x in scoped['ranked_items_new']]
    signatures={name:str(inspect.signature(ns[name])) for name in ['dcg','ndcg','evaluate_retrieval','evaluate_retrieval_turn2session','process_item_flat_index','fetch_expansion_from_cache','resolve_expansion','increment_date','infer_time_range','get_anscheck_prompt','prepare_prompt']}
    for name in ['__init__','prepare_retriever','run_flat_retrieval']:signatures['DenseRetrievalMaster.'+name]=str(inspect.signature(getattr(ns['DenseRetrievalMaster'],name)))
    result={'scope':'Original indexing/metrics/cache/date/prompt functions and original judge-label/time-partition statements; controlled tokenizer/CoN/date responses, not API inference',
      'original_sources':sources,'demo_sha256':hashlib.sha256((P/'复现/scripts/demo_longmemeval.py').read_bytes()).hexdigest(),
      'signatures':signatures,'checks_passed':checks,'observations':obs,'python':sys.version,'numpy':np.__version__}
    (P/'复现/outputs/contracts_trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return 'PASS: {} boundary checks; {} signatures'.format(len(checks),len(signatures))
if __name__=='__main__':
    log=io.StringIO()
    with contextlib.redirect_stdout(log):result=main()
    (P/'复现/outputs/contracts_stdout.txt').write_text(log.getvalue(),encoding='utf8');print(result)