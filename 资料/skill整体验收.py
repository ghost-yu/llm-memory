"""Snapshot consistency for nine manually reviewed readings, not semantic grading."""
import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parents[1]
EXPECTED={'Titans':(15,11),'It':(13,5),'Nested':(16,11),'MemGPT':(18,33),'Mem0':(14,28),'Zep':(16,20),'A-MEM':(23,24),'Evaluating':(27,12),'LongMemEval':(28,14)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    reports=sorted(P.glob('*/复现/outputs/skill_revision_check.json'));assert len(reports)==9
    rows=[];links=0
    for path in reports:
        paper=path.parents[2];name=paper.name
        key=next(k for k in EXPECTED if name.startswith(k));wanted,sig_count=EXPECTED[key]
        r=json.loads(path.read_text(encoding='utf8'));assert r['status']=='passed'
        assert r.get('runtime_checks',r.get('checks'))==wanted
        artifacts=r['artifacts']
        if isinstance(artifacts,dict):artifacts=[dict(v,path=k) for k,v in artifacts.items()]
        for item in artifacts:
            f=paper/item['path'];assert sha(f)==item['sha256'],str(f)
        tracepath=paper/'复现/outputs/contracts_trace.json';trace=json.loads(tracepath.read_text(encoding='utf8'))
        signatures=trace.get('signatures',trace.get('contracts'))
        observed=trace.get('checks_passed',trace.get('checks'))
        extra=0
        if key=='Evaluating':
            pool=json.loads((paper/'复现/outputs/pooling_trace.json').read_text(encoding='utf8'))
            assert all(pool['checks_passed'].values()) and pool['signature']=='(token_embeddings, mask)'
            extra=1
        assert len(signatures)+extra==sig_count,(name,len(signatures),sig_count)
        if isinstance(observed,dict):assert all(observed.values())
        else:assert isinstance(observed,list) and len(observed)>0 and all(isinstance(x,str) and x for x in observed)
        record=paper/'资料/skill内容核查.md';doc=paper/'解释.md';readme=paper/'复现/README.md'
        content=doc.read_text(encoding='utf8')
        for term in ['【必须会】','【建议会】','【可以暂时不掌握】','部分成功']:assert term in content,(name,term)
        assert not any(term in content.splitlines()[0] for term in ['零基础','从零开始','逐行精读','小白'])
        assert content.count('$$')%2==0
        for md in [doc,record,readme]:
            text=re.sub(r'(?ms)^~~~[^\n]*\n.*?^~~~[^\n]*(?:\n|$)','',md.read_text(encoding='utf8'))
            for target in re.findall(r'\]\(([^)]+)\)',text):
                if target.startswith(('http','#')):continue
                assert (md.parent/target.strip('<>')).resolve().exists(),(name,target)
                links+=1
        rows.append({'paper':name,'runtime_conditions':wanted,'signatures_or_contracts':sig_count,'revision_report_sha256':sha(path),'explanation_sha256':sha(doc),'manual_record_sha256':sha(record),'trace_sha256':sha(tracepath),'artifacts_verified':len(artifacts),'reproduction_status':'部分成功'})
    assert sum(x['runtime_conditions'] for x in rows)==170
    assert sum(x['signatures_or_contracts'] for x in rows)==158
    finalmd=P/'资料/skill整体验收.md';assert finalmd.exists()
    for target in re.findall(r'\]\(([^)]+)\)',finalmd.read_text(encoding='utf8')):
        if target.startswith(('http','#')):continue
        dest=(finalmd.parent/target.strip('<>')).resolve()
        assert dest==(P/'资料/skill整体验收.json').resolve() or dest.exists(),target;links+=1
    result={'status':'passed','role':'Current nine-paper evidence/hash/link snapshot only; semantic acceptance is documented separately and cannot be inferred from this script','papers':9,'runtime_conditions':170,'signatures_or_contracts':158,'local_links_checked':links,'manual_acceptance':'资料/skill整体验收.md','manual_acceptance_sha256':sha(finalmd),'rows':rows}
    (P/'资料/skill整体验收.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(status='passed',papers=9,runtime_conditions=170,signatures_or_contracts=158,local_links=links)))
if __name__=='__main__':main()