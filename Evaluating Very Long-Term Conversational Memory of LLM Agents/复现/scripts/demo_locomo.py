"""True LoCoMo data: lexical evidence retrieval, original scorer probes; no answer model."""
import ast, contextlib, hashlib, io, json, math, re, string, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import nltk, numpy as np, regex
from nltk.stem import PorterStemmer
ROOT=Path(__file__).resolve().parents[2];REPO=ROOT/'代码'/'locomo-official';OUT=ROOT/'复现'/'outputs'
DATA=REPO/'data'/'locomo10.json';SOURCE=REPO/'task_eval'/'evaluation.py';ps=PorterStemmer()
ns=dict(globals());names=['normalize_answer','f1_score','f1','eval_question_answering','exact_match_score']
nodes=[n for n in ast.parse(SOURCE.read_text(encoding='utf-8')).body if getattr(n,'name',None) in names]
assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes),str(SOURCE),'exec'),ns)
STOP=set('a an the and or to of in on at for with is are was were be been do does did what which when where who why how can could would should i you he she it they we my your his her their our has have had'.split())
def terms(text):return [ps.stem(w) for w in re.findall('[a-z0-9]+',str(text).lower()) if w not in STOP]
class BM25:
    def __init__(self,docs):
        self.docs=docs;self.tokens=[Counter(terms(x['text'])) for x in docs];self.lengths=[sum(x.values()) for x in self.tokens];self.avg=sum(self.lengths)/max(1,len(docs));self.postings=defaultdict(list)
        for i,c in enumerate(self.tokens):
            for term,tf in c.items():self.postings[term].append((i,tf))
    def rank(self,query):
        n=len(self.docs);scores=[0.0]*n
        for term in set(terms(query)):
            hits=self.postings.get(term,[]);df=len(hits)
            if not df:continue
            idf=math.log(1+(n-df+.5)/(df+.5))
            for i,tf in hits:scores[i]+=idf*tf*2.5/(tf+1.5*(.25+.75*self.lengths[i]/max(self.avg,1)))
        return sorted(range(n),key=lambda i:(-scores[i],i)),scores

def documents(sample):
    docs=[];conversation=sample['conversation']
    sessions=sorted([x for x in conversation if re.fullmatch(r'session_[0-9]+',x)],key=lambda x:int(x.split('_')[1]))
    for session in sessions:
        for turn in conversation[session]:
            text=conversation.get(session+'_date_time','')+' '+turn['speaker']+': '+turn.get('text','')
            if turn.get('blip_caption'):text+=' [image caption: '+turn['blip_caption']+']'
            docs.append(dict(id=turn['dia_id'],text=text,session=session))
    return docs

def main():
    OUT.mkdir(exist_ok=True);data=json.loads(DATA.read_text(encoding='utf-8'));ks=[1,5,10,25,50];rows=[];stats=[];missing=[];counts=Counter();checks={};scores_for_k={k:[] for k in ks}
    for sample in data:
        docs=documents(sample);index=BM25(docs);ids=[x['id'] for x in docs];idset=set(ids)
        assert len(ids)==len(idset)
        stats.append(dict(sample=sample['sample_id'],turns=len(docs),sessions=len(set(x['session'] for x in docs)),qas=len(sample['qa'])))
        eval_lines={k:[] for k in ks};temporary=[]
        for qi,qa in enumerate(sample['qa']):
            cat=qa['category'];counts[str(cat)]+=1
            for ev in qa.get('evidence',[]):
                if ev not in idset:missing.append(dict(sample=sample['sample_id'],question_index=qi,evidence=ev))
            if cat==5 or not qa.get('evidence'):continue
            ranking,score=index.rank(qa['question']);retrieved={str(k):[ids[i] for i in ranking[:k]] for k in ks}
            # Retrieval above only receives question and document index. Annotation is used only below for scoring.
            recalls={str(k):sum(ev in retrieved[str(k)] for ev in qa['evidence'])/len(qa['evidence']) for k in ks}
            recent=ids[-10:];rr=sum(ev in recent for ev in qa['evidence'])/len(qa['evidence'])
            row=dict(sample=sample['sample_id'],question_index=qi,category=cat,question=qa['question'],evidence=qa['evidence'],retrieved=retrieved,recalls=recalls,recent10_ids=recent,recent10_recall=rr,top_document=docs[ranking[0]])
            rows.append(row);temporary.append(row)
            for k in ks:eval_lines[k].append(dict(qa,prediction='',prediction_context=retrieved[str(k)]))
        for k in ks:
            _,_,official_recall=ns['eval_question_answering'](eval_lines[k])
            direct=[x['recalls'][str(k)] for x in temporary]
            assert np.allclose(official_recall,direct);scores_for_k[k].extend(official_recall)
    checks['official_recall_matches_direct']=all(len(x)==len(rows) for x in scores_for_k.values())
    checks['recall_monotone_topk']=all(all(r['recalls'][str(a)]<=r['recalls'][str(b)] for a,b in zip(ks,ks[1:])) for r in rows)
    checks['all_ids_unique_per_conversation']=True
    probes={}
    probes['f1_numeric']=float(ns['f1_score']('red car','red fast car'));checks['f1_numeric_matches']=abs(probes['f1_numeric']-.8)<1e-12
    probes['comma_list_extra_predictions']=float(ns['f1']('apple, banana, invented','apple, banana'));checks['extra_predictions_unpenalized_observed']=probes['comma_list_extra_predictions']==1
    probes['exact_match_word_set']=bool(ns['exact_match_score']('red car','car red red'));checks['exact_match_ignores_order_duplicates_observed']=probes['exact_match_word_set']
    probes['normalization']=ns['normalize_answer']('The apple, and a banana!');checks['normalization_rule']=probes['normalization']=='apple banana'
    adversarial=[dict(category=5,answer='',evidence=[],prediction='Not mentioned, but I invent that she lives in Paris.')]
    probes['adversarial_keyword_with_hallucination']=ns['eval_question_answering'](adversarial)[0][0];checks['adversarial_keyword_only_observed']=probes['adversarial_keyword_with_hallucination']==1
    none=[dict(category=4,answer='apple',evidence=['D1:1'],prediction='banana')]
    probes['missing_context_default_recall']=ns['eval_question_answering'](none)[2][0];checks['missing_context_defaults_one_observed']=probes['missing_context_default_recall']==1
    report={}
    for cat in sorted(set(r['category'] for r in rows)):
        subset=[r for r in rows if r['category']==cat]
        report[str(cat)]=dict(n=len(subset),bm25={str(k):sum(r['recalls'][str(k)] for r in subset)/len(subset) for k in ks},recent10=sum(r['recent10_recall'] for r in subset)/len(subset))
    overall=dict(n=len(rows),bm25={str(k):float(np.mean(scores_for_k[k])) for k in ks},recent10=float(np.mean([r['recent10_recall'] for r in rows])))
    result=dict(scope='10-conversation released dataset, BM25 turn evidence retrieval; original evaluation functions; no answering LLM',commit='3eb6f2c585f5e1699204e3c3bdf7adc5c28cb376',python=sys.version,versions=dict(numpy=np.__version__,nltk=nltk.__version__,regex=regex.__version__),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA,SOURCE]},configuration=dict(k_values=ks,k1=1.5,b=.75,unit='individual turn with speaker/date/caption text',query='question only',tie_break='original chronological document order'),dataset_stats=stats,category_counts=dict(counts),missing_evidence_ids=missing,checks=checks,metric_probes=probes,overall=overall,by_category=report,rows=rows)
    (OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(checks.values()),checks
    return dict(overall=overall,checks=checks,category_counts=dict(counts),missing_evidence_ids=len(missing))
if __name__=='__main__':
    log=io.StringIO()
    with contextlib.redirect_stdout(log):summary=main()
    (OUT/'scorer_stdout.txt').write_text(log.getvalue(),encoding='utf-8');print(json.dumps(summary,indent=2))
