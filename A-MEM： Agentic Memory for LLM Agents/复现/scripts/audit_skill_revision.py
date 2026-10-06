"""Evidence consistency, not automatic semantic assessment."""
import ast,hashlib,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    trace=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    assert sha(P/'复现/scripts/demo_amem.py')==trace['source_sha256']
    for repo,commit in [('A-mem-historical','c3bb1ee6d4825b13460dd26be1444b5f870ddb64'),('A-mem-sys-historical','aec6d34c6035d3a8f56df37d741f25e3adcecfea')]:
        path=P/'代码'/repo
        assert subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()==commit
        assert not subprocess.check_output(['git','-C',str(path),'status','--porcelain'],text=True).strip()
    for name,h in trace['original_sources'].items():assert sha(P/name)==h
    spec=importlib.util.spec_from_file_location('amem_contract_trace',P/'复现/scripts/trace_contracts.py')
    t=importlib.util.module_from_spec(spec);sys.modules[spec.name]=t;spec.loader.exec_module(t)
    ns=dict(t.d.ns,np=t.np,os=t.os,pickle=t.pickle,SentenceTransformer=t.Encoder,cosine_similarity=t.cosine)
    t.d.classes(t.d.EVAL/'memory_layer.py',['SimpleEmbeddingRetriever'],ns)
    for name,sig in trace['signatures'].items():
        owner,method=name.split('.')
        if owner=='demo':obj=t.d
        elif owner=='SimpleEmbeddingRetriever':obj=ns[owner]
        elif owner in ('MemoryNote','AgenticMemorySystem'):obj=t.d.ns[owner]
        else:obj=getattr(t.d,owner)
        assert str(inspect.signature(getattr(obj,method)))==sig,name
    assert len(trace['signatures'])==24 and len(trace['checks_passed'])==23 and all(trace['checks_passed'].values())
    obs=trace['observations'];assert obs['duplicate_id_counts']=={'notes':1,'documents':2}
    assert obs['retriever']['k0_original']==[0,1] and obs['retriever']['k0_adapter']==[]
    assert obs['retriever']['embedding_shape']==[2,2] and obs['retriever']['cosine_shape']==[1,2]
    assert obs['analyze_provider_failure_unbound_response'].startswith('UnboundLocalError')
    assert obs['later_action_failure_no_rollback'].startswith('TypeError')
    output=P/'复现/outputs/skill_revision_check.json';files=[];links=0
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_amem.py','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','复现/outputs/contracts_stdout.txt','复现/outputs/results.json','代码/A-mem-historical/utils.py']
    for name in names:
        f=P/name;assert f.is_file() and f.stat().st_size>0
        files.append({'path':name,'sha256':sha(f),'bytes':f.stat().st_size})
        if f.suffix=='.py':ast.parse(f.read_text(encoding='utf8'))
        if f.suffix=='.md':
            text=re.sub(r'(?ms)^~~~[^\n]*\n.*?^~~~[^\n]*(?:\n|$)','',f.read_text(encoding='utf8'))
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if target.startswith(('http','#')):continue
                dest=(f.parent/target.strip('<>')).resolve()
                assert dest==output.resolve() or dest.exists(),target
                links+=1
    doc=(P/'解释.md').read_text(encoding='utf8');assert doc.count('$$')%2==0
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','部分成功','未找到','9.1','9.2','9.3','9.4']:assert term in doc
    result={'status':'passed','scope':'24 signatures, 23 observed boundary conditions, locked clean source commits and file/link consistency; not semantic content certification','runtime_checks':23,'local_links_checked':links,'artifacts':files,'manual_content_review':'资料/skill内容核查.md'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 24 signatures, 23 boundary checks,',links,'links,',len(files),'artifacts')
if __name__=='__main__':main()