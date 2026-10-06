"""Evidence consistency only, not automated semantic content grading."""
import ast,hashlib,importlib.util,inspect,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=P/'复现/scripts/demo_cms.py'
    trace=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    assert trace['source_sha256']==sha(source)
    spec=importlib.util.spec_from_file_location('cms_audit',source)
    demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
    assert len(trace['signatures'])==11
    for path,sig in trace['signatures'].items():
        obj=demo
        for part in path.split('.'):obj=getattr(obj,part)
        assert str(inspect.signature(obj))==sig
    assert len(trace['checks_passed'])==16 and trace['parameter_count']==1656
    assert trace['schedule']['records'][-1]['counts']==[4,2,1]
    assert trace['frozen_parameters_but_changed_output_max_abs']>0
    assert trace['observed_errors']['zero_period']['type']=='ZeroDivisionError'
    assert trace['short_schedule']['counts']==[1,0,0]
    assert set(trace['checkpoint_keys'])=={'seed','scope','states'}
    assert max(trace['checkpoint_prediction_max_error'].values())<1e-7
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_cms.py','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','复现/outputs/demo_results.json','复现/outputs/toy_cms_checkpoint.pt']
    files=[];links=0;output=P/'复现/outputs/skill_revision_check.json'
    for name in names:
        f=P/name;assert f.is_file() and f.stat().st_size>0
        files.append({'path':name,'sha256':sha(f),'bytes':f.stat().st_size})
        if f.suffix=='.py':ast.parse(f.read_text(encoding='utf8'))
        if f.suffix=='.md':
            for target in re.findall(r'\]\(([^)]+)\)',f.read_text(encoding='utf8')):
                if target.startswith(('http','#')):continue
                dest=(f.parent/target.strip('<>')).resolve()
                assert dest==output.resolve() or dest.exists(),target;links+=1
    doc=(P/'解释.md').read_text(encoding='utf8')
    assert doc.count('$$')%2==0
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','未找到','部分成功','11.1','11.4','9.1','6.1','10.1']:assert term in doc
    report={'status':'passed','scope':'11 signatures, runtime/boundary evidence and artifact consistency; does not certify semantic completeness','runtime_checks':16,'local_links_checked':links,'artifacts':files,'manual_content_review':'资料/skill内容核查.md'}
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    assert output.is_file()
    print('PASS: 11 signatures, 16 runtime/boundary checks,',links,'links,',len(files),'artifacts')
if __name__=='__main__':main()
