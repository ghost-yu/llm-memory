"""Historical MemGPT core/tool bodies + offline deterministic controller + SQLite.
Not an LLM, not the full historical Agent runtime, not original paper accuracy.
"""
import ast,json,math,sqlite3,random,uuid,re,hashlib,platform
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'代码/MemGPT-historical'
OUT=ROOT/'复现/outputs'
SHA='a0139b5fdc203f827168cb741c9f4fea3cec09bf'


def load_original_symbols():
    namespace={'Optional':Optional,'math':math,'json':json,'RETRIEVAL_QUERY_DEFAULT_PAGE_SIZE':5,'JSON_ENSURE_ASCII':False}
    specs=[('memgpt/memory.py',{'CoreMemory'}),('memgpt/functions/function_sets/base.py',{'core_memory_append','core_memory_replace','conversation_search','archival_memory_insert','archival_memory_search'})]
    sources=[]
    for name,wanted in specs:
        path=REPO/name;content=path.read_text(encoding='utf8');tree=ast.parse(content)
        nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in wanted]
        assert {n.name for n in nodes}==wanted
        # Keep original AST bodies unchanged; skip module imports requiring full runtime.
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),namespace)
        sources.append({'path':name,'symbols':sorted(wanted),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return namespace,sources


class SQLiteStore:
    def __init__(self,path):
        self.conn=sqlite3.connect(path)
        self.conn.execute('CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, kind TEXT, role TEXT, content TEXT, timestamp TEXT)')
    def add(self,kind,content,role='user'):
        self.conn.execute('INSERT INTO records(kind,role,content,timestamp) VALUES(?,?,?,?)',(kind,role,content,'2024-02-12 12:00:00'))
        self.conn.commit()
    def query(self,kind,query,count,start):
        where='kind=? AND instr(lower(content),lower(?))>0'
        total=self.conn.execute('SELECT COUNT(*) FROM records WHERE '+where,(kind,query)).fetchone()[0]
        rows=self.conn.execute('SELECT role,content,timestamp FROM records WHERE '+where+' ORDER BY id LIMIT ? OFFSET ?',(kind,query,count,start)).fetchall()
        return rows,total
    def insert(self,content):self.add('archive',content)
    def search(self,query,count=5,start=0):
        rows,total=self.query('archive',query,count,start)
        return [{'timestamp':t,'content':c} for role,c,t in rows],total
    def text_search(self,query,count=5,start=0):
        rows,total=self.query('recall',query,count,start)
        return [{'timestamp':t,'message':{'role':role,'content':c}} for role,c,t in rows],total
    def close(self):self.conn.close()


class OfflineHost:
    def __init__(self,symbols,db,budget=1200):
        self.symbols=symbols;self.store=SQLiteStore(db);self.budget=budget
        self.memory=symbols['CoreMemory'](persona='Research assistant.',human='',persona_char_limit=100,human_char_limit=200)
        self.persistence_manager=SimpleNamespace(recall_memory=self.store,archival_memory=self.store)
        self.instructions='Memory tools are available. This is a deterministic controller, not an LLM.'
        self.queue=[];self.summary='';self.evicted=0;self.warnings=0;self.rebuilds=0;self.max_chars=0;self.trace=[]
    def rebuild_memory(self):self.rebuilds+=1
    def context(self):return self.instructions+repr(self.memory)+self.summary+json.dumps(self.queue,ensure_ascii=False)
    def append(self,block,role='tool'):
        text=json.dumps(block,ensure_ascii=False);self.store.add('recall',text,role)
        self.queue.append(block)
        if len(self.context())>.75*self.budget:self.warnings+=1
        # Each tool call+reply is one atomic block; do not split it when evicting.
        while len(self.context())>self.budget and self.queue:
            self.queue.pop(0);self.evicted+=1
            self.summary='Evicted '+str(self.evicted)+' blocks. Details remain in recall storage.'
        assert len(self.context())<=self.budget
        self.max_chars=max(self.max_chars,len(self.context()))
    def event(self,text):self.append({'role':'user','content':text},'user')
    def call(self,name,args,request_heartbeat=True):
        try:result=self.symbols[name](self,**args);success=True
        except Exception as e:result=str(e);success=False
        block={'name':name,'args':args,'result':result,'success':success,'request_heartbeat':request_heartbeat,'next_event':'heartbeat' if request_heartbeat or not success else 'yield'}
        self.trace.append(block);self.append(block)
        return result,success
    def save(self,path):
        path.write_text(json.dumps({'core':self.memory.to_dict(),'queue':self.queue,'summary':self.summary,'budget_chars':self.budget},ensure_ascii=False,indent=2),encoding='utf8')
    def restore(self,path):
        s=json.loads(path.read_text(encoding='utf8'));self.memory=self.symbols['CoreMemory'](persona=s['core']['persona'],human=s['core']['human'],persona_char_limit=100,human_char_limit=200)
        self.queue=s['queue'];self.summary=s['summary'];assert len(self.context())<=self.budget


def result_rows(text):
    return json.loads(text[text.index('['):]) if text.startswith('Showing ') else []


def solve(host,start,paginate=True,max_calls=100):
    current=start;calls=0;steps=[];seen=set()
    for hop in range(12):
        if current in seen:return None,calls,steps
        seen.add(current);page=0;found=None
        while True:
            if calls>=max_calls:return None,calls,steps
            text,ok=host.call('archival_memory_search',{'query':current,'page':page},True);calls+=1
            steps.append({'key':current,'page':page,'result':text})
            if not ok:return None,calls,steps
            for row in result_rows(text):
                match=re.search(r'Key: ([0-9a-f-]{36}); Value: ([0-9a-f-]{36})',row)
                if match and match.group(1)==current:found=match.group(2);break
            if found is not None:break
            pages=re.search(r'\(page \d+/(\d+)\)',text)
            if not paginate or not pages or page>=int(pages.group(1)):break
            page+=1
        if found is None:return current,calls,steps
        current=found
    return None,calls,steps


def main():
    OUT.mkdir(exist_ok=True)
    # Use a fresh uniquely named DB; preserve earlier run DBs if any.
    db=OUT/('memory-'+uuid.uuid4().hex[:8]+'.sqlite')
    symbols,sources=load_original_symbols();host=OfflineHost(symbols,db)
    host.call('core_memory_append',{'name':'human','content':'City: Beijing'},False)
    host.call('core_memory_replace',{'name':'human','old_content':'City: Beijing','new_content':'City: Hangzhou'},False)
    before=host.memory.human
    error,ok=host.call('core_memory_append',{'name':'human','content':'X'*300},True)
    assert not ok and host.memory.human==before
    # Explicit error recovery: move long notes to archive, do not overfill core.
    host.call('archival_memory_insert',{'content':'Long note: '+'X'*300},False)
    host.event('Project Aster secret code is K4P-8276.')
    for i in range(40):host.event('Filler discussion '+str(i)+': '+'routine details '*5)
    fifo_answer_available='K4P-8276' in host.context();assert not fifo_answer_available
    recall,ok=host.call('conversation_search',{'query':'Aster secret','page':0},True)
    assert ok and 'K4P-8276' in recall
    example_recall={'fifo_has_answer_before_search':fifo_answer_available,'result':recall,'result_reentered_context':'K4P-8276' in host.context()}
    rng=random.Random(2026);runs=[]
    for depth in [1,2,3,4]:
        for trial in range(5):
            chain=[str(uuid.UUID(int=rng.getrandbits(128))) for _ in range(depth+1)]
            for k,v in zip(chain,chain[1:]):
                # Seven mentions put the real Key record on a later search page.
                for j in range(7):host.call('archival_memory_insert',{'content':'Mention '+k+' unrelated note '+str(j)},False)
                host.call('archival_memory_insert',{'content':'Key: '+k+'; Value: '+v},False)
            for i in range(20):host.event('Noise after archive upload '+str(i)+' '+'routine '*10)
            fifo_contains_gold=chain[-1] in host.context();assert not fifo_contains_gold
            first,n_first,_=solve(host,chain[0],paginate=False)
            one,n_one,_=solve(host,chain[0],paginate=True,max_calls=1)
            full,n_full,steps=solve(host,chain[0],paginate=True)
            assert full==chain[-1]
            runs.append({'depth_links':depth,'trial':trial,'start':chain[0],'gold':chain[-1],'fifo_contains_gold':fifo_contains_gold,'first_page_answer':first,'one_call_answer':one,'full_answer':full,'first_page_correct':first==chain[-1],'one_call_correct':one==chain[-1],'full_correct':full==chain[-1],'full_calls':n_full,'trace':steps})
    host.save(OUT/'memory_state.json');saved_core=host.memory.to_dict();max_chars=host.max_chars;evicted=host.evicted;warnings=host.warnings;rebuilds=host.rebuilds
    selected_trace=host.trace[:7];host.store.close()
    reloaded=OfflineHost(symbols,db);reloaded.restore(OUT/'memory_state.json')
    assert reloaded.memory.to_dict()==saved_core
    recall_reload,_=reloaded.call('conversation_search',{'query':'Aster secret','page':0})
    assert 'K4P-8276' in recall_reload
    reopen_answer,_,_=solve(reloaded,runs[-1]['start']);assert reopen_answer==runs[-1]['gold']
    reloaded.store.close()
    result={'scope':'official core/tool bodies with SQLite adapters and deterministic controller; NOT LLM accuracy','environment':{'python':platform.python_version(),'stdlib_only':True},'repository_commit':SHA,'source_symbols':sources,'config':{'budget_chars':1200,'page_size':5,'depth_links':[1,2,3,4],'trials_per_depth':5,'seed':2026,'archive_search':'case-insensitive literal substring, not embeddings','summary':'metadata only, not LLM summarization'},'checks':{'core_replace':saved_core,'overflow_preserved_old_core':True,'recall_after_eviction':example_recall,'db_reopen_recall_and_nested_kv':True,'rebuild_memory_calls':rebuilds,'max_observed_context_chars':max_chars,'evicted_atomic_blocks':evicted,'warning_events':warnings},'database_file':db.name,'core_and_error_trace':selected_trace,'runs':runs,'summary':{str(d):{name:sum(z[name] for z in runs if z['depth_links']==d)/5 for name in ['first_page_correct','one_call_correct','full_correct']} for d in [1,2,3,4]}}
    (OUT/'demo_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'checks':result['checks'],'summary':result['summary'],'database_file':db.name},ensure_ascii=True,indent=2))
    print('PASS: original symbols, core edits, overflow, eviction/recall, pagination, chaining, SQLite reopen')
if __name__=='__main__':main()
