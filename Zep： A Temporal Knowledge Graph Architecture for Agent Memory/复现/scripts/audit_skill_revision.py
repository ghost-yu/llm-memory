"""Source/signature/artifact consistency only; prose reviewed separately."""
import ast,hashlib,importlib.util,inspect,json,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[2];REPO=P/'代码/graphiti-historical'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=P/'复现/scripts/demo_zep.py';trace=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    assert sha(source)==trace['source_sha256']
    assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()=='77cb67cdfea7a080f217236b56f8ca39b25ca0e4'
    assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()
    for name,h in trace['original_sources'].items():assert sha(REPO/name)==h
    spec=importlib.util.spec_from_file_location('zep_contract_demo',source);d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
    for name,sig in trace['signatures'].items():
        parts=name.split('.')
        if parts[0]=='demo':obj=d;parts=parts[1:]
        elif hasattr(d,parts[0]):obj=getattr(d,parts[0]);parts=parts[1:]
        else:obj=d.ns[parts[0]];parts=parts[1:]
        for part in parts:obj=getattr(obj,part)
        assert str(inspect.signature(obj))==sig,name
    assert len(trace['signatures'])==20 and len(trace['checks_passed'])==16 and all(trace['checks_passed'].values())
    obs=trace['observations'];assert obs['nonoverlap_fact_mutation']['fact']=='rewritten by response'
    assert obs['duplicate_retained_interval']['invalid_at']=='2025-02-01T00:00:00+00:00'
    assert 'AttributeError' in obs['wrong_date_type_error']
    assert sorted(obs['parallel_stages'])==['contradictions','dates','duplicate']
    output=P/'复现/outputs/skill_revision_check.json';files=[];links=0
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_zep.py','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','复现/outputs/results.json','代码/graphiti-historical/graphiti_core/graphiti.py']
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
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','部分成功','未找到','7.1','7.2','7.3','7.4']:assert term in doc
    result={'status':'passed','scope':'20 runtime signatures, 16 observed boundary checks, original sources and artifact/link consistency; not semantic certification','runtime_checks':16,'local_links_checked':links,'artifacts':files,'manual_content_review':'资料/skill内容核查.md'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS: 20 signatures, 16 boundary checks,',links,'links,',len(files),'artifacts')
if __name__=='__main__':main()