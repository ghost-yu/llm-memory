# Nested Learning 内容要求与证据核查

对象：本地arXiv:2512.24695v1（52页）的主要概念/机制、关键架构与实验，以及链式CMS教学demo。用户暂不做全文翻译，每次完成一篇和小demo；不将完整论文规模训练作为小demo完成条件。

| skill要求 | 当前内容位置 | 原文/源码/运行对照 |
|---|---|---|
| 论文身份、版本、边界 | 开头、§1 | 本地PDF和元数据；单复数标题差异；没有确认官方代码，第三方未冒充作者实现 |
| 论文地图与实现地图 | §2、§11 | 方法/实验/附录地图；本地入口、预训练、模型、更新器、评价、checkpoint与绘图；无官方commit，实际源码hash固定 |
| 执行路径 | §11/11.1—11.4 | main→CMS构造→A预训练→deepcopy→run_one→写前evaluate→forward/loss→update→边界评价/保存 |
| 概念目的/公式/shape/code四视图 | §3—9、§11 | 频率、外积、动量、DGD、CMS、初始化、self-generated target分别解释并标明实际/缺失代码 |
| 核心公式步骤、符号、例子、等级 | §4—9.1 | 外积/EMA/近端56→57/70—74/86—89及94—97；样本、参数、状态布局与数值例子；未实现高阶/通用算法不造实现 |
| 关键架构图箭头、参数、训练推理 | §9.1 | 对照第30页图5，图省略norm，立方栏是学习层级；chunk/BPTT/frequency不混读；本地仅对应CMS段 |
| 实验表/曲线 | §10/10.1、§12 | 表1/2/6原数字与反例；第38页表3—5具体数字/公平性；曲线没有精确数据不造小数；合成任务不等于Agent成功率 |
| 核心函数/方法完整契约 | §11.1 | 实际inspect读取11签名；所有参数默认/类型形状/返回/副作用；局部adaptation未用target参数说明 |
| 核心代码块与API/变量/形状 | §11.2—11.4 | 注册/forward、梯度周期、loss/读写顺序原代码，意义/调用链/API/变量表/数值与掌握等级；12参数Tensor布局 |
| 首次Python/PyTorch语法 | §11及11.2—11.4 | class/继承/init/super/ModuleList与Sequential、推导式、with/no_grad、autograd与backward、原地操作、tuple/生成器；不捏造不存在的decorator |
| 连续变量路线与LLM边界 | §9/11 | 8地址float32输入→[8,32]→[8,8]→loss[]→12梯度→buffers→参数；未含tokenizer/LM head/量化/SFT/真实解码 |
| 命令、资源与实际失败/成功 | 复现README、§12 | 指定解释器/参数解释、CPU/dtype/RAM/disk；16边界检查，0周期失败、短列表漏块、模型checkpoint不是全训练状态 |
| 文末六项 | §13 | 三等级、Paper↔Code表含未找到/未实现、部分成功、未解决问题；原Hope/M3/benchmark未复现 |

新证据：trace_contracts.py读取原代码、独立对照4步更新、核对pending buffer、12参数.grad未填充、冻结参数但输出变化、错误periods与checkpoint边界。contracts_trace.json含原代码SHA-256，16项检查包括负例观察；旧demo数据未修改。旧交付检查仍独立核验9600条块记录、跨seed均值和重载指标。

保留的不确定性：官方仓库/权重的当前可用性；完整MLP的DGD作用、目标detach和gate范围；公式71/75排版、90参考状态索引、92负点积梯度符号；原实验部分指标/split/bin细口径、全部配置、重复方差和成本。主解释没有以本地CPU教学网络取代这些缺失项。

结论：本篇在上述核心阅读与适度demo边界内已补齐并核查。完整Hope、M3、所有理论变体证明/实现与论文规模benchmark仍不是已复现结果；九篇整体目标尚有其余论文待逐条核查。
