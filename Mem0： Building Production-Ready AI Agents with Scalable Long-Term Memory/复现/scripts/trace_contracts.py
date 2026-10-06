"""Mem0 original method contracts with local providers; no real model/API."""
import hashlib,importlib.util,inspect,json,tempfile
from pathlib import Path
P=Path(__file__).resolve().parents[2];SOURCE=P/'复现/scripts/demo_mem0.py'
spec=importlib.util.spec_from_file_location('mem0_demo_trace',SOURCE)
demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
def main():
    signatures={}
    for name in demo.METHODS:signatures['Memory.'+name]=str(inspect.signature(getattr(demo.Memory,name)))
    for name in ['parse_messages','get_fact_retrieval_messages','remove_code_blocks','parse_vision_messages']:
        signatures[name]=str(inspect.signature(demo.ns[name]))
    for owner,names in [(demo.ns['SQLiteManager'],['__init__','add_history','get_history']),(demo.Embedder,['embed']),(demo.Vectors,['__init__','insert','snapshot','get','update','delete','search']),(demo.Provider,['__init__','generate_response'])]:
        for name in names:signatures[owner.__name__+'.'+name]=str(inspect.signature(getattr(owner,name)))
    for name in ['load','setup','main']:signatures['demo.'+name]=str(inspect.signature(getattr(demo,name)))
    checks=[];observations={}
    with tempfile.TemporaryDirectory(prefix='mem0-contract-') as tmp:
        tmp=Path(tmp);m=demo.setup(tmp/'vectors.sqlite',tmp/'history.sqlite')
        metadata={'custom':'original'};filters={'tag':'one'}
        first=m.add('city=Beijing',user_id='alice',metadata=metadata,filters=filters)['results'][0]['id']
        assert filters=={'tag':'one','user_id':'alice'}
        assert metadata['user_id']=='alice' and metadata['data']=='city=Beijing'
        assert m.vector_store.get(first).payload['custom']=='original'
        checks.extend(['add mutates supplied filters','create mutates supplied metadata'])
        # No tag filter on this update: same user record is retrieved.
        created=m.vector_store.get(first).payload['created_at']
        update=m.add('city=Hangzhou',user_id='alice')
        assert update['results'][0]['id']==first
        payload=m.vector_store.get(first).payload
        assert payload['created_at']==created and 'custom' not in payload
        checks.extend(['update preserves ID/time','update drops unprovided custom metadata'])
        calls=len(m.llm.calls);before=m.vector_store.snapshot()
        duplicate=m.add('city=Hangzhou',user_id='alice')
        assert duplicate['results']==[] and m.vector_store.snapshot()==before and len(m.llm.calls)==calls+2
        checks.append('NONE still uses both provider stages')
        calls=len(m.llm.calls);bad=m.add('BAD_JSON',user_id='alice')
        assert bad['results']==[] and m.vector_store.snapshot()==before and len(m.llm.calls)==calls+2
        checks.append('bad extraction still enters update stage')
        try:m.search('city')
        except ValueError:checks.append('missing scope rejected')
        else:raise AssertionError('unscoped search accepted')
        empty_scope=m.search('city',filters={'user_id':None})
        assert empty_scope=={'results':[]};checks.append('None-valued scope key accepted observed')
        v=demo.Embedder().embed('中文123');assert len(v)==64 and all(x==0 for x in v)
        low=m.search('中文123',user_id='alice');assert len(low['results'])==1 and low['results'][0]['score']==0
        checks.extend(['non-Latin query maps to zero vector','zero score still returned by adapter'])
        # Raw writes skip system, preserve other roles, and do not call Provider.
        n=len(m.llm.calls);raw=m.add([{'role':'system','content':'skip'},{'role':'assistant','content':'keep'}],user_id='raw',infer=False)
        assert len(raw['results'])==1 and raw['results'][0]['memory']=='keep' and len(m.llm.calls)==n
        checks.append('infer False skips system only and provider')
        # Controlled invalid ID followed by ADD: original catch continues the loop.
        provider=m.llm
        class Scripted:
            def __init__(self):self.n=0
            def generate_response(self,messages,response_format=None):
                self.n+=1
                if self.n==1:return json.dumps({'facts':['city=Osaka']})
                return json.dumps({'memory':[{'id':'99','text':'city=Osaka','event':'UPDATE'},{'id':'new','text':'hobby=walking','event':'ADD'}]})
        m.llm=Scripted();partial=m.add('ignored',user_id='alice')
        assert [x['event'] for x in partial['results']]==['ADD']
        assert m.vector_store.get(first).payload['data']=='city=Hangzhou'
        checks.append('invalid action ID skipped while later ADD succeeds')
        m.llm=provider
        history=m.db.get_history(first);assert 'is_deleted' not in history[0]
        checks.append('history API omits is_deleted')
        observations={'mutated_filters':filters,'mutated_metadata':metadata,'updated_payload':payload,'empty_scope_result':empty_scope,'zero_query_results':low,'partial_actions_result':partial,'provider_stage_cost_duplicate':2,'provider_stage_cost_BAD_JSON':2}
        m.vector_store.conn.close();m.db.connection.close()
        m=demo.setup(tmp/'split-v.sqlite',tmp/'split-h.sqlite')
        db=m.db
        class FailHistory:
            def add_history(self,*args,**kwargs):raise RuntimeError('injected history failure')
        m.db=FailHistory()
        try:m._create_memory('city=Tokyo',{},metadata={'user_id':'test'})
        except RuntimeError:pass
        else:raise AssertionError('history injection ignored')
        assert len(m.vector_store.snapshot())==1 and db.connection.execute('SELECT COUNT(*) FROM history').fetchone()[0]==0
        checks.append('vector write survives subsequent history failure')
        observations['history_failure']={'vector_records':1,'history_records':0,'boundary':'controlled failure, isolated temp databases'}
        m.vector_store.conn.close();db.connection.close()
    result={'scope':'original Mem0 methods with controlled providers and SQLite adapters; no natural-language quality or paper benchmark','source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'original_sources':{p:hashlib.sha256((demo.REPO/p).read_bytes()).hexdigest() for p in demo.FILES},'signatures':signatures,'observations':observations,'checks_passed':checks}
    (P/'复现/outputs/contracts_trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(checks),'contract/boundary checks;',len(signatures),'actual signatures')
if __name__=='__main__':main()
