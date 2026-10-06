"""Execute isolated original functions; controlled responses are not LLM inference."""
import asyncio, hashlib, importlib.util, inspect, json, sys
from datetime import datetime, timezone
from pathlib import Path
P=Path(__file__).resolve().parents[2]
source=P/'复现/scripts/demo_zep.py'
spec=importlib.util.spec_from_file_location('zep_contract_demo',source)
d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
checks={};observations={}
def check(name,value):
    assert value,name
    checks[name]=bool(value)
class Scripted:
    def __init__(self,responses):self.responses=responses;self.calls=[]
    async def generate_response(self,prompt,response_model=None):
        self.calls.append(prompt['stage']);return self.responses[prompt['stage']]
def edge(uid,fact='old',valid='2025-01-01T00:00:00Z',end=None):
    return d.EntityEdge(uid,'LIVES_IN',fact,'alice',fact,d.clock,d.dt(valid) if valid else None,d.dt(end) if end else None)
async def main():
    ensure=d.ns['ensure_utc'];rrf=d.ns['rrf']
    naive=datetime(2025,1,1,8)
    converted=ensure(d.dt('2025-01-01T08:00:00+08:00'))
    check('UTC_offset_converted',converted==d.dt('2025-01-01T00:00:00Z'))
    check('naive_assumed_UTC',ensure(naive)==d.dt('2025-01-01T08:00:00Z'))
    check('UTC_identity_and_None',ensure(d.clock) is d.clock and ensure(None) is None)
    observations['timezone']={'offset_result':converted.isoformat(),'naive_result':ensure(naive).isoformat()}
    old=edge('old');new=edge('new','new','2025-02-01T00:00:00Z')
    before=d.snapshot([old]);invalid=d.ns['resolve_edge_contradictions'](new,[old])
    check('in_place_and_deep_snapshot',invalid[0] is old and old.invalid_at==new.valid_at and before[0]['invalid_at'] is None)
    old.expired_at=d.dt('2025-01-02T00:00:00Z')
    newer=edge('newer','newer','2025-03-01T00:00:00Z')
    d.ns['resolve_edge_contradictions'](newer,[old])
    check('nonoverlap_preserves_fields',old.invalid_at==new.valid_at and old.expired_at==d.dt('2025-01-02T00:00:00Z'))
    equal=edge('equal','equal',valid='2025-02-01T00:00:00Z')
    check('equal_start_not_resolved',d.ns['resolve_edge_contradictions'](new,[equal])==[] and equal.invalid_at is None)
    p=Scripted({'duplicate':{'is_duplicate':True,'uuid':old.uuid}})
    check('dedupe_returns_existing_identity',await d.ns['dedupe_extracted_edge'](p,new,[old]) is old)
    p=Scripted({'duplicate':{'is_duplicate':True,'uuid':'missing'}})
    check('unknown_duplicate_uuid_falls_back',await d.ns['dedupe_extracted_edge'](p,new,[old]) is new)
    ended=edge('ended',end='2024-12-31T00:00:00Z',valid='2024-01-01T00:00:00Z')
    p=Scripted({'contradictions':{'invalidated_edges':[{'uuid':'missing','fact':'ignored'},{'uuid':'ended','fact':'rewritten by response'}]}})
    candidates=await d.ns['get_edge_contradictions'](p,new,[ended])
    check('unknown_contradiction_ignored_known_fact_mutated',len(candidates)==1 and candidates[0] is ended and ended.fact=='rewritten by response')
    check('nonoverlap_does_not_undo_fact_mutation',d.ns['resolve_edge_contradictions'](new,candidates)==[] and ended.fact=='rewritten by response')
    observations['nonoverlap_fact_mutation']=d.snapshot([ended])[0]
    p=Scripted({'dates':{'valid_at':123,'invalid_at':None}})
    try:
        await d.ns['extract_edge_dates'](p,new,d.EpisodicNode('new',d.clock),[])
    except AttributeError as ex:
        observations['wrong_date_type_error']=type(ex).__name__+': '+str(ex)
    else:raise AssertionError('integer date accepted')
    check('integer_date_not_caught_as_ValueError','AttributeError' in observations['wrong_date_type_error'])
    old=edge('duplicate','same',end='2025-02-01T00:00:00Z');old.expired_at=d.clock
    new=edge('newdup','same')
    p=Scripted({'duplicate':{'is_duplicate':True,'uuid':old.uuid},'dates':{'valid_at':None,'invalid_at':None},'contradictions':{'invalidated_edges':[]}})
    resolved,invalid=await d.ns['resolve_extracted_edge'](p,new,[old],[old],d.EpisodicNode('same',d.clock),[])
    check('None_dates_preserve_existing_interval',resolved is old and resolved.invalid_at==d.dt('2025-02-01T00:00:00Z') and invalid==[])
    observations['duplicate_retained_interval']=d.snapshot([resolved])[0]
    observations['parallel_stages']=p.calls
    check('three_stages_run_even_duplicate',sorted(p.calls)==['contradictions','dates','duplicate'])
    check('rrf_empty_and_stable_ties',rrf([])==[] and rrf([['b'],['a']])==['b','a'])
    check('rrf_repeated_id_counts_again',rrf([['a','a'],['b']])==['a','b'])
    try:rrf([['a']],rank_const=0)
    except ZeroDivisionError as ex:observations['rank_const_zero_error']=type(ex).__name__
    else:raise AssertionError('rank_const=0 accepted')
    check('rrf_zero_rank_const_fails',observations['rank_const_zero_error']=='ZeroDivisionError')
    names=['ensure_utc','extract_edge_dates','get_edge_contradictions','dedupe_extracted_edge','resolve_edge_contradictions','resolve_extracted_edge','rrf']
    signatures={name:str(inspect.signature(d.ns[name])) for name in names}
    for name in ['dt','serial','snapshot','active_at','load','semaphore_gather','utc_now']:
        signatures['demo.'+name]=str(inspect.signature(getattr(d,name)))
    for owner,names in [(d.EntityEdge,['__init__']),(d.EpisodicNode,['__init__']),(d.PromptAdapter,['__init__','__call__']),(d.Provider,['__init__','generate_response'])]:
        for name in names:signatures[owner.__name__+'.'+name]=str(inspect.signature(getattr(owner,name)))
    output={'scope':'Original seven functions with controlled interface replacements; no Graphiti package import or LLM inference',
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_sources':d.SOURCES,
      'signatures':signatures,'checks_passed':checks,'observations':observations,'python':sys.version}
    (P/'复现/outputs/contracts_trace.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(checks),'boundary checks;',len(signatures),'signatures')
if __name__=='__main__':asyncio.run(main())
