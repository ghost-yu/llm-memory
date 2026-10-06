# LongMemEval 的 skill 内容核查

2026-10-05，人工对照SKILL.md/reading-playbook。来源2410.10813v2原PDF28页、全文/渲染、8a44eb1bb033842b12c67c594ac2094fc3028526源码、原始S数据固定revision与SHA256。解释v2和历史公开实现，不把后续清理/V2当本篇。保持用户不全文翻译、小demo边界。

| 要求 | 内容/权威证据 | 结论与边界 |
|---|---|---|
| 身份与范围 | §1原PDF、元数据/代码版本/数据来源 | 作者/日期/revision/字节/哈希清楚，M未下载，实验提交精确映射未知 |
| 论文/仓库地图 | §2/6，index/retrieval/generation/evaluation | 检索/阅读/标签分开，无新训练loss/checkpoint，在线循环未找到运行证据 |
| 执行路径 | §6/7/9.1–9.3，60原题与提示toy | AST避API/CUDA；constructor绕过；key不带答案/has_answer，只在评分用label |
| 概念四视图 | §3–5/9.1–9.4 | 五能力六源码类别与ABS重叠；key/value、粒度、矩阵形状与原BM25分开 |
| 关键公式协议 | 实例/key/检索/DCG/BM25/日期稳定分组 | 符号/索引/shape/步骤/数值/直觉/源码/等级；第二名折扣=1不是通常log2(j+1) |
| 图协议 | 本轮看原page_07.png图4，§8/9.4 | CP红虚线为控制点、蓝虚线为集合、key/value箭头/Question/reader/参数和无loss明示 |
| 实验协议 | §8图3/5/6、表3/4、judge表6 | 正例Oracle/真实长历史/预算/精确增益、公平性与局限；相对与百分点补齐 |
| 核心完整契约 | §9.1及14真实签名，CLI默认和demo宿主 | 参数/默认/类型/返回/引用修改/调用/对应/等级；14含constructor/工厂签名未执行 |
| 原代码协议 | §5.3/9.2索引扩展/9.3清标签judge/9.4日期 | 原块/目的/API/行/变量表/shape/公式/等级/例子完整，非只贴代码 |
| Python语法 | §6/9.1–9.4 | class/self/object.__new__/AST、list/dict推导式、all空、+=引用、pop原对象、子串、with/异常；无训练autograd场景，不编造 |
| 连续变量流 | §7真实54session例，§9.2–9.4 | 文本/ID/date平行列表→BM25→位置→value→prompt；字典来源标签不进入key |
| 环境、命令与失败 | README/原13checks120记录；新增28/14 | CPU/3.7.6/NumPy1.21.6/vendor BM25；bad类型/日期/缺end/部分输入修改记录 |
| 文末六项 | §10 | 三等级/PaperCode未找到/部分成功+证据/待解问题齐全 |

人工重点：
1. 用户侧索引assistant-only空文本/noans，turn零文档；用户has_answer缺失KeyError，turn数字1可过bool成员断言。原9题空gold单列，不修作者口径掩盖。
2. gold空any0/all1/NDCG0；ranking若重复NDCG可超1，真实60题排列检查已通过，不能把负例当真实结果。turn2session通过增effective_k覆盖k个不同session，预算不同。
3. 扩展separate原地改平行列表、split-merge新列表重复ID；空userfact list可删除匹配key，None只添加空前缀；未运行sent_tokenize分支。
4. infer_time_range对JSON missing end未完整校验，increment_date负责真实日历；日期start hack保留。原turn时间块用子串，s1误命中s10_1，已隔离执行证明。
5. 原prepare_prompt flat-turn恢复当前与下一消息，pop原entry里has_answer；useronly=True TypeError从静态风险升级实测；toy不写278MB原数据。
6. flat k0无历史断言，orig k0全历史，token预算0截后仍构造问题。word-count tokenizer与受控CoN只证明提示流程，未证明真实阅读质量。
7. 原judge标签'yes'子串把Yesterday否定文本计真，原语句执行而非API；模板质量/人工约97–98%一致率不是所有输出的保证。
8. 图4控制点虚线不表示梯度；表3/4和图6有正负/交互，不把所有格说为改进、不跨2024/2026产品排名。

环境Windows11Pro，物理可见16454352KiB≈15.69GiB，G盘约37.28GiB快照；AnacondaPython3.7.6/NumPy1.21.6/vendor rank-bm25 0.2.2，CPU，无模型/付费API/GPU训练。S原278,025,796bytes哈希固定，M2.745GB未下载；完整官方Linux/CUDA环境未安装。

证据：[新增JSON](../复现/outputs/contracts_trace.json)、[原打印和失败](../复现/outputs/contracts_stdout.txt)、[新增脚本](../复现/scripts/trace_contracts.py)、[原60题检索](../复现/outputs/results.json)、[一致性核验](../复现/outputs/skill_revision_check.json)。自动脚本验证哈希/干净提交/签名/观察/链接，不评分中文语义；旧audit逐原题/排名/原口径/诊断均值重查。

复现状态：**部分成功**。本篇阅读与小demo修订核查完成；真实Stella/事实生成/日期推断/CoN答案/judge/完整benchmark未复现。九篇各自均需保持这一范围，整体验收另检查当前所有文档与证据，不能把28个构造条件当论文成绩。