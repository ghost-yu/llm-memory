"""Original MemGPT bodies + isolated boundary probes; no model/API calls."""
import ast,hashlib,importlib.util,inspect,json,platform,tempfile
from pathlib import Path
from types import SimpleNamespace,MethodType
P=Path(__file__).resolve().parents[2];SOURCE=P/'复现/scripts/demo_memgpt.py'
spec=importlib.util.spec_from_file_location('memgpt_demo_trace',SOURCE)
demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
def main():
    symbols,sources=demo.load_original_symbols();Core=symbols['CoreMemory']
    core=Core('P','abc abc',20,20)
    length=core.edit_replace('human','abc','x');assert length==3 and core.human=='x x'
    errors={}
    for name,args in [('empty_old',('human','','z')),('missing_old',('human','missing','z')),('bad_field',('other','x','z'))]:
        old=core.to_dict()
        try:core.edit_replace(*args)
        except (ValueError,KeyError) as exc:errors[name]={'type':type(exc).__name__,'message':str(exc)}
        else:raise AssertionError(name)
        assert core.to_dict()==old
    try:core.edit_human('x'*21)
    except ValueError:pass
    else:raise AssertionError('overflow accepted')
    assert core.human=='x x'
    loaded=Core.load(core.to_dict());assert loaded.human_char_limit is None
    assert loaded.edit_human('x'*21)==21
    original_memory=demo.REPO/'memgpt/memory.py'
    tree=ast.parse(original_memory.read_text(encoding='utf8'))
    owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EmbeddingArchivalMemory')
    method=next(n for n in owner.body if isinstance(n,ast.FunctionDef) and n.name=='search')
    namespace={'get_local_time':lambda:'probe-time'}
    exec(compile(ast.Module(body=[method],type_ignores=[]),str(original_memory),'exec'),namespace)
    fake=SimpleNamespace(cache={'probe':[SimpleNamespace(text='item '+str(i)) for i in range(12)]},top_k=100)
    fake.search=MethodType(namespace['search'],fake)
    rows,total=fake.search('probe',count=5,start=0)
    assert len(rows)==5 and total==5
    host_stub=SimpleNamespace(persistence_manager=SimpleNamespace(archival_memory=fake))
    page0=symbols['archival_memory_search'](host_stub,'probe',0)
    page1=symbols['archival_memory_search'](host_stub,'probe',1)
    assert '(page 0/0)' in page0 and 'item 5' in page1
    probes={}
    with tempfile.TemporaryDirectory(prefix='memgpt-contract-') as folder:
        folder=Path(folder);host=demo.OfflineHost(symbols,folder/'probe.sqlite')
        for i in range(12):host.store.insert('probe item '+str(i))
        text,ok=host.call('archival_memory_search',{'query':'probe','page':0},False)
        assert ok and '(page 0/2)' in text
        text1,ok=host.call('archival_memory_search',{'query':'probe','page':'1'},True)
        assert ok and len(demo.result_rows(text1))==5
        bad,ok=host.call('archival_memory_search',{'query':'probe','page':'bad'},False)
        assert not ok and host.trace[-1]['next_event']=='heartbeat'
        empty,ok=host.call('archival_memory_search',{'query':'no-hit'},False)
        assert ok and empty=='No results found.'
        value,ok=host.call('core_memory_append',{'name':'human','content':'Fact'},False)
        assert ok and value is None and host.trace[-1]['next_event']=='yield'
        # A tool result enters recall/queue, with a paired atomic block.
        assert host.trace[-1] in host.queue and 'Fact' in host.context()
        host.save(folder/'state.json');state=json.loads((folder/'state.json').read_text(encoding='utf8'))
        host.store.close();reload=demo.OfflineHost(symbols,folder/'probe.sqlite');reload.restore(folder/'state.json')
        assert reload.memory.to_dict()==state['core'] and reload.memory.human_char_limit==200
        probes={'adapter_page0':text,'adapter_page1_count':len(demo.result_rows(text1)),'invalid_page_message':bad,'saved_keys':list(state),'limits_restored_by_custom_constructor':True}
        reload.store.close()
    agent_tree=ast.parse((demo.REPO/'memgpt/agent.py').read_text(encoding='utf8'))
    agent=next(n for n in agent_tree.body if isinstance(n,ast.ClassDef) and n.name=='Agent')
    step=next(n for n in agent.body if isinstance(n,ast.FunctionDef) and n.name=='step')
    return_lengths=[len(n.value.elts) for n in ast.walk(step) if isinstance(n,ast.Return) and isinstance(n.value,ast.Tuple)]
    assert 5 in return_lengths
    objects={}
    for name in ['__init__','__repr__','to_dict','load','edit_persona','edit_human','edit','edit_append','edit_replace']:
        objects['CoreMemory.'+name]=str(inspect.signature(getattr(Core,name)))
    for name in ['core_memory_append','core_memory_replace','conversation_search','archival_memory_insert','archival_memory_search']:objects[name]=str(inspect.signature(symbols[name]))
    for cls,names in [(demo.SQLiteStore,['__init__','add','query','insert','search','text_search','close']),(demo.OfflineHost,['__init__','rebuild_memory','context','append','event','call','save','restore'])]:
        for name in names:objects[cls.__name__+'.'+name]=str(inspect.signature(getattr(cls,name)))
    for name in ['load_original_symbols','result_rows','solve','main']:objects['demo.'+name]=str(inspect.signature(getattr(demo,name)))
    checks=['replace all matches','empty replacement rejected','missing replacement rejected','invalid field rejected','overflow preserves state','CoreMemory.load drops limits observed','raw historical search total equals page length observed','raw backend manual next page exists','original tool page header mismatch observed','SQLite adapter supplies full total','string page coercion','invalid page triggers heartbeat','empty query result success','None tool return success','tool reply enters context','JSON/SQLite reopen','custom restore preserves limits','Agent.step actual five-item tuple']
    result={'scope':'isolated original-body and adapter contracts; no full Agent, model or embedding backend',
      'environment':{'python':platform.python_version(),'stdlib_only':True},'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'original_sources':sources,'signatures':objects,
      'errors':errors,'historical_archival_search':{'cached_candidates':12,'returned_rows':5,'returned_total':total,'page0_header':page0.split(':',1)[0],'page1_manual':page1,'boundary':'cached fake passages; actual original search/tool bodies, no vector retrieval'},
      'CoreMemory_load_human_char_limit':loaded.human_char_limit,'adapter_probes':probes,'Agent_step_return_tuple_lengths':return_lengths,'checks_passed':checks}
    (P/'复现/outputs/contracts_trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(checks),'contract/boundary checks;',len(objects),'actual signatures')
if __name__=='__main__':main()
