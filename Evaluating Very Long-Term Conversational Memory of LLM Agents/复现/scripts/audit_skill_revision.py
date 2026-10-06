"""Evidence consistency only; prose is reviewed in skill content record."""
import ast,hashlib,importlib.util,inspect,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[2];REPO=P/'代码/locomo-official'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    trace=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    pool=json.loads((P/'复现/outputs/pooling_trace.json').read_text(encoding='utf8'))
    source=P/'复现/scripts/demo_locomo.py';assert sha(source)==trace['source_sha256']
    assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip()=='3eb6f2c585f5e1699204e3c3bdf7adc5c28cb376'
    assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain']).decode().strip()
    for name,h in trace['original_sources'].items():assert sha(P/name)==h
    assert sha(P/pool['source'])==pool['source_sha256']
    spec=importlib.util.spec_from_file_location('locomo_contract_demo',source);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    gpt=REPO/'task_eval/gpt_utils.py'
    gptnode=next(n for n in ast.parse(gpt.read_text(encoding='utf8')).body if getattr(n,'name',None)=='get_input_context')
    ns={};exec(compile(ast.Module(body=[gptnode]),str(gpt),'exec'),ns)
    for name,sig in trace['signatures'].items():
        if name.startswith('BM25.'):obj=getattr(d.BM25,name.split('.')[1])
        elif name.startswith('demo.'):obj=getattr(d,name.split('.')[1])
        elif name=='get_input_context':obj=ns[name]
        else:obj=d.ns[name]
        assert str(inspect.signature(obj))==sig,name
    poolnode=next(n for n in ast.parse((P/pool['source']).read_text(encoding='utf8')).body if getattr(n,'name',None)=='mean_pooling')
    assert [x.arg for x in poolnode.args.args]==['token_embeddings','mask'] and pool['signature']=='(token_embeddings, mask)'
    assert len(trace['signatures'])==11 and len(trace['checks_passed'])==22 and all(trace['checks_passed'].values())
    assert len(pool['checks_passed'])==5 and all(pool['checks_passed'].values())
    assert pool['input_shape']==[3,3,2] and pool['mask_shape']==[3,3] and pool['output_shape']==[3,2]
    assert pool['observations']['binary_result']==[3.0,5.0] and pool['observations']['all_masked_is_nan']
    obs=trace['observations'];assert 'old' in obs['budgeted_context'] and 'new' not in obs['budgeted_context']
    assert 'DATE: DAY2' in obs['budgeted_context'] and obs['metric_ignored'][0]==[2/3]
    # Replay one real lexical ranking; all row gold/recall consistency handled by old audit.
    r=json.loads((P/'复现/outputs/results.json').read_text(encoding='utf8'))
    data=json.loads(d.DATA.read_text(encoding='utf8'));byid={s['sample_id']:s for s in data}
    first=r['rows'][0];docs=d.documents(byid[first['sample']]);ranking,_=d.BM25(docs).rank(first['question'])
    assert [docs[i]['id'] for i in ranking[:50]]==first['retrieved']['50']
    assert abs(sum(row['recent10_recall'] for row in r['rows'])/1536-r['overall']['recent10'])<1e-12
    output=P/'复现/outputs/skill_revision_check.json';files=[];links=0
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_locomo.py','复现/scripts/trace_contracts.py','复现/scripts/trace_pooling.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','复现/outputs/contracts_stdout.txt','复现/outputs/pooling_trace.json','复现/outputs/results.json']
    for name in names:
        f=P/name;assert f.is_file() and f.stat().st_size>0
        files.append({'path':name,'sha256':sha(f),'bytes':f.stat().st_size})
        if f.suffix=='.py':ast.parse(f.read_text(encoding='utf8'))
        if f.suffix=='.md':
            text=re.sub(r'(?ms)^~~~[^\n]*\n.*?^~~~[^\n]*(?:\n|$)','',f.read_text(encoding='utf8'))
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if target.startswith(('http','#')):continue
                dest=(f.parent/target.strip('<>')).resolve();assert dest==output.resolve() or dest.exists(),target
                links+=1
    doc=(P/'解释.md').read_text(encoding='utf8');assert doc.count('$$')%2==0
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','部分成功','未找到','7.1','7.2','7.3','7.4','2.4']:assert term in doc
    result={'status':'passed','scope':'11 runtime metric/host/context signatures, original pooling AST signature, 27 observed conditions, source/file consistency and one real ranking replay; not semantic completeness certification','runtime_checks':27,'signatures_checked':12,'local_links_checked':links,'artifacts':files,'manual_content_review':'资料/skill内容核查.md'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 12 signatures, 27 boundaries,',links,'links,',len(files),'artifacts; real ranking replay')
if __name__=='__main__':main()