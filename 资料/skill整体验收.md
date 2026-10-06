# 九篇论文的 skill 整体验收

2026-10-05。目标来自用户要求按 [paper-code-deep-reading](C:/Users/hgfhg/.codex/skills/paper-code-deep-reading/SKILL.md) 完成大模型记忆方向精读；按 [reading-playbook](C:/Users/hgfhg/.codex/skills/paper-code-deep-reading/references/reading-playbook.md) 检查。沿用用户已选择的九篇范围、每次完成一篇、不全文翻译和适度demo。完整训练/商业部署/所有模型benchmark不作为此次小demo交付要求。

九篇的中文解释、PDF、代码或明确未找到说明、复现README/scripts/outputs/图片/资料均保留。本轮逐篇修改并按原PDF/源码/运行结果核对，当前整组已完成9/9。自动审计仅核来源、签名、实测/文件/链接一致性；内容是否准确依赖逐篇人工核对，不能以文件存在或标题命中推断合格。

| 篇目 | 当前内容记录 | 已执行本轮条件/签名契约 | 复现状态 |
|---|---|---|---|
| Titans | [逐项记录](<../Titans： Learning to Memorize at Test Time/资料/skill内容核查.md>) | 15 / 11；第三方原模块与MAC/状态边界 | 部分成功 |
| MIRAS | [逐项记录](<../It's All Connected： A Journey Through Test-Time Memorization, Attentional Bias, Retention, and Online Optimization/资料/skill内容核查.md>) | 13 / 5；Huber/归一化/漂移机制 | 部分成功 |
| Nested Learning | [逐项记录](<../Nested Learning： The Illusion of Deep Learning Architectures/资料/skill内容核查.md>) | 16 / 11；CMS更新周期/梯度/冻结/重载 | 部分成功 |
| MemGPT | [逐项记录](<../MemGPT： Towards LLMs as Operating Systems/资料/skill内容核查.md>) | 18 / 33；原CoreMemory/工具/分页接口 | 部分成功 |
| Mem0 | [逐项记录](<../Mem0： Building Production-Ready AI Agents with Scalable Long-Term Memory/资料/skill内容核查.md>) | 14 / 28；动作/metadata/身份/两库失败 | 部分成功 |
| Zep | [逐项记录](<../Zep： A Temporal Knowledge Graph Architecture for Agent Memory/资料/skill内容核查.md>) | 16 / 20；UTC/旧边引用/日期/排序 | 部分成功 |
| A-MEM | [逐项记录](<../A-MEM： Agentic Memory for LLM Agents/资料/skill内容核查.md>) | 23 / 24；链接/演化/索引/失败残留 | 部分成功 |
| LoCoMo | [逐项记录](<../Evaluating Very Long-Term Conversational Memory of LLM Agents/资料/skill内容核查.md>) | 27 / 12；评分/截断/真实tensor池化 | 部分成功 |
| LongMemEval | [逐项记录](<../LongMemEval： Benchmarking Chat Assistants on Long-Term Interactive Memory/资料/skill内容核查.md>) | 28 / 14；原索引/扩展/日期/提示/judge语句 | 部分成功 |

合170项机制/边界条件与158个签名/契约。条件含刻意触发的失败和局限，签名含未执行模型工厂/静态接口，数字不等于测试覆盖率、模型准确率或论文完整复现。各篇trace/JSON区分实际运行、仅静态核对和受控替代。

逐项验收依据如下，每项在九份内容记录中定位到解释章节与原材料：
1. 精确论文版本/作者/日期、仓库身份/commit或未找到、阅读范围；官方/第三方/教学代码分开，缺实验精确release不补造。
2. 论文问题/贡献/方法/公式/图表/局限地图；README/依赖/入口/数据/模型或外部provider/指标/checkpoint/缺失资源地图。
3. 真实入口→数据→构建→核心运算→输出→评价链；原完整入口未运行明确静态，本地可执行链保存证据。
4. 核心概念目的→公式→type/shape→具体代码四视图，系统对象不伪装神经权重。
5. 关键式LaTeX/符号索引/类型形状/小步骤/数值例/直觉/映射/掌握等级；未确认布局/记号明确待解，不编造所有理论证明。
6. 关键原图框/箭头/参数/输入输出/训练推理与源码对应；Zep原文无编号架构图，教学流明确不是论文原图。
7. 表/曲线数据任务/指标方向/基线/精确绝对相对变化/公平性/可支持结论和边界；没有数据点的曲线不捏造；异常原表数字保留。
8. 核心方法owner、所有参数/默认/type/shape、return/修改、调用位置/论文/等级；类型注解与实际返回差异已校正解释。
9. 关键原代码用途/位置/API/有效行/变量表/shape/论文/例子/等级，非只贴大块。
10. 首次Python/PyTorch语法按真实出现解释，连续变量流可追踪；未有nn.Module/损失/量化等不虚构。
11. 复现级别/环境/资源/命令与配置/真实输出/失败/限制；受控provider、hash/BM25、AST隔离、CPU例子不冒充完整模型。
12. 中性命名/目录与文末六项：三等级、Paper↔Code必要时标未找到、部分成功证据、未解决问题。未提供全文中文论文，不宣称已翻译。

当前源文件/文档已逐篇核查。整体验收又读取全部九份内容记录、对照此前已实际精读的原材料/运行证据，并检查当前报告哈希仍匹配文档和脚本。LoCoMo内容记录中“prompt未运行”的旧表述已改为受控上下文构造；LongMemEval仓库地图的静态说法已改为原toy提示构造。未留下待逐条内容核查的论文。

早期逐篇记录中“其余篇待推进”等句子为该篇完成当时的历史状态，不覆写证据以改变历史；当前全局状态以本记录和skill补齐进度为准。未完成的原论文全量训练/全部数据/真实API/生产性能列为研究和后续实验事项，已在解释中逐项标边界，不是这次精读交付中被隐藏的遗漏。

可重跑 [整组一致性脚本](skill整体验收.py)，结果 [JSON](skill整体验收.json)；技术 [最终核验](最终核验.json)另查9篇/228PDF页和主交付链接。脚本通过不自动证明语义；上表和要求对应才是本轮内容验收依据。研究结论仍须遵循每篇“部分成功”和来源不确定性的限定。