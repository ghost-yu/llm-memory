"""Original Graphiti temporal functions with controlled collaborators, no full Graphiti runtime."""
import ast, asyncio, hashlib, json, logging, sqlite3, sys, uuid
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from time import time
from types import SimpleNamespace as NS
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'代码'/'graphiti-historical';OUT=ROOT/'复现'/'outputs'
def dt(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
@dataclass
class EntityEdge:
    uuid:str
    name:str
    fact:str
    user:str
    value:str
    created_at:datetime
    valid_at:datetime|None=None
    invalid_at:datetime|None=None
    expired_at:datetime|None=None
@dataclass
class EpisodicNode:
    content:str
    valid_at:datetime
class LLMClient: pass
async def semaphore_gather(*tasks): return await asyncio.gather(*tasks)
clock=dt('2025-01-02T00:00:00Z')
def utc_now(): return clock
class PromptAdapter:
    def __init__(self,stage):self.stage=stage
    def __call__(self,context):return dict(stage=self.stage,context=context)
class Provider:
    def __init__(self):self.calls=[];self.dates={}
    async def generate_response(self,prompt,response_model=None):
        c=prompt['context'];stage=prompt['stage']
        if stage=='dates': response=self.dates[c['edge_fact']]
        elif stage=='duplicate':
            old=next((e for e in c['related_edges'] if e['fact']==c['extracted_edges']['fact']),None)
            response=dict(is_duplicate=old is not None,uuid=old['uuid'] if old else None)
        else: response=dict(invalidated_edges=[dict(uuid=e['uuid'],fact=e['fact']) for e in c['existing_edges'] if e['fact']!=c['new_edge']['fact']])
        self.calls.append(dict(stage=stage,context=c,response=response));return response
prompt_library=NS(extract_edge_dates=NS(v1=PromptAdapter('dates')),dedupe_edges=NS(edge=PromptAdapter('duplicate')),invalidate_edges=NS(v2=PromptAdapter('contradictions')))
EdgeDates=EdgeDuplicate=InvalidatedEdges=object
ns=dict(globals(),logger=logging.getLogger('zepdemo'))
SOURCES={}
def load(path,names):
    text=(REPO/path).read_text(encoding='utf-8');SOURCES[path]=hashlib.sha256((REPO/path).read_bytes()).hexdigest()
    nodes=[n for n in ast.parse(text).body if getattr(n,'name',None) in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(REPO/path),'exec'),ns)
load('graphiti_core/utils/datetime_utils.py',['ensure_utc'])
load('graphiti_core/utils/maintenance/temporal_operations.py',['extract_edge_dates','get_edge_contradictions'])
load('graphiti_core/utils/maintenance/edge_operations.py',['dedupe_extracted_edge','resolve_edge_contradictions','resolve_extracted_edge'])
load('graphiti_core/search/search_utils.py',['rrf'])
def serial(x):
    if isinstance(x,datetime):return x.isoformat()
    raise TypeError(type(x).__name__)
def snapshot(edges):return json.loads(json.dumps([asdict(e) for e in edges],default=serial))
def active_at(rows,date,user='alice'):
    q=dt(date);return [e['value'] for e in rows if e['user']==user and (e['valid_at'] is None or dt(e['valid_at'])<=q) and (e['invalid_at'] is None or q<dt(e['invalid_at']))]
async def main():
    global clock
    OUT.mkdir(exist_ok=True);provider=Provider();edges=[];snapshots=[];checks={}
    async def ingest(value,valid,received,user='alice'):
        global clock
        clock=dt(received);ns['clock']=clock;ns['utc_now']=lambda:clock
        fact=user+' lives in '+value;edge=EntityEdge(uuid.uuid4().hex,'LIVES_IN',fact,user,value,clock)
        provider.dates[fact]=dict(valid_at=valid,invalid_at=None)
        # Host selects same user/predicate candidates; this is not neural retrieval.
        candidates=[e for e in edges if e.user==user and e.name=='LIVES_IN']
        episode=EpisodicNode(fact,dt(valid))
        resolved,invalidated=await ns['resolve_extracted_edge'](provider,edge,candidates,candidates,episode,[])
        if all(e.uuid!=resolved.uuid for e in edges):edges.append(resolved)
        snapshots.append(dict(received=received,value=value,resolved=resolved.uuid,invalidated=[e.uuid for e in invalidated],edges=snapshot(edges)))
        return resolved
    beijing=await ingest('Beijing','2025-01-01T00:00:00Z','2025-01-02T00:00:00Z')
    shanghai=await ingest('Shanghai','2025-03-01T00:00:00Z','2025-03-02T00:00:00Z')
    hangzhou=await ingest('Hangzhou','2025-02-01T00:00:00Z','2025-04-01T00:00:00Z')
    checks['late_old_event_not_current']=hangzhou.invalid_at==shanghai.valid_at and shanghai.invalid_at is None
    checks['old_fact_closes_at_intermediate']=beijing.invalid_at==hangzhou.valid_at
    checks['expired_at_preserved_on_revision']=beijing.expired_at==dt('2025-03-02T00:00:00Z')
    n=len(edges);duplicate=await ingest('Shanghai','2025-03-01T00:00:00Z','2025-04-02T00:00:00Z')
    checks['duplicate_keeps_uuid_and_count']=duplicate.uuid==shanghai.uuid and len(edges)==n
    await ingest('Paris','2025-01-01T00:00:00Z','2025-04-03T00:00:00Z','bob')
    rows=snapshot(edges);querydates=['2025-01-15T00:00:00Z','2025-02-15T00:00:00Z','2025-03-15T00:00:00Z']
    answers=[active_at(rows,q) for q in querydates]
    checks['valid_time_answers']=answers==[['Beijing'],['Hangzhou'],['Shanghai']]
    checks['half_open_boundary']=active_at(rows,'2025-03-01T00:00:00Z')==['Shanghai']
    checks['group_scope']=active_at(rows,querydates[-1],'bob')==['Paris']
    before_late=active_at(snapshots[1]['edges'],'2025-02-15T00:00:00Z')
    checks['transaction_snapshot_changes_past_answer']=before_late==['Beijing'] and answers[1]==['Hangzhou']
    checks['historical_facts_retained']=len([e for e in rows if e['user']=='alice'])==3
    # Boundary/non-overlap and same-start limitations of original function.
    past=EntityEdge('past','LIVES_IN','old','test','old',clock,dt('2024-01-01T00:00:00Z'),dt('2025-01-01T00:00:00Z'))
    new=EntityEdge('new','LIVES_IN','new','test','new',clock,dt('2025-01-01T00:00:00Z'))
    checks['nonoverlap_not_invalidated']=ns['resolve_edge_contradictions'](new,[past])==[]
    equal=EntityEdge('equal','LIVES_IN','equal','test','equal',clock,new.valid_at)
    checks['equal_start_unresolved_observed']=ns['resolve_edge_contradictions'](new,[equal])==[] and equal.invalid_at is None
    provider.dates['bad']=dict(valid_at='not-a-date',invalid_at=None)
    bad=EntityEdge('bad','LIVES_IN','bad','test','bad',clock)
    parsed=await ns['extract_edge_dates'](provider,bad,EpisodicNode('bad',clock),[])
    checks['invalid_date_returns_none']=parsed==(None,None)
    ranking=ns['rrf']([['beijing','shanghai'],['hangzhou','shanghai'],['paris','shanghai']])
    checks['rrf_multi_list_agreement']=ranking==['shanghai','beijing','hangzhou','paris']
    # Shanghai score=1.5; others=1. Stable insertion order breaks remaining ties.
    dbpath=OUT/('temporal-'+uuid.uuid4().hex[:12]+'.sqlite');conn=sqlite3.connect(dbpath)
    conn.execute('CREATE TABLE snapshots(received TEXT, payload TEXT)')
    conn.executemany('INSERT INTO snapshots VALUES(?,?)',[(s['received'],json.dumps(s,ensure_ascii=False)) for s in snapshots]);conn.commit();conn.close()
    conn=sqlite3.connect(dbpath);restored=[json.loads(x[0]) for x in conn.execute('SELECT payload FROM snapshots ORDER BY rowid')];conn.close()
    checks['sqlite_snapshot_reopen_exact']=restored==snapshots
    result=dict(scope='Original temporal resolution and RRF functions; dataclass/prompt/provider/SQLite host replacements',commit='77cb67cdfea7a080f217236b56f8ca39b25ca0e4',python=sys.version,sources=SOURCES,checks=checks,snapshots=snapshots,final=rows,query_dates=querydates,answers=answers,before_late_answer=before_late,rrf_ranking=ranking,model_calls=provider.calls,database=dbpath.name,equal_start_limitation='Original strict valid_at comparison leaves equal-start contradictory edges unresolved')
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=serial),encoding='utf-8')
    assert all(checks.values()),checks
    print(json.dumps(dict(checks=checks,records=len(rows),controlled_calls=len(provider.calls)),indent=2))
if __name__=='__main__':asyncio.run(main())
