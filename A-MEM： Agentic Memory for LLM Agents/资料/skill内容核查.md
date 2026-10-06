# A-MEM 的 skill 内容核查

2026-10-05，按 SKILL.md / reading-playbook 逐项人工核对，不把自动文件脚本当中文语义评分。原资料：2502.12110v11原PDF28页、全文/渲染图、两份锁定仓库、原demo及本轮隔离原方法执行。保持用户暂不全文翻译、小demo边界，一篇完成后再进入下一篇。

| 要求 | 已检查的内容 / 权威证据 | 判定和限制 |
|---|---|---|
| 精确身份与边界 | §1版本v11/作者/日期；资料/代码版本.json；原PDF | 区分v1、v11和评测/系统两仓，提交不冒充实验确切版本 |
| 论文/仓库地图 | §1；memory_layer/test_advanced/load_dataset/utils/data；系统retriever/controller | 数据与QA入口找到，DialSim/百万规模确切复跑入口未找到：两锁定仓库Python/README相关关键词检索无命中 |
| 真实路径 | §6/9，原constructor→analyze→process→dict/index→query→consolidate | 原方法体执行，模型/128哈希adapter与真实原检索器probe分开 |
| 目的—数学—类型—源码 | §3–5及9.1–9.3 | 七字段/向量/候选/链接/旧元数据，不把演化说成梯度学习 |
| 关键公式协议 | 原PDF§3式1–10；§3–5/9.3 | 符号/索引/列表长度/余弦小例/步骤/映射/等级；式6左侧L_i与文字新笔记符号差异保留 |
| 图协议 | 图片/page-3.png本轮视觉核对，§5/9.3 | 图2盒/箭头/外部参数模型/无训练支路/写读形状；box概念非编造类 |
| 实验协议 | §8/9.3；原表1–4、图3、附录 | 原数/百分点相对差、k调参、类别列疑点、数据范围、费用/存储/时间边界；不自行修论文单位 |
| 核心完整契约 | §9.1；24真实签名；系统原选定方法/MemoryNote静态核对 | 默认/全部参数/类型/返回/修改/调用链/映射/等级；save/load签名和行为静态，未冒充缓存复现 |
| 原代码块协议 | §6/9.2：旧邻居更新、原retriever search、链接循环 | 原代码→目的→调用位置→API→有效行→变量表→shape→例子→公式→等级 |
| Python首次语法 | §6/9.2 | self/class/staticmethod/classmethod/kwargs/with/切片/推导式/引用/异常；无nn.Module/autograd，不填不存在模块 |
| 连续变量流 | §3–6/9.2–9.3 | 文本→结构响应→笔记→[N,d]→索引[C]→元数据修改→文本；384/128/二维probe区分 |
| 命令、环境、失败和证据 | README；results原14条件；contracts_trace新增23/24；stdout | Win11Pro/Python3.12.14/NumPy2.3.5；原requirements另列；不掩盖越界/部分修改/错误回退 |
| 文末六项 | §10 | 三等级/PaperCode/未找到说明/部分成功和证据/未解问题 |

人工重点：
1. 原MemoryNote.links注解Dict，但评测路径实际整数list；系统路径实际记忆ID，不能混同。
2. analyze_content JSON失败返回原str，构造才出错；provider先失败，except中的response未绑定产生第二个错误。受控JSON/type负例绕过真实provider校验，非证明后端必定输出非法JSON。
3. duplicate id让dict1/corpus2，原find索引可能IndexError。evo_threshold0报错前已写dict/文档、evo_cnt递增，无自动回滚。
4. 原邻居循环受tags长度限制，contexts不足回退；未知actions忽略但label仍真；前update成功后strengthen失败不会恢复旧字段。
5. 负位置与重复链接被Python直接接受，越界会失败；append先于j检查导致k1重复邻居两次，返回非严格k。
6. 原SimpleEmbeddingRetriever的NumPy[-k:]在k0返回全库，128哈希替代器k0为空。这次执行原class method，encode/cosine为受控二维协作者，不是MiniLM/sklearn导入验证。
7. 原retriever首次corpus直接引用documents，重复文档保留多行、document_ids同文本覆盖到最后位置；所有文档/笔记位置要一起看。
8. 系统错排名位置和[:k]丢邻居仍由原旧demo证明，没有修补源码掩盖。
9. utils.calculate_metrics用set token而不是计数式F1；中文小例按原表达式计算，未import会下载NLTK/模型的完整utils。
10. v11表头与正文“两倍”的不一致、7512/1986范围、表8最佳k、百万3.7µs边界均保留为待解；未据demo宣称问答性能。

本轮实测23条件/24签名，通过包含失败局限的观察，旧14条件/6评测响应和系统1响应独立保存。两个仓库HEAD和原源码哈希由audit复核，仓库无本轮修改。资源快照：Windows11Pro，物理可见16454352KiB≈15.69GiB，G盘空闲约37.28GiB；标准库/NumPy CPU执行，无新模型/付费请求/GPU训练。原依赖环境未安装，完整QA数据/k/后端协议未重跑。

证据：[追踪JSON](../复现/outputs/contracts_trace.json)、[追踪脚本](../复现/scripts/trace_contracts.py)、[故意失败/原打印](../复现/outputs/contracts_stdout.txt)、[旧demo](../复现/outputs/results.json)、[一致性结果](../复现/outputs/skill_revision_check.json)。

复现状态：**部分成功**。当前解读及小机制边界已修订核查，真实LLM/MiniLM/Chroma、原QA表格及性能未复现。九篇整体还需LoCoMo/LongMemEval，不能只据本篇结束目标。