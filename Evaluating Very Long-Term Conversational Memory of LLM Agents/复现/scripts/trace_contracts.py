"""Original metric functions/context builder with controlled local inputs."""
import ast,contextlib,hashlib,importlib.util,inspect,io,json,sys
from pathlib import Path
from types import SimpleNamespace as NS
P=Path(__file__).resolve().parents[2]
source=P/'复现/scripts/demo_locomo.py'
spec=importlib.util.spec_from_file_location('locomo_contract_demo',source);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
checks={};obs={}
def check(name,test):
    assert test,name
    checks[name]=bool(test)
def error(name,fn,kind):
    try:fn()
    except kind as ex:obs[name]=type(ex).__name__+': '+str(ex);check(name,True)
    else:raise AssertionError(name)
def qa(category=4,answer='apple',prediction='apple',evidence=None,context=None):
    q=dict(category=category,answer=answer,prediction=prediction,evidence=['D1:1'] if evidence is None else evidence)
    if context is not None:q['prediction_context']=context
    return q
class Encoding:
    def encode(self,text):return text.split()
def main():
    f=d.ns
    check('normalize_comma_merges_words',f['normalize_answer']('red,car')=='redcar')
    check('stemmer_equates_plural',f['f1_score']('cars','car')==1)
    check('multiset_penalizes_repeated_prediction',abs(f['f1_score']('apple apple','apple')-2/3)<1e-12)
    check('empty_F1_zero_but_set_EM_true',f['f1_score']('','')==0 and f['exact_match_score']('','') is True)
    check('list_item_reuse_no_global_penalty',f['f1']('apple','apple, apple')==1 and f['f1']('apple, banana','apple')==1)
    result=f['eval_question_answering']([qa(category=3,answer='apple; banana')])
    check('open_domain_uses_first_semicolon_answer',result[0]==[1.0])
    lines=[qa(answer='apple web',prediction='apple')]
    a=f['eval_question_answering'](lines,metric='f1');b=f['eval_question_answering'](lines,metric='exact_match')
    check('metric_argument_does_not_select_EM',a==b and abs(a[0][0]-2/3)<1e-12)
    original=json.dumps(lines,sort_keys=True);f['eval_question_answering'](lines)
    check('scorer_does_not_mutate_QA',json.dumps(lines,sort_keys=True)==original)
    error('nonempty_evidence_empty_context_IndexError',lambda:f['eval_question_answering']([qa(context=[])]),IndexError)
    check('empty_evidence_context_defaults_one',f['eval_question_answering']([qa(evidence=[],context=[])])[2]==[1])
    check('summary_recall_coarse_session',f['eval_question_answering']([qa(evidence=['D1:1','D1:2'],context=['S1'])])[2]==[1.0])
    check('first_context_ID_controls_mode',f['eval_question_answering']([qa(context=['S2','D1:1'])])[2]==[0.0])
    check('evidence_duplicates_preserved_denominator',f['eval_question_answering']([qa(evidence=['D1:1','D1:1','D2:1'],context=['D1:1'])])[2]==[2/3])
    check('category5_keyword_negation_still_passes',f['eval_question_answering']([qa(category=5,prediction='It is NOT not mentioned; she lives in Paris.')])[0]==[1])
    error('unknown_category_ValueError',lambda:f['eval_question_answering']([qa(category=6)]),ValueError)
    error('prediction_list_not_supported',lambda:f['eval_question_answering']([qa(prediction=['apple'])]),AttributeError)
    check('empty_batch_returns_empty_lists',f['eval_question_answering']([])==([],0.0,[]))
    bm=d.BM25([dict(text='alpha'),dict(text='beta')])
    check('query_repetitions_deduplicated',bm.rank('alpha alpha')==bm.rank('alpha'))
    check('unknown_query_tie_chronological',bm.rank('XYZ')[0]==[0,1] and bm.rank('XYZ')[1]==[0.,0.])
    check('BM25_empty_docs_safe',d.BM25([]).rank('q')==([],[]))
    sample={'conversation':{'session_2_date_time':'DAY2','session_2':[dict(speaker='B',text='new',dia_id='D2:1',blip_caption='CAPTION')],'session_1_date_time':'DAY1','session_1':[dict(speaker='A',text='old',dia_id='D1:1')]}}
    docs=d.documents(sample)
    check('documents_numeric_sessions_and_caption',docs[0]['id']=='D1:1' and 'B: new' in docs[1]['text'] and 'CAPTION' in docs[1]['text'])
    gpt=d.REPO/'task_eval/gpt_utils.py';ns={'MAX_LENGTH':{'stub':10000},'PER_QA_TOKEN_BUDGET':1}
    tree=ast.parse(gpt.read_text(encoding='utf8'));node=next(n for n in tree.body if getattr(n,'name',None)=='get_input_context')
    exec(compile(ast.Module(body=[node]),str(gpt),'exec'),ns)
    args=NS(model='stub',batch_size=1);ns['MAX_LENGTH']['stub']=14
    context=ns['get_input_context'](sample['conversation'],0,Encoding(),args)
    obs['budgeted_context']=context
    check('budget_builder_keeps_old_session_first','old' in context and 'new' not in context)
    obs['metric_ignored']=a;obs['repeated_evidence_recall']=2/3
    signatures={name:str(inspect.signature(f[name])) for name in d.names}
    for owner,names in [(d.BM25,['__init__','rank'])]:
        for name in names:signatures[owner.__name__+'.'+name]=str(inspect.signature(getattr(owner,name)))
    for name in ['terms','documents','main']:signatures['demo.'+name]=str(inspect.signature(getattr(d,name)))
    signatures['get_input_context']=str(inspect.signature(ns['get_input_context']))
    result={'scope':'Original five scorers, original context builder with word-count encoding/budget globals, and BM25/document host boundaries; no model inference',
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_sources':{str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [d.SOURCE,d.DATA,gpt]},
      'checks_passed':checks,'signatures':signatures,'observations':obs,'python':sys.version,'versions':dict(numpy=d.np.__version__,nltk=d.nltk.__version__)}
    (P/'复现/outputs/contracts_trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return 'PASS: {} boundaries; {} signatures'.format(len(checks),len(signatures))
if __name__=='__main__':
    log=io.StringIO()
    with contextlib.redirect_stdout(log):result=main()
    (P/'复现/outputs/contracts_stdout.txt').write_text(log.getvalue(),encoding='utf8');print(result)