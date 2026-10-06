# Mem0 内容要求与证据核查

范围：本地arXiv:2504.19413v1（23页）的基础事实流水线、图变体、主要实验；mem0ai/mem0锁定历史commit 6d13e8300143b61aefc3a1ab5fb936f6d52008a4；原八方法+辅助对象在受控provider/SQLite上的机制demo。用户暂不全文翻译，不把完整模型benchmark当小demo完成条件。

| 要求 | 内容位置 | 核对依据/结论 |
|---|---|---|
| 身份版本、来源、边界 | §1 | 原PDF/元数据/作者历史repo/commit/包版本，非确定的实验release；官方完整评测入口未找到 |
| 论文地图/仓库地图 | §1 | 方法/图/算法/实验/附录与config/prompts/main/utils/storage/graph/providers；无新网络训练/checkpoint |
| 执行路径 | §4/7 | str→add身份/并行分支→parse/提示→facts→embedding/top5→UUID映射→JSON动作→库/历史→search，替代处明确 |
| 目的—公式—类型—代码 | §3—5/7.4 | 提取P/Ω、余弦、四动作、图三元组，系统对象shape与LLM token shape分开 |
| 关键公式符号、步骤、例子和等级 | §3.1—3.3/6.4 | 关键公式已LaTeX；t/m/n/s/d明确、消息/向量例子；F1/词精度/judge/分位数示例为解释而非原评分复现 |
| 关键图 | §3/3.3/5/5.1 | 直接对照PDF第4/5页图2/3，箭头/独立summary/实体关系/冲突/数据库、参数与非训练运算、缺图运行的边界 |
| 原实验表/曲线 | §6.1—6.4 | 表1分类与反例、表2质量/token/延迟、公平性、绝对与相对差；graph多跳下降；std不是CI，写入成本未计入回答指标 |
| 函数契约 | §7.1—7.3/5.1 | 28实际签名含原8方法/4辅助/3历史/13替代与入口，全部参数默认、返回、变更、调用位置；额外graph核心静态契约/实际limit差异 |
| 原代码块与变量shape | §4/7.4 | 并行、临时ID、提取/创建/检索代码，目的/API/步骤/变量表/shape/对应公式/等级，str/list/dict而非虚构Tensor |
| Python/PyTorch | §4/7.2—7.4 | self/type/AST、Pydantic继承/Field、推导式/字典展开、Future/with/锁、f-string/异常；未用torch不制造训练步骤 |
| 连续数据路线与LLM范围 | §3.3/7.4 | 64列表向量、ID映射、对象/JSON流；真实tokenizer/Transformer/KV/解码/量化/SFT未运行，抽取/更新模型未训练 |
| 命令、配置、资源与失败 | README/§4.5/7 | 原13断言/14provider/5记录保留；新14边界检查有故意错误、None值范围、metadata丢字段、跨库部分失败；环境/资源/命令明确 |
| 文末六项 | §8 | 三等级、Paper↔Code含未找到、部分成功的证据/未运行项、未知问题 |

新trace只在临时两库执行，原源码/主demo/旧数据库未改。实验显示NONE和BAD_JSON都仍2次provider；UPDATE新metadata丢旧custom；None-valued身份键可通过；零query向量score0也返回；坏ID动作被跳过而下一ADD成功；history故障发生在向量写入之后。测试通过包含这些负例，不证明生产隔离、事务或自然语言质量正确。

图路径未执行：静态核查graph.search实际list输出/写死top5，代码DELETE r不同于论文invalid关系。官方全模型SDK/Neo4j/真实embedding与LoCoMo评分均未验证，不能将repo名称或paper题目当可靠性认证。

结论：本篇核心阅读与适度机制demo已补齐并核查。完整论文模型/所有后端/图时间推理/benchmark仍未复现；整组九篇目标继续，尚有其余论文待逐条核查。自动核验仅来源、签名、证据、文件一致性，不能给本表语义判分。
