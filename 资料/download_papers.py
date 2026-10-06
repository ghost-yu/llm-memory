from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests, re, json, hashlib
from bs4 import BeautifulSoup
import fitz

ROOT = Path(__file__).resolve().parent.parent
PAPERS = [
 ('2501.00663', 'Titans: Learning to Memorize at Test Time', '模型内部记忆', '视频一直接链接', '测试时通过神经记忆模块写入和检索信息。'),
 ('2504.13173', "It's All Connected: A Journey Through Test-Time Memorization, Attentional Bias, Retention, and Online Optimization", '模型内部记忆', 'Google 博客关联工作（MIRAS）', '用关联记忆、学习目标、保留机制和更新算法统一分析序列模型。'),
 ('2512.24695', 'Nested Learning: The Illusion of Deep Learning Architectures', '模型内部记忆', '视频一简介所链接 Google 博客的论文', '讨论多层优化、不同更新频率的记忆，以及 Hope 架构。'),
 ('2504.19413', 'Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory', 'Agent 外部记忆', '对应视频二提及的 Mem0 系统', '从对话抽取、整合和检索事实，并讨论图记忆扩展。'),
 ('2501.13956', 'Zep: A Temporal Knowledge Graph Architecture for Agent Memory', 'Agent 外部记忆', '对应视频二提及的 Zep 系统', '用时序知识图谱追踪事实、关系及其时间变化。'),
 ('2310.08560', 'MemGPT: Towards LLMs as Operating Systems', 'Agent 外部记忆', '方向补充，未确认视频逐字讨论该论文', '借鉴操作系统分层内存，让 Agent 管理有限上下文与外部存储。'),
 ('2502.12110', 'A-MEM: Agentic Memory for LLM Agents', 'Agent 外部记忆', '方向补充，未确认视频逐字讨论该论文', '让记忆形成带关联的笔记，并随新信息组织和演化。'),
 ('2402.17753', 'Evaluating Very Long-Term Conversational Memory of LLM Agents', '记忆评测', '方向补充：LoCoMo，Mem0 论文使用的基准', '评估长时间、多会话对话中的记忆能力。'),
 ('2410.10813', 'LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory', '记忆评测', '方向补充：Zep 论文使用的基准', '检查信息提取、跨会话推理、时间推理、知识更新和拒答能力。'),
]

def download(item):
    ident, title, category, relation, purpose = item
    folder = ROOT / re.sub(r'[<>:"/\\|?*]', '：', title)
    info = folder / '资料'
    info.mkdir(parents=True, exist_ok=True)
    r = requests.get('https://arxiv.org/abs/' + ident, timeout=60)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    found_title = soup.find('meta', attrs={'name':'citation_title'})['content']
    if found_title.casefold() != title.casefold():
        raise ValueError('Title mismatch: ' + found_title)
    meta = soup.find('meta', attrs={'name':'citation_pdf_url'})
    pdf_url = meta['content'] if meta else 'https://arxiv.org/pdf/' + ident
    versions = re.findall(r'\[v(\d+)\]', soup.get_text())
    version = 'v' + str(max(map(int, versions))) if versions else '未提取'
    if version != '未提取':
        pdf_url = 'https://arxiv.org/pdf/' + ident + version
    p = requests.get(pdf_url, timeout=90)
    p.raise_for_status()
    if not p.content.startswith(b'%PDF-'):
        raise ValueError('Not a PDF: ' + ident)
    path = folder / '原论文.pdf'
    path.write_bytes(p.content)
    doc = fitz.open(path)
    first_text = doc[0].get_text()
    (info / '首页文本.txt').write_text(first_text, encoding='utf-8')
    doc[0].get_pixmap(matrix=fitz.Matrix(0.8,0.8)).save(info / '首页.png')
    record = dict(arxiv=ident, title=title, category=category, relation=relation,
        purpose=purpose, version=version, pdf_url=pdf_url, local_pdf=str(path),
        pages=len(doc), bytes=len(p.content), sha256=hashlib.sha256(p.content).hexdigest(),
        authors=[m['content'] for m in soup.find_all('meta', attrs={'name':'citation_author'})])
    (info / '论文元数据.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    (info / 'arxiv页面.html').write_text(r.text,encoding='utf-8')
    doc.close()
    return record

if __name__ == '__main__':
    records, errors = [], []
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(download,p):p for p in PAPERS}
        for f in as_completed(jobs):
            try:
                result=f.result(); records.append(result)
                print(result['arxiv'],result['version'],result['pages'],'pages',flush=True)
            except Exception as e:
                errors.append({'arxiv':jobs[f][0],'error':str(e)})
                print('FAILED',jobs[f][0],str(e),flush=True)
    records.sort(key=lambda r: [p[0] for p in PAPERS].index(r['arxiv']))
    (ROOT / '资料' / '下载清单.json').write_text(json.dumps({'papers':records,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
