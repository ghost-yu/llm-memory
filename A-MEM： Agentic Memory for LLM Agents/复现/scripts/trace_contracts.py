"""Actual original class methods; deterministic providers and encoding collaborators."""
import ast,contextlib,hashlib,importlib.util,inspect,io,json,logging,os,pickle,sys
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
P=Path(__file__).resolve().parents[2]
source=P/'复现/scripts/demo_amem.py'
spec=importlib.util.spec_from_file_location('amem_contract_demo',source);d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
Note=d.ns['MemoryNote'];System=d.ns['AgenticMemorySystem'];checks={};obs={}
def check(name,test):
    assert test,name
    checks[name]=bool(test)
def error(name,fn,kind):
    try:fn()
    except kind as ex:obs[name]=type(ex).__name__+': '+str(ex);check(name,True)
    else:raise AssertionError(name)
def note(uid,content=None,**kwargs):
    fields=dict(keywords=['cache'],context='original '+uid,category='test',tags=['cache']);fields.update(kwargs)
    return Note(content or uid,id=uid,**fields)
class Response:
    def __init__(self,response):self.response=response;self.calls=0
    def get_completion(self,*a,**kw):self.calls+=1;return self.response
def system(response=None,threshold=100):
    m=System(evo_threshold=threshold)
    r=Response(response or json.dumps({'should_evolve':False}))
    m.llm_controller=NS(llm=r);return m,r
def seed(m,notes,indices=None):
    m.memories={n.id:n for n in notes};m.retriever=d.Retriever()
    m.retriever.add_documents([n.content for n in notes])
    if indices is not None:m.retriever.search=lambda query,k=5:indices
class Encoder:
    def __init__(self,name):self.name=name
    def encode(self,texts):
        return np.array([[1.,0.] if x in ('a','query') else [0.,1.] for x in texts])
def cosine(a,b):
    a=np.asarray(a);b=np.asarray(b)
    aa=np.linalg.norm(a,axis=1,keepdims=True);bb=np.linalg.norm(b,axis=1,keepdims=True)
    return (a/np.maximum(aa,1e-12))@(b/np.maximum(bb,1e-12)).T
def main():
    m,r=system()
    check('empty_find_tuple_raw_list',m.find_related_memories('q')==('',[]) and m.find_related_memories_raw('q')==[])
    zero=note('z',importance_score=0.0,context='',category='')
    check('falsy_defaults_replace_zero',zero.importance_score==1.0 and zero.context=='General' and zero.category=='Uncategorized')
    tags=['initial'];n=note('alias',tags=tags);tags.append('external')
    check('provided_nonempty_tags_aliased',n.tags is tags and n.tags==['initial','external'])
    r=Response('not-json')
    check('analyze_invalid_json_returns_string',Note.analyze_content('test',NS(llm=r))=='not-json')
    error('constructor_invalid_analysis_string',lambda:Note('test',llm_controller=NS(llm=r)),TypeError)
    def explode(*a,**kw):raise RuntimeError('provider failure')
    error('analyze_provider_failure_unbound_response',lambda:Note.analyze_content('test',NS(llm=NS(get_completion=explode))),UnboundLocalError)
    r=Response(json.dumps(dict(keywords=['k'],context='ctx',tags=['t'])))
    n=Note('test',keywords=['fixed'],context='fixed',tags=['fixed'],llm_controller=NS(llm=r))
    check('missing_category_triggers_analysis',r.calls==1 and n.category=='Uncategorized' and n.context=='fixed')
    m,r=system();m.add_note('a',id='same',keywords=['a'],context='a',tags=['a'],category='test')
    m.add_note('b',id='same',keywords=['b'],context='b',tags=['b'],category='test')
    check('duplicate_id_breaks_alignment',len(m.memories)==1 and len(m.retriever.corpus)==2)
    obs['duplicate_id_counts']={'notes':len(m.memories),'documents':len(m.retriever.corpus)}
    error('duplicate_id_query_IndexError',lambda:m.find_related_memories('b'),IndexError)
    response={'should_evolve':True,'actions':[]}
    m,r=system(json.dumps(response),threshold=0)
    error('zero_threshold_after_partial_insert',lambda:m.add_note('a',id='zero',keywords=['a'],context='a',tags=['a'],category='test'),ZeroDivisionError)
    check('zero_threshold_mutations_remain','zero' in m.memories and len(m.retriever.corpus)==1 and m.evo_cnt==1)
    response={'should_evolve':True,'actions':['update_neighbor'],'new_context_neighborhood':[],'new_tags_neighborhood':[['changed']]}
    m,r=system(json.dumps(response));a=note('a');b=note('b');seed(m,[a,b],[1,0])
    label,n=m.process_memory(note('new'))
    check('short_tags_truncate_missing_context_fallback',label and b.tags==['changed'] and b.context=='original b' and a.tags==['cache'])
    response={'should_evolve':True,'actions':['merge','prune']}
    m,r=system(json.dumps(response));seed(m,[a],[0]);label,n=m.process_memory(note('new'))
    check('unknown_actions_ignored_but_evolve_true',label and n.links==[] and a.content=='a')
    response={'should_evolve':True,'actions':['update_neighbor','strengthen'],'new_context_neighborhood':['already changed'],'new_tags_neighborhood':[['changed']],'suggested_connections':None,'tags_to_update':[]}
    m,r=system(json.dumps(response));a=note('a');seed(m,[a],[0])
    error('later_action_failure_no_rollback',lambda:m.process_memory(note('new')),TypeError)
    check('previous_action_mutation_retained',a.context=='already changed' and a.tags==['changed'])
    m,r=system('{invalid');seed(m,[note('a')],[0])
    error('process_bad_json_propagates',lambda:m.process_memory(note('new')),json.JSONDecodeError)
    m,r=system();a=note('a');b=note('b',links=[-1]);seed(m,[a,b],[1])
    raw=m.find_related_memories_raw('q',1)
    check('negative_link_reads_last_note',raw.count('memory content: b')==2)
    b.links=[0,0,0];raw=m.find_related_memories_raw('q',1)
    check('duplicate_links_append_before_budget_check',raw.count('memory content: a')==2)
    b.links=[99]
    error('out_of_range_link_IndexError',lambda:m.find_related_memories_raw('q',1),IndexError)
    ns=dict(d.ns,np=np,os=os,pickle=pickle,SentenceTransformer=Encoder,cosine_similarity=cosine)
    d.classes(d.EVAL/'memory_layer.py',['SimpleEmbeddingRetriever'],ns)
    retriever=ns['SimpleEmbeddingRetriever']();docs=['a','b'];retriever.add_documents(docs)
    check('original_retriever_first_corpus_alias',retriever.corpus is docs and retriever.embeddings.shape==(2,2))
    original_zero=retriever.search('query',0).tolist();adapter=d.Retriever();adapter.add_documents(['a','b'])
    check('original_k_zero_returns_all_adapter_none',original_zero==[0,1] and adapter.search('query',0)==[])
    check('original_topk_indices_actual_ndarray',isinstance(retriever.search('query',1),np.ndarray) and retriever.search('query',1).tolist()==[0])
    obs['retriever']={'k0_original':original_zero,'k0_adapter':adapter.search('query',0),'embedding_shape':list(retriever.embeddings.shape),'cosine_shape':list(cosine([[1.,0.]],retriever.embeddings).shape)}
    retriever.add_documents(['a'])
    check('original_duplicate_document_map_last_position',len(retriever.corpus)==3 and retriever.document_ids['a']==2)
    signatures={}
    for owner,names in [(Note,['__init__','analyze_content']),(System,['__init__','add_note','consolidate_memories','process_memory','find_related_memories','find_related_memories_raw']),(ns['SimpleEmbeddingRetriever'],['__init__','add_documents','search','save','load','load_from_local_memory']),(d.Retriever,['__init__','encode','add_documents','search']),(d.Provider,['__init__','get_completion']),(d.LLMController,['__init__'])]:
        for name in names:signatures[owner.__name__+'.'+name]=str(inspect.signature(getattr(owner,name)))
    for name in ['classes','state','main']:signatures['demo.'+name]=str(inspect.signature(getattr(d,name)))
    result={'scope':'Original evaluation MemoryNote, AgenticMemorySystem, SimpleEmbeddingRetriever methods; controlled JSON/encoder/cosine collaborator, not MiniLM or provider schema validation',
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_sources':{str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [d.EVAL/'memory_layer.py',d.SYSTEM/'agentic_memory/memory_system.py']},
      'signatures':signatures,'checks_passed':checks,'observations':obs,'python':sys.version,'numpy':np.__version__}
    (P/'复现/outputs/contracts_trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    return 'PASS: {} boundary checks; {} signatures'.format(len(checks),len(signatures))
if __name__=='__main__':
    log=io.StringIO()
    with contextlib.redirect_stdout(log):result=main()
    (P/'复现/outputs/contracts_stdout.txt').write_text(log.getvalue(),encoding='utf8')
    print(result)