from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent.parent
records=json.loads((ROOT/'资料'/'下载清单.json').read_text(encoding='utf-8'))['papers']
repos={
 '2501.00663':('https://github.com/waylandzhang/titans-pytorch','视频作者提供的第三方实现；未确认是 Google 官方代码'),
 '2504.19413':('https://github.com/mem0ai/mem0','Mem0 项目仓库；当前代码不保证等同论文实验版本'),
 '2501.13956':('https://github.com/getzep/graphiti','Zep 的 Graphiti 引擎仓库；不代表完整商业服务'),
 '2310.08560':('https://github.com/letta-ai/letta','MemGPT 后续发展的 Letta 仓库；不是锁定的历史实验版本'),
 '2502.12110':('https://github.com/agiresearch/A-mem','论文页面链接的记忆系统实现'),
 '2402.17753':('https://github.com/snap-research/locomo','LoCoMo 基准仓库'),
 '2410.10813':('https://github.com/xiaowu0162/LongMemEval','LongMemEval 基准仓库'),
}
lines=['# 大模型记忆论文索引','', '整理日期：2026-10-02。已下载 9 篇英文原论文，按论文完整标题建立目录，Windows 不允许的半角冒号替换为全角冒号。', '',
 '本次范围是查找、下载和建立阅读入口。已核对 arXiv 标题、版本、PDF 文件头、可打开性、页数和首页；没有完成全文精读、源码分析或实验复现。下载版本和 SHA256 见 `资料/下载清单.json`。', '',
 '## 视频来源与对应关系','',
 '- [视频一：Google Titans：大模型记忆论文解读](https://www.bilibili.com/video/BV1jjCQB1E7f/)：简介直接链接 Titans 论文，也链接 Google 的 Nested Learning 博客。两篇是不同工作。',
 '- [视频二：一口气搞懂AI Agent五种记忆架构/SQLite/mem0/Zep/LangMem实测竞速](https://www.bilibili.com/video/BV1DabS6vEba/)：简介讨论工程系统，没有给出一份逐项论文列表。Mem0 和 Zep 是按系统名称匹配的论文；其他条目明确作为方向补充。',
 '- 视频对应关系根据 B 站公开 API 返回的标题和简介确定，未观看完整视频、未获得字幕。简介快照已保存到 `资料/BV*.json`。', '',
 '## 两条研究路线','',
 '模型内部记忆研究如何把信息写进可更新的神经记忆状态，涉及测试时学习、关联记忆、遗忘门和多时间尺度更新。Agent 外部记忆研究如何在模型之外存储、更新和检索事实，再把需要的信息放入上下文。两者都叫“记忆”，但实验、代码入口和资源要求不同。', '',
 '| 路线 | 论文 | 与视频的关系 | 原文与下载 |','|---|---|---|---|']
for r in records:
    rel=Path(r['local_pdf']).relative_to(ROOT).as_posix()
    lines.append(f"| {r['category']} | {r['title']} | {r['relation']} | [arXiv](https://arxiv.org/abs/{r['arxiv']}) · [本地 PDF](<{rel}>) · {r['version']} / {r['pages']} 页 |")
lines+=['','## 阅读入口','',
 '如果目标是搭建能跨会话记住用户的 Agent，可以依次看 MemGPT → Mem0 → Zep → A-MEM，并配合 LoCoMo、LongMemEval 检查评测设计。如果目标是研究模型结构和测试时记忆，可以按 Titans → MIRAS → Nested Learning 阅读。这里是根据主题依赖给出的阅读顺序，不是性能排名。','']
for r in records:
    lines += [f"### {r['title']}",'',r['purpose'], '',f"来源：[arXiv:{r['arxiv']}{r['version']}](https://arxiv.org/abs/{r['arxiv']}{r['version']})。",'']
    if r['arxiv'] in repos:
        url,status=repos[r['arxiv']]
        lines += [f'代码入口：[仓库]({url})。{status}。','']
    else:
        lines += ['代码入口：本次未确认可对应论文实验的官方仓库；不以其他同名项目替代。','']
lines+=['## 视频中的其他工程资料','',
 '- [LangMem 官方文档](https://langchain-ai.github.io/langmem/)和[发布说明](https://www.langchain.com/blog/langmem-sdk-launch)：它是长期记忆工具库，本次未找到对应独立论文，不把博客当论文。代码：[langchain-ai/langmem](https://github.com/langchain-ai/langmem)。',
 '- [视频二的 Waku Agent 仓库](https://github.com/ShenSeanChen/Waku-agent)：视频简介给出的工程演示入口，可查找 `examples/memory_native`；本次未分析该目录。',
 '- SQLite、向量数据库属于实现和存储选择，不与这次论文列表逐项对应。',
 '- [Google Nested Learning 博客](https://research.google/blog/introducing-nested-learning-a-new-ml-paradigm-for-continual-learning/)及[作者发布 PDF](https://abehrouz.github.io/files/NL.pdf)。本地保存的是 arXiv v1；不能声称与视频发布时的作者 PDF 逐字一致。','',
 '## 后续精读边界','',
 '【必须会】区分上下文、神经记忆与外部存储；理解写入、更新、遗忘和检索。',
 '【建议会】研究测试时更新规则、时序事实失效、多会话评测和检索误差。',
 '【可以暂时不掌握】分布式训练、服务部署与数据库调优。','',
 'Paper ↔ Code 目前仅确认到仓库入口；具体公式、张量形状和类/函数对应尚未分析。复现状态：未复现。没有克隆代码、安装运行依赖、下载模型权重或调用付费模型。未制作中文译本。']
(ROOT/'论文索引.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

sheet=Image.new('RGB',(1200,1650),'#dddddd')
draw=ImageDraw.Draw(sheet)
for i,r in enumerate(records):
    path=Path(r['local_pdf']).parent/'资料'/'首页.png'
    img=Image.open(path).convert('RGB'); img.thumbnail((380,510))
    x=(i%3)*400+(400-img.width)//2; y=(i//3)*550+30
    sheet.paste(img,(x,y)); draw.text(((i%3)*400+15,(i//3)*550+8),r['arxiv']+' '+r['version'],fill='black')
sheet.save(ROOT/'资料'/'PDF首页核验.png')
print('Indexed',len(records),'PDFs; bytes:',sum(r['bytes'] for r in records))
