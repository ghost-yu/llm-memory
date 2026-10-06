"""Execute official classes via AST with controlled LLM and hash-vector retrieval."""
import ast, contextlib, hashlib, io, json, logging, math, re, sys, uuid
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS
from typing import List, Dict, Optional, Any, Tuple
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'复现'/'outputs'
EVAL=ROOT/'代码'/'A-mem-historical';SYSTEM=ROOT/'代码'/'A-mem-sys-historical'
class Retriever:
    def __init__(self,model_name='offline-hash'):
        self.corpus=[];self.embeddings=[];self.model=NS(get_config_dict=lambda:dict(model_name='offline-hash'))
    def encode(self,text):
        v=[0.0]*128
        for token in re.findall('[a-z]+',text.lower()):v[int(hashlib.sha256(token.encode()).hexdigest()[:8],16)%128]+=1
        norm=math.sqrt(sum(x*x for x in v)) or 1;return [x/norm for x in v]
    def add_documents(self,docs):
        self.corpus.extend(docs);self.embeddings.extend(self.encode(x) for x in docs)
    def search(self,query,k=5):
        q=self.encode(query);return sorted(range(len(self.corpus)),key=lambda i:(-sum(a*b for a,b in zip(q,self.embeddings[i])),i))[:k]
class Provider:
    def __init__(self):self.calls=[];self.evolutions=0
    def get_completion(self,prompt,response_format=None,**kw):
        if 'Content for analysis:' in prompt:
            content=prompt.split('Content for analysis:',1)[1].strip();cache='cache' in content
            response=dict(keywords=['cache','storage','web'] if cache else ['painting','art','hobby'],context='cache storage for web' if cache else 'art painting hobby',tags=['software','cache','storage'] if cache else ['art','painting','hobby']);stage='analyze'
        else:
            self.evolutions+=1;go=self.evolutions==3
            response=dict(should_evolve=go,actions=['strengthen','update_neighbor'] if go else [],suggested_connections=[1] if go else [],tags_to_update=['cache','LRU','eviction'] if go else [],new_context_neighborhood=['cache uses LRU eviction','art painting hobby'] if go else [],new_tags_neighborhood=[['cache','LRU','eviction'],['art','painting','hobby']] if go else []);stage='evolve'
        self.calls.append(dict(stage=stage,prompt=prompt,response=response));return json.dumps(response)
class LLMController:
    def __init__(self,*a,**kw):self.llm=Provider()
ns=dict(globals(),SimpleEmbeddingRetriever=Retriever,logger=logging.getLogger('amemdemo'))
def classes(path,names,namespace):
    nodes=[n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.ClassDef) and n.name in names]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
source=EVAL/'memory_layer.py';classes(source,['MemoryNote','AgenticMemorySystem'],ns)
def state(m):return [dict(vars(n)) for n in m.memories.values()]
def main():
    OUT.mkdir(exist_ok=True);checks={};steps=[];m=ns['AgenticMemorySystem'](model_name='offline-hash',evo_threshold=100)
    art=m.add_note('Alice enjoys art painting',time='202501011000',id='art')
    steps.append(dict(stage='art',notes=state(m)))
    cache=m.add_note('Alice built a cache storage for web',time='202501021000',id='cache')
    original_content=m.memories[cache].content;old_document=m.retriever.corpus[1]
    steps.append(dict(stage='cache',notes=state(m)))
    neighbors=m.find_related_memories('cache LRU eviction')[1];checks['noninsertion_neighbor_order']=neighbors==[1,0]
    new=m.add_note('Alice added LRU eviction to the cache',time='202501031000',id='lru')
    checks['attributes_generated']=bool(m.memories[new].keywords) and bool(m.memories[new].tags)
    checks['new_link_to_cache']=m.memories[new].links==[1]
    checks['target_neighbor_evolved']=m.memories[cache].context=='cache uses LRU eviction' and 'LRU' in m.memories[cache].tags
    checks['unrelated_neighbor_unchanged']=m.memories[art].context=='art painting hobby'
    checks['raw_content_preserved']=m.memories[cache].content==original_content
    checks['stale_index_before_consolidation_observed']=m.retriever.corpus[1]==old_document and 'eviction' not in m.retriever.corpus[1]
    seed=m.retriever.search('eviction',1);raw=m.find_related_memories_raw('eviction',k=1)
    checks['linked_memory_expands_seed']=seed==[2] and original_content in raw and m.memories[new].content in raw
    steps.append(dict(stage='evolved_before_consolidation',notes=state(m),corpus=list(m.retriever.corpus),retrieved_text=raw))
    m.consolidate_memories();checks['consolidation_refreshes_document']='LRU eviction' in m.retriever.corpus[1]
    checks['index_note_count_alignment']=len(m.retriever.corpus)==len(m.memories)==3
    checks['evolution_history_not_populated_observed']=m.memories[cache].evolution_history==[]
    final=state(m);persist=OUT/('notes-'+uuid.uuid4().hex[:12]+'.json');persist.write_text(json.dumps(dict(notes=final,corpus=m.retriever.corpus),ensure_ascii=False,indent=2),encoding='utf-8')
    stored=json.loads(persist.read_text(encoding='utf-8'));m2=ns['AgenticMemorySystem']();m2.memories={x['id']:ns['MemoryNote'](**x) for x in stored['notes']};m2.retriever=Retriever();m2.retriever.add_documents(stored['corpus'])
    checks['host_state_reload_exact']=state(m2)==final and m2.find_related_memories_raw('eviction',1)==m.find_related_memories_raw('eviction',1)
    # System repository negative observations: rank positions are used as insertion indices.
    syspath=SYSTEM/'agentic_memory'/'memory_system.py';tree=ast.parse(syspath.read_text(encoding='utf-8'));sn=dict(globals(),logger=logging.getLogger('systemcheck'))
    classes(syspath,['MemoryNote'],sn)
    owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AgenticMemorySystem')
    names=['find_related_memories','process_memory','search_agentic']
    exec(compile(ast.Module(body=[n for n in owner.body if getattr(n,'name',None) in names],type_ignores=[]),str(syspath),'exec'),sn)
    S=type('OriginalSystemSelectedMethods',(),{n:sn[n] for n in names});sysm=S()
    sysm.memories={x:sn['MemoryNote'](content=x,context=x,id=x,tags=[x],keywords=[x]) for x in ['art','cache']}
    metadata=dict(content='cache',context='cache',keywords=['cache'],tags=['cache'])
    sysm.retriever=NS(search=lambda q,k:dict(ids=[['cache']],metadatas=[[metadata]],distances=[[0.0]]))
    sysm._evolution_system_prompt='{context} {content} {keywords} {nearest_neighbors_memories} {neighbor_number}'
    response=dict(should_evolve=True,actions=['update_neighbor'],suggested_connections=[],tags_to_update=[],new_context_neighborhood=['evolved_cache'],new_tags_neighborhood=[['LRU']])
    sysm.llm_controller=NS(llm=NS(get_completion=lambda *a,**kw:json.dumps(response)))
    sysm.process_memory(sn['MemoryNote']('new',context='new',keywords=['new']))
    checks['system_rank_index_mismatch_observed']=sysm.memories['art'].context=='evolved_cache' and sysm.memories['cache'].context=='cache'
    sysm.memories['lru']=sn['MemoryNote']('lru',id='lru',links=['cache'])
    sysm.retriever=NS(search=lambda q,k:dict(ids=[['lru']],metadatas=[[dict(content='lru')]],distances=[[0.0]]))
    sys_result=sysm.search_agentic('LRU',k=1)
    checks['system_full_seed_budget_drops_links_observed']=[x['id'] for x in sys_result]==['lru']
    result=dict(scope='Original evaluation MemoryNote/AgenticMemorySystem classes with replaced LLMController/SimpleEmbeddingRetriever; selected system methods for negative checks',python=sys.version,commits=dict(evaluation='c3bb1ee6d4825b13460dd26be1444b5f870ddb64',system='aec6d34c6035d3a8f56df37d741f25e3adcecfea'),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,syspath]},checks=checks,steps=steps,final=final,refreshed_corpus=m.retriever.corpus,model_calls=m.llm_controller.llm.calls,seed_indices=seed,linked_retrieved_text=raw,system_wrong_update={x:n.context for x,n in sysm.memories.items()},system_search_result=sys_result,state_file=persist.name)
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');assert all(checks.values()),checks
    return dict(checks=checks,notes=len(final),controlled_calls=len(result['model_calls']))
if __name__=='__main__':
    log=io.StringIO()
    with contextlib.redirect_stdout(log):summary=main()
    (OUT/'original_stdout.txt').write_text(log.getvalue(),encoding='utf-8');print(json.dumps(summary,indent=2))
