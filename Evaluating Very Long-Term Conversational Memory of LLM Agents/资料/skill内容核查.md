# LoCoMo 的 skill 内容核查

2026-10-05。对照SKILL.md/reading-playbook人工核对，脚本不自动评定中文语义。主来源2402.17753v1原PDF19页、全文/渲染和锁定3eb6f2c585f5e1699204e3c3bdf7adc5c28cb376仓库；阅读初版论文与晚期公开10组子集，严格区分版本。暂不全文翻译，使用用户小demo边界，不要求付费模型/全部训练。

| 要求 | 内容与权威证据位置 | 结论/边界 |
|---|---|---|
| 身份与范围 | §1原PDF/版本JSON/README | v1日期、作者、代码晚于v1；50组/7512与10组/1986不同 |
| 论文与仓库地图 | §1，task_eval/generative_agents/scripts/data/requirements | Conda导出非pip要求；完整事件/MiniGPT-5入口未找到，README仍Coming soon |
| 真实路径 | §5/7/7.1，evaluate_qa parse_args→backend→score；本地documents→BM25→recall | 未运行回答器，prediction空串仅用原recall，gold不进入排名 |
| 概念四视图 | §2–5/7.1–7.4 | persona/事件/观察/摘要/gold区别，向量与离散结构区别 |
| 数学协议 | 时间条件、单/多答案F1、evidence recall、BM25、mean_pooling | 符号/类型/步骤/微例/源码/等级；集合教学符号与原标注list计数不同；BM25 unique query/max(avg,1)已纠正 |
| 图协议 | 原图3本轮查看page-5.png，§2.4；任务图2/图4对应§3/6 | 信息方向/虚线可选图像/参数模型/shape/推理与另任务训练区分 |
| 实验协议 | §6表2/3/4和图4、附录表5/6，原PDF和page-7渲染 | 指标/模型/数据/k/数值/公平性/上限；247.4非法比例和32.1/32.4不一致保留，不自行修数 |
| 核心函数契约 | §7.1，11运行签名+pooling1；入口CLI全部默认 | owner/参数/默认/返回/状态/调用/论文/等级，metric参数/lens/空batch真实语义 |
| 核心原代码协议 | §7.2F1/recall，7.3池化，7.4上下文循环 | 原块→目的→API→有效行→变量表→shape→映射/例子→等级 |
| Python/PyTorch语法 | §7.1–7.4 | 无self函数与BM25方法、推导式/Counter&/切片/with捕获、masked_fill/bool/broadcast/sum/autograd；无新nn.Module模型，不编造 |
| 连续变量流 | documents/terms/BM25/QA/池化逐步流 | query-only，turn/session不同单位，Tensor[B,L,d]→[B,d]；上下文构造以受控tokenizer执行，真实模型没运行 |
| 环境/命令/失败/实测 | README；旧9检查/1536题；新增22+5，JSON/stdout | 3.7.6词面与3.12.14/torch2.14.1cpu两runtime；错误/NaN记录而非隐去 |
| 文末六项 | §8 | 三等级、PaperCode、未找到、部分成功证据与待解问题均明确 |

人工重点：
1. normalize删逗号/标点不替换空格，red,car合成redcar；词干F1与set EM不一致，空F1=0/EM=True。
2. metric='exact_match'不切换评分，category3参考分号只取第一段；category5关键词即使含否定仍给1。
3. evidence非空/context空IndexError；缺context/空evidence默认recall1；第一context字符控制整路粒度；重复标注按次数计数。真实1536题已排除空evidence且各k取回非空，不靠默认1抬高。
4. 原get_input_context逐会话升序，预算不足保留旧内容不含新内容，仍加新DATE标题。word-count预算14明确触发，初19探针可容纳两段因而断言失败，检查后调整输入，不改原函数。不是实际GPT tokenizer能力测试。
5. 原mean_pooling仅bool mask筛分子而原数值mask求分母；二值正常，全零NaN，非二值不等于权重均值。真实torch验证输入不变/梯度，不能推断完整rag_utils模型跑通。
6. BM25查询set去重复、avg分母max1、空词0分按原序；索引只可见date/speaker/text/caption，标注排名后使用。教学BM25不等于原DRAGON。
7. 新审核复算一条真实top50排名与旧文件相符、Recent10均值一致；旧audit复核1536题的question/evidence/recall、9异常与数据数量。没有问答LLM正确率。
8. 图3的数据生成LLM记忆与被测QA模型分开，图片/人工阶段未运行，完整事件FactScore和MiniGPT-5不冒充已复现。

资源：Windows11Pro，物理可见内存16454352KiB≈15.69GiB、G盘37.28GiB为本轮快照。评分宿主Anaconda3.7.6/NumPy1.21.6/NLTK3.4.5/regex2.5.141；池化复用Titans现有venv3.12.14/torch2.14.1+cpu，单线程，不新建模型/GPU训练/API请求/图像下载。原linux-64完整依赖未安装。

证据：[新增评分追踪](../复现/outputs/contracts_trace.json)、[张量追踪](../复现/outputs/pooling_trace.json)、[原打印与故意失败](../复现/outputs/contracts_stdout.txt)、[原1536题结果](../复现/outputs/results.json)、[一致性核验](../复现/outputs/skill_revision_check.json)。脚本核哈希/干净提交/签名/观察/链接，不证明中文自动合格。

复现状态：**部分成功**。27项构造边界条件和12签名与旧9检查已核查；真实LLM/原检索器/初50组/事实及视觉评测未复现。当前篇阅读与机制修订完成，九篇整体还需LongMemEval，目标未完成。