"""Source, runtime observations, signatures and artifact consistency only."""
import ast,hashlib,importlib.util,inspect,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[2];R=P/'代码/LongMemEval-historical'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    t=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    assert sha(P/'复现/scripts/demo_longmemeval.py')==t['demo_sha256']
    assert subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD']).decode().strip()=='8a44eb1bb033842b12c67c594ac2094fc3028526'
    assert not subprocess.check_output(['git','-C',str(R),'status','--porcelain']).decode().strip()
    for name,h in t['original_sources'].items():assert sha(R/name)==h
    spec=importlib.util.spec_from_file_location('lm_contract_trace',P/'复现/scripts/trace_contracts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    for name,sig in t['signatures'].items():
        if name.startswith('DenseRetrievalMaster.'):obj=getattr(m.ns['DenseRetrievalMaster'],name.split('.')[1])
        else:obj=m.ns[name]
        assert str(inspect.signature(obj))==sig
    assert len(t['checks_passed'])==28 and all(t['checks_passed'].values()) and len(t['signatures'])==14
    obs=t['observations'];assert obs['duplicate_ranking_metric'][2]>1
    assert 'OLDUSER' in obs['round_prompt'] and 'OLDASSISTANT' in obs['round_prompt'] and 'has_answer' not in obs['round_prompt']
    assert obs['partition_false_match']==['s10_1','other_1'] and 'Yesterday' in obs['judge_label_input']
    output=P/'复现/outputs/skill_revision_check.json';files=[];links=0
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_longmemeval.py','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','复现/outputs/contracts_stdout.txt','复现/outputs/results.json','代码/LongMemEval-historical/src/generation/run_generation.py']
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
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','部分成功','未找到','9.1','9.2','9.3','9.4']:assert term in doc
    result={'status':'passed','scope':'14 original signatures, 28 observed boundary conditions and locked-source/file/link consistency; not prose semantic certification','runtime_checks':28,'local_links_checked':links,'artifacts':files,'manual_content_review':'资料/skill内容核查.md'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 14 signatures, 28 boundaries,',links,'links,',len(files),'artifacts')
if __name__=='__main__':main()