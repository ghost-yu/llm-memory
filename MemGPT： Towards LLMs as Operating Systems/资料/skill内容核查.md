# MemGPT 内容要求与证据核查

范围：arXiv:2310.08560v2（13页）的系统机制、原图/主要实验；作者项目历史commit a0139b5fdc203f827168cb741c9f4fea3cec09bf；原CoreMemory/工具执行与本地适度demo。暂不全文翻译、不安装完整历史包或调用付费/外部模型。

| 要求 | 内容位置 | 原文/源码/运行证据 |
|---|---|---|
| 身份、版本、官方来源、边界 | 开头/§1 | 原PDF/元数据、作者历史项目来源；锁定clean SHA，非论文精确experiment release，Python版本约束明确 |
| 论文/代码地图 | §2/7 | 论文方法/图表/附录，CLI→Agent→tools→存储/摘要；明确本地入口与替代后端/缺失环境 |
| 实际执行路径 | §7/9.2/9.3 | 主demo→原AST→host→tool→SQLite→反馈/队列→分页/下一key；官方Agent路径静态阅读不声称运行 |
| 四视图、公式与符号 | §3/6/8.1/9.3 | 文本目的、预算/分页工程公式、对象类型和实际源码；系统没有新训练损失，未虚构Tensor记忆/权重更新 |
| 关键公式步骤/数字/等级 | §3/6/6.1/8.1 | budget拼接与预留、页offset/末页、相似度和ROUGE说明；假设例与原paper编号分开，SIM聚合未确认则保留不确定 |
| 图与参数/训练推理 | §5/7/7.1 | 对照PDF第3页图3颜色/箭头/各框，事件→读写→反馈；模型参数属底层LLM，不属于外部数据库 |
| 实验表和曲线 | §8/8.1 | 对照第5页表2/3、图5及其他轨迹；原数/绝对相对变化、指标方向、参考自比较、成本与可支持结论；曲线不捏造点值 |
| 核心对象完整契约 | §7.1/9.1/9.2 | 原CoreMemory9项+tools5项+本地19项，共33签名实测；Agent等静态所有参数/默认/返回/副作用；实际step5项不同于4项注解 |
| 原代码/API/变量解释 | §6.1/9.3 | 原后端slice、原编辑、原分页、本地调用反馈4块；逐步解释、调用关系、变量表、数据布局与实际例 |
| 首次Python语法 | §9/9.3 | class/object/init/classmethod、self显式/隐式、AST/compile/exec、tuple/推导式、**args、try/except、with、SQL参数绑定；不加入未用PyTorch概念 |
| 连续数据路线、LLM边界 | §7.1/9.3 | 字符串→参数dict→DBtuple/dict列表→格式化str→atomic block→context→regex；未加载tokenizer/attention/KV/LM head/解码/量化，不能说char==token |
| 命令、环境、成功与失败 | §10/README | bundled Python/旧包约束、RAM/disk、18项检查；原search总量不一致、空old/缺old/非法字段/页错误、load丢限制均保留 |
| 文末六项 | §11 | 三等级、Paper↔Code、部分成功证据、缺完整模型/embedding/judge与未知项 |

原文件与主demo均未修改。新trace执行原EmbeddingArchivalMemory.search方法体时，预填充12条假Passage缓存，仅确认原切片/返回/工具页头问题；不能确认真实embedding、HNSW、原Agent运行成功。旧20/20来自adapter的完整total与确定性控制器，说明工具协议/分页机制，不是模型自主检索能力。

人工核对新文明确：原search返回页长被当total、缓存插入后可见性未验证、step注解4/实际5、CoreMemory.load默认无限制、自定义restore并未恢复完整host计数/budget/trace、solve漏召回时可提前把current误判终点。文件自动核验只检查证据一致，不给语义打分。

结论：在上述系统精读与适度demo范围内补齐并核查；完整历史runtime、自主LLM策略、向量检索、递归摘要质量、MSC/Wikipedia原实验仍未复现。整组九篇还剩待核查内容，不将本篇局部通过当作整体目标完成。
