"""Artifact/signature/runtime consistency only, not prose semantic grading."""
import ast,hashlib,importlib.util,inspect,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[2];REPO=P/'代码/mem0-historical'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=P/'复现/scripts/demo_mem0.py';trace=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    assert sha(source)==trace['source_sha256']
    assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()=='6d13e8300143b61aefc3a1ab5fb936f6d52008a4'
    assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()
    for name,h in trace['original_sources'].items():assert sha(REPO/name)==h
    spec=importlib.util.spec_from_file_location('mem0_audit',source);demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
    for path,sig in trace['signatures'].items():
        parts=path.split('.')
        if parts[0]=='demo':obj=demo;parts=parts[1:]
        elif parts[0]=='SQLiteManager':obj=demo.ns[parts[0]];parts=parts[1:]
        elif hasattr(demo,parts[0]):obj=getattr(demo,parts[0]);parts=parts[1:]
        else:obj=demo.ns[parts[0]];parts=parts[1:]
        for part in parts:obj=getattr(obj,part)
        assert str(inspect.signature(obj))==sig
    assert len(trace['signatures'])==28 and len(trace['checks_passed'])==14
    obs=trace['observations'];assert obs['history_failure']['vector_records']==1 and obs['history_failure']['history_records']==0
    assert obs['provider_stage_cost_duplicate']==obs['provider_stage_cost_BAD_JSON']==2
    assert 'custom' not in obs['updated_payload']
    assert obs['zero_query_results']['results'][0]['score']==0
    assert [x['event'] for x in obs['partial_actions_result']['results']]==['ADD']
    output=P/'复现/outputs/skill_revision_check.json';files=[];links=0
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_mem0.py','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','复现/outputs/results.json','代码/mem0-historical/mem0/memory/graph_memory.py']
    for name in names:
        f=P/name;assert f.is_file() and f.stat().st_size>0
        files.append({'path':name,'sha256':sha(f),'bytes':f.stat().st_size})
        if f.suffix=='.py':ast.parse(f.read_text(encoding='utf8'))
        if f.suffix=='.md':
            link_text=re.sub(r'(?ms)^~~~[^\n]*\n.*?^~~~[^\n]*(?:\n|$)','',f.read_text(encoding='utf8'))
            for target in re.findall(r'\]\(([^)]+)\)',link_text):
                if target.startswith(('http','#')):continue
                dest=(f.parent/target.strip('<>')).resolve();assert dest==output.resolve() or dest.exists(),target;links+=1
    doc=(P/'解释.md').read_text(encoding='utf8');assert doc.count('$$')%2==0
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','部分成功','未找到','7.1','7.4','5.1','4.5','3.3']:assert term in doc
    result={'status':'passed','scope':'28 signatures, 14 runtime/boundary observations and source/file consistency; not semantic completeness certification','runtime_checks':14,'local_links_checked':links,'artifacts':files,'manual_content_review':'资料/skill内容核查.md'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');assert output.is_file()
    print('PASS: 28 signatures, 14 runtime/boundary checks,',links,'links,',len(files),'artifacts')
if __name__=='__main__':main()
