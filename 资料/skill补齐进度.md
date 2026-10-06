# 按 paper-code-deep-reading 补齐进度

当前目标是对已交付九篇逐条核对 skill 及 reading-playbook，并补足内容。之前“九篇主体精读与小demo完成”的交付仍保留，但文件核验不能证明这次内容验收完成。用户要求暂不全文翻译；每次完成一篇，完整论文训练不作为小demo的完成要求。

核查依据：[SKILL.md](C:/Users/hgfhg/.codex/skills/paper-code-deep-reading/SKILL.md)、[reading-playbook.md](C:/Users/hgfhg/.codex/skills/paper-code-deep-reading/references/reading-playbook.md)。

每篇检查：身份与版本；论文/仓库地图；真实执行路径；目的—公式—类型形状—源码四视图；关键公式符号/步骤/例子/等级；架构图箭头与训练推理；实验条件/变化/公平性/边界；核心函数完整契约；核心原代码逐步解释与变量表；首次Python/PyTorch语法；连续形状流；命令/环境/真实成功及失败；文末六项。

记录内容位置和原PDF/源码/运行证据，并人工对照说明是否准确。自动脚本只核验文件、来源、签名、实测结果与链接一致性，不自动给中文内容判合格。

| 论文 | 本轮状态 | 证据/下一步 |
|---|---|---|
| Titans | 已修订并核查 | [内容记录](<../Titans： Learning to Memorize at Test Time/资料/skill内容核查.md>)；[运行与文件证据](<../Titans： Learning to Memorize at Test Time/复现/outputs/skill_revision_check.json>) |
| MIRAS | 已修订并核查 | [内容记录](<../It's All Connected： A Journey Through Test-Time Memorization, Attentional Bias, Retention, and Online Optimization/资料/skill内容核查.md>)；[运行与文件证据](<../It's All Connected： A Journey Through Test-Time Memorization, Attentional Bias, Retention, and Online Optimization/复现/outputs/skill_revision_check.json>) |
| Nested | 已修订并核查 | [内容记录](<../Nested Learning： The Illusion of Deep Learning Architectures/资料/skill内容核查.md>)；[运行与文件证据](<../Nested Learning： The Illusion of Deep Learning Architectures/复现/outputs/skill_revision_check.json>) |
| MemGPT | 已修订并核查 | [内容记录](<../MemGPT： Towards LLMs as Operating Systems/资料/skill内容核查.md>)；[运行与文件证据](<../MemGPT： Towards LLMs as Operating Systems/复现/outputs/skill_revision_check.json>) |
| Mem0 | 已修订并核查 | [内容记录](<../Mem0： Building Production-Ready AI Agents with Scalable Long-Term Memory/资料/skill内容核查.md>)；[运行与文件证据](<../Mem0： Building Production-Ready AI Agents with Scalable Long-Term Memory/复现/outputs/skill_revision_check.json>) |
| Zep | 已修订并核查 | [内容记录](<../Zep： A Temporal Knowledge Graph Architecture for Agent Memory/资料/skill内容核查.md>)；[运行与文件证据](<../Zep： A Temporal Knowledge Graph Architecture for Agent Memory/复现/outputs/skill_revision_check.json>) |
| A-MEM | 已修订并核查 | [内容记录](<../A-MEM： Agentic Memory for LLM Agents/资料/skill内容核查.md>)；[运行与文件证据](<../A-MEM： Agentic Memory for LLM Agents/复现/outputs/skill_revision_check.json>) |
| Evaluating | 已修订并核查 | [内容记录](<../Evaluating Very Long-Term Conversational Memory of LLM Agents/资料/skill内容核查.md>)；[运行与文件证据](<../Evaluating Very Long-Term Conversational Memory of LLM Agents/复现/outputs/skill_revision_check.json>) |
| LongMemEval | 已修订并核查 | [内容记录](<../LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory/资料/skill内容核查.md>)；[运行与文件证据](<../LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory/复现/outputs/skill_revision_check.json>) |

进度：9/9；本轮精读修订与逐项内容核查已完成。整体验收见 [要求与证据](skill整体验收.md) 和 [文件/来源一致性](skill整体验收.json)。Titans新增15项检查包含负例：5→3非整块续接失败，mask关闭loss仍有衰减；原模块未修复，不将检查通过描述为完整源码无bug。

MIRAS新增13项机制/契约边界检查通过；保留向量value广播的使用限制，纠正表4的消融标签，并将联合/每列simplex、三种多维Huber区别写清。完整Moneta/Yaad/Memora语言模型及原论文表格仍未复现。

Nested新增16项机制/契约边界检查、11个真实签名；慢块参数冻结不意味着输出冻结，0周期失败和短periods静默漏块均已记录，checkpoint只保存模型状态。旧9600条更新记录/快照/重载指标再次核查通过；完整Hope/M3和原规模benchmark仍未复现。

MemGPT新增18项原函数/替代后端边界检查、33个真实签名；原EmbeddingArchivalMemory.search返回页长却被工具当总量，已用预填充缓存隔离执行证明，原源码未改。Agent.step实际5项与注解4项差异亦记录。旧20条轨迹/SQLite再核查通过，不能当作完整Agent或语义检索复现。

Mem0新增14项边界检查、28个真实签名；NONE/坏JSON仍2阶段调用、metadata修改和丢字段、None范围键、零向量返回、无效动作后继续与跨库部分失败均明确。旧13检查/14provider/5记录及SQLite历史重新核验通过；真实模型、图后端、原benchmark未复现。

Zep新增16项边界检查、20个真实签名；原候选fact在区间判断前修改、None日期保留旧有效期、重复仍三任务、UTC假设及RRF错误输入均有实测。原14项/16响应/5SQLite快照重查通过；托管服务、完整包、真实模型与DMR/LongMemEval未复现。该篇完成后为6/9；A-MEM已接着完成核查。

A-MEM新增23项边界观察/24真实签名，包含重复ID字典与索引不齐、阈值0及后续action失败残留、坏JSON/分析回退错误、原k0全返回与替代空结果差异、负/重复/越界链接。原14项/6评测响应和1986题数据重查；真实模型/Chroma/QA数字未复现。该篇完成后为7/9；LoCoMo已接着完成核查。

LoCoMo新增22项评分/上下文/宿主条件及5项真实CPU PyTorch池化条件，合27项/12签名；context空列表、参数不切EM、列表标注/首ID粒度、旧会话预算优先及全零mask NaN均明确。原1536题/9检查、真实排名回放和均值重查通过。该篇完成后为8/9，LongMemEval已接着完成；真实QA/DRAGON/事件/视觉任务未复现。

LongMemEval新增28条件/14原签名，原60题120排名、13检查、各口径均值重查；原提示pop标签、useronly异常、扩展空列表、缺end、时间子串和judge Yesterday误判均有实测。当前全部9/9已逐项核查，170条件/158签名契约汇总及当前哈希一致性通过。论文完整训练/真实模型benchmark仍未复现，各篇均保留部分成功状态。
