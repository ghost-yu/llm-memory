# MemGPT 小 demo 运行说明

直接执行固定历史提交的 CoreMemory 和五个工具函数，配合本地 SQLite adapter 与确定性控制器。不是 LLM、不运行完整 Agent、不代表论文准确率。详见[解释.md](../解释.md)。

## 环境与命令

已验证 Python 3.12.14，主脚本只用标准库。它通过 AST 提取依赖独立原类/函数体；原包 pymemgpt 0.3.1 声明 Python >=3.10,<3.12，因此不能说旧包已安装或整体兼容 Python 3.12。

在 G:\大模型记忆 的 PowerShell 执行：

~~~powershell
$p=Get-ChildItem -Directory | Where-Object Name -like 'MemGPT*'
& 'C:\Users\hgfhg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' ($p.FullName+'\复现\scripts\demo_memgpt.py')
python ($p.FullName+'\复现\scripts\plot_demo.py')
~~~

第一步用 bundled Python 运行主实验。第二步用已有 Anaconda Python 3.7.6、Matplotlib 3.1.3 和 NumPy 读取 JSON 绘图。没有模型 API、API key、embedding、网络或 GPU。requirements.txt 说明两个环境的范围，未安装完整历史依赖。

每次主运行创建新的 memory-随机后缀.sqlite，保留旧数据库；JSON 和图表指向最近一次运行。源代码位于 ../代码/MemGPT-historical，HEAD 锁定 a0139b5fdc203f827168cb741c9f4fea3cec09bf，函数体未改写。代码版本对应论文 v2 发布日附近，未证明精确生成论文表格。

## 数据和范围

本地字符预算 1,200，core persona/human 上限 100/200 字符，page size=5。字符预算不是 token 预算。SQLite 使用字符串匹配，不是原 semantic search。固定时间戳是合成数据。

先验证 core append、replace、超限错误和转存，再写一条 Aster secret code 与 40 条填充消息。旧记录移出当前上下文后，经原 conversation_search 工具重新读回。

多跳 KV：边数 1—4，各 5 次，固定 seed=2026 的随机 UUID。每条真正 key 前插入 7 条提及它的干扰记录，把正确条目放到后续页；再加入噪声移出初始上下文。控制器只从工具返回的 Key/Value 动态决定下一 key，不读取 gold 作为答案。

只查第一页、只允许一次调用都为 0/20，完整分页+函数链为 20/20。这是构造性工具流程核验，不是 LLM 自主规划、自然语言检索或真实记忆准确率。max_calls=1 是本地工具预算对照，不是完整官方 heartbeat 消融。

## 实测与检查

core 从 Beijing 改成 Hangzhou；超限 append 失败后旧值不变。最大观察上下文 1,191 字符，换出 1,005 个 atomic block，988 次压力计数。一个工具调用及其回复作为整块换出。

摘要只记换出数量，不执行 LLM summarization。压力仅计数，不由 LLM 接收后自主处理。OfflineHost.rebuild_memory 计数，context 动态读 core 字符串；没有执行原 Agent.rebuild_memory。

主实验退出码 0。关闭数据库、创建新 host、恢复 JSON 后，core、Aster recall 和最后 KV 链均正确恢复。

- [主脚本](scripts/demo_memgpt.py)与[绘图脚本](scripts/plot_demo.py)。
- [原始结果](outputs/demo_results.json)：原符号来源散列、环境、20 个任务、分页轨迹。
- [状态 JSON](outputs/memory_state.json)：core、队列与摘要；SQLite 名称见原始结果的 database_file。
- [PNG](outputs/demo_summary.png)与[SVG](outputs/demo_summary.svg)。
- [交付检查](outputs/delivery_check.json)：版本、文件、链接、DB 内容及结果核验。

复现状态：部分成功。机制精读和小 demo 完成；完整历史包运行、自主 LLM、tokenizer、embedding/HNSW、递归摘要及论文 MSC/Wikipedia 指标未复现。

## 本轮原函数契约与历史后端边界检查

~~~powershell
$p=Get-ChildItem -Directory | Where-Object Name -like 'MemGPT*'
& 'C:\Users\hgfhg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' ($p.FullName+'\复现\scripts\trace_contracts.py')
& 'C:\Users\hgfhg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' ($p.FullName+'\复现\scripts\audit_skill_revision.py')
& 'C:\Users\hgfhg\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '资料\check_memgpt.py'
~~~

第一步导入教学模块及选定原函数体，记录33个真实签名，检查core编辑/限长/恢复、工具返回/错误事件、分页与JSON/SQLite。临时数据库建在TemporaryDirectory里，退出清理临时probe，原交付DB和结果不改。它还直接执行历史EmbeddingArchivalMemory.search原方法体，使用12条预填充假Passage缓存；不请求embedding/向量数据库。第二步核查来源哈希、原checkout、运行证据、文档结构和链接，不自动判定中文语义合格。第三步重新检查原20条查询轨迹、原SQLite记录与版本。

实测第一步退出码0：PASS: 18 contract/boundary checks; 33 actual signatures。证据见[contracts_trace.json](outputs/contracts_trace.json)、[skill_revision_check.json](outputs/skill_revision_check.json)和[内容核查](../资料/skill内容核查.md)。CoreMemory.load不恢复limits的事实已观察；custom restore才显式重新限制。新错误用例保留真实ValueError/KeyError，旧core不变。

关键修订：历史原search对12候选返回5条且total=5，原工具页头变为page0/0；手动查下一页仍有候选。SQLite adapter返回真实total=12，页头page0/2。因此旧20/20不覆盖原后端的该接口问题。Agent.step注解为4元组，但源码实际返回5项，新AST记录也为5。完整Agent/parser/API仍未运行，也未修改原历史源码。

资源记录：Windows 11专业版；本工作区机器约15.69 GiB可见RAM、G盘空闲37.31 GiB。新检查为标准库CPU、秒级小运行，少量临时SQLite文件，不加载模型、下载数据或调用GPU/API。与完整历史包的Python约束和依赖独立，不能由本次通过认定旧包支持3.12或原API今天可重跑。

首次新增文件核验将源码块中的函数调用语法误识别成Markdown链接，导致静态链接检查失败；已让链接检查忽略~~~代码块后重跑。它是核验器的解析误报，不是原工具执行失败。
