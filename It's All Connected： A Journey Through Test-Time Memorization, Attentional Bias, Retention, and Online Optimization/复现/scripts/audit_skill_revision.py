"""Artifact/runtime consistency only; does not certify prose semantics."""
import ast, hashlib, inspect, importlib.util, json, re
from pathlib import Path
P=Path(__file__).resolve().parents[2]
SOURCE=P/'复现/scripts/demo_miras.py'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    trace=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    assert trace['source_sha256']==sha(SOURCE)
    spec=importlib.util.spec_from_file_location('demo_audit',SOURCE)
    demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
    for name,sig in trace['signatures'].items(): assert str(inspect.signature(getattr(demo,name)))==sig
    assert len(trace['checks_passed'])==13
    assert trace['episode_replay']['matches_saved'] and trace['episode_replay']['corruptions']==13
    assert trace['write']['input_unchanged']
    assert trace['observed_errors']['invalid_mode']['type']=='ValueError'
    assert trace['observed_errors']['wrong_key_shape']['type']=='RuntimeError'
    assert trace['shift_steps']=={'l2':14,'huber':23}
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_miras.py','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/demo_results.json','复现/outputs/contracts_trace.json','图片/page-11.png','图片/page-12.png']
    artifacts=[];links=0
    for name in names:
        p=P/name;assert p.is_file() and p.stat().st_size>0
        artifacts.append({'path':name,'sha256':sha(p),'bytes':p.stat().st_size})
        if p.suffix=='.py': ast.parse(p.read_text(encoding='utf8'))
        if p.suffix=='.md':
            text=p.read_text(encoding='utf8')
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if target.startswith(('http','#')): continue
                resolved=(p.parent/target.strip('<>')).resolve()
                output=(P/'复现/outputs/skill_revision_check.json').resolve()
                assert resolved==output or resolved.exists(),target
                links+=1
    doc=(P/'解释.md').read_text(encoding='utf8')
    assert doc.count('$$')%2==0
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','未找到','部分成功','12.1','12.5','8.1','9.1','11.1']: assert term in doc,term
    result={'status':'passed','scope':'source signatures, archived runtime evidence, document structure and file/link consistency; not semantic completeness certification','runtime_checks':13,'local_links_checked':links,'artifacts':artifacts,'manual_content_review':'资料/skill内容核查.md'}
    (P/'复现/outputs/skill_revision_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    assert (P/'复现/outputs/skill_revision_check.json').is_file()
    print('PASS: 5 signatures, 13 runtime/boundary checks,',links,'links;',len(artifacts),'artifacts')
if __name__=='__main__': main()
