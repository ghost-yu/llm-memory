"""Offline mechanism demo: original AST method bodies; controlled providers."""
import ast, concurrent.futures, hashlib, json, logging, math, re, sqlite3, threading, uuid, warnings, sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo
import pydantic
from pydantic import BaseModel, Field
ROOT=Path(__file__).resolve().parents[2]
REPO=ROOT/'代码'/'mem0-historical'
OUT=ROOT/'复现'/'outputs'
METHODS=['add','_add_to_vector_store','_add_to_graph','search','_search_vector_store','_create_memory','_update_memory','_delete_memory']
FILES=['mem0/configs/prompts.py','mem0/memory/utils.py','mem0/configs/base.py','mem0/memory/storage.py','mem0/memory/main.py']
ns=dict(globals(), logger=logging.getLogger('demo'),pytz=NS(timezone=ZoneInfo),capture_event=lambda *a,**kw:None)
def load(path,names=None):
    tree=ast.parse((REPO/path).read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom)) and (names is None or getattr(n,'name',None) in names)]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(REPO/path),'exec'),ns)
load(FILES[0])
load(FILES[1],['parse_messages','get_fact_retrieval_messages','remove_code_blocks','parse_vision_messages'])
load(FILES[2],['MemoryItem'])
load(FILES[3],['SQLiteManager'])
tree=ast.parse((REPO/FILES[4]).read_text(encoding='utf-8'))
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Memory')
exec(compile(ast.Module(body=[n for n in cls.body if getattr(n,'name',None) in METHODS],type_ignores=[]),str(REPO/FILES[4]),'exec'),ns)
Memory=type('OriginalMethodsOfflineContainer',(),{n:ns[n] for n in METHODS})
class Embedder:
    def embed(self,text,memory_action=None):
        v=[0.0]*64
        for token in re.findall('[a-z]+',text.lower()): v[int(hashlib.sha256(token.encode()).hexdigest()[:8],16)%64]+=1
        norm=math.sqrt(sum(x*x for x in v)) or 1
        return [x/norm for x in v]
class Vectors:
    def __init__(self,path):
        self.conn=sqlite3.connect(path,check_same_thread=False);self.lock=threading.Lock()
        self.conn.execute('CREATE TABLE IF NOT EXISTS vectors(id TEXT PRIMARY KEY, vector TEXT, payload TEXT)');self.conn.commit()
    def insert(self,vectors,ids,payloads):
        with self.lock,self.conn: self.conn.executemany('INSERT INTO vectors VALUES(?,?,?)',[(i,json.dumps(v),json.dumps(p)) for i,v,p in zip(ids,vectors,payloads)])
    def snapshot(self):
        with self.lock: return [dict(id=i,vector=json.loads(v),payload=json.loads(p)) for i,v,p in self.conn.execute('SELECT * FROM vectors ORDER BY id')]
    def get(self,vector_id):
        row=next(x for x in self.snapshot() if x['id']==vector_id);return NS(id=row['id'],payload=row['payload'])
    def update(self,vector_id,vector,payload):
        with self.lock,self.conn: self.conn.execute('UPDATE vectors SET vector=?,payload=? WHERE id=?',(json.dumps(vector),json.dumps(payload),vector_id))
    def delete(self,vector_id):
        with self.lock,self.conn: self.conn.execute('DELETE FROM vectors WHERE id=?',(vector_id,))
    def search(self,query,vectors,limit,filters):
        rows=[NS(id=x['id'],payload=x['payload'],score=sum(a*b for a,b in zip(vectors,x['vector']))) for x in self.snapshot() if all(x['payload'].get(k)==v for k,v in filters.items())]
        return sorted(rows,key=lambda x:(-x.score,x.id))[:limit]
class Provider:
    def __init__(self): self.calls=[];self.actions=[]
    def generate_response(self,messages,response_format=None):
        if len(messages)==2:
            text=messages[-1]['content'];facts=re.findall(r'user: (.*)',text)
            response='BAD_JSON' if any(x=='BAD_JSON' for x in facts) else json.dumps({'facts':[x for x in facts if '=' in x or x.startswith('DELETE ')]})
            stage='extract'
        else:
            text=messages[0]['content'].split('Below is the current content of my memory',1)[1]
            fence=chr(96)*3
            blocks=re.findall(fence+r'\s*([\s\S]*?)\s*'+fence,text)
            old,new=map(ast.literal_eval,blocks[:2]);actions=[]
            for fact in new:
                key=fact[7:] if fact.startswith('DELETE ') else fact.split('=',1)[0]
                match=next((x for x in old if x['text'].startswith(key+'=')),None)
                if fact.startswith('DELETE '):
                    if match: actions.append(dict(id=match['id'],text=match['text'],event='DELETE'))
                elif match: actions.append(dict(id=match['id'],text=fact,event='NONE' if match['text']==fact else 'UPDATE',old_memory=match['text']))
                else: actions.append(dict(id='new',text=fact,event='ADD'))
            self.actions=actions;response=json.dumps({'memory':actions});stage='update'
        self.calls.append(dict(stage=stage,response=response));return response
def setup(vpath,hpath):
    m=Memory();m.config=NS(custom_fact_extraction_prompt=None,custom_update_memory_prompt=None,llm=NS(config={}))
    m.embedding_model=Embedder();m.vector_store=Vectors(vpath);m.llm=Provider();m.db=ns['SQLiteManager'](str(hpath));m.enable_graph=False;m.api_version='v1.1';return m
def main():
    OUT.mkdir(exist_ok=True);run=uuid.uuid4().hex[:12];vp=OUT/('vectors-'+run+'.sqlite');hp=OUT/('history-'+run+'.sqlite');m=setup(vp,hp);steps=[];checks={}
    def add(text,user='alice',infer=True):
        result=m.add(text,user_id=user,infer=infer);steps.append(dict(input=text,user=user,infer=infer,result=result,policy_actions=list(m.llm.actions) if infer else [],snapshot=m.vector_store.snapshot()));return result
    first=add('city=Beijing')['results'][0]['id'];created=m.vector_store.get(first).payload['created_at']
    hobby=add('hobby=cycling')['results'][0]['id']
    histlen=len(m.db.get_history(first));duplicate=add('city=Beijing')
    checks['NONE_no_write']=duplicate['results']==[] and len(m.db.get_history(first))==histlen and m.llm.actions[0]['event']=='NONE'
    update=add('city=Hangzhou');checks['UPDATE_preserves_id_created_at']=update['results'][0]['id']==first and m.vector_store.get(first).payload['created_at']==created
    add('DELETE hobby');checks['DELETE_removed_live_memory']=all(x['id']!=hobby for x in m.vector_store.snapshot())
    checks['DELETE_history_tombstone']=m.db.connection.execute('SELECT is_deleted FROM history WHERE memory_id=? AND event=?',(hobby,'DELETE')).fetchone()[0]==1
    add('city=Shanghai','bob');alice=m.search('city',user_id='alice');bob=m.search('city',user_id='bob')
    checks['user_isolation']=[x['memory'] for x in alice['results']]==['city=Hangzhou'] and [x['memory'] for x in bob['results']]==['city=Shanghai']
    before=m.vector_store.snapshot();add('BAD_JSON');checks['invalid_extraction_no_write']=before==m.vector_store.snapshot()
    n=len(m.llm.calls)
    for text in ['city=Beijing','city=Hangzhou','city=Hangzhou']: add(text,'raw',False)
    checks['infer_false_skips_provider']=len(m.llm.calls)==n
    raw=m.search('city',user_id='raw');checks['raw_conflicts_duplicates']=len(raw['results'])==3
    checks['ADD_UPDATE_history']=[x['event'] for x in m.db.get_history(first)]==['ADD','UPDATE']
    try: m.search('city');checks['missing_scope_rejected']=False
    except ValueError: checks['missing_scope_rejected']=True
    final=m.vector_store.snapshot();histories={x:m.db.get_history(x) for x in [first,hobby]};calls=m.llm.calls
    m.vector_store.conn.close();m.db.connection.close();m2=setup(vp,hp)
    checks['persisted_vectors_exact']=m2.vector_store.snapshot()==final
    checks['persisted_history_exact']={x:m2.db.get_history(x) for x in histories}==histories
    checks['persisted_search_exact']=m2.search('city',user_id='alice')==alice
    result=dict(scope='Original method bodies with controlled grammar provider and local SQLite vector adapter; no natural-language model or paper benchmark',python=sys.version,pydantic=pydantic.__version__,commit='6d13e8300143b61aefc3a1ab5fb936f6d52008a4',sources={p:hashlib.sha256((REPO/p).read_bytes()).hexdigest() for p in FILES},methods=METHODS,checks=checks,steps=steps,final=final,histories=histories,model_calls=calls,searches=dict(alice=alice,bob=bob,raw=raw),databases=[vp.name,hp.name])
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    m2.vector_store.conn.close();m2.db.connection.close()
    assert all(checks.values()),checks
    print(json.dumps(dict(checks=checks,model_calls=len(calls),final_records=len(final)),indent=2))
if __name__=='__main__': main()
