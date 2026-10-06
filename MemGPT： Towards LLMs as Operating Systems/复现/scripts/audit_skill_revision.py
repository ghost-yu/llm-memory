"""Runtime/source/document consistency, not semantic completeness grading."""
import ast,hashlib,importlib.util,inspect,json,re,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[2];REPO=P/'代码/MemGPT-historical'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=P/'复现/scripts/demo_memgpt.py';trace=json.loads((P/'复现/outputs/contracts_trace.json').read_text(encoding='utf8'))
    assert trace['source_sha256']==sha(source)
    assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()=='a0139b5fdc203f827168cb741c9f4fea3cec09bf'
    assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()
    spec=importlib.util.spec_from_file_location('memgpt_audit',source);demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
    symbols,_=demo.load_original_symbols()
    for item in trace['original_sources']:assert sha(REPO/item['path'])==item['sha256']
    for path,sig in trace['signatures'].items():
        parts=path.split('.')
        if parts[0]=='CoreMemory':obj=symbols['CoreMemory'];parts=parts[1:]
        elif parts[0]=='demo':obj=demo;parts=parts[1:]
        elif parts[0] in ['SQLiteStore','OfflineHost']:obj=getattr(demo,parts[0]);parts=parts[1:]
        else:obj=symbols[parts[0]];parts=[]
        for part in parts:obj=getattr(obj,part)
        assert str(inspect.signature(obj))==sig
    assert len(trace['signatures'])==33 and len(trace['checks_passed'])==18
    raw=trace['historical_archival_search']
    assert raw['cached_candidates']==12 and raw['returned_total']==5 and '(page 0/0)' in raw['page0_header']
    assert '(page 0/2)' in trace['adapter_probes']['adapter_page0']
    assert trace['CoreMemory_load_human_char_limit'] is None and 5 in trace['Agent_step_return_tuple_lengths']
    output=P/'复现/outputs/skill_revision_check.json';files=[];links=0
    names=['解释.md','资料/skill内容核查.md','复现/README.md','复现/scripts/demo_memgpt.py','复现/scripts/trace_contracts.py','复现/scripts/audit_skill_revision.py','复现/outputs/contracts_trace.json','复现/outputs/demo_results.json','代码/MemGPT-historical/memgpt/memory.py','代码/MemGPT-historical/memgpt/agent.py']
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
    for term in ['【必须会】','【建议会】','【可以暂时不掌握】','部分成功','9.1','9.3','6.1','7.1','8.1']:assert term in doc
    result={'status':'passed','scope':'33 signatures, original commit/hash and boundary evidence, file/structure consistency; not semantic completeness certification','runtime_checks':18,'local_links_checked':links,'artifacts':files,'manual_content_review':'资料/skill内容核查.md'}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');assert output.is_file()
    print('PASS: 33 signatures, 18 runtime/boundary checks,',links,'links,',len(files),'artifacts')
if __name__=='__main__':main()
